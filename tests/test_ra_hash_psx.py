"""Tests for ra_hash_psx: a synthetic minimal PS1 disc image (raw 2352-byte
sectors, header_size=24) so the ISO9660 + SYSTEM.CNF + PS-X EXE parsing is
verified without needing a real disc image. Cross-checked against real
library data separately (see Tareas/backlog.md, DUP-DISC-RA-1): 124/259 real
.bin/.cue files hashed here matched RetroAchievements' own cached hashes
exactly, which is the actual proof this reimplements RA's algorithm
correctly -- this test only guards the byte-parsing logic against regressions.
"""

from __future__ import annotations

import hashlib
import struct
from pathlib import Path

from rom_manager.retroachievements.ra_hash_psx import compute_psx_ra_hash

_SECTOR_SIZE = 2352
_HEADER_SIZE = 24


def _msf_bytes(lba: int) -> bytes:
    total = lba + 150
    frames = total % 75
    total //= 75
    seconds = total % 60
    minutes = total // 60

    def bcd(n: int) -> int:
        return ((n // 10) << 4) | (n % 10)

    return bytes([bcd(minutes), bcd(seconds), bcd(frames)])


def _dir_record(name: str, sector: int, size: int) -> bytes:
    name_bytes = name.encode("ascii")
    rec = bytearray(33 + len(name_bytes))
    rec[2:6] = struct.pack("<I", sector)
    rec[10:14] = struct.pack("<I", size)
    rec[32] = len(name_bytes)
    rec[33:] = name_bytes
    if len(name_bytes) % 2 == 0:
        rec.append(0)
    rec[0] = len(rec)
    return bytes(rec)


def _build_psx_image(tmp_path: Path) -> Path:
    """Sector 16 = PVD (root dir -> sector 20), sector 20 = root directory
    (SYSTEM.CNF -> sector 21, TEST.EXE -> sector 22), sector 21 = SYSTEM.CNF
    content, sector 22 = a minimal PS-X EXE header (declared size 0, so the
    hash covers exactly this one 2048-byte sector)."""
    total_sectors = 23
    data = bytearray(total_sectors * _SECTOR_SIZE)

    def user_data(sector: int) -> memoryview:
        start = sector * _SECTOR_SIZE + _HEADER_SIZE
        return memoryview(data)[start : start + 2048]

    def sector_header(sector: int, sync: bool) -> None:
        start = sector * _SECTOR_SIZE
        if sync:
            data[start : start + 12] = bytes([0x00, *([0xFF] * 10), 0x00])
        data[start + 12 : start + 15] = _msf_bytes(sector)

    # Sector 16: sync pattern + PVD (logical block size @128, root dir record @156)
    sector_header(16, sync=True)
    pvd = user_data(16)
    pvd[0] = 1  # volume descriptor type 1 = Primary Volume Descriptor
    pvd[1:6] = b"CD001"
    pvd[128:130] = struct.pack("<H", 2048)
    root_rec = _dir_record(".", 20, 2048)
    pvd[156 : 156 + len(root_rec)] = root_rec

    # Sector 20: root directory contents
    sector_header(20, sync=False)
    root_dir = user_data(20)
    system_cnf_content = b"BOOT = cdrom:\\TEST.EXE;1\r\n"
    entries = _dir_record("SYSTEM.CNF;1", 21, len(system_cnf_content)) + _dir_record(
        "TEST.EXE;1", 22, 2048
    )
    root_dir[: len(entries)] = entries

    # Sector 21: SYSTEM.CNF content
    sector_header(21, sync=False)
    user_data(21)[: len(system_cnf_content)] = system_cnf_content

    # Sector 22: minimal PS-X EXE header (declared body size 0 -> hash range is
    # exactly this sector, 2048 bytes starting at the header)
    sector_header(22, sync=False)
    exe_sector = user_data(22)
    exe_sector[0:8] = b"PS-X EXE"
    exe_sector[28:32] = struct.pack("<I", 0)

    bin_path = tmp_path / "game.bin"
    bin_path.write_bytes(bytes(data))
    return bin_path


def test_compute_psx_ra_hash_matches_manual_computation(tmp_path: Path) -> None:
    bin_path = _build_psx_image(tmp_path)

    result = compute_psx_ra_hash(bin_path)

    # Independently reproduce what the hash *should* be: exe_name ("TEST.EXE",
    # no ";1") + the exe sector's full 2048 bytes (declared size 0 -> +2048).
    raw = bin_path.read_bytes()
    exe_sector_start = 22 * _SECTOR_SIZE + _HEADER_SIZE
    expected = hashlib.md5()
    expected.update(b"TEST.EXE")
    expected.update(raw[exe_sector_start : exe_sector_start + 2048])

    assert result == expected.hexdigest()


def test_compute_psx_ra_hash_unsupported_extension_returns_none(tmp_path: Path) -> None:
    p = tmp_path / "game.zip"
    p.write_bytes(b"not a disc image")

    assert compute_psx_ra_hash(p) is None


def test_compute_psx_ra_hash_missing_system_cnf_returns_none(tmp_path: Path) -> None:
    """A .bin with no readable ISO9660 filesystem at all (e.g. an audio
    track's raw data, not the data track) must fail closed, not raise."""
    p = tmp_path / "audio_track.bin"
    p.write_bytes(bytes(_SECTOR_SIZE * 4))  # all zeros -- no sync pattern, no CD001

    assert compute_psx_ra_hash(p) is None
