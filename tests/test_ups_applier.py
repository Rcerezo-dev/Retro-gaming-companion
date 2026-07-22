"""Tests for UPS patch applier."""

from __future__ import annotations

import struct
from pathlib import Path

import pytest

from rom_manager.patch.ips_applier import PatchError
from rom_manager.patch.ups_applier import apply_ups


def _vlq(value: int) -> bytes:
    """Encode an integer as UPS VLQ."""
    out = []
    while True:
        x = value & 0x7F
        value >>= 7
        if value == 0:
            out.append(x | 0x80)
            break
        out.append(x)
        value -= 1
    return bytes(out)


def _make_ups(source: bytes, target: bytes) -> bytes:
    """Build a minimal UPS patch from source→target."""
    # Find differing regions and produce hunks
    max_len = max(len(source), len(target))
    src = source + b"\x00" * (max_len - len(source))
    tgt = target + b"\x00" * (max_len - len(target))

    hunks = b""
    i = 0
    last_write = 0
    while i < max_len:
        if src[i] != tgt[i]:
            offset = i - last_write
            xor_data = b""
            while i < max_len and src[i] != tgt[i]:
                xor_data += bytes([src[i] ^ tgt[i]])
                i += 1
            hunks += _vlq(offset) + xor_data + b"\x00"
            last_write = i + 1
        else:
            i += 1

    body = b"UPS1" + _vlq(len(source)) + _vlq(len(target)) + hunks
    footer = struct.pack("<III", 0, 0, 0)  # fake CRC32s
    return body + footer


def test_apply_ups_identity(tmp_path: Path) -> None:
    source = b"ABCDEFGH"
    patch_data = _make_ups(source, source)
    rom = tmp_path / "rom.sfc"
    patch = tmp_path / "patch.ups"
    out = tmp_path / "out.sfc"
    rom.write_bytes(source)
    patch.write_bytes(patch_data)
    hunks = apply_ups(rom, patch, out)
    assert out.read_bytes() == source
    assert hunks == 0


def test_apply_ups_single_hunk(tmp_path: Path) -> None:
    source = b"Hello World"
    target = b"Hello UPS!!"
    patch_data = _make_ups(source, target)
    rom = tmp_path / "rom.sfc"
    patch = tmp_path / "patch.ups"
    out = tmp_path / "out.sfc"
    rom.write_bytes(source)
    patch.write_bytes(patch_data)
    apply_ups(rom, patch, out)
    assert out.read_bytes() == target


def test_apply_ups_two_hunks(tmp_path: Path) -> None:
    source = b"AAABBBCCC"
    target = b"AAAXBBYYY"
    patch_data = _make_ups(source, target)
    rom = tmp_path / "rom.sfc"
    patch = tmp_path / "patch.ups"
    out = tmp_path / "out.sfc"
    rom.write_bytes(source)
    patch.write_bytes(patch_data)
    hunks = apply_ups(rom, patch, out)
    assert out.read_bytes() == target
    assert hunks == 2


def test_invalid_header(tmp_path: Path) -> None:
    rom = tmp_path / "rom.sfc"
    patch = tmp_path / "bad.ups"
    rom.write_bytes(b"data")
    patch.write_bytes(b"NOPE" + b"\x00" * 16)
    with pytest.raises(PatchError, match="Cabecera"):
        apply_ups(rom, patch, tmp_path / "out.sfc")


def test_source_size_mismatch(tmp_path: Path) -> None:
    source = b"ABCD"
    patch_data = _make_ups(source, b"XBCD")
    rom = tmp_path / "rom.sfc"
    patch = tmp_path / "patch.ups"
    rom.write_bytes(b"AB")  # wrong size
    patch.write_bytes(patch_data)
    with pytest.raises(PatchError, match="Tamaño ROM"):
        apply_ups(rom, patch, tmp_path / "out.sfc")


def test_truncated_patch_raises_patch_error_not_index_error(tmp_path: Path) -> None:
    """REV43-18: a .ups cut short mid-VLQ must fail cleanly, not with an
    unhandled IndexError (the same guard bps_applier._read_vlq already has)."""
    rom = tmp_path / "rom.sfc"
    patch = tmp_path / "truncated.ups"
    rom.write_bytes(b"ABCD")
    patch.write_bytes(b"UPS1")  # header only, truncated before any VLQ byte
    with pytest.raises(PatchError, match="truncado"):
        apply_ups(rom, patch, tmp_path / "out.sfc")


def test_extend_target(tmp_path: Path) -> None:
    """Target longer than source — output padded."""
    source = b"AB"
    target = b"ABCD"
    patch_data = _make_ups(source, target)
    rom = tmp_path / "rom.sfc"
    patch = tmp_path / "patch.ups"
    out = tmp_path / "out.sfc"
    rom.write_bytes(source)
    patch.write_bytes(patch_data)
    apply_ups(rom, patch, out)
    assert out.read_bytes() == target
