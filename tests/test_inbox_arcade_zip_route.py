"""INBOX-CFG-4: un ZIP arcade completo nunca debe extraerse — el ZIP es el ROM.

Antes de este fix, ``_run_inbox_pipeline`` extraía cualquier ZIP suelto sin
distinguir arcade de consola, reventando sets MAME completos en chips sueltos
(incidente Día49). ``_is_arcade_zip_container`` es la comprobación que evita
que ese ZIP llegue siquiera a ``extract_zip()``.
"""

from __future__ import annotations

import zipfile
import zlib
from pathlib import Path

from rom_manager.web.inbox_pipeline import _is_arcade_zip_container

CHIP_A = b"PROGRAM ROM CHIP A"
CHIP_B = b"GRAPHICS ROM CHIP B"
CRC_A = f"{zlib.crc32(CHIP_A) & 0xFFFFFFFF:08X}"
CRC_B = f"{zlib.crc32(CHIP_B) & 0xFFFFFFFF:08X}"
ARCADE_CRC_INDEX = {CRC_A: {"pacgame"}, CRC_B: {"pacgame"}}


def _make_zip(path: Path, entries: dict[str, bytes]) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return path


def test_full_arcade_coverage_is_detected(tmp_path: Path) -> None:
    zp = _make_zip(tmp_path / "pacgame.zip", {"prog.u1": CHIP_A, "gfx.u2": CHIP_B})
    assert _is_arcade_zip_container(zp, ARCADE_CRC_INDEX) is True


def test_console_zip_is_not_arcade(tmp_path: Path) -> None:
    zp = _make_zip(tmp_path / "Some Game (USA).zip", {"Some Game (USA).nes": b"not arcade data"})
    assert _is_arcade_zip_container(zp, ARCADE_CRC_INDEX) is False


def test_mixed_zip_is_not_arcade(tmp_path: Path) -> None:
    """Un solo miembro fuera del índice arcade basta para descartarlo — mejor
    extraerlo de más (comportamiento previo) que arriesgarse a mover algo mal."""
    zp = _make_zip(tmp_path / "mixed.zip", {"prog.u1": CHIP_A, "readme.txt": b"not a rom"})
    assert _is_arcade_zip_container(zp, ARCADE_CRC_INDEX) is False


def test_empty_zip_is_not_arcade(tmp_path: Path) -> None:
    zp = tmp_path / "empty.zip"
    with zipfile.ZipFile(zp, "w"):
        pass
    assert _is_arcade_zip_container(zp, ARCADE_CRC_INDEX) is False


def test_corrupt_file_is_not_arcade(tmp_path: Path) -> None:
    bad = tmp_path / "corrupt.zip"
    bad.write_bytes(b"not actually a zip")
    assert _is_arcade_zip_container(bad, ARCADE_CRC_INDEX) is False
