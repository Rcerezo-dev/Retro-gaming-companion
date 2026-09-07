"""Generic raw-CD-sector reader shared by every optical-disc RA hasher.

Extracted from ``ra_hash_psx.py`` (DUP-DISC-RA-1c): the sector/header-size
auto-detection and MSF math are disc-format-agnostic — RA's own C reference
(``cdreader.c::cdreader_determine_sector_size``/``cdreader_read_sector``)
uses the exact same routine for PSX, Saturn, Sega CD and Dreamcast, so this
class is the one place that logic lives instead of drifting across three
near-identical copies.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

_SYNC_PATTERN = bytes([0x00, *([0xFF] * 10), 0x00])
_CUE_FILE_RE = re.compile(r'FILE\s+"([^"]+)"|FILE\s+(\S+)', re.IGNORECASE)
_MAX_HASH_SIZE = 64 * 1024 * 1024  # rcheevos' MAX_BUFFER_SIZE (rc_hash_internal.h)


def _bcd(b: int) -> int:
    return (b >> 4) * 10 + (b & 0x0F)


def _msf_to_lba(msf: bytes) -> int:
    m, s, f = _bcd(msf[0]), _bcd(msf[1]), _bcd(msf[2])
    return ((m * 60) + s) * 75 + f - 150


class _CdImage:
    """Raw-CD-sector accessor for the data track at the start of *file_path*
    (single FILE, no other tracks ahead of it in the same file -- true for
    virtually every single-track dump, since RA only ever reads one specific
    track per console: track 1 for PSX/Saturn/Sega CD, track 3 for
    Dreamcast)."""

    def __init__(self, file_path: Path):
        self._fh = open(file_path, "rb")
        self.sector_size, self.header_size, self.first_sector = self._detect_geometry()

    def _detect_geometry(self) -> tuple[int, int, int]:
        for sector_size in (2352, 2336):
            self._fh.seek(16 * sector_size)
            header = self._fh.read(32)
            if len(header) >= 30 and header[:12] == _SYNC_PATTERN:
                header_size = 24 if header[25:30] == b"CD001" else 16
                # header was read from sector 16 (the PVD); the disc's own
                # embedded MSF address must be converted back to a track-
                # relative sector by subtracting that same probe offset.
                first_sector = _msf_to_lba(header[12:15]) - 16
                return sector_size, header_size, first_sector
        self._fh.seek(16 * 2048)
        header = self._fh.read(6)
        if header[1:6] == b"CD001":
            return 2048, 0, 0
        self._fh.seek(0, 2)
        size = self._fh.tell()
        if size % 2352 == 0:
            return 2352, 24, 0
        if size % 2336 == 0:
            return 2336, 8, 0
        # No sync pattern, no CD001 signature, size isn't even a multiple of
        # a known sector size -- there is no positive evidence this is a CD
        # image at all (e.g. an arcade ROM chip dump). A sentinel outside
        # _CUE_MODE_BY_GEOMETRY's keys, not a blind MODE1/2048 guess.
        return 0, 0, 0

    def read_sector(self, sector: int, n: int = 2048) -> bytes:
        offset = (sector - self.first_sector) * self.sector_size + self.header_size
        if offset < 0:
            return b""
        self._fh.seek(offset)
        return self._fh.read(n)

    def read_range(self, sector: int, size: int) -> bytes:
        out = bytearray()
        remaining = size
        while remaining > 0:
            chunk = self.read_sector(sector, min(2048, remaining))
            if not chunk:
                break
            out += chunk
            remaining -= len(chunk)
            sector += 1
        return bytes(out)

    def close(self) -> None:
        self._fh.close()

    def __enter__(self) -> _CdImage:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def _root_dir_location(cd: _CdImage) -> tuple[int, int, int] | None:
    """(dir_sector, num_sectors, logical_block_size) of the ISO9660 root directory."""
    pvd = cd.read_sector(16, 2048)
    if len(pvd) < 190:
        return None
    root_rec = pvd[156:190]
    dir_sector = root_rec[2] | (root_rec[3] << 8) | (root_rec[4] << 16)
    logical_block_size = pvd[128] | (pvd[129] << 8)
    dir_len = root_rec[10] | (root_rec[11] << 8) | (root_rec[12] << 16) | (root_rec[13] << 24)
    num_sectors = 1 if logical_block_size == 0 else max(1, dir_len // logical_block_size)
    return dir_sector, num_sectors, logical_block_size


def _find_entry(
    cd: _CdImage, dir_sector: int, num_sectors: int, name: str
) -> tuple[int, int, bool] | None:
    """(sector, size, is_directory) of *name* inside the directory starting at
    *dir_sector*, or None."""
    target = name.upper()
    target_len = len(target)
    sector = dir_sector
    for _ in range(num_sectors):
        buf = cd.read_sector(sector, 2048)
        pos = 0
        while pos < len(buf):
            rec_len = buf[pos]
            if rec_len == 0:
                break
            name_len = buf[pos + 32]
            entry_name = buf[pos + 33 : pos + 33 + name_len]
            if name_len >= target_len:
                prefix = entry_name[:target_len].decode("ascii", "replace").upper()
                next_byte = entry_name[target_len : target_len + 1]
                if (name_len == target_len or next_byte == b";") and prefix == target:
                    entry_sector = buf[pos + 2] | (buf[pos + 3] << 8) | (buf[pos + 4] << 16)
                    entry_size = (
                        buf[pos + 10]
                        | (buf[pos + 11] << 8)
                        | (buf[pos + 12] << 16)
                        | (buf[pos + 13] << 24)
                    )
                    is_dir = bool(buf[pos + 25] & 0x02)
                    return entry_sector, entry_size, is_dir
            pos += rec_len
        sector += 1
    return None


def _find_root_file(cd: _CdImage, name: str) -> tuple[int, int] | None:
    """(sector, size) of *name*, resolving ``\\``-separated subdirectory path
    components first (e.g. "TEKKEN3\\SLUS_004.02") -- a boot reference may
    point into a subfolder, not just the ISO9660 root (common on PS1, not an
    edge case; the same generic lookup -- rcheevos' ``rc_cd_find_file_sector``
    -- is what every console hasher here uses, PSX included)."""
    root = _root_dir_location(cd)
    if root is None:
        return None
    dir_sector, num_sectors, logical_block_size = root

    parts = [p for p in name.split("\\") if p]
    if not parts:
        return None

    for part in parts[:-1]:
        entry = _find_entry(cd, dir_sector, num_sectors, part)
        if entry is None or not entry[2]:
            return None
        dir_sector, entry_size, _ = entry
        num_sectors = 1 if logical_block_size == 0 else max(1, entry_size // logical_block_size)

    entry = _find_entry(cd, dir_sector, num_sectors, parts[-1])
    if entry is None:
        return None
    return entry[0], entry[1]


def _first_cue_bin(cue_path: Path) -> Path | None:
    """Path of the first ``FILE`` entry in a .cue sheet -- track 1, the only
    track every hasher here reads (single-track discs, or the data track of
    a multi-FILE cue where track 1 happens to be data)."""
    try:
        text = cue_path.read_text(errors="replace")
    except OSError:
        return None
    m = _CUE_FILE_RE.search(text)
    if not m:
        return None
    name = m.group(1) or m.group(2)
    return cue_path.parent / name


def _extract_chd(
    chd_path: Path, chdman_path: Path | None, tmp_dir: str, out_name: str
) -> Path | None:
    """Run ``chdman extractcd`` into *tmp_dir*/*out_name* (".cue" for a
    single-track CD CHD, ".gdi" for a GD-ROM CHD -- chdman picks the sheet
    format from the output extension) and return that path, or None on any
    failure."""
    # chdman_path may be a bare command name resolved via PATH (not a literal
    # file relative to cwd) -- don't require .exists(), let subprocess itself
    # raise/fail if it truly can't be found.
    if chdman_path is None:
        return None
    out_path = Path(tmp_dir) / out_name
    try:
        subprocess.run(
            [str(chdman_path), "extractcd", "-i", str(chd_path), "-o", str(out_path), "-f"],
            check=True,
            capture_output=True,
            timeout=300,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None
    return out_path if out_path.exists() else None
