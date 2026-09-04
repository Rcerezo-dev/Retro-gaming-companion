"""Loaders for arcade ROM catalogs (MAME XML and FBNeo/Logiqx DAT).

Both return a dict of ``{stem_lowercase: (title, year, manufacturer)}``
where *stem* is the canonical MAME set name (= ZIP filename without extension).

Usage
-----
- MAME listxml: generated with ``mame -listxml > mame.xml``
- FBNeo DAT: downloaded from https://github.com/libretro/FBNeo/tree/master/dats
"""

from __future__ import annotations

import itertools
import re as _re
import xml.etree.ElementTree as ET
from pathlib import Path


def load_mame_xml(path: Path) -> dict[str, tuple[str, str, str]]:
    """Parse a MAME listxml file.

    Returns ``{name: (description, year, manufacturer)}``.
    Skips BIOS, devices, and non-runnable entries to keep the index lean.
    Clones are included (they have their own set name and description).
    """
    result: dict[str, tuple[str, str, str]] = {}
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        # ARCADE-RENAME-BUG-1a: el tag de hijo real (<machine> vs <game>) no se
        # puede inferir del tag raíz -- "MAME 2003-Plus.dat" real tiene
        # root.tag == "mame" con hijos <game>, no <machine>, y el guess
        # anterior devolvía 0 machines en silencio para ese DAT. Encadenar
        # ambos iteradores cubre los dos formatos sin adivinar.
        machines = itertools.chain(root.iter("machine"), root.iter("game"))
        for machine in machines:
            if machine.get("isbios") == "yes" or machine.get("isdevice") == "yes":
                continue
            if machine.get("runnable") == "no":
                continue
            name = machine.get("name", "").strip().lower()
            if not name:
                continue
            desc_el = machine.find("description")
            description = desc_el.text.strip() if desc_el is not None and desc_el.text else name
            year_el = machine.find("year")
            year = year_el.text.strip() if year_el is not None and year_el.text else ""
            mfr_el = machine.find("manufacturer")
            manufacturer = mfr_el.text.strip() if mfr_el is not None and mfr_el.text else ""
            result[name] = (description, year, manufacturer)
    except (ET.ParseError, OSError):
        pass
    return result


def load_fbneo_dat(path: Path) -> dict[str, tuple[str, str, str]]:
    """Parse an FBNeo / Logiqx DAT file.

    These use ``<game name="sf2" description="Street Fighter II…">`` —
    we index by the *name* attribute (= ZIP stem), not by ROM SHA1.
    Returns ``{name: (description, year, manufacturer)}``.
    """
    result: dict[str, tuple[str, str, str]] = {}
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        for game in root.iter("game"):
            name = game.get("name", "").strip().lower()
            if not name:
                continue
            description = (game.get("description") or "").strip() or name
            year = (game.get("year") or "").strip()
            manufacturer = (game.get("manufacturer") or "").strip()
            result[name] = (description, year, manufacturer)
    except (ET.ParseError, OSError):
        pass
    return result


# INICIO-FIX-2: el listxml oficial de MAME pesa cientos de MB (~11 s de parseo)
# y esto se llama en cada junk-scan y cada refresh de /api/library-extras —
# memoizar por firma de los .xml del directorio (nombre, mtime, tamaño).
_infra_cache: dict[Path, tuple[tuple, set[str]]] = {}


def load_arcade_infra_names(directory: Path) -> set[str]:
    """Set names that ``load_mame_xml`` skips: BIOS, devices, non-runnable.

    These are the loose ZIPs in an unorganized library that will never match
    the playable catalog (JUNK-SMART-2) — c1541.zip, kb_pcat101.zip, sb16.zip…
    Only MAME XML carries the flags; FBNeo DATs are ignored.
    """
    names: set[str] = set()
    if not directory.exists():
        return names
    xml_files = sorted(f for f in directory.iterdir() if f.suffix.lower() == ".xml")
    try:
        sig: tuple | None = tuple(
            (f.name, f.stat().st_mtime_ns, f.stat().st_size) for f in xml_files
        )
    except OSError:
        sig = None  # archivo desaparecido a mitad — parsear sin cachear
    cached = _infra_cache.get(directory)
    if sig is not None and cached and cached[0] == sig:
        return cached[1]
    for f in xml_files:
        try:
            tree = ET.parse(f)
            root = tree.getroot()
            machines = root.iter("machine") if root.tag != "datafile" else root.iter("game")
            for machine in machines:
                if (
                    machine.get("isbios") == "yes"
                    or machine.get("isdevice") == "yes"
                    or machine.get("runnable") == "no"
                ):
                    name = machine.get("name", "").strip().lower()
                    if name:
                        names.add(name)
        except (ET.ParseError, OSError):
            pass
    if sig is not None:
        _infra_cache[directory] = (sig, names)
    return names


_NON_ARCADE_DAT_RE = _re.compile(r"\bonly\)", _re.IGNORECASE)
_ARCADE_ONLY_DAT_RE = _re.compile(r"\barcade only\)", _re.IGNORECASE)


def _is_console_only_dat(filename: str) -> bool:
    """ARCADE-DAT-CONTAMINATION-2: True si *filename* es un DAT de FBNeo para
    un núcleo de CONSOLA (p. ej. ``FinalBurn Neo (..., Game Gear only).dat``),
    no de arcade.

    FBNeo publica DATs "solo esta plataforma" para cada núcleo que emula,
    arcade incluido — si alguno de los de consola acaba en el mismo
    directorio que los de arcade (fácil: se descargan del mismo repo), sus
    CRCs contaminan ``load_arcade_crc_index``/``load_arcade_manifest`` y un
    ZIP de esa consola puede votar como "set arcade completo". Un DAT
    termina en "..., X only).dat" para cualquier X — el único que debe
    contar como arcade es el que dice literalmente "Arcade only)".
    """
    return bool(_NON_ARCADE_DAT_RE.search(filename)) and not _ARCADE_ONLY_DAT_RE.search(filename)


def load_arcade_crc_index(directory: Path) -> dict[str, set[str]]:
    """``crc32_upper → {set names}`` de los DAT arcade (Logiqx: ``<rom crc>``).

    ZIP-ROUTE-2: identifica un ZIP arcade renombrado votando los CRC de sus
    entradas (el header del ZIP ya los trae, sin descomprimir). Un CRC puede
    vivir en varios sets (parent/clones), por eso el valor es un set de
    nombres y la identidad la decide la cobertura de votos, no un hit suelto.
    Solo se leen los ``.dat``; el listxml de MAME no lleva una lista de roms
    fiable para esto y parsear sus cientos de MB solo para CRCs es caro.
    """
    index: dict[str, set[str]] = {}
    if not directory.exists():
        return index
    for f in sorted(directory.iterdir()):
        if f.suffix.lower() != ".dat" or _is_console_only_dat(f.name):
            continue
        try:
            for _, elem in ET.iterparse(str(f)):
                if elem.tag in ("game", "machine"):
                    name = elem.get("name", "").strip().lower()
                    if name:
                        for rom in elem.findall("rom"):
                            crc = (rom.get("crc") or "").strip().upper()
                            if crc:
                                index.setdefault(crc, set()).add(name)
                    elem.clear()
        except (ET.ParseError, OSError):
            pass
    return index


def load_arcade_manifest(directory: Path) -> dict[str, list[tuple[str, str, int]]]:
    """``machine_name → [(rom_name, crc32_upper, size_bytes), …]`` de los DAT arcade.

    ARCADE-RECON-1: complementa a ``load_arcade_crc_index()`` (que solo dice
    "este CRC vive en estos sets") con la lista completa de roms esperados
    por máquina — necesaria para calcular cobertura (¿están TODOS los chips
    de un set entre los sueltos del Inbox, no solo uno?). Mismo recorrido
    que ``load_arcade_crc_index``; se deja como función aparte porque cada
    caller normalmente solo necesita una de las dos vistas.
    """
    manifest: dict[str, list[tuple[str, str, int]]] = {}
    if not directory.exists():
        return manifest
    for f in sorted(directory.iterdir()):
        if f.suffix.lower() != ".dat" or _is_console_only_dat(f.name):
            continue
        try:
            for _, elem in ET.iterparse(str(f)):
                if elem.tag in ("game", "machine"):
                    name = elem.get("name", "").strip().lower()
                    if name:
                        roms = []
                        for rom in elem.findall("rom"):
                            crc = (rom.get("crc") or "").strip().upper()
                            if not crc:
                                continue
                            roms.append((rom.get("name", ""), crc, int(rom.get("size") or 0)))
                        if roms:
                            # Un mismo nombre de máquina puede aparecer en varios DAT
                            # (MAME propio + FBNeo "Arcade only" se solapan mucho) —
                            # sin deduplicar, un chip compartido cuenta dos veces y
                            # ARCADE-RECON exigiría dos copias físicas del mismo chip.
                            existing = manifest.setdefault(name, [])
                            seen = set(existing)
                            for rom in roms:
                                if rom not in seen:
                                    existing.append(rom)
                                    seen.add(rom)
                    elem.clear()
        except (ET.ParseError, OSError):
            pass
    return manifest


def load_arcade_dir(directory: Path) -> dict[str, tuple[str, str, str, str]]:
    """Load all arcade catalog files from *directory*.

    Returns ``{stem: (title, year, manufacturer, source_filename)}``.
    Supports MAME XML (``*.xml``) and FBNeo/Logiqx DAT (``*.dat``).
    Later files override earlier ones on name collision.
    """
    result: dict[str, tuple[str, str, str, str]] = {}
    if not directory.exists():
        return result

    for f in sorted(directory.iterdir()):
        if f.suffix.lower() == ".xml":
            entries = load_mame_xml(f)
        elif f.suffix.lower() == ".dat":
            entries = load_fbneo_dat(f)
        else:
            continue
        for stem, (title, year, manufacturer) in entries.items():
            result[stem] = (title, year, manufacturer, f.name)
    return result
