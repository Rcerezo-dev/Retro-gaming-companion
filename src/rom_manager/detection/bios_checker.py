"""BIOS file checker — detects which required BIOS files are present in the library.

Each entry has:
  filename: canonical filename RetroArch expects
  md5:      expected MD5 (None = skip hash check, presence-only)
  platform: human-readable platform name
  required: True = core will not work without it; False = optional (some features)
  notes:    short description
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

KNOWN_BIOS: list[dict] = [
    # PlayStation
    {
        "filename": "scph5500.bin",
        "md5": "8dd7d5296a650fac7319bce665a6a53c",
        "platform": "PlayStation",
        "required": True,
        "notes": "BIOS JP (v3.0)",
    },
    {
        "filename": "scph5501.bin",
        "md5": "490f666e1afb15b7362b406ed1cea246",
        "platform": "PlayStation",
        "required": True,
        "notes": "BIOS US (v3.0)",
    },
    {
        "filename": "scph5502.bin",
        "md5": "32736f17079d0b2b7024407c39bd3050",
        "platform": "PlayStation",
        "required": True,
        "notes": "BIOS EU (v3.0)",
    },
    {
        "filename": "scph1001.bin",
        "md5": "924e392ed05558ffdb115408c263dccf",
        "platform": "PlayStation",
        "required": False,
        "notes": "BIOS US (v2.2) — alternativa",
    },
    # PlayStation 2
    {
        "filename": "ps2-0230a-20080220.bin",
        "md5": None,
        "platform": "PlayStation 2",
        "required": True,
        "notes": "BIOS — el MD5 varía por región/versión",
    },
    {
        "filename": "SCPH-70012_BIOS_V12_USA_200.BIN",
        "md5": None,
        "platform": "PlayStation 2",
        "required": False,
        "notes": "BIOS US v12 (comprobación por nombre)",
    },
    # PSP
    {
        "filename": "ppge_atlas.zim",
        "md5": None,
        "platform": "PSP",
        "required": False,
        "notes": "PPSSPP UI atlas (opcional)",
    },
    # Game Boy Advance
    {
        "filename": "gba_bios.bin",
        "md5": "a860e8c0b6d573d191e4ec7db1b1e4f6",
        "platform": "Game Boy Advance",
        "required": False,
        "notes": "BIOS oficial GBA — mejora compatibilidad",
    },
    # Famicom Disk System
    {
        "filename": "disksys.rom",
        "md5": "ca30b50f880eb660a320674ed365ef7a",
        "platform": "Famicom Disk System",
        "required": True,
        "notes": "BIOS FDS obligatoria",
    },
    # Sega CD / Mega-CD
    {
        "filename": "bios_CD_U.bin",
        "md5": "2efd74e3232ff260e371b99f84024f7f",
        "platform": "Sega CD",
        "required": True,
        "notes": "BIOS US",
    },
    {
        "filename": "bios_CD_E.bin",
        "md5": "e66fa1dc5820d254611fdcdba0662372",
        "platform": "Sega CD",
        "required": True,
        "notes": "BIOS EU",
    },
    {
        "filename": "bios_CD_J.bin",
        "md5": "278a9397d192149e84e820ac621a8edd",
        "platform": "Sega CD",
        "required": True,
        "notes": "BIOS JP",
    },
    # Sega Saturn
    {
        "filename": "sega_101.bin",
        "md5": "85ec9ca47d8f6807718151cbcca8b964",
        "platform": "Sega Saturn",
        "required": True,
        "notes": "BIOS JP",
    },
    {
        "filename": "mpr-17933.bin",
        "md5": "3240872c70984b6cbfda1586cab68dbe",
        "platform": "Sega Saturn",
        "required": True,
        "notes": "BIOS US/EU",
    },
    # Dreamcast
    {
        "filename": "dc_boot.bin",
        "md5": "e10c53c2f8b90bab96ead2d368858623",
        "platform": "Dreamcast",
        "required": True,
        "notes": "BIOS Dreamcast",
    },
    {
        "filename": "dc_flash.bin",
        "md5": "0a93f7940c455905bea6e392dfde92a4",
        "platform": "Dreamcast",
        "required": True,
        "notes": "Flash Dreamcast",
    },
    # Neo Geo
    {
        "filename": "neogeo.zip",
        "md5": None,
        "platform": "Neo Geo",
        "required": True,
        "notes": "BIOS Neo Geo (MAME) — MD5 varía por versión",
    },
    # PC Engine CD
    {
        "filename": "syscard3.pce",
        "md5": "38179df8f4ac870017db21ebcbf53114",
        "platform": "PC Engine",
        "required": True,
        "notes": "Super System Card 3.0",
    },
    # Atari Lynx
    {
        "filename": "lynxboot.img",
        "md5": "fcd403db69f54290b51035d82f835e7b",
        "platform": "Atari Lynx",
        "required": True,
        "notes": "BIOS Lynx",
    },
    # Nintendo DS
    {
        "filename": "bios7.bin",
        "md5": "df692a80a5b1bc90728bc3dfc76cd948",
        "platform": "Nintendo DS",
        "required": True,
        "notes": "ARM7 BIOS",
    },
    {
        "filename": "bios9.bin",
        "md5": "a392174eb3e572fed6447e956bde4b25",
        "platform": "Nintendo DS",
        "required": True,
        "notes": "ARM9 BIOS",
    },
    {
        "filename": "firmware.bin",
        "md5": None,
        "platform": "Nintendo DS",
        "required": True,
        "notes": "Firmware NDS",
    },
]


@dataclass(slots=True)
class BiosCheckResult:
    filename: str
    platform: str
    required: bool
    notes: str
    found: bool
    found_path: str = ""
    md5_match: bool | None = None  # None = not checked (no expected MD5)
    expected_md5: str = ""


def _md5_of(path: Path) -> str:
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(4 * 1024 * 1024):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return ""


def check_bios(search_dirs: list[Path]) -> list[dict]:
    """Check which BIOS files are present in any of the given directories.

    *search_dirs* should include:
    - ``library_root``
    - ``library_root/bios/``
    - RetroArch system folder (``retroarch_path/../system/``)
    """
    # Collect all candidate files indexed by lowercase filename
    candidates: dict[str, list[Path]] = {}
    for d in search_dirs:
        if not d or not d.exists():
            continue
        try:
            for f in d.rglob("*"):
                if f.is_file():
                    candidates.setdefault(f.name.lower(), []).append(f)
        except (OSError, PermissionError):
            pass

    results = []
    for entry in KNOWN_BIOS:
        fname = entry["filename"]
        matches = candidates.get(fname.lower(), [])
        found = bool(matches)
        found_path = str(matches[0]) if matches else ""
        md5_match: bool | None = None
        expected_md5 = entry["md5"] or ""
        if found and expected_md5:
            actual = _md5_of(matches[0])
            md5_match = actual.lower() == expected_md5.lower()

        results.append(
            {
                "filename": fname,
                "platform": entry["platform"],
                "required": entry["required"],
                "notes": entry["notes"],
                "found": found,
                "found_path": found_path,
                "md5_match": md5_match,
                "expected_md5": expected_md5,
            }
        )

    return results
