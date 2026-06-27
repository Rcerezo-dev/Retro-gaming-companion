from __future__ import annotations

import re
import unicodedata

INVALID_WINDOWS_CHARS = '<>:"/\\|?*'

# Parenthesised or bracketed annotations to strip when normalizing for matching.
# Examples: (World), (USA), (Rev 1), (Beta), [!], [b1], [T+Eng by Someone]
_ANNOTATION_RE = re.compile(r"\([^)]*\)|\[[^\]]*\]")

# File extension: a dot followed by 1–6 alphanumeric chars at the end of the string.
_EXTENSION_RE = re.compile(r"\.\w{1,6}$")


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
