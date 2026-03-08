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
