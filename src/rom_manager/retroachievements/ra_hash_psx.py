"""PSX (PlayStation 1) disc hashing per RetroAchievements' hashing spec.

RA does not hash the whole disc image -- it locates SYSTEM.CNF inside the
ISO9660 filesystem on the data track, extracts the boot executable name from
the BOOT= line, and hashes: exe_name (as ASCII text) + the boot executable's
raw bytes (PS-X EXE header included). This is a from-scratch reimplementation
of that algorithm, cross-checked against rcheevos' reference implementation
(github.com/RetroAchievements/rcheevos, src/rhash/hash_disc.c::rc_hash_psx +
src/rhash/cdreader.c) -- not a port of the C, but byte-for-byte faithful to
it, including its quirks (case-sensitive "BOOT"/"cdrom:" match) since a
"cleaner" reimplementation would compute a *different*, non-matching hash.

Supports: bare .bin, .cue+.bin (first FILE only -- track 1, the only one RA
reads, is always the first FILE in a cue), and .chd (extracted via chdman,
see AppConfig/tools/chdman.exe). ZIP-wrapped images and .ccd/.ecm/.img/.pbp
are not supported yet -- return None. Multi-FILE cue sheets with a nonzero
pregap on track 1 (very rare for PS1) are also out of scope; sector geometry
auto-detection (sync pattern -> file-size-modulo fallback) covers everything
else RA's own reader does.
"""

from __future__ import annotations

import hashlib
import re
import struct
import subprocess
import tempfile
from pathlib import Path

_SYNC_PATTERN = bytes([0x00, *([0xFF] * 10), 0x00])
_MAX_HASH_SIZE = 64 * 1024 * 1024
_CUE_FILE_RE = re.compile(r'FILE\s+"([^"]+)"|FILE\s+(\S+)', re.IGNORECASE)


def _bcd(b: int) -> int:
    return (b >> 4) * 10 + (b & 0x0F)


def _msf_to_lba(msf: bytes) -> int:
    m, s, f = _bcd(msf[0]), _bcd(msf[1]), _bcd(msf[2])
    return ((m * 60) + s) * 75 + f - 150


class _CdImage:
    """Raw-CD-sector accessor for the data track at the start of *file_path*
    (single FILE, no other tracks ahead of it in the same file -- true for
    virtually every PS1 dump, since RA only ever reads track 1)."""

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
    components first (e.g. "TEKKEN3\\SLUS_004.02") -- a SYSTEM.CNF's BOOT=
    line may point into a subfolder, not just the ISO9660 root (common on
    PS1, not an edge case)."""
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


def _parse_boot_exe_name(data: bytes) -> str | None:
    """Extract the boot executable name from a SYSTEM.CNF's BOOT= line.

    Matches rcheevos byte-for-byte: "BOOT" and the "cdrom:" prefix are
    matched case-*sensitively* (not "boot"/"CDROM:") -- real SYSTEM.CNF
    files always use this exact casing, and replicating the same match
    (rather than a more lenient one) is what makes our hash equal RA's.
    """
    idx = data.find(b"BOOT")
    n = len(data)
    while idx != -1:
        ptr = idx + 4
        while ptr < n and data[ptr : ptr + 1].isspace():
            ptr += 1
        if ptr < n and data[ptr] == ord("="):
            ptr += 1
            while ptr < n and data[ptr : ptr + 1].isspace():
                ptr += 1
            if data[ptr : ptr + 6] == b"cdrom:":
                ptr += 6
            while ptr < n and data[ptr : ptr + 1] == b"\\":
                ptr += 1
            start = ptr
            while ptr < n and not data[ptr : ptr + 1].isspace() and data[ptr : ptr + 1] != b";":
                ptr += 1
            if ptr > start:
                return data[start:ptr].decode("ascii", errors="replace")
            return None
        idx = data.find(b"BOOT", idx + 1)
    return None


def _find_boot_executable(cd: _CdImage) -> tuple[str, int, int] | None:
    loc = _find_root_file(cd, "SYSTEM.CNF")
    if loc:
        sector, _size = loc
        exe_name = _parse_boot_exe_name(cd.read_sector(sector, 2048))
        if exe_name:
            found = _find_root_file(cd, exe_name)
            if found:
                return exe_name, found[0], found[1]
    found = _find_root_file(cd, "PSX.EXE")
    if found:
        return "PSX.EXE", found[0], found[1]
    return None


def _hash_from_cd_image(cd: _CdImage) -> str | None:
    boot = _find_boot_executable(cd)
    if not boot:
        return None
    exe_name, sector, _iso_size = boot
    header = cd.read_sector(sector, 32)
    if len(header) < 32 or header[:7] != b"PS-X EX":
        return None
    exe_size = struct.unpack_from("<I", header, 28)[0] + 2048
    exe_size = min(exe_size, _MAX_HASH_SIZE)

    digest = hashlib.md5()
    digest.update(exe_name.encode("ascii", errors="replace"))
    digest.update(cd.read_range(sector, exe_size))
    return digest.hexdigest()


def _first_cue_bin(cue_path: Path) -> Path | None:
    try:
        text = cue_path.read_text(errors="replace")
    except OSError:
        return None
    m = _CUE_FILE_RE.search(text)
    if not m:
        return None
    name = m.group(1) or m.group(2)
    return cue_path.parent / name


def _hash_bin_file(bin_path: Path) -> str | None:
    if not bin_path.exists():
        return None
    try:
        with _CdImage(bin_path) as cd:
            return _hash_from_cd_image(cd)
    except OSError:
        return None


def _hash_chd_file(chd_path: Path, chdman_path: Path | None) -> str | None:
    # chdman_path may be a bare command name resolved via PATH (not a literal
    # file relative to cwd) -- don't require .exists(), let subprocess itself
    # raise/fail if it truly can't be found.
    if chdman_path is None:
        return None
    with tempfile.TemporaryDirectory(prefix="rommgr_chd_") as tmp:
        out_cue = Path(tmp) / "out.cue"
        try:
            subprocess.run(
                [str(chdman_path), "extractcd", "-i", str(chd_path), "-o", str(out_cue), "-f"],
                check=True,
                capture_output=True,
                timeout=300,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
            return None
        if not out_cue.exists():
            return None
        return compute_psx_ra_hash(out_cue)


_CUE_MODE_BY_GEOMETRY = {
    (2352, 24): "MODE2/2352",
    (2352, 16): "MODE1/2352",
    (2048, 0): "MODE1/2048",
    (2336, 8): "MODE2/2336",
}


def detect_bin_cue_mode(bin_path: Path) -> str | None:
    """CUE ``MODE`` string for a bare .bin's detected sector geometry (e.g.
    "MODE2/2352"), or None if the geometry isn't one of the standard ones a
    synthesized single-track .cue can declare, or the track doesn't start at
    the beginning of the file (``first_sector != 0`` -- a pregap-adjusted
    dump; too rare here to be worth a general synthetic .cue)."""
    try:
        with _CdImage(bin_path) as cd:
            if cd.first_sector != 0:
                return None
            return _CUE_MODE_BY_GEOMETRY.get((cd.sector_size, cd.header_size))
    except OSError:
        return None


def compute_psx_ra_hash(path: Path, *, chdman_path: Path | None = None) -> str | None:
    """RetroAchievements MD5 hash for a PS1 disc image, or None if the format
    isn't supported yet or the image couldn't be read. *chdman_path* is
    required to hash a .chd (pass ``AppConfig.chdman_path`` or similar)."""
    suffix = path.suffix.lower()
    if suffix == ".cue":
        bin_path = _first_cue_bin(path)
        return _hash_bin_file(bin_path) if bin_path else None
    if suffix == ".bin":
        return _hash_bin_file(path)
    if suffix == ".chd":
        return _hash_chd_file(path, chdman_path)
    return None
