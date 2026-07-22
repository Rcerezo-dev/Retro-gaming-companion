"""Folder-analysis response builders: junk scan + non-gaming folder breakdown.

Pure functions: typed params → JSON-ready dicts. No global job state.
"""

from __future__ import annotations

import logging
import os as _os
import re as _re
import zipfile as _zipfile
from collections import Counter
from pathlib import Path as _Path

import rom_manager.detection.platform_detector as _platform_detector
from rom_manager.config import AppConfig
from rom_manager.detection.platform_detector import PLATFORM_BY_FOLDER
from rom_manager.utils.media_types import IMAGE_EXTS
from rom_manager.web.handlers.system import _ES_PLATFORM_FOLDERS

_logger = logging.getLogger(__name__)

# JUNK-FIX-4: container/arcade extensions that are legitimate ROMs only in the
# right folder context — a .zip loose in Unknown\ is still unprocessed, but a
# .zip inside snes\/arcade\/etc. *is* the ROM (RetroArch loads zips directly;
# arcade cores require the archive itself, see zip_extractor._ARCADE_FOLDER_NAMES).
_CONTEXT_GAMING_EXTS = {".zip", ".rar", ".7z", ".fs"}

# Union of both folder-name sources: PLATFORM_BY_FOLDER (synonyms used for
# ambiguous-extension detection, e.g. "jaguar") and _ES_PLATFORM_FOLDERS values
# (the actual slugs the app organizes into, e.g. "atarijaguar") — the two don't
# fully agree, and a real ROM can legitimately sit under either spelling.
_RECOGNIZED_PLATFORM_FOLDERS = set(PLATFORM_BY_FOLDER) | {
    v.lower() for v in _ES_PLATFORM_FOLDERS.values()
}

# JUNK-SMART-1: .bin/.rom are gaming extensions but also the classic disguise of
# loose arcade-romset chips (Día39: 3.309 chips u082.bin-style passed the
# whitelist clean). They only get flagged when the evidence agrees: no catalog
# match in the DB, chip-style name, no .cue sibling, and small file.
_CHIP_CANDIDATE_EXTS = {".bin", ".rom"}
_CHIP_MAX_BYTES = 8 * 1024 * 1024  # every chip found in JUNK-CLEAN-1 was ≤8 MB
# ponytail: naive stem heuristic (u082, ic12, mpr-12345a…); it also matches
# bare numeric titles like "1942" — acceptable because the category is
# review-only, never auto-delete (JUNK-SMART-3 tags it `review`)
_CHIP_STEM = _re.compile(r"^[a-z0-9]{0,4}[-_.]?\d{1,5}[a-z]{0,2}$", _re.IGNORECASE)
_CHIP_CATEGORY = "Chips sueltos (sin match en catálogo)"

# JUNK-SMART-2: subcategorías de ZIPs sueltos fuera de carpeta de plataforma,
# clasificados con lo que la app ya sabe (catálogo arcade, XML de MAME,
# _KNOWN_BIOS_MAP). Sin evidencia siguen en "ZIPs no-ROM".
_ZIP_CAT_BIOS = "BIOS conocidas (mover a bios/, no borrar)"
_ZIP_CAT_INFRA = "Infraestructura MAME (bios/devices, no jugable)"
_ZIP_CAT_ARCADE = "ROMs arcade sin organizar (no borrar)"
_ZIP_CAT_COLLECTION = "Colecciones fuente (revisar)"
# ZIP-ROUTE-1: ZIP con una sola entrada cuyo CRC (leído del header, sin
# descomprimir) está en No-Intro/Redump → juego de consola con identidad exacta
_ZIP_CAT_CONSOLE = "ROMs de consola identificadas (mover a su plataforma)"
# ZIP-ROUTE-5: colección fuente = contenedor con mayoría de .zip/.chd dentro.
# Sustituye la heurística por nombre (" - " daba ~39 falsos positivos de 56:
# juegos sueltos tipo "Fire Emblem - ..." caían como colecciones).
_NESTED_ROM_EXTS = {".zip", ".chd"}
# ZIP-ROUTE-2: sets arcade identificados votando los CRC de las entradas contra
# los DAT arcade. Cobertura total → renombrar al nombre de set y mover (los
# cores arcade piden el ZIP intacto con el nombre exacto del set); cobertura
# parcial → probablemente el mismo juego de otra versión de romset (puede no
# arrancar en el core instalado) → revisar.
_ZIP_CAT_ARCADE_IDENT = "ROMs arcade identificadas (renombrar al set y mover)"
_ZIP_CAT_ARCADE_OTHER = "Sets arcade de otra versión (revisar)"
# ZIP-ROUTE-3: sin CRC en ningún DAT (romhack/traducción parcheada) pero con
# una sola entrada de extensión inequívoca → la plataforma la da la extensión
_ZIP_CAT_ROMHACK = "ROMs/romhacks por extensión (mover a su plataforma)"

# ZIP-ROUTE-4: categorías con identidad/destino — el job de colocación necesita
# los metadatos (identified_as/platform) de TODOS sus archivos, no solo de los
# 50 que se muestran; son categorías pequeñas por naturaleza (decenas).
_ZIP_ROUTE_CATS = {
    _ZIP_CAT_BIOS,
    _ZIP_CAT_ARCADE,
    _ZIP_CAT_COLLECTION,
    _ZIP_CAT_CONSOLE,
    _ZIP_CAT_ARCADE_IDENT,
    _ZIP_CAT_ARCADE_OTHER,
    _ZIP_CAT_ROMHACK,
}

# JUNK-SMART-3: confianza por categoría. safe_delete = basura por extensión
# (tier 0, borrable en masa); review = probable basura pero mirar antes
# (lección de INBOX-FIX-5); misplaced = NO es basura, hay que mover/organizar.
_CATEGORY_CONFIDENCE = {
    _CHIP_CATEGORY: "review",
    _ZIP_CAT_INFRA: "review",
    _ZIP_CAT_COLLECTION: "review",
    "ZIPs no-ROM": "review",
    "RARs": "review",
    "7-Zips": "review",
    _ZIP_CAT_BIOS: "misplaced",
    _ZIP_CAT_ARCADE: "misplaced",
    _ZIP_CAT_CONSOLE: "misplaced",
    _ZIP_CAT_ARCADE_IDENT: "misplaced",
    _ZIP_CAT_ARCADE_OTHER: "review",
    _ZIP_CAT_ROMHACK: "misplaced",
}


def _zip_entries(fpath: _Path) -> list[_zipfile.ZipInfo] | None:
    """Entradas (no-directorio) del ZIP, o None si no se puede abrir."""
    try:
        with _zipfile.ZipFile(fpath) as z:
            return [i for i in z.infolist() if not i.is_dir()]
    except (OSError, _zipfile.BadZipFile):
        return None


def _is_source_collection(infos: list[_zipfile.ZipInfo]) -> bool:
    """ZIP-ROUTE-5: varias entradas y la mayoría son .zip/.chd anidados."""
    nested = sum(1 for i in infos if _os.path.splitext(i.filename)[1].lower() in _NESTED_ROM_EXTS)
    return len(infos) > 1 and nested * 2 >= len(infos)


def _vote_arcade_set(
    infos: list[_zipfile.ZipInfo], arcade_crc_index: dict[str, set[str]]
) -> tuple[str, float] | None:
    """ZIP-ROUTE-2: (mejor set, cobertura 0-1) votando los CRC de las entradas,
    o None si ningún CRC vota. Cobertura 1.0 = todas las entradas pertenecen
    al set → identidad segura; parcial = otra versión de romset, revisar."""
    votes: Counter[str] = Counter()
    for i in infos:
        if i.file_size == 0:  # un archivo vacío (CRC 0) votaría a sets espurios
            continue
        for set_name in arcade_crc_index.get(f"{i.CRC:08X}", ()):
            votes[set_name] += 1
    if not votes:
        return None
    best, count = votes.most_common(1)[0]
    return best, count / len(infos)


def _single_rom_platform(infos: list[_zipfile.ZipInfo]) -> str | None:
    """ZIP-ROUTE-3: plataforma por la extensión de la única entrada del ZIP.

    Para romhacks/traducciones: el ROM parcheado no tiene CRC en ningún DAT,
    pero un ``.sfc``/``.gba``/… dentro identifica la plataforma sin dudas.
    Las extensiones con contexto (``.md`` = ¿Mega Drive o markdown?) se
    excluyen: dentro de un ZIP no hay carpeta que desambigüe.
    """
    if len(infos) != 1:
        return None
    ext = _os.path.splitext(infos[0].filename)[1].lower()
    if ext in _platform_detector.PLATFORM_CONTEXT_BY_EXTENSION:
        return None
    return _platform_detector.PLATFORM_BY_EXTENSION.get(ext)


def _build_junk_scan(
    folder_path: str,
    matched_paths: set[str] | None = None,
    arcade_names: set[str] | None = None,
    mame_infra_names: set[str] | None = None,
    known_bios_files: set[str] | None = None,
    crc_index: dict[str, tuple[str, str, str | None]] | None = None,
    arcade_crc_index: dict[str, set[str]] | None = None,
) -> dict:
    """Scan a folder and classify non-gaming files as junk.

    *matched_paths* (JUNK-SMART-1) enables the evidence tier: normalized
    lowercase paths of files with a catalog match in the DB. With it, unmatched
    .bin/.rom files that look like loose romset chips get their own category;
    without it (``None``) those extensions are skipped as before — the setup
    pipeline deletes everything this returns, so the tier stays off there.

    *arcade_names* (JUNK-SMART-2) enables loose-ZIP classification (empty sets
    are fine — ``None`` keeps everything in "ZIPs no-ROM" as before):
    lowercase stems of playable arcade sets; *mame_infra_names* are the
    BIOS/device/non-runnable stems from the MAME XML; *known_bios_files* are
    lowercase filenames from ``_KNOWN_BIOS_MAP``.

    *crc_index* (ZIP-ROUTE-1) enables exact console-ROM identification for
    loose single-entry ZIPs via the CRC32 already stored in the ZIP header
    (``CatalogMatcher.crc_index()``); ``None`` keeps the previous behavior.

    *arcade_crc_index* (ZIP-ROUTE-2, ``load_arcade_crc_index``) identifies
    renamed arcade sets by voting entry CRCs; ``None`` disables the pass.
    """
    _GAMING_EXTS = {
        ".gba",
        ".gb",
        ".gbc",
        ".nes",
        ".sfc",
        ".smc",
        ".md",
        ".smd",
        ".sms",
        ".gen",
        ".n64",
        ".z64",
        ".v64",
        ".nds",
        ".3ds",
        ".iso",
        ".chd",
        ".cue",
        # .bin/.rom viven en _CHIP_CANDIDATE_EXTS (tier de evidencia), no aquí
        ".cdi",
        ".gdi",
        ".pbp",
        ".gcm",
        ".rvz",
        ".nsp",
        ".xci",
        ".pce",
        ".ws",
        ".wsc",
        ".ngc",
        ".ngp",
        ".gg",
        ".lynx",
        ".a26",
        ".a52",
        ".a78",
        ".col",
        ".vb",
        ".img",
        ".mdf",
        ".ecm",
        ".nrg",
        ".ccd",
        ".bios",
        ".sav",
        ".srm",
        ".state",
        ".sta",
        ".ml1",
        ".mcr",
        ".mc",
        ".mem",
        ".rtc",
        ".xml",
        ".m3u",
        ".png",
        ".jpg",
        ".jpeg",
        ".mp4",
        ".webp",
        ".sgm",
        ".nv",
        ".brm",
        ".brmc",
        ".fds",
        ".crt",
        ".prg",
        ".fx",
        ".hi",
    }
    _CONFIG_EXTS = {
        ".cfg",
        ".ini",
        ".toml",
        ".json",
        ".txt",
        ".sh",
        ".bat",
        ".conf",
        ".opt",
        ".ovr",
        ".rmp",
    }
    _JUNK_CATEGORIES: dict[str, str] = {
        ".ipynb": "Jupyter Notebooks",
        ".py": "Scripts Python",
        ".js": "Scripts JavaScript",
        ".xlsx": "Excel",
        ".xls": "Excel",
        ".docx": "Word",
        ".doc": "Word",
        ".pptx": "PowerPoint",
        ".ppt": "PowerPoint",
        ".pdf": "PDFs",
        ".zip": "ZIPs no-ROM",
        ".rar": "RARs",
        ".7z": "7-Zips",
        ".tar": "Tarballs",
        ".gz": "Tarballs",
        ".bz2": "Tarballs",
        ".exe": "Ejecutables",
        ".dll": "Ejecutables",
        ".apk": "APKs Android",
        ".mp3": "Audio",
        ".flac": "Audio",
        ".ogg": "Audio",
        ".wav": "Audio",
        ".avi": "Vídeo (no-gaming)",
        ".mkv": "Vídeo (no-gaming)",
        ".mov": "Vídeo (no-gaming)",
        ".psd": "Imágenes editables",
        ".ai": "Imágenes editables",
        ".svg": "SVGs",
        ".html": "HTML/Web",
        ".css": "HTML/Web",
        ".log": "Logs",
        ".db": "Bases de datos",
        ".sqlite": "Bases de datos",
    }

    p = _Path(folder_path)
    if not p.is_dir():
        return {"error": f"Carpeta no encontrada: {folder_path}"}

    categories: dict[str, list[dict]] = {}
    total_junk_bytes = 0

    # Savestates numerados de RetroArch (.state1, .state23…) — solo .state está
    # en la whitelist y los slots extra salían como falsos positivos
    _numbered_state = _re.compile(r"\.state\d+$")

    # saves/ lo gestiona el sync; BIOS/ y Android/ nunca se tratan como ROMs
    # (regla del proyecto) — ninguno es objetivo de la limpieza de basura.
    # "System Volume Information" es una carpeta de sistema de Windows —
    # tocarla puede dar "acceso denegado" y nunca es contenido del usuario.
    _excluded_dirs = {"saves", "bios", "android", "system volume information"}

    for dirpath, dirs, files in _os.walk(p):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d.lower() not in _excluded_dirs]
        rel_parts = _Path(dirpath).relative_to(p).parts
        in_platform_folder = any(part.lower() in _RECOGNIZED_PLATFORM_FOLDERS for part in rel_parts)
        dir_has_cue = any(f.lower().endswith(".cue") for f in files)
        for fname in files:
            fpath = _Path(dirpath) / fname
            ext = fpath.suffix.lower()
            identified: tuple[str, str, str | None] | None = None
            arcade_vote: tuple[str, float] | None = None
            hack_platform: str | None = None
            if ext in _CHIP_CANDIDATE_EXTS:
                # Tier de evidencia (JUNK-SMART-1): extensión gaming, pero si la BD
                # no lo reconoce y todo apunta a chip suelto, va a categoría propia
                if matched_paths is None:
                    continue
                if _os.path.normpath(str(fpath)).lower() in matched_paths:
                    continue
                if dir_has_cue or not _CHIP_STEM.match(fpath.stem):
                    continue
                cat = _CHIP_CATEGORY
            elif ext == ".zip" and not in_platform_folder and arcade_names is not None:
                # JUNK-SMART-2: un ZIP suelto se clasifica por lo que ya sabemos de él
                stem = fpath.stem.lower()
                if known_bios_files and fname.lower() in known_bios_files:
                    cat = _ZIP_CAT_BIOS
                elif mame_infra_names and stem in mame_infra_names:
                    cat = _ZIP_CAT_INFRA
                elif stem in arcade_names:
                    cat = _ZIP_CAT_ARCADE
                else:
                    # ZIP-ROUTE-1/5: el contenido manda sobre el nombre — los
                    # tags del nombre mienten ("(XBLA)", "(Disk 1)" envuelven
                    # ROMs normales) y " - " en el título daba falsas colecciones
                    infos = _zip_entries(fpath)
                    if infos and len(infos) == 1 and crc_index is not None:
                        identified = crc_index.get(f"{infos[0].CRC:08X}")
                    if identified:
                        cat = _ZIP_CAT_CONSOLE
                    elif infos and _is_source_collection(infos):
                        cat = _ZIP_CAT_COLLECTION
                    else:
                        # ZIP-ROUTE-2: sin identidad de consola ni pinta de
                        # colección → votar los CRC contra los sets arcade
                        if infos and arcade_crc_index:
                            arcade_vote = _vote_arcade_set(infos, arcade_crc_index)
                        if arcade_vote and arcade_vote[1] == 1.0:
                            cat = _ZIP_CAT_ARCADE_IDENT
                        elif arcade_vote:
                            cat = _ZIP_CAT_ARCADE_OTHER
                        else:
                            # ZIP-ROUTE-3: romhack — plataforma por extensión
                            hack_platform = _single_rom_platform(infos) if infos else None
                            if hack_platform:
                                cat = _ZIP_CAT_ROMHACK
                            else:
                                cat = _JUNK_CATEGORIES[".zip"]
            else:
                if ext in _GAMING_EXTS or ext in _CONFIG_EXTS or _numbered_state.match(ext):
                    continue
                if ext in _CONTEXT_GAMING_EXTS and in_platform_folder:
                    continue
                cat = _JUNK_CATEGORIES.get(ext, f"Otros ({ext or 'sin extensión'})")
            try:
                size = fpath.stat().st_size
            except OSError:
                size = 0
            if cat == _CHIP_CATEGORY and size > _CHIP_MAX_BYTES:
                continue
            total_junk_bytes += size
            if cat not in categories:
                categories[cat] = []
            try:
                rel = str(fpath.relative_to(p))
            except ValueError:
                rel = str(fpath)
            item = {"path": rel, "full_path": str(fpath), "size_bytes": size}
            if identified:
                item["identified_as"], item["dat"], item["platform"] = identified
            elif arcade_vote:
                item["identified_as"] = arcade_vote[0]
                item["coverage"] = round(arcade_vote[1], 2)
            elif hack_platform:
                item["platform"] = hack_platform
            categories[cat].append(item)

    cat_list = []
    for cat, files_list in sorted(
        categories.items(), key=lambda x: -sum(f["size_bytes"] for f in x[1])
    ):
        total = sum(f["size_bytes"] for f in files_list)
        display_cap = None if cat in _ZIP_ROUTE_CATS else 50
        cat_list.append(
            {
                "category": cat,
                "confidence": _CATEGORY_CONFIDENCE.get(cat, "safe_delete"),
                "count": len(files_list),
                "total_bytes": total,
                "files": sorted(files_list, key=lambda f: -f["size_bytes"])[:display_cap],
                # Todas las rutas de la categoría (files se corta a 50 solo para mostrar);
                # /api/junk-delete necesita la lista completa
                "paths": [f["full_path"] for f in files_list],
            }
        )

    return {
        "folder": folder_path,
        "total_junk_files": sum(c["count"] for c in cat_list),
        "total_junk_bytes": total_junk_bytes,
        "categories": cat_list,
    }


def _build_folder_analysis(folder_path: str, config: AppConfig) -> dict:
    """Analyse a folder: count extensions, find broken PSX sets, flag conversion needs."""
    _ROM_EXTS = {
        ".gba",
        ".gb",
        ".gbc",
        ".nes",
        ".snes",
        ".sfc",
        ".md",
        ".smd",
        ".gen",
        ".n64",
        ".z64",
        ".v64",
        ".nds",
        ".3ds",
        ".psx",
        ".ps1",
        ".iso",
        ".chd",
        ".cue",
        ".bin",
        ".cdi",
        ".gdi",
        ".pbp",
        ".elf",
        ".gcm",
        ".nkit",
        ".rvz",
        ".wbfs",
        ".nsp",
        ".xci",
    }
    _SAVE_EXTS = {".sav", ".srm", ".state", ".sta", ".mcr", ".mc"}
    _NEEDS_CONVERSION = {
        ".img": "imagen de disco — puede ser CD-ROM (.img/.ccd) o HDD; verificar si acompaña .ccd/.sub",
        ".mdf": "imagen Alcohol 120% — convertir a .chd o .cue/.bin con mdf2iso",
        ".mds": "descriptor Alcohol 120% — acompaña .mdf",
        ".ccd": "CloneCD descriptor — convertir a .chd con chdman",
        ".sub": "datos de subcódigo CloneCD — acompaña .ccd/.img",
        ".nrg": "imagen Nero — convertir a .iso o .chd",
        ".ecm": "Error Code Modeler — descomprimir con ecmtools antes de convertir a CHD",
    }

    p = _Path(folder_path)
    if not p.is_dir():
        return {
            "error": f"Carpeta no encontrada: {folder_path}",
            "extensions": [],
            "cue_missing_bin": [],
            "bin_orphan": [],
            "needs_conversion": [],
        }

    ext_counter: Counter[str] = Counter()
    cue_files: list[_Path] = []
    bin_files: set[str] = set()

    for f in p.rglob("*"):
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        ext_counter[ext] += 1
        if ext == ".cue":
            cue_files.append(f)
        elif ext == ".bin":
            bin_files.add(f.stem.lower())

    extensions = []
    for ext, count in sorted(ext_counter.items(), key=lambda x: -x[1]):
        if ext in _ROM_EXTS:
            cat = "rom"
        elif ext in _SAVE_EXTS:
            cat = "save"
        elif ext in _NEEDS_CONVERSION:
            cat = "needs_conversion"
        elif ext in IMAGE_EXTS | {".xml", ".txt", ".cfg", ".db"}:
            cat = "asset/meta"
        else:
            cat = "unknown"
        extensions.append({"ext": ext or "(sin extensión)", "count": count, "category": cat})

    cue_missing_bin: list[str] = []
    for cue in cue_files:
        try:
            text = cue.read_text(errors="replace")
            bins_referenced = _re.findall(r'FILE\s+"?([^"]+\.bin)"?', text, _re.IGNORECASE)
            for bin_name in bins_referenced:
                if not (cue.parent / bin_name).exists():
                    cue_missing_bin.append(cue.name)
                    break
        except OSError:
            pass

    cue_stems = {c.stem.lower() for c in cue_files}
    bin_orphan = [
        f.name for f in p.rglob("*.bin") if f.is_file() and f.stem.lower() not in cue_stems
    ]
    needs_conversion = [
        {"ext": ext, "note": note} for ext, note in _NEEDS_CONVERSION.items() if ext in ext_counter
    ]

    return {
        "folder": folder_path,
        "extensions": extensions,
        "cue_missing_bin": sorted(cue_missing_bin),
        "bin_orphan": sorted(bin_orphan),
        "needs_conversion": needs_conversion,
    }
