"""Tests for the save-state PNG extractor."""
import struct
import tempfile
import zlib
from pathlib import Path

from rom_manager.utils.state_reader import find_state_thumbnails


def _make_png(fill: int = 0xFF) -> bytes:
    """Build a minimal (but valid-structure) 1x1 PNG."""
    sig = b"\x89PNG\r\n\x1a\n"

    def chunk(name: bytes, data: bytes) -> bytes:
        crc = struct.pack(">I", 0)  # fake CRC — parser only checks IEND presence
        return struct.pack(">I", len(data)) + name + data + crc

    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(bytes([0, fill, fill, fill])))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


def test_sidecar_png_found():
    png = _make_png()
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "Castlevania.state0.png").write_bytes(png)
        results = find_state_thumbnails("Castlevania", [d])
    assert len(results) == 1
    slot, data = results[0]
    assert slot == 0
    assert data == png


def test_multiple_slots_sorted():
    png = _make_png()
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        for i in [2, 0, 1]:
            (d / f"Game.state{i}.png").write_bytes(png)
        results = find_state_thumbnails("Game", [d])
    assert [s for s, _ in results] == [0, 1, 2]


def test_embedded_png_in_raw_state():
    png = _make_png(0xAB)
    # .state file = some junk bytes + PNG blob
    state_data = b"\x00" * 16 + png + b"\xFF" * 8
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "Game.state1").write_bytes(state_data)
        results = find_state_thumbnails("Game", [d])
    assert len(results) == 1
    slot, data = results[0]
    assert slot == 1
    assert data == png


def test_embedded_png_in_zlib_state():
    png = _make_png(0x77)
    # .state file = 4-byte header + zlib-compressed PNG
    compressed = zlib.compress(b"\x00" * 8 + png)
    state_data = b"RACH" + compressed  # fake 4-byte header
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "Game.state0").write_bytes(state_data)
        results = find_state_thumbnails("Game", [d])
    assert len(results) == 1
    _, data = results[0]
    assert data == png


def test_no_thumbnails_returns_empty():
    with tempfile.TemporaryDirectory() as tmp:
        results = find_state_thumbnails("MissingGame", [Path(tmp)])
    assert results == []


def test_sidecar_preferred_over_embedded():
    png_sidecar = _make_png(0x11)
    png_embedded = _make_png(0x22)
    state_data = b"\x00" * 4 + png_embedded
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "Game.state0").write_bytes(state_data)
        (d / "Game.state0.png").write_bytes(png_sidecar)
        results = find_state_thumbnails("Game", [d])
    assert len(results) == 1
    _, data = results[0]
    assert data == png_sidecar  # sidecar wins
