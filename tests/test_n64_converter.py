"""Tests for the N64 ROM byte-swap converter."""

from __future__ import annotations

from pathlib import Path

from rom_manager.converters.n64_converter import convert_to_z64, detect_n64_format

_MAGIC_V64 = b"\x37\x80\x40\x12"
_MAGIC_N64 = b"\x40\x12\x37\x80"


def test_convert_v64_to_z64(tmp_path: Path) -> None:
    source = tmp_path / "rom.v64"
    source.write_bytes(_MAGIC_V64 + b"\xaa\xbb\xcc\xdd")
    result = convert_to_z64(source)
    assert result.success
    target = tmp_path / "rom.z64"
    assert target.exists()
    assert detect_n64_format(target) == "z64"


def test_convert_v64_odd_size_no_padding_leaks_into_output(tmp_path: Path) -> None:
    """REV43-21: an odd-sized .v64 (not a multiple of 2) used to come out of
    convert_to_z64 one byte larger than the source, with a stray 0x00 pad
    byte from the swap operation leaked into the output."""
    source = tmp_path / "rom.v64"
    payload = _MAGIC_V64 + b"\xaa\xbb\xcc"  # 7 bytes total, odd
    source.write_bytes(payload)
    result = convert_to_z64(source)
    assert result.success
    target = tmp_path / "rom.z64"
    assert target.stat().st_size == len(payload)


def test_convert_n64_size_not_multiple_of_4_no_padding_leaks_into_output(
    tmp_path: Path,
) -> None:
    """Same as above for .n64 (word-swapped), padded to a multiple of 4."""
    source = tmp_path / "rom.n64"
    payload = _MAGIC_N64 + b"\xaa\xbb\xcc"  # 7 bytes total, not a multiple of 4
    source.write_bytes(payload)
    result = convert_to_z64(source)
    assert result.success
    target = tmp_path / "rom.z64"
    assert target.stat().st_size == len(payload)


def test_convert_does_not_overwrite_existing_target(tmp_path: Path) -> None:
    """REV43-20: unlike chd_converter, convert_to_z64 used to overwrite the
    target unconditionally. A pre-existing target must be left untouched."""
    source = tmp_path / "rom.v64"
    source.write_bytes(_MAGIC_V64 + b"\xaa\xbb\xcc\xdd")
    target = tmp_path / "rom.z64"
    target.write_bytes(b"pre-existing content, do not touch")

    result = convert_to_z64(source, target)

    assert not result.success
    assert "ya existe" in result.error
    assert target.read_bytes() == b"pre-existing content, do not touch"
