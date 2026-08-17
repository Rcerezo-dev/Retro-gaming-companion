"""Detect a multi-disc tag ("Disc 2", "Disco 2", "cd2"...) in a filename.

Shared by the rename planner (``planner/operation_planner.py``, keeps each
disc's target filename distinct) and duplicate detection
(``web/builders/duplicates.py``, keeps real discs out of "same game, discard
the rest" groups). No-Intro/Redump dumps use the canonical "(Disc N)" form;
real-world libraries are messier ("FF7 Disc1.cue", "game-cd2.bin", Spanish
"Disco 2"), so the pattern matches those too rather than only the strict form.
"""

from __future__ import annotations

import re

_DISC_TAG_RE = re.compile(
    r"\(?\b(?:disc|disk|disco|cd)[\s_.-]*?(\d{1,2})\b\)?",
    re.IGNORECASE,
)


def find_disc_number(filename: str) -> int | None:
    """Return the disc number found anywhere in *filename*, or None."""
    m = _DISC_TAG_RE.search(filename)
    return int(m.group(1)) if m else None


def find_disc_tag(filename: str) -> str | None:
    """Return the disc tag found in *filename*, normalized as "(Disc N)"."""
    num = find_disc_number(filename)
    return f"(Disc {num})" if num is not None else None


def has_disc_tag(text: str) -> bool:
    """True if *text* already contains a recognizable disc tag."""
    return _DISC_TAG_RE.search(text) is not None
