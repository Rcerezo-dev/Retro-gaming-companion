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

DUP-DISC-RA-1c: the raw-sector reader and ISO9660 directory walk
(``ra_cd_image.py``) are shared with ``ra_hash_saturn_dreamcast.py`` --
rcheevos uses the exact same ``cdreader.c``/``rc_cd_find_file_sector`` for
every console, PSX included, not something PSX-specific.
"""

from __future__ import annotations

import hashlib
import struct
import tempfile
from pathlib import Path

from rom_manager.retroachievements.ra_cd_image import (
    _MAX_HASH_SIZE,
    _CdImage,
    _extract_chd,
    _find_root_file,
    _first_cue_bin,
)


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


def _hash_bin_file(bin_path: Path) -> str | None:
    if not bin_path.exists():
        return None
    try:
        with _CdImage(bin_path) as cd:
            return _hash_from_cd_image(cd)
    except OSError:
        return None


def _hash_chd_file(chd_path: Path, chdman_path: Path | None) -> str | None:
    with tempfile.TemporaryDirectory(prefix="rommgr_chd_") as tmp:
        out_cue = _extract_chd(chd_path, chdman_path, tmp, "out.cue")
        if out_cue is None:
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


def _boot_serial_from_bin(bin_path: Path) -> str | None:
    if not bin_path.exists():
        return None
    try:
        with _CdImage(bin_path) as cd:
            boot = _find_boot_executable(cd)
    except OSError:
        return None
    if not boot:
        return None
    # RA-HASH-SUBDIR-1: BOOT= may point into a subdirectory ("TEKKEN3\SLUS_004.02")
    # -- the serial itself is only the last path component, unlike the hash's
    # exe_name (which keeps the full path, that's what RA's own hash uses).
    return boot[0].rsplit("\\", 1)[-1]


def detect_psx_boot_serial(path: Path, *, chdman_path: Path | None = None) -> str | None:
    """Boot executable name from a PS1 disc's own SYSTEM.CNF (e.g. "SLUS_004.02"),
    read the same way as ``compute_psx_ra_hash``.

    CATALOG-MATCH-REGION-1: a No-Intro/Redump title-fallback match can't tell
    "Tekken 3 (USA)" from "Tekken 3 (Europe)" once the region tag is stripped
    for comparison, and the file's own SHA1 never matches a .chd (the DAT
    hashes the raw track). The disc's real boot serial does -- normalize it
    (strip punctuation, uppercase) and compare against each DAT candidate's
    ``CatalogEntry.serial`` for an exact match, real content instead of a guess.
    """
    suffix = path.suffix.lower()
    if suffix == ".cue":
        bin_path = _first_cue_bin(path)
        return _boot_serial_from_bin(bin_path) if bin_path else None
    if suffix == ".bin":
        return _boot_serial_from_bin(path)
    if suffix == ".chd":
        with tempfile.TemporaryDirectory(prefix="rommgr_chd_serial_") as tmp:
            out_cue = _extract_chd(path, chdman_path, tmp, "out.cue")
            return _boot_serial_from_bin(_first_cue_bin(out_cue)) if out_cue else None
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
