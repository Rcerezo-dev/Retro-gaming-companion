"""Internal ROM header identity (MATCH-HEADER-1).

No-Intro DAT files (this project's catalog format) carry no serial/game-code
field — only name/size/hashes — so a file whose SHA1 isn't in the catalog and
whose filename doesn't fuzzy-match anything is invisible to duplicate
detection, however clearly it's a copy/hack/bad-dump of a game already in the
library. Several cartridge platforms embed a reliable identity in the ROM
itself: NDS and GBA carts carry Nintendo's globally-unique 4-char game code,
and GB/GBC carts carry an internal title. Reading it straight from the file
gives real, verifiable identity — not a filename guess.

This is deliberately narrow: only the platforms with a fixed-offset header
Nintendo actually standardized. NES (no such field in the raw dump) and
compressed containers (.zip) are out of scope here.
"""

from __future__ import annotations

import re
from pathlib import Path

# Extensions this module can read an internal identity from.
SUPPORTED_EXTENSIONS = frozenset({".nds", ".gba", ".gb", ".gbc"})

# A real Nintendo game code is always exactly 4 uppercase letters/digits.
# Files whose DB `platform` doesn't actually match their bytes — a wrong
# folder, a stray non-Nintendo ROM mislabeled by extension — do exist in
# real libraries (confirmed live 2026-09-12: 2 rows with platform="Game Boy
# Advance" whose source_path pointed at a Sega Mega Drive .md file).
# Reading whatever garbage bytes sit at a GBA/NDS offset in an unrelated
# file could otherwise "look like" a 4-char code and coincidentally collide
# with a real one. This format check is a cheap first filter.
_GAME_CODE_RE = re.compile(r"^[A-Z0-9]{4}$")


def _read_nds_id(data: bytes) -> str | None:
    # NDS header: 0x00-0x0B game title, 0x0C-0x0F game code (4 chars).
    if len(data) < 0x10:
        return None
    code = data[0x0C:0x10].split(b"\x00")[0].decode("ascii", errors="replace").strip()
    return code if code and _GAME_CODE_RE.match(code) else None


def _read_gba_id(data: bytes) -> str | None:
    # GBA header: 0xA0-0xAB game title, 0xAC-0xAF game code, 0xB2 fixed
    # value (must be 0x96 on every real GBA cart) — a cheap, well-known
    # validity check that a mislabeled/misplaced non-GBA file will fail.
    if len(data) < 0xB3 or data[0xB2] != 0x96:
        return None
    code = data[0xAC:0xB0].split(b"\x00")[0].decode("ascii", errors="replace").strip()
    return code if code and _GAME_CODE_RE.match(code) else None


def _read_gb_id(data: bytes) -> str | None:
    # GB/GBC header: 0x134-0x143 title (16 bytes, last byte doubles as the
    # CGB flag on GBC carts) — no separate short code on this generation,
    # so the (truncated) title itself is the best available signal.
    if len(data) < 0x144:
        return None
    raw = data[0x134:0x144]
    title = raw.split(b"\x00")[0].decode("ascii", errors="replace").strip()
    return title or None


_READERS = {
    ".nds": _read_nds_id,
    ".gba": _read_gba_id,
    ".gb": _read_gb_id,
    ".gbc": _read_gb_id,
}


def extract_internal_id(path: Path, extension: str) -> str | None:
    """Return the internal game code/title embedded in *path*'s header, or
    ``None`` if the extension isn't supported, the file is too short/unreadable,
    or the header field is empty."""
    reader = _READERS.get(extension.lower())
    if reader is None:
        return None
    try:
        with open(path, "rb") as f:
            data = f.read(0x200)
    except OSError:
        return None
    return reader(data)
