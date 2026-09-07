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

from rom_manager.retroachievements.ra_hash_psx import (
    compute_psx_ra_hash,
    detect_bin_cue_mode,
    detect_psx_boot_serial,
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


def _build_psx_image(tmp_path: Path) -> Path:
    """Sector 16 = PVD (root dir -> sector 20), sector 20 = root directory
    (SYSTEM.CNF -> sector 21, TEST.EXE -> sector 22), sector 21 = SYSTEM.CNF
    content, sector 22 = a minimal PS-X EXE header (declared size 0, so the
    hash covers exactly this one 2048-byte sector)."""
    # CHDMAN-TEST-COMPRESS-1: 23 sectores (el mínimo que cubre el layout real)
    # hace fallar la compresión por defecto de chdman.exe -- 64 da margen de
    # sobra (el umbral real medido fue 28) sin cambiar nada del contenido.
    total_sectors = 64
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

    # CHDMAN-TEST-COMPRESS-1: sectores 23.. son solo relleno con header válido
    # (sin datos) -- chdman.exe 0.251 falla a comprimir (cdlz/cdzl/cdfl, no a
    # -c none) discos de menos de ~28 sectores, algo que nunca ocurre con un
    # .bin real. El hash RA solo lee hasta el sector 22 (tamaño de EXE
    # declarado 0), así que este relleno no afecta a ningún test de hash.
    for sector in range(23, total_sectors):
        sector_header(sector, sync=False)

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


def test_detect_psx_boot_serial(tmp_path: Path) -> None:
    bin_path = _build_psx_image(tmp_path)
    assert detect_psx_boot_serial(bin_path) == "TEST.EXE"


def test_detect_psx_boot_serial_unsupported_format(tmp_path: Path) -> None:
    pbp = tmp_path / "game.pbp"
    pbp.write_bytes(b"not a disc")
    assert detect_psx_boot_serial(pbp) is None


def _build_psx_image_with_subdir_boot(tmp_path: Path) -> Path:
    """Same layout as ``_build_psx_image``, but ``BOOT=`` points into a
    subdirectory (``cdrom:\\TEST\\GAME.EXE``) -- the RA-HASH-SUBDIR-1 case:
    the boot executable does not live in the ISO9660 root, a common PS1
    pattern (e.g. real-world ``TEKKEN3\\SLUS_004.02``)."""
    total_sectors = 25
    data = bytearray(total_sectors * _SECTOR_SIZE)

    def user_data(sector: int) -> memoryview:
        start = sector * _SECTOR_SIZE + _HEADER_SIZE
        return memoryview(data)[start : start + 2048]

    def sector_header(sector: int, sync: bool) -> None:
        start = sector * _SECTOR_SIZE
        if sync:
            data[start : start + 12] = bytes([0x00, *([0xFF] * 10), 0x00])
        data[start + 12 : start + 15] = _msf_bytes(sector)

    sector_header(16, sync=True)
    pvd = user_data(16)
    pvd[0] = 1
    pvd[1:6] = b"CD001"
    pvd[128:130] = struct.pack("<H", 2048)
    root_rec = _dir_record(".", 20, 2048)
    pvd[156 : 156 + len(root_rec)] = root_rec

    # Sector 20: root directory -- SYSTEM.CNF + a "TEST" subdirectory (sector 23)
    sector_header(20, sync=False)
    root_dir = user_data(20)
    system_cnf_content = b"BOOT = cdrom:\\TEST\\GAME.EXE;1\r\n"
    entries = _dir_record("SYSTEM.CNF;1", 21, len(system_cnf_content)) + _dir_record(
        "TEST", 23, 2048, is_dir=True
    )
    root_dir[: len(entries)] = entries

    sector_header(21, sync=False)
    user_data(21)[: len(system_cnf_content)] = system_cnf_content

    # Sector 23: "TEST" subdirectory contents -- GAME.EXE (sector 24)
    sector_header(23, sync=False)
    sub_dir = user_data(23)
    sub_entries = _dir_record("GAME.EXE;1", 24, 2048)
    sub_dir[: len(sub_entries)] = sub_entries

    sector_header(24, sync=False)
    exe_sector = user_data(24)
    exe_sector[0:8] = b"PS-X EXE"
    exe_sector[28:32] = struct.pack("<I", 0)

    bin_path = tmp_path / "game.bin"
    bin_path.write_bytes(bytes(data))
    return bin_path


def test_compute_psx_ra_hash_boot_in_subdirectory(tmp_path: Path) -> None:
    """RA-HASH-SUBDIR-1: BOOT= pointing into a subfolder must resolve, not
    silently return None."""
    bin_path = _build_psx_image_with_subdir_boot(tmp_path)

    result = compute_psx_ra_hash(bin_path)

    raw = bin_path.read_bytes()
    exe_sector_start = 24 * _SECTOR_SIZE + _HEADER_SIZE
    expected = hashlib.md5()
    expected.update(b"TEST\\GAME.EXE")
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


def test_detect_bin_cue_mode_rejects_file_with_no_geometry_evidence(tmp_path: Path) -> None:
    """Regression (found against the real library): an arcade ROM chip dump
    (e.g. 'mpr-15574.bin', 1048576 bytes -- not a multiple of 2352 or 2336,
    no sync pattern, no CD001) used to fall through _detect_geometry's final
    'return 2048, 0, 0' and get reported as a valid PS1 disc geometry with
    zero positive evidence. Must return None instead."""
    p = tmp_path / "mpr-15574.bin"
    p.write_bytes(bytes(1_048_576))

    assert detect_bin_cue_mode(p) is None
