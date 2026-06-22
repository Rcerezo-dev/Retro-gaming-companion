"""DAT-DL-1 + DAT-DL-2: platform → libretro-database URL map and downloader."""

from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from rom_manager.catalog.catalog_loader import _load_dat_file

_BASE = (
    "https://raw.githubusercontent.com/libretro/libretro-database"
    "/master/metadat"
)

# (source_dir, filename_stem)  —  source_dir is "no-intro" or "redump"
# Local cache lives at: dest_dir / {"nointro","redump"} / f"{stem}.dat"
_PLATFORM_DAT_MAP: dict[str, tuple[str, str]] = {
    # ── Nintendo cartridge (No-Intro) ──────────────────────────────────────
    "NES":                  ("no-intro", "Nintendo - Nintendo Entertainment System"),
    "Famicom Disk System":  ("no-intro", "Nintendo - Family Computer Disk System"),
    "SNES":                 ("no-intro", "Nintendo - Super Nintendo Entertainment System"),
    "Nintendo 64":          ("no-intro", "Nintendo - Nintendo 64"),
    "Game Boy":             ("no-intro", "Nintendo - Game Boy"),
    "Game Boy Color":       ("no-intro", "Nintendo - Game Boy Color"),
    "Game Boy Advance":     ("no-intro", "Nintendo - Game Boy Advance"),
    "Nintendo DS":          ("no-intro", "Nintendo - Nintendo DS"),
    "Nintendo 3DS":         ("no-intro", "Nintendo - Nintendo 3DS"),
    "Virtual Boy":          ("no-intro", "Nintendo - Virtual Boy"),
    "Pokemon Mini":         ("no-intro", "Nintendo - Pokemon Mini"),
    # ── Nintendo disc (Redump) ──────────────────────────────────────────────
    "GameCube":             ("redump",   "Nintendo - GameCube"),
    "Wii":                  ("redump",   "Nintendo - Wii"),
    "Wii U":                ("redump",   "Nintendo - Wii U"),
    # ── Sega cartridge (No-Intro) ───────────────────────────────────────────
    "Master System":        ("no-intro", "Sega - Master System - Mark III"),
    "Sega Mega Drive":      ("no-intro", "Sega - Mega Drive - Genesis"),
    "Sega 32X":             ("no-intro", "Sega - 32X"),
    "Game Gear":            ("no-intro", "Sega - Game Gear"),
    # ── Sega disc (Redump) ─────────────────────────────────────────────────
    "Sega CD":              ("redump",   "Sega - Mega CD & Sega CD"),
    "Sega Saturn":          ("redump",   "Sega - Saturn"),
    "Dreamcast":            ("redump",   "Sega - Dreamcast"),
    # ── Sony (Redump) ──────────────────────────────────────────────────────
    "PlayStation":          ("redump",   "Sony - PlayStation"),
    "PlayStation 2":        ("redump",   "Sony - PlayStation 2"),
    "PlayStation 3":        ("redump",   "Sony - PlayStation 3"),
    "PSP":                  ("redump",   "Sony - PlayStation Portable"),
    "PS Vita":              ("redump",   "Sony - PlayStation Vita"),
    # ── NEC ────────────────────────────────────────────────────────────────
    "PC Engine":            ("no-intro", "NEC - PC Engine - TurboGrafx 16"),
    "SuperGrafx":           ("no-intro", "NEC - PC Engine SuperGrafx"),
    "PC-FX":                ("redump",   "NEC - PC-FX & PC-FXGA"),
    # ── SNK ────────────────────────────────────────────────────────────────
    "Neo Geo Pocket":       ("no-intro", "SNK - Neo Geo Pocket"),
    "Neo Geo Pocket Color": ("no-intro", "SNK - Neo Geo Pocket Color"),
    # ── Atari ──────────────────────────────────────────────────────────────
    "Atari 2600":           ("no-intro", "Atari - 2600"),
    "Atari 5200":           ("no-intro", "Atari - 5200"),
    "Atari 7800":           ("no-intro", "Atari - 7800"),
    "Atari Lynx":           ("no-intro", "Atari - Lynx"),
    "Atari Jaguar":         ("no-intro", "Atari - Jaguar"),
    # ── Bandai ─────────────────────────────────────────────────────────────
    "WonderSwan":           ("no-intro", "Bandai - WonderSwan"),
    "WonderSwan Color":     ("no-intro", "Bandai - WonderSwan Color"),
    # ── Other handhelds / micro-consoles ───────────────────────────────────
    "Game & Watch":         ("no-intro", "Nintendo - Game and Watch"),
    "Watara Supervision":   ("no-intro", "Watara - Supervision"),
    # ── Home computers ─────────────────────────────────────────────────────
    "Intellivision":        ("no-intro", "Mattel - Intellivision"),
    "ColecoVision":         ("no-intro", "Coleco - ColecoVision"),
    "MSX":                  ("no-intro", "Microsoft - MSX"),
    "MSX 2":                ("no-intro", "Microsoft - MSX 2"),
    "Commodore 64":         ("no-intro", "Commodore - 64"),
    "Amiga":                ("no-intro", "Commodore - Amiga"),
}

# Reverse cache-subdir name: "no-intro" → "nointro", "redump" → "redump"
_SUBDIR: dict[str, str] = {"no-intro": "nointro", "redump": "redump"}


@dataclass
class DatDownloadResult:
    platform: str
    success: bool
    path: Path | None = None
    entries: int = 0
    error: str = ""


def dat_url(platform: str) -> str | None:
    """Return the raw-GitHub URL for *platform*'s DAT, or None if unknown."""
    entry = _PLATFORM_DAT_MAP.get(platform)
    if not entry:
        return None
    source, stem = entry
    return f"{_BASE}/{source}/{stem}.dat"


def known_platforms() -> list[str]:
    """Return sorted list of platforms with a known DAT mapping."""
    return sorted(_PLATFORM_DAT_MAP)


def download_dat(
    platform: str,
    dest_dir: Path,
    *,
    timeout: int = 30,
) -> DatDownloadResult:
    """Download the DAT for *platform* into *dest_dir/{nointro|redump}/*.

    Never raises; network and parse errors are captured in the result.
    """
    url = dat_url(platform)
    if url is None:
        return DatDownloadResult(
            platform=platform,
            success=False,
            error=f"Plataforma desconocida: no hay DAT mapeado para '{platform}'",
        )

    source, stem = _PLATFORM_DAT_MAP[platform]
    subdir = dest_dir / _SUBDIR[source]
    subdir.mkdir(parents=True, exist_ok=True)
    dest = subdir / f"{stem}.dat"

    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = resp.read()
    except urllib.error.URLError as exc:
        return DatDownloadResult(
            platform=platform,
            success=False,
            error=f"Error de red: {exc.reason}",
        )
    except OSError as exc:
        return DatDownloadResult(
            platform=platform,
            success=False,
            error=f"Error de red: {exc}",
        )

    dest.write_bytes(data)

    try:
        entries = _load_dat_file(dest)
    except Exception as exc:  # noqa: BLE001
        dest.unlink(missing_ok=True)
        return DatDownloadResult(
            platform=platform,
            success=False,
            error=f"DAT descargado pero no se pudo parsear: {exc}",
        )

    if not entries:
        dest.unlink(missing_ok=True)
        return DatDownloadResult(
            platform=platform,
            success=False,
            error="DAT descargado pero contiene 0 entradas válidas",
        )

    return DatDownloadResult(
        platform=platform,
        success=True,
        path=dest,
        entries=len(entries),
    )
