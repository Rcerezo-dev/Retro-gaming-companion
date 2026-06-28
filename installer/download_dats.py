"""Build-time script: download the most common platform DATs to installer/bundled_dats/.

Run once before compiling the Inno Setup installer:
    python installer/download_dats.py

The bundled DATs are installed to {app}\\.rommgr\\catalogs\\ so the app works
out-of-the-box without the user having to download them from Settings.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rom_manager.catalog.dat_downloader import download_dat  # noqa: E402

_BUNDLE_PLATFORMS = [
    # ── No-Intro (cartuchos) — ficheros pequeños, todos incluidos ─────────────
    "NES",
    "Famicom Disk System",
    "SNES",
    "Nintendo 64",
    "Game Boy",
    "Game Boy Color",
    "Game Boy Advance",
    "Nintendo DS",
    "Nintendo 3DS",
    "Virtual Boy",
    "Pokemon Mini",
    "Master System",
    "Sega Mega Drive",
    "Sega 32X",
    "Game Gear",
    "PC Engine",
    "SuperGrafx",
    "Neo Geo Pocket",
    "Neo Geo Pocket Color",
    "Atari 2600",
    "Atari 5200",
    "Atari 7800",
    "Atari Lynx",
    "Atari Jaguar",
    "WonderSwan",
    "WonderSwan Color",
    "Watara Supervision",
    "Intellivision",
    "ColecoVision",
    "MSX",
    "Commodore 64",
    # ── Redump (óptico) — solo los más pequeños/populares ────────────────────
    # PS2, GC, Wii, PSP, PS Vita: demasiado grandes para bundlear
    # Game & Watch, MSX 2, Sega CD, PC-FX: 404 en libretro-database
    "PlayStation",
    "Sega Saturn",
    "Dreamcast",
]

_DEST = Path(__file__).parent / "bundled_dats"


def main() -> int:
    print(f"Descargando {len(_BUNDLE_PLATFORMS)} DATs a {_DEST} ...")
    ok = 0
    for platform in _BUNDLE_PLATFORMS:
        result = download_dat(platform, _DEST)
        if result.success:
            assert result.path is not None
            print(f"  OK  {platform}: {result.entries} entradas -> {result.path.name}")
            ok += 1
        else:
            print(f"  ERR {platform}: {result.error}", file=sys.stderr)
    print(f"\n{ok}/{len(_BUNDLE_PLATFORMS)} DATs listos.")
    return 0 if ok == len(_BUNDLE_PLATFORMS) else 1


if __name__ == "__main__":
    sys.exit(main())
