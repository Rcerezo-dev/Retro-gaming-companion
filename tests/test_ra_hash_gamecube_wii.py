"""Tests for ra_hash_gamecube_wii: a synthetic minimal GameCube disc image
(just the fields RA's own algorithm actually reads: magic word, apploader
sizes, boot DOL offset table, one non-empty segment) so the byte-parsing
logic is verified without needing a real disc image. Cross-checked against
real library data separately (see Tareas/backlog.md, INBOX-RA-HASH-GAP):
2 real GameCube .iso files hashed here matched RetroAchievements' own cached
hashes exactly ("The Legend of Zelda: The Wind Waker", "Metroid Prime 2:
Echoes") -- this test only guards the byte-parsing logic against regressions.
"""

from __future__ import annotations

import hashlib
import struct
from pathlib import Path

from rom_manager.retroachievements.ra_hash_gamecube_wii import (
    compute_gamecube_ra_hash,
    compute_wii_ra_hash,
)

_BASE_HEADER_SIZE = 0x2440
_APPLOADER_HEADER_SIZE = 0x20
_HEADER_SIZE = _BASE_HEADER_SIZE + _APPLOADER_HEADER_SIZE  # body=trailer=0
_SEGMENT_DATA = b"segment zero data byte content!"  # arbitrary, non-empty


def _build_gamecube_image(tmp_path: Path, *, magic: bytes | None = b"\xc2\x33\x9f\x3d") -> Path:
    dol_offset = _HEADER_SIZE
    segment_offset = dol_offset + 0xD8
    total_size = segment_offset + len(_SEGMENT_DATA)

    buf = bytearray(total_size)
    if magic is not None:
        buf[0x1C:0x20] = magic
    # apploader_body_size / apploader_trailer_size = 0 (already zero-filled)
    buf[0x420:0x424] = struct.pack(">I", dol_offset)

    addr_table = bytearray(0xD8)
    addr_table[0:4] = struct.pack(">I", segment_offset)  # segment 0 offset
    addr_table[0x90:0x94] = struct.pack(">I", len(_SEGMENT_DATA))  # segment 0 size
    buf[dol_offset : dol_offset + 0xD8] = addr_table

    buf[segment_offset : segment_offset + len(_SEGMENT_DATA)] = _SEGMENT_DATA

    path = tmp_path / "game.iso"
    path.write_bytes(bytes(buf))
    return path


def test_compute_gamecube_ra_hash_matches_manual_computation(tmp_path: Path) -> None:
    path = _build_gamecube_image(tmp_path)
    result = compute_gamecube_ra_hash(path)

    raw = path.read_bytes()
    expected = hashlib.md5()
    expected.update(raw[:_HEADER_SIZE])
    expected.update(_SEGMENT_DATA)

    assert result == expected.hexdigest()


def test_compute_gamecube_ra_hash_rejects_wrong_magic(tmp_path: Path) -> None:
    path = _build_gamecube_image(tmp_path, magic=b"\x00\x00\x00\x00")
    assert compute_gamecube_ra_hash(path) is None


def test_compute_gamecube_ra_hash_missing_file_returns_none(tmp_path: Path) -> None:
    assert compute_gamecube_ra_hash(tmp_path / "does-not-exist.iso") is None


def test_compute_wii_ra_hash_rejects_non_wii_file(tmp_path: Path) -> None:
    path = tmp_path / "game.iso"
    path.write_bytes(b"not a wii disc" + b"\x00" * 0x100)
    assert compute_wii_ra_hash(path) is None


# ── Wii encrypted-disc synthetic image ────────────────────────────────────────
# One game partition (type 0, never skipped) with a tiny TMD blob and exactly
# one 0x8000-byte cluster of "encrypted" data -- enough to exercise partition
# table parsing, the update-partition skip, and the cluster hash (which reads
# the raw bytes directly, no AES: real disc encryption is irrelevant to RA's
# hash, only the 0x400-byte per-cluster header is skipped).
_PART_TABLE_OFFSET = 0x60000
_PART_BASE = 0x61000
_TMD_OFFSET = 0x400
_TMD_SIZE = 0x100
_TMD_DATA = (b"TMD-DATA" * 0x100)[:_TMD_SIZE]
_PART_DATA_OFFSET = 0x70000
_CLUSTER_PAYLOAD = bytes(i % 256 for i in range(0x7C00))


def _build_wii_encrypted_image(tmp_path: Path) -> Path:
    total_size = _PART_DATA_OFFSET + 0x8000
    buf = bytearray(total_size)
    buf[0x18:0x1C] = b"\x5d\x1c\x9e\xa3"
    buf[0x61] = 0x00  # encrypted

    buf[0x4E000:0x4E004] = b"PAL "  # region code

    # partition_info_table: 1 partition in group 0, table at _PART_TABLE_OFFSET
    buf[0x40000:0x40004] = struct.pack(">I", 1)
    buf[0x40004:0x40008] = struct.pack(">I", _PART_TABLE_OFFSET >> 2)
    buf[0x40008:0x40020] = b"\x00" * 24  # groups 1-3 empty

    # partition table: one entry (part_base>>2, type=0 -- never the update partition)
    buf[_PART_TABLE_OFFSET : _PART_TABLE_OFFSET + 4] = struct.pack(">I", _PART_BASE >> 2)
    buf[_PART_TABLE_OFFSET + 4 : _PART_TABLE_OFFSET + 8] = struct.pack(">I", 0)

    # TMD size/offset at part_base+0x2A4
    buf[_PART_BASE + 0x2A4 : _PART_BASE + 0x2A8] = struct.pack(">I", _TMD_SIZE)
    buf[_PART_BASE + 0x2A8 : _PART_BASE + 0x2AC] = struct.pack(">I", _TMD_OFFSET >> 2)
    buf[_PART_BASE + _TMD_OFFSET : _PART_BASE + _TMD_OFFSET + _TMD_SIZE] = _TMD_DATA

    # partition data offset/size at part_base+0x2B8 -- exactly one cluster.
    buf[_PART_BASE + 0x2B8 : _PART_BASE + 0x2BC] = struct.pack(">I", _PART_DATA_OFFSET >> 2)
    buf[_PART_BASE + 0x2BC : _PART_BASE + 0x2C0] = struct.pack(">I", 0x8000 >> 2)

    buf[_PART_DATA_OFFSET + 0x400 : _PART_DATA_OFFSET + 0x400 + 0x7C00] = _CLUSTER_PAYLOAD

    path = tmp_path / "game.iso"
    path.write_bytes(bytes(buf))
    return path


def test_compute_wii_ra_hash_encrypted_matches_manual_computation(tmp_path: Path) -> None:
    path = _build_wii_encrypted_image(tmp_path)
    result = compute_wii_ra_hash(path)

    expected = hashlib.md5()
    expected.update(path.read_bytes()[0:0x80])  # main header
    expected.update(b"PAL ")  # region code
    expected.update(_TMD_DATA)
    expected.update(_CLUSTER_PAYLOAD)

    assert result == expected.hexdigest()
