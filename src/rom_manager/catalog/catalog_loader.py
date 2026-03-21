from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class CatalogEntry:
    title: str
    sha1: str
    md5: str
    crc32: str
    size_bytes: int


def load_nointro_dat(path: Path) -> dict[str, CatalogEntry]:
    """Parse a No-Intro DAT file (Logiqx XML) and return a sha1→CatalogEntry mapping.

    The DAT format looks like:
        <game name="Tetris (World) (Rev 1)">
            <rom name="..." size="32768" crc="46df91ad" md5="..." sha1="..."/>
        </game>

    SHA1 keys are stored in uppercase to match the output of hash_calculator.
    """
    tree = ET.parse(path)
    root = tree.getroot()

    entries: dict[str, CatalogEntry] = {}
    for game in root.iter("game"):
        title = game.get("name", "").strip()
        for rom in game.findall("rom"):
            sha1 = rom.get("sha1", "").strip().upper()
            if not sha1:
                continue
            entries[sha1] = CatalogEntry(
                title=title,
                sha1=sha1,
                md5=rom.get("md5", "").strip().upper(),
                crc32=rom.get("crc", "").strip().upper(),
                size_bytes=int(rom.get("size", 0)),
            )
    return entries


def load_dat_directory(directory: Path) -> dict[str, CatalogEntry]:
    """Load all .dat files from a directory and merge them into a single mapping.

    Later files overwrite earlier ones on SHA1 collision (last file wins).
    """
    merged: dict[str, CatalogEntry] = {}
    for dat_file in sorted(directory.glob("*.dat")):
        merged.update(load_nointro_dat(dat_file))
    return merged


def load_nointro_dat_with_header(path: Path) -> tuple[str, dict[str, CatalogEntry]]:
    """Parse a No-Intro/Redump DAT file and return (platform_label, sha1→CatalogEntry).

    platform_label is extracted from <header><name>, with the "No-Intro: " or "Redump - "
    prefix stripped.  Falls back to the file stem if the header element is absent.
    """
    import re as _re

    tree = ET.parse(path)
    root = tree.getroot()

    platform_label = path.stem
    header_el = root.find("header")
    if header_el is not None:
        name_el = header_el.find("name")
        if name_el is not None and name_el.text:
            platform_label = name_el.text.strip()
            # Strip "No-Intro: " / "Redump - " prefix
            platform_label = _re.sub(
                r"^(No-Intro|Redump)[:\s\-]+", "", platform_label, flags=_re.IGNORECASE
            ).strip()

    entries: dict[str, CatalogEntry] = {}
    for game in root.iter("game"):
        title = game.get("name", "").strip()
        for rom in game.findall("rom"):
            sha1 = rom.get("sha1", "").strip().upper()
            if not sha1:
                continue
            entries[sha1] = CatalogEntry(
                title=title,
                sha1=sha1,
                md5=rom.get("md5", "").strip().upper(),
                crc32=rom.get("crc", "").strip().upper(),
                size_bytes=int(rom.get("size", 0) or 0),
            )
    return platform_label, entries


def load_dat_files_by_platform(
    *directories: Path,
) -> list[tuple[str, dict[str, CatalogEntry]]]:
    """Load each .dat file in the given directories separately.

    Returns a list of (platform_label, sha1→CatalogEntry) tuples, one per file.
    Non-existent directories are silently skipped.
    """
    results: list[tuple[str, dict[str, CatalogEntry]]] = []
    for directory in directories:
        if not directory.exists():
            continue
        for dat_file in sorted(directory.glob("*.dat")):
            try:
                platform_label, entries = load_nointro_dat_with_header(dat_file)
                if entries:
                    results.append((platform_label, entries))
            except ET.ParseError:
                continue
    return results
