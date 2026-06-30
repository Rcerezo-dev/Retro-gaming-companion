"""Tests for the IPS patch applier."""

import struct
import tempfile
from pathlib import Path

import pytest

from rom_manager.patch.ips_applier import PatchError, apply_ips


def _make_ips(records: list[tuple[int, bytes | tuple[int, int]]]) -> bytes:
    """Build a minimal IPS patch byte-string.

    records: list of (offset, data_bytes) for normal records
                   or (offset, (run_len, fill_byte)) for RLE records.
    """
    out = bytearray(b"PATCH")
    for offset, payload in records:
        ob = bytes([(offset >> 16) & 0xFF, (offset >> 8) & 0xFF, offset & 0xFF])
        out += ob
        if isinstance(payload, tuple):
            run_len, fill = payload
            out += struct.pack(">H", 0)  # size=0 → RLE
            out += struct.pack(">H", run_len)
            out += bytes([fill])
        else:
            out += struct.pack(">H", len(payload))
            out += payload
    out += b"EOF"
    return bytes(out)


def _apply(rom: bytes, patch: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        rom_p = d / "rom.bin"
        patch_p = d / "rom.ips"
        out_p = d / "rom_patched.bin"
        rom_p.write_bytes(rom)
        patch_p.write_bytes(patch)
        apply_ips(rom_p, patch_p, out_p)
        return out_p.read_bytes()


def test_normal_record_overwrites_bytes():
    rom = b"\x00" * 16
    patch = _make_ips([(4, b"\xde\xad\xbe\xef")])
    result = _apply(rom, patch)
    assert result[4:8] == b"\xde\xad\xbe\xef"
    assert result[:4] == b"\x00\x00\x00\x00"


def test_rle_record_fills_range():
    rom = b"\x00" * 16
    patch = _make_ips([(2, (5, 0xFF))])
    result = _apply(rom, patch)
    assert result[2:7] == b"\xff\xff\xff\xff\xff"
    assert result[0:2] == b"\x00\x00"


def test_patch_extends_rom():
    rom = b"\x00" * 4
    patch = _make_ips([(8, b"\xaa\xbb")])
    result = _apply(rom, patch)
    assert len(result) == 10
    assert result[8:10] == b"\xaa\xbb"


def test_multiple_records():
    rom = b"\x00" * 16
    patch = _make_ips([(0, b"\x01"), (8, b"\x02")])
    result = _apply(rom, patch)
    assert result[0] == 0x01
    assert result[8] == 0x02


def test_invalid_header_raises():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        rom_p = d / "rom.bin"
        bad_p = d / "bad.ips"
        out_p = d / "out.bin"
        rom_p.write_bytes(b"\x00" * 8)
        bad_p.write_bytes(b"NOTIPS\x00")
        with pytest.raises(PatchError):
            apply_ips(rom_p, bad_p, out_p)


def test_ips32_header():
    rom = b"\x00" * 16
    # IPS32 uses 4-byte offsets and EEOF marker
    out = bytearray(b"IPS32")
    offset = 4
    out += struct.pack(">I", offset)
    out += struct.pack(">H", 3)
    out += b"\x11\x22\x33"
    out += b"EEOF"
    result = _apply(rom, bytes(out))
    assert result[4:7] == b"\x11\x22\x33"
