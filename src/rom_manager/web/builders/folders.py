"""Folder-analysis response builders: junk scan + non-gaming folder breakdown.

Pure functions: typed params → JSON-ready dicts. No global job state.
"""

from __future__ import annotations

import logging
import os as _os
import re as _re
from collections import Counter
from pathlib import Path as _Path

from rom_manager.config import AppConfig

_logger = logging.getLogger(__name__)


def _build_junk_scan(folder_path: str) -> dict:
    """Scan a folder and classify non-gaming files as junk."""
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
        ".bin",
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
        ".rom",
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
    # (regla del proyecto) — ninguno es objetivo de la limpieza de basura
    _excluded_dirs = {"saves", "bios", "android"}

    for dirpath, dirs, files in _os.walk(p):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d.lower() not in _excluded_dirs]
        for fname in files:
            fpath = _Path(dirpath) / fname
            ext = fpath.suffix.lower()
            if ext in _GAMING_EXTS or ext in _CONFIG_EXTS or _numbered_state.match(ext):
                continue
            cat = _JUNK_CATEGORIES.get(ext, f"Otros ({ext or 'sin extensión'})")
            try:
                size = fpath.stat().st_size
            except OSError:
                size = 0
            total_junk_bytes += size
            if cat not in categories:
                categories[cat] = []
            try:
                rel = str(fpath.relative_to(p))
            except ValueError:
                rel = str(fpath)
            categories[cat].append({"path": rel, "full_path": str(fpath), "size_bytes": size})

    cat_list = []
    for cat, files_list in sorted(
        categories.items(), key=lambda x: -sum(f["size_bytes"] for f in x[1])
    ):
        total = sum(f["size_bytes"] for f in files_list)
        cat_list.append(
            {
                "category": cat,
                "count": len(files_list),
                "total_bytes": total,
                "files": sorted(files_list, key=lambda f: -f["size_bytes"])[:50],
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
        elif ext in {".jpg", ".jpeg", ".png", ".webp", ".xml", ".txt", ".cfg", ".db"}:
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
