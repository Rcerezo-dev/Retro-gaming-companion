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
    "Game Boy Advance",
    "SNES",
    "Sega Mega Drive",
    "NES",
    "Game Boy Color",
    "Game Boy",
    "Nintendo 64",
    "PlayStation",
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
