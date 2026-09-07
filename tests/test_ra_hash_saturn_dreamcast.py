"""Tests for ra_hash_saturn_dreamcast: synthetic minimal Saturn/Dreamcast disc
images (same raw-2352-byte-sector construction as test_ra_hash_psx.py) so the
header/ISO9660 parsing is verified without needing a real disc image. Unlike
PSX, this hasn't been cross-checked against real RA cache data yet (no
Saturn/Dreamcast library on this machine) -- see DUP-DISC-RA-1c in
Tareas/backlog.md.
"""

from __future__ import annotations

import hashlib
import struct
from pathlib import Path

from rom_manager.retroachievements.ra_hash_saturn_dreamcast import (
    compute_dreamcast_ra_hash,
    compute_saturn_ra_hash,
)

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


def _dir_record(name: str, sector: int, size: int, *, is_dir: bool = False) -> bytes:
    name_bytes = name.encode("ascii")
    rec = bytearray(33 + len(name_bytes))
    rec[2:6] = struct.pack("<I", sector)
    rec[10:14] = struct.pack("<I", size)
    rec[25] = 0x02 if is_dir else 0x00
    rec[32] = len(name_bytes)
    rec[33:] = name_bytes
    if len(name_bytes) % 2 == 0:
        rec.append(0)
    rec[0] = len(rec)
    return bytes(rec)


def _new_image(total_sectors: int):
    data = bytearray(total_sectors * _SECTOR_SIZE)

    def user_data(sector: int) -> memoryview:
        start = sector * _SECTOR_SIZE + _HEADER_SIZE
        return memoryview(data)[start : start + 2048]

    def sector_header(sector: int, sync: bool) -> None:
        start = sector * _SECTOR_SIZE
        if sync:
            data[start : start + 12] = bytes([0x00, *([0xFF] * 10), 0x00])
        data[start + 12 : start + 15] = _msf_bytes(sector)

    return data, user_data, sector_header


def _build_saturn_image(tmp_path: Path, *, magic: bytes = b"SEGA SEGASATURN ") -> Path:
    data, user_data, sector_header = _new_image(20)

    sector_header(0, sync=True)
    header = user_data(0)
    header[0:16] = magic
    header[16:32] = b"SATURN-TEST-DISC"

    # Sector 16: sync + CD001 -- geometry detection only, Saturn's own hash
    # never reads the ISO9660 filesystem.
    sector_header(16, sync=True)
    pvd = user_data(16)
    pvd[0] = 1
    pvd[1:6] = b"CD001"
    pvd[128:130] = struct.pack("<H", 2048)

    bin_path = tmp_path / "saturn.bin"
    bin_path.write_bytes(bytes(data))
    return bin_path


def test_compute_saturn_ra_hash_matches_manual_computation(tmp_path: Path) -> None:
    bin_path = _build_saturn_image(tmp_path)

    result = compute_saturn_ra_hash(bin_path)

    raw = bin_path.read_bytes()
    header_start = 0 * _SECTOR_SIZE + _HEADER_SIZE
    expected = hashlib.md5(raw[header_start : header_start + 512]).hexdigest()
    assert result == expected


def test_compute_saturn_ra_hash_rejects_non_saturn_header(tmp_path: Path) -> None:
    bin_path = _build_saturn_image(tmp_path, magic=b"NOT A SATURN HDR")
    assert compute_saturn_ra_hash(bin_path) is None


def test_compute_saturn_ra_hash_unsupported_extension_returns_none(tmp_path: Path) -> None:
    p = tmp_path / "game.iso"
    p.write_bytes(b"not a disc image")
    assert compute_saturn_ra_hash(p) is None


def _build_dreamcast_image(tmp_path: Path, *, boot_name: bytes = b"1ST_READ.BIN") -> Path:
    data, user_data, sector_header = _new_image(24)

    # Sector 0: 256-byte IP.BIN meta block
    sector_header(0, sync=True)
    ipbin = user_data(0)
    ipbin[0:16] = b"SEGA SEGAKATANA "
    ipbin[96:112] = boot_name.ljust(16, b" ")[:16]

    # Sector 16: PVD -> root dir at sector 20 (same layout as the PSX fixture)
    sector_header(16, sync=True)
    pvd = user_data(16)
    pvd[0] = 1
    pvd[1:6] = b"CD001"
    pvd[128:130] = struct.pack("<H", 2048)
    root_rec = _dir_record(".", 20, 2048)
    pvd[156 : 156 + len(root_rec)] = root_rec

    # Sector 20: root directory -- boot executable at sector 21
    sector_header(20, sync=False)
    root_dir = user_data(20)
    entries = _dir_record(f"{boot_name.decode()};1", 21, 2048)
    root_dir[: len(entries)] = entries

    # Sector 21: boot executable content
    sector_header(21, sync=False)
    user_data(21)[:] = bytes([0xAB]) * 2048

    bin_path = tmp_path / "dreamcast.bin"
    bin_path.write_bytes(bytes(data))
    return bin_path


def test_compute_dreamcast_ra_hash_matches_manual_computation(tmp_path: Path) -> None:
    bin_path = _build_dreamcast_image(tmp_path)

    result = compute_dreamcast_ra_hash(bin_path)

    raw = bin_path.read_bytes()
    ipbin_start = 0 * _SECTOR_SIZE + _HEADER_SIZE
    exe_start = 21 * _SECTOR_SIZE + _HEADER_SIZE
    expected = hashlib.md5()
    expected.update(raw[ipbin_start : ipbin_start + 256])
    expected.update(raw[exe_start : exe_start + 2048])

    assert result == expected.hexdigest()


def test_compute_dreamcast_ra_hash_rejects_non_dreamcast_header(tmp_path: Path) -> None:
    data, user_data, sector_header = _new_image(20)
    sector_header(0, sync=True)
    user_data(0)[0:16] = b"NOT A DC HEADER "
    bin_path = tmp_path / "not_dreamcast.bin"
    bin_path.write_bytes(bytes(data))

    assert compute_dreamcast_ra_hash(bin_path) is None


def test_compute_dreamcast_ra_hash_gdi_resolves_track_3(tmp_path: Path) -> None:
    """.gdi lists one file per track -- the hasher must open track 3 by
    number, not just grab the last line or the biggest file."""
    bin_path = _build_dreamcast_image(tmp_path)
    bin_path.rename(tmp_path / "track03.bin")
    gdi_path = tmp_path / "game.gdi"
    gdi_path.write_text(
        "3\n1 0 0 2352 track01.bin 0\n2 750 0 2352 track02.raw 0\n3 4500 4 2352 track03.bin 0\n",
        encoding="utf-8",
    )
    # track01/track02 referenced but never opened by our hasher -- Dreamcast
    # only ever reads track 3 (RA's own rc_hash_dreamcast does the same).

    result = compute_dreamcast_ra_hash(gdi_path)

    assert result == compute_dreamcast_ra_hash(tmp_path / "track03.bin")


def test_compute_dreamcast_ra_hash_unsupported_extension_returns_none(tmp_path: Path) -> None:
    p = tmp_path / "game.cdi"
    p.write_bytes(b"not a disc image")
    assert compute_dreamcast_ra_hash(p) is None
