"""GameCube/Wii disc hashing per RetroAchievements' hashing spec.

RA does not hash the whole disc image -- for GameCube it hashes the
apploader header plus every non-empty ``main.dol`` code/data segment (18
segments max: 7 code + 11 data); for Wii it hashes the 128-byte main header,
the 4-byte region code, and, per game partition (the "update" partition,
type 1, is always skipped), the title metadata (TMD) and the partition data
itself -- read as raw encrypted bytes if the disc is still encrypted (no AES
needed: RA hashes the *encrypted* cluster bytes directly, skipping only the
0x400-byte hash block at the start of every 0x8000-byte cluster), or via the
same apploader/DOL algorithm as GameCube (with an extra 2-bit offset shift)
if the disc has been pre-decrypted. This is a from-scratch reimplementation
of that algorithm, cross-checked against rcheevos' reference implementation
(github.com/RetroAchievements/rcheevos, src/rhash/hash_disc.c::
rc_hash_gamecube / rc_hash_wii / rc_hash_wii_disc /
rc_hash_nintendo_disc_partition) -- not a port of the C, but byte-for-byte
faithful to it, since a "cleaner" reimplementation would compute a
*different*, non-matching hash. Verified against real games in this
library's own RA hash cache (``.rommgr/ra_cache/ra_hashes_16.json``): "The
Legend of Zelda: The Wind Waker" and "Metroid Prime 2: Echoes" both hash to
their known RA MD5 exactly.

Supports: raw, uncompressed disc images only (``.iso``/``.gcm`` for
GameCube, ``.iso`` for Wii) -- RA's own algorithm requires random access to
arbitrary byte offsets across the whole disc, which only a raw image gives
for free. ``.rvz`` (Dolphin's compressed format) and any other compressed
container are NOT supported here and return None -- there is no decompression
tool for that format in this project's toolset (unlike ``.chd``, which
``chdman`` already handles for PSX), and adding one would mean a new runtime
dependency the project's stdlib-only rule doesn't allow for. The Wii disc
path is implemented faithfully from the spec above but is UNVERIFIED against
real cached RA hashes -- this library has no real Wii discs to test against
(``F:\\Juegos Retro\\wii\\`` only holds a homebrew WAD, no commercial games);
GameCube is the one actually confirmed end-to-end. WiiWare (.wad) is out of
scope -- it isn't a disc image and isn't what INBOX-RA-HASH-GAP asked for.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import BinaryIO

_BASE_HEADER_SIZE = 0x2440
_MAX_HEADER_SIZE = 1024 * 1024
_MAX_CHUNK_SIZE = 1024 * 1024

_GAMECUBE_MAGIC = bytes((0xC2, 0x33, 0x9F, 0x3D))
_WII_MAGIC = bytes((0x5D, 0x1C, 0x9E, 0xA3))

_WII_MAIN_HEADER_SIZE = 0x80
_WII_REGION_CODE_ADDRESS = 0x4E000
_WII_CLUSTER_SIZE = 0x7C00
_WII_MAX_CLUSTER_COUNT = 1024
_WII_UPDATE_PARTITION_TYPE = 1


def _u32(data: bytes, offset: int = 0) -> int:
    return int.from_bytes(data[offset : offset + 4], "big")


def _hash_nintendo_disc_partition(
    md5: hashlib._Hash, f: BinaryIO, part_offset: int, wii_shift: int
) -> None:
    """Append the header + every non-empty main.dol segment for one
    partition (GameCube's only partition at offset 0, or one already-
    decrypted Wii partition at *part_offset*) to *md5*."""
    f.seek(part_offset + _BASE_HEADER_SIZE + 0x14)
    apploader_body_size = _u32(f.read(4))
    apploader_trailer_size = _u32(f.read(4))
    header_size = _BASE_HEADER_SIZE + 0x20 + apploader_body_size + apploader_trailer_size
    header_size = min(header_size, _MAX_HEADER_SIZE)

    f.seek(part_offset)
    header = f.read(header_size)
    md5.update(header)

    # GetBootDOLOffset -- header_size is always > 0x423, header already has it.
    dol_offset = _u32(header, 0x420) << wii_shift

    f.seek(part_offset + dol_offset)
    addr_buffer = f.read(0xD8)
    dol_offsets = [_u32(addr_buffer, ix * 4) << wii_shift for ix in range(18)]
    dol_sizes = [_u32(addr_buffer, 0x90 + ix * 4) << wii_shift for ix in range(18)]

    for offset, size in zip(dol_offsets, dol_sizes):
        if size == 0:
            continue
        f.seek(part_offset + offset)
        remaining = size
        while remaining > _MAX_CHUNK_SIZE:
            md5.update(f.read(_MAX_CHUNK_SIZE))
            remaining -= _MAX_CHUNK_SIZE
        md5.update(f.read(remaining))


def compute_gamecube_ra_hash(path: Path) -> str | None:
    """RetroAchievements MD5 for a raw GameCube disc image (``.iso``/``.gcm``),
    or None if the format isn't a recognized GameCube disc."""
    try:
        with path.open("rb") as f:
            f.seek(0x1C)
            if f.read(4) != _GAMECUBE_MAGIC:
                return None
            md5 = hashlib.md5()
            _hash_nintendo_disc_partition(md5, f, 0, 0)
            return md5.hexdigest()
    except OSError:
        return None


def _hash_wii_disc(md5: hashlib._Hash, f: BinaryIO) -> None:
    f.seek(0x61)
    encrypted = f.read(1) == b"\x00"

    f.seek(0)
    md5.update(f.read(_WII_MAIN_HEADER_SIZE))

    f.seek(_WII_REGION_CODE_ADDRESS)
    md5.update(f.read(4))

    f.seek(0x40000)
    partition_info_table = [_u32(f.read(4)) for _ in range(8)]
    total_partition_count = sum(partition_info_table[0::2])
    if total_partition_count == 0:
        raise ValueError("No partitions found")

    partition_table: list[tuple[int, int]] = []
    for jx in range(0, 8, 2):
        count = partition_info_table[jx]
        f.seek(partition_info_table[jx + 1] << 2)
        for _ in range(count):
            part_offset_raw = _u32(f.read(4))
            part_type = _u32(f.read(4))
            partition_table.append((part_offset_raw, part_type))

    for part_offset_raw, part_type in partition_table:
        if part_type == _WII_UPDATE_PARTITION_TYPE:
            continue
        part_base = part_offset_raw << 2

        f.seek(part_base + 0x2A4)
        tmd_size = _u32(f.read(4))
        tmd_offset = _u32(f.read(4)) << 2
        tmd_size = min(tmd_size, _WII_CLUSTER_SIZE)
        f.seek(part_base + tmd_offset)
        md5.update(f.read(tmd_size))

        f.seek(part_base + 0x2B8)
        part_offset = _u32(f.read(4)) << 2
        part_size = _u32(f.read(4)) << 2

        if encrypted:
            cluster_count = min(part_size // 0x8000, _WII_MAX_CLUSTER_COUNT)
            for ix in range(cluster_count):
                f.seek(part_offset + (ix * 0x8000) + 0x400)
                md5.update(f.read(_WII_CLUSTER_SIZE))
        else:
            _hash_nintendo_disc_partition(md5, f, part_offset, 2)


def compute_wii_ra_hash(path: Path) -> str | None:
    """RetroAchievements MD5 for a raw Wii disc image (``.iso``), or None if
    the format isn't a recognized Wii disc. UNVERIFIED against a real cached
    RA hash -- see module docstring, this library has no Wii discs to test
    against; implemented faithfully from the rcheevos source instead."""
    try:
        with path.open("rb") as f:
            f.seek(0x18)
            if f.read(4) != _WII_MAGIC:
                return None
            md5 = hashlib.md5()
            _hash_wii_disc(md5, f)
            return md5.hexdigest()
    except (OSError, ValueError):
        return None
