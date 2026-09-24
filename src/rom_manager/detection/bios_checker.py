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

from rom_manager.detection.platform_detector import bios_definitions


@dataclass(slots=True, frozen=True)
class BiosDef:
    filename: str
    md5: str | None
    platform: str
    required: bool
    notes: str


# DEVPROFILE-1c: los datos viven en platforms.toml ([[bios]]), fuente única
# compartida con la detección de plataforma — ver bios_definitions().
KNOWN_BIOS: list[BiosDef] = [
    BiosDef(
        filename=entry["filename"],
        md5=entry.get("md5"),
        platform=entry["platform"],
        required=entry["required"],
        notes=entry.get("notes", ""),
    )
    for entry in bios_definitions()
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
        fname = entry.filename
        matches = candidates.get(fname.lower(), [])
        found = bool(matches)
        found_path = str(matches[0]) if matches else ""
        md5_match: bool | None = None
        expected_md5 = entry.md5 or ""
        if found and expected_md5:
            actual = _md5_of(matches[0])
            md5_match = actual.lower() == expected_md5.lower()

        results.append(
            {
                "filename": fname,
                "platform": entry.platform,
                "required": entry.required,
                "notes": entry.notes,
                "found": found,
                "found_path": found_path,
                "md5_match": md5_match,
                "expected_md5": expected_md5,
            }
        )

    return results
