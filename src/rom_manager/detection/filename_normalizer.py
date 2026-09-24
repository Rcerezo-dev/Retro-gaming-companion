from __future__ import annotations

import re
import unicodedata

INVALID_WINDOWS_CHARS = '<>:"/\\|?*'

# Parenthesised or bracketed annotations to strip when normalizing for matching.
# Examples: (World), (USA), (Rev 1), (Beta), [!], [b1], [T+Eng by Someone]
_ANNOTATION_RE = re.compile(r"\([^)]*\)|\[[^\]]*\]")

# File extension: a dot followed by 1–6 alphanumeric chars at the end of the string.
_EXTENSION_RE = re.compile(r"\.\w{1,6}$")

# CATALOG-MATCH-VARIANT-1: a translation patch, ROM hack, or hacked subset is
# never interchangeable with the game it's based on — normalize_for_match()
# strips these markers along with region/revision tags, so without this guard
# a translated/hacked file gets treated as "the same game" as its untranslated
# original. Found live 2026-09-09: a single NES game (Zelda) had 22
# translation-patch files all matched to the same DAT entry and grouped as
# "duplicates" of it in the review queue. Deliberately narrow (evidenced
# patterns only, not every ROM-tagging convention) to avoid false positives
# on the vast majority of filenames that only carry region/revision tags:
# romhacking.net translation tags ([T+Eng...] / [T-Spa...]), an explicit
# "(hack" tag, a "subset" ROM hack, or the No-Intro "[h]"/"[h1]" hack flag.
_NON_CANONICAL_VARIANT_RE = re.compile(r"\[T[+-]|\(hack\b|\bsubset\b|\[h\d*\]", re.IGNORECASE)


def sanitize_filename(value: str) -> str:
    sanitized = value
    for char in INVALID_WINDOWS_CHARS:
        sanitized = sanitized.replace(char, "_")
    sanitized = sanitized.strip().rstrip(".")
    return " ".join(sanitized.split())


def normalize_for_match(name: str) -> str:
    """Normalize a filename or catalog title for fuzzy name-based matching.

    Steps
    -----
    1. Strip file extension (e.g. ``.gb``, ``.bin``).
    2. Remove all parenthesised/bracketed annotations: ``(World)``, ``[!]`` …
    3. Replace underscores and hyphens with spaces.
    4. Lowercase and collapse whitespace.

    Both a raw filename and a catalog title should produce the same key for
    the same game:
        ``"Tetris (World) [!].gb"``  →  ``"tetris"``
        ``"Tetris (World)"``          →  ``"tetris"``
        ``"tetris_world.gb"``         →  ``"tetris world"``
    """
    # 0. NFKD + strip combining marks so é==e, ü==u, etc.
    name = "".join(c for c in unicodedata.normalize("NFKD", name) if not unicodedata.combining(c))
    # 1. Strip extension
    name = _EXTENSION_RE.sub("", name)
    # 2. Remove annotations
    name = _ANNOTATION_RE.sub("", name)
    # 3. Underscores and hyphens → spaces
    name = name.replace("_", " ").replace("-", " ")
    # 4. Lowercase + collapse whitespace
    return " ".join(name.lower().split())


def is_non_canonical_variant(filename: str) -> bool:
    """True if *filename* carries a translation-patch/hack/subset marker.

    Such a file is never interchangeable with the game it's based on, even
    though its ``normalize_for_match()`` key collapses to the same string —
    callers that treat two same-key files as "the same game" (catalog title
    fallback, duplicate-review title unions) must not do so across this
    boundary.
    """
    return bool(_NON_CANONICAL_VARIANT_RE.search(filename))
