"""Tests for the BPS patch applier."""
import struct
import tempfile
from pathlib import Path

import pytest

from rom_manager.patch.bps_applier import apply_bps
from rom_manager.patch.ips_applier import PatchError


def _vlq(value: int) -> bytes:
    """Encode a BPS variable-length quantity."""
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


def _make_bps(source: bytes, target: bytes, actions: list[bytes]) -> bytes:
    """Build a minimal BPS patch (no CRC validation — applier trusts the data)."""
    meta = b""
    header = (
        b"BPS1"
        + _vlq(len(source))
        + _vlq(len(target))
        + _vlq(len(meta))
        + meta
    )
    body = b"".join(actions)
    # Footer: 3 × fake CRC32 (not verified by applier)
    footer = struct.pack("<III", 0, 0, 0)
    return header + body + footer


def _source_read(length: int) -> bytes:
    """BPS SourceRead action: copy N bytes from source at current position."""
    return _vlq(((length - 1) << 2) | 0)


def _target_read(data: bytes) -> bytes:
    """BPS TargetRead action: embed literal bytes."""
    return _vlq(((len(data) - 1) << 2) | 1) + data


def _source_copy(length: int, offset_delta: int) -> bytes:
    """BPS SourceCopy action with signed delta offset."""
    if offset_delta >= 0:
        enc = (offset_delta << 1) | 0
    else:
        enc = ((-offset_delta) << 1) | 1
    return _vlq(((length - 1) << 2) | 2) + _vlq(enc)


def test_source_read():
    source = b"Hello, world!"
    target = source  # identical copy
    patch = _make_bps(source, target, [_source_read(len(source))])
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "rom.bin").write_bytes(source)
        (d / "patch.bps").write_bytes(patch)
        apply_bps(d / "rom.bin", d / "patch.bps", d / "out.bin")
        assert (d / "out.bin").read_bytes() == target


def test_target_read():
    source = b"\x00" * 8
    new_data = b"ABCDEFGH"
    patch = _make_bps(source, new_data, [_target_read(new_data)])
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "rom.bin").write_bytes(source)
        (d / "patch.bps").write_bytes(patch)
        apply_bps(d / "rom.bin", d / "patch.bps", d / "out.bin")
        assert (d / "out.bin").read_bytes() == new_data


def test_mixed_actions():
    source = b"AAAA" + b"\x00" * 4
    # Keep first 4 bytes (SourceRead), replace last 4 with literal
    target = b"AAAA" + b"BBBB"
    patch = _make_bps(source, target, [
        _source_read(4),
        _target_read(b"BBBB"),
    ])
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "rom.bin").write_bytes(source)
        (d / "patch.bps").write_bytes(patch)
        apply_bps(d / "rom.bin", d / "patch.bps", d / "out.bin")
        assert (d / "out.bin").read_bytes() == target


def test_source_copy():
    source = b"XY" + b"\x00" * 6
    # SourceCopy: jump to offset 0, copy 2 bytes → "XY", then jump to 1, copy 2 → "YX" wait
    # Simpler: copy "XY" from offset 0, then copy "XY" again from offset 0 (delta = -2)
    target = b"XYXY" + b"\x00" * 4
    patch = _make_bps(source, target, [
        _source_copy(2, 0),   # src_rel starts 0 → reads source[0:2]="XY"; src_rel=2
        _source_copy(2, -2),  # src_rel += -2 → src_rel=0 again → "XY"
        _source_read(4),      # copy remaining zeros
    ])
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "rom.bin").write_bytes(source)
        (d / "patch.bps").write_bytes(patch)
        apply_bps(d / "rom.bin", d / "patch.bps", d / "out.bin")
        assert (d / "out.bin").read_bytes() == target


def test_invalid_header():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "rom.bin").write_bytes(b"\x00" * 4)
        (d / "bad.bps").write_bytes(b"JUNK" + b"\x00" * 12)
        with pytest.raises(PatchError, match="Invalid BPS header"):
            apply_bps(d / "rom.bin", d / "bad.bps", d / "out.bin")


def test_source_size_mismatch():
    source = b"ABC"
    target = b"ABC"
    # Claim source_size=10 but actual source is 3
    patch = b"BPS1" + _vlq(10) + _vlq(3) + _vlq(0) + _source_read(3) + struct.pack("<III", 0, 0, 0)
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "rom.bin").write_bytes(source)
        (d / "patch.bps").write_bytes(patch)
        with pytest.raises(PatchError, match="Source size mismatch"):
            apply_bps(d / "rom.bin", d / "patch.bps", d / "out.bin")
