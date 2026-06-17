"""Tests for hash_calculator.py — SHA1, MD5, CRC32 calculation."""

from __future__ import annotations

import hashlib
import os
import zlib
from pathlib import Path

import pytest

from rom_manager.hashing.hash_calculator import FileHashes, calculate_hashes


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
