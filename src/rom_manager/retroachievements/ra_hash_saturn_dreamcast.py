"""Sega Saturn and Dreamcast disc hashing per RetroAchievements' hashing spec.

DUP-DISC-RA-1c: same purpose as ``ra_hash_psx.py`` (let duplicate-detection
tell "no RA data yet" from "already have the RA-supported copy") extended to
the two other disc consoles the project cares about. Cross-checked against
rcheevos' reference implementation (github.com/RetroAchievements/rcheevos,
src/rhash/hash_disc.c::rc_hash_sega_cd / rc_hash_dreamcast) -- not a port of
the C, but byte-for-byte faithful to it. Shares the raw-sector reader and
ISO9660 directory walk with the PSX module (``ra_cd_image.py``); Wii is
explicitly out of scope (RA hashes it very differently, not a CD at all).

Saturn: RA does NOT parse any filesystem here -- it hashes the raw 512-byte
volume+ROM header at the very start of track 1 verbatim (rcheevos' own
comment: "hashing the volume and ROM headers is sufficient for identifying
the game" -- a full boot-executable hash was deliberately rejected as
overkill, unlike PSX/Dreamcast). Sega CD uses the exact same function and
header layout in rcheevos (just a different magic string); not implemented
here since this project has no Sega CD content, but ``_hash_track1_header``
would need only its magic added to `_TRACK1_HEADER_MAGICS` to support it.

Dreamcast: the data track (track 3 on a real GD-ROM) starts with a 256-byte
IP.BIN meta block ("SEGA SEGAKATANA " magic); RA hashes that block verbatim,
then locates the boot executable named at IP.BIN offset 96 (via the same
generic ISO9660 lookup PSX uses) and hashes its raw bytes -- no filename text
mixed in this time, unlike PSX. GD-ROM's track 3 is normally its own file
(.gdi lists one file per track); mil-cd (single-track Dreamcast-on-plain-CD)
and any container where track 3 shares a file with earlier tracks are out of
scope -- return None, same policy as PSX's own documented gaps.
"""

from __future__ import annotations

import hashlib
import re
import tempfile
from pathlib import Path

from rom_manager.retroachievements.ra_cd_image import (
    _MAX_HASH_SIZE,
    _CdImage,
    _extract_chd,
    _find_root_file,
    _first_cue_bin,
)

_TRACK1_HEADER_SIZE = 512
_TRACK1_HEADER_MAGICS = (b"SEGA SEGASATURN ",)  # Sega CD's "SEGADISCSYSTEM  " not needed yet

_DREAMCAST_MAGIC = b"SEGA SEGAKATANA "
_DREAMCAST_HEADER_SIZE = 256
_DREAMCAST_BOOT_FIELD = slice(96, 112)  # 16 bytes, https://mc.pp.se/dc/ip0000.bin.html

_GDI_LINE_RE = re.compile(r'^\s*(\d+)\s+-?\d+\s+\d+\s+\d+\s+(?:"([^"]+)"|(\S+))')


# ── Saturn ─────────────────────────────────────────────────────────────────


def _hash_track1_header(cd: _CdImage) -> str | None:
    header = cd.read_sector(0, _TRACK1_HEADER_SIZE)
    if len(header) < _TRACK1_HEADER_SIZE or header[:16] not in _TRACK1_HEADER_MAGICS:
        return None
    return hashlib.md5(header).hexdigest()


def _hash_saturn_bin_file(bin_path: Path) -> str | None:
    if not bin_path.exists():
        return None
    try:
        with _CdImage(bin_path) as cd:
            return _hash_track1_header(cd)
    except OSError:
        return None


def compute_saturn_ra_hash(path: Path, *, chdman_path: Path | None = None) -> str | None:
    """RetroAchievements MD5 hash for a Saturn disc image, or None if the
    format isn't supported yet or the image couldn't be read."""
    suffix = path.suffix.lower()
    if suffix == ".cue":
        bin_path = _first_cue_bin(path)
        return _hash_saturn_bin_file(bin_path) if bin_path else None
    if suffix == ".bin":
        return _hash_saturn_bin_file(path)
    if suffix == ".chd":
        with tempfile.TemporaryDirectory(prefix="rommgr_chd_saturn_") as tmp:
            out_cue = _extract_chd(path, chdman_path, tmp, "out.cue")
            return compute_saturn_ra_hash(out_cue) if out_cue else None
    return None


# ── Dreamcast ──────────────────────────────────────────────────────────────


def _hash_dreamcast_from_cd_image(cd: _CdImage) -> str | None:
    header = cd.read_sector(0, _DREAMCAST_HEADER_SIZE)
    if len(header) < _DREAMCAST_HEADER_SIZE or header[:16] != _DREAMCAST_MAGIC:
        return None

    boot_field = header[_DREAMCAST_BOOT_FIELD]
    end = 0
    while end < len(boot_field) and not boot_field[end : end + 1].isspace():
        end += 1
    if end == 0:  # boot filename missing from IP.BIN -- nothing runnable to hash
        return None
    exe_name = boot_field[:end].decode("ascii", errors="replace")

    found = _find_root_file(cd, exe_name)
    if found is None:
        return None
    sector, size = found
    size = min(size, _MAX_HASH_SIZE)

    digest = hashlib.md5()
    digest.update(header)
    digest.update(cd.read_range(sector, size))
    return digest.hexdigest()


def _hash_dreamcast_bin_file(bin_path: Path) -> str | None:
    if not bin_path.exists():
        return None
    try:
        with _CdImage(bin_path) as cd:
            return _hash_dreamcast_from_cd_image(cd)
    except OSError:
        return None


def _gdi_track_path(gdi_path: Path, track_num: int) -> Path | None:
    """Path of the track numbered *track_num* in a .gdi sheet (each GD-ROM
    track is normally its own file, unlike a multi-FILE .cue)."""
    try:
        lines = gdi_path.read_text(errors="replace").splitlines()
    except OSError:
        return None
    for line in lines:
        m = _GDI_LINE_RE.match(line)
        if m and int(m.group(1)) == track_num:
            name = m.group(2) or m.group(3)
            return gdi_path.parent / name
    return None


def compute_dreamcast_ra_hash(path: Path, *, chdman_path: Path | None = None) -> str | None:
    """RetroAchievements MD5 hash for a Dreamcast disc image, or None if the
    format isn't supported yet or the image couldn't be read. *chdman_path*
    is required to hash a .chd."""
    suffix = path.suffix.lower()
    if suffix == ".gdi":
        track_path = _gdi_track_path(path, 3)
        return _hash_dreamcast_bin_file(track_path) if track_path else None
    if suffix == ".cue":
        bin_path = _first_cue_bin(path)
        return _hash_dreamcast_bin_file(bin_path) if bin_path else None
    if suffix == ".bin":
        return _hash_dreamcast_bin_file(path)
    if suffix == ".chd":
        with tempfile.TemporaryDirectory(prefix="rommgr_chd_dreamcast_") as tmp:
            out_gdi = _extract_chd(path, chdman_path, tmp, "out.gdi")
            return compute_dreamcast_ra_hash(out_gdi) if out_gdi else None
    return None
