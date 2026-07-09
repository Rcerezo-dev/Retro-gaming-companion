"""Loaders for arcade ROM catalogs (MAME XML and FBNeo/Logiqx DAT).

Both return a dict of ``{stem_lowercase: (title, year, manufacturer)}``
where *stem* is the canonical MAME set name (= ZIP filename without extension).

Usage
-----
- MAME listxml: generated with ``mame -listxml > mame.xml``
- FBNeo DAT: downloaded from https://github.com/libretro/FBNeo/tree/master/dats
"""

from __future__ import annotations

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
        # root tag can be <mame> or <datafile>
        machines = root.iter("machine") if root.tag != "datafile" else root.iter("game")
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


def load_arcade_infra_names(directory: Path) -> set[str]:
    """Set names that ``load_mame_xml`` skips: BIOS, devices, non-runnable.

    These are the loose ZIPs in an unorganized library that will never match
    the playable catalog (JUNK-SMART-2) — c1541.zip, kb_pcat101.zip, sb16.zip…
    Only MAME XML carries the flags; FBNeo DATs are ignored.
    """
    names: set[str] = set()
    if not directory.exists():
        return names
    for f in sorted(directory.iterdir()):
        if f.suffix.lower() != ".xml":
            continue
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
    return names


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
