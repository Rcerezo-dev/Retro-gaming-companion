"""Tests for hash_calculator.py — SHA1, MD5, CRC32 calculation."""

from __future__ import annotations

import hashlib
import os
import threading
import zlib
from pathlib import Path

import pytest

from rom_manager.hashing.hash_calculator import (
    FileHashes,
    HashingCancelled,
    calculate_hashes,
    calculate_hashes_batch,
)


def _expected(data: bytes) -> FileHashes:
    crc = zlib.crc32(data) & 0xFFFFFFFF
    return FileHashes(
        sha1=hashlib.sha1(data).hexdigest().upper(),
        md5=hashlib.md5(data).hexdigest().upper(),
        crc32=f"{crc:08X}",
    )


class TestCalculateHashes:
    def test_known_bytes(self, tmp_path: Path) -> None:
        data = b"Hello, Retro Vault!"
        p = tmp_path / "rom.bin"
        p.write_bytes(data)
        result = calculate_hashes(p)
        expected = _expected(data)
        assert result.sha1 == expected.sha1
        assert result.md5 == expected.md5
        assert result.crc32 == expected.crc32

    def test_empty_file(self, tmp_path: Path) -> None:
        p = tmp_path / "empty.nes"
        p.write_bytes(b"")
        result = calculate_hashes(p)
        expected = _expected(b"")
        assert result.sha1 == expected.sha1
        assert result.md5 == expected.md5
        assert result.crc32 == expected.crc32

    def test_output_is_uppercase_hex(self, tmp_path: Path) -> None:
        p = tmp_path / "game.gba"
        p.write_bytes(os.urandom(256))
        result = calculate_hashes(p)
        assert result.sha1 == result.sha1.upper()
        assert result.md5 == result.md5.upper()
        assert result.crc32 == result.crc32.upper()

    def test_sha1_length_is_40(self, tmp_path: Path) -> None:
        p = tmp_path / "game.sfc"
        p.write_bytes(b"\x00" * 512)
        assert len(calculate_hashes(p).sha1) == 40

    def test_md5_length_is_32(self, tmp_path: Path) -> None:
        p = tmp_path / "game.sfc"
        p.write_bytes(b"\x00" * 512)
        assert len(calculate_hashes(p).md5) == 32

    def test_crc32_length_is_8(self, tmp_path: Path) -> None:
        p = tmp_path / "game.sfc"
        p.write_bytes(b"\x00" * 512)
        assert len(calculate_hashes(p).crc32) == 8

    def test_crc32_padded_with_zeros(self, tmp_path: Path) -> None:
        # b"\x00" has CRC32 = 0, so the output should be "00000000" not "0"
        p = tmp_path / "zero.bin"
        p.write_bytes(b"\x00")
        result = calculate_hashes(p)
        assert len(result.crc32) == 8
        assert all(c in "0123456789ABCDEF" for c in result.crc32)

    def test_file_not_found_raises(self, tmp_path: Path) -> None:
        with pytest.raises(OSError):
            calculate_hashes(tmp_path / "nonexistent.gba")

    def test_large_file_chunked(self, tmp_path: Path) -> None:
        """Verify multi-chunk reading gives the same result as a single hash."""
        data = os.urandom(3 * 1024 * 1024)  # 3 MB > CHUNK_SIZE (1 MB)
        p = tmp_path / "large.iso"
        p.write_bytes(data)
        result = calculate_hashes(p)
        expected = _expected(data)
        assert result.sha1 == expected.sha1
        assert result.md5 == expected.md5
        assert result.crc32 == expected.crc32

    def test_null_bytes_handled(self, tmp_path: Path) -> None:
        data = b"\x00\xff\x00\xff" * 128
        p = tmp_path / "nulls.nes"
        p.write_bytes(data)
        result = calculate_hashes(p)
        assert result == _expected(data)

    def test_deterministic(self, tmp_path: Path) -> None:
        data = os.urandom(1024)
        p = tmp_path / "game.rom"
        p.write_bytes(data)
        assert calculate_hashes(p) == calculate_hashes(p)


class TestStopEvent:
    """PERF-1a — cancellation via stop_event."""

    def test_preset_stop_event_raises(self, tmp_path: Path) -> None:
        # Multi-chunk file so the read loop runs at least once.
        p = tmp_path / "big.iso"
        p.write_bytes(os.urandom(3 * 1024 * 1024))
        stop = threading.Event()
        stop.set()
        with pytest.raises(HashingCancelled):
            calculate_hashes(p, stop_event=stop)

    def test_unset_stop_event_completes(self, tmp_path: Path) -> None:
        data = b"Retro Vault"
        p = tmp_path / "game.gba"
        p.write_bytes(data)
        stop = threading.Event()  # never set
        assert calculate_hashes(p, stop_event=stop) == _expected(data)

    def test_empty_file_with_preset_stop_does_not_raise(self, tmp_path: Path) -> None:
        # Empty file: the read loop never iterates, so there is no chunk
        # boundary at which to cancel — it completes instantly.
        p = tmp_path / "empty.nes"
        p.write_bytes(b"")
        stop = threading.Event()
        stop.set()
        assert calculate_hashes(p, stop_event=stop) == _expected(b"")


class TestBatch:
    """PERF-1b — parallel hashing across files."""

    def test_batch_matches_sequential(self, tmp_path: Path) -> None:
        paths = []
        for i in range(10):
            p = tmp_path / f"rom_{i}.bin"
            p.write_bytes(os.urandom(2048 + i))
            paths.append(p)

        batch = calculate_hashes_batch(paths, max_workers=4)

        assert set(batch) == set(paths)
        for p in paths:
            assert batch[p] == calculate_hashes(p)

    def test_empty_paths_returns_empty(self) -> None:
        assert calculate_hashes_batch([]) == {}

    def test_preset_stop_event_returns_empty(self, tmp_path: Path) -> None:
        p = tmp_path / "rom.bin"
        p.write_bytes(os.urandom(1024))
        stop = threading.Event()
        stop.set()
        assert calculate_hashes_batch([p], stop_event=stop) == {}

    def test_missing_file_omitted_not_raised(self, tmp_path: Path) -> None:
        good = tmp_path / "good.bin"
        good.write_bytes(b"\x01\x02\x03")
        missing = tmp_path / "missing.bin"  # never created → OSError when hashed

        batch = calculate_hashes_batch([good, missing], max_workers=2)

        assert good in batch
        assert missing not in batch
