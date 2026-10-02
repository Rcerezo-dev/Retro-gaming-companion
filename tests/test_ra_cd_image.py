"""Regression for a bug found live on the RG556 (2026-10-02): a short
single-track raw-sector dump (e.g. a GD-ROM boot track) that doesn't reach
sector 16 fell through _detect_geometry's blind size-modulo fallback, which
hard-coded header_size=24 (MODE2 FORM1) -- wrong for a MODE1 track (Jet Set
Radio's track 3), reading 8 bytes into the next field and returning garbage
instead of the "SEGA SEGAKATANA " magic.
"""

from __future__ import annotations

from pathlib import Path

from rom_manager.retroachievements.ra_cd_image import _CdImage

_SECTOR_SIZE = 2352
_SYNC = bytes([0x00, *([0xFF] * 10), 0x00])


def _make_short_raw_image(tmp_path: Path, *, mode: int, sectors: int = 5) -> Path:
    """A raw-sector dump with fewer than 17 sectors -- the sync-pattern probe
    at sector 16 (the primary detection path) can't reach that far, forcing
    execution into the file-size-modulo fallback."""
    data = bytearray(sectors * _SECTOR_SIZE)
    data[0:12] = _SYNC
    data[15] = mode
    header_size = 16 if mode == 1 else 24
    data[header_size : header_size + 16] = b"SEGA SEGAKATANA "
    p = tmp_path / "track03.bin"
    p.write_bytes(bytes(data))
    return p


def test_short_mode1_track_detects_header_size_16(tmp_path: Path) -> None:
    p = _make_short_raw_image(tmp_path, mode=1)
    with _CdImage(p) as cd:
        assert cd.sector_size == 2352
        assert cd.header_size == 16
        assert cd.read_sector(0, 16) == b"SEGA SEGAKATANA "


def test_short_mode2_track_detects_header_size_24(tmp_path: Path) -> None:
    p = _make_short_raw_image(tmp_path, mode=2)
    with _CdImage(p) as cd:
        assert cd.sector_size == 2352
        assert cd.header_size == 24
        assert cd.read_sector(0, 16) == b"SEGA SEGAKATANA "


def test_short_image_without_sync_pattern_keeps_old_default(tmp_path: Path) -> None:
    """No positive evidence either way (e.g. a corrupt/blank dump) -- keep the
    pre-existing MODE2 FORM1 default rather than guessing MODE1."""
    data = bytearray(5 * _SECTOR_SIZE)  # all zeros, no sync pattern anywhere
    p = tmp_path / "blank.bin"
    p.write_bytes(bytes(data))
    with _CdImage(p) as cd:
        assert cd.sector_size == 2352
        assert cd.header_size == 24
