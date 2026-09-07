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


def strip_disc_tag(text: str) -> str:
    """Remove the disc tag (see :func:`find_disc_number`) from *text*, if any.

    DUP-CROSSFMT-1: used to build a cross-format duplicate key that groups
    "Disc 1"/"Disc 2" of the same release together — same trade-off
    ``canonical_title`` already accepts (it doesn't encode the disc number
    either), safe because callers still gate on ``_is_disc_set`` before
    treating the cluster as an actual duplicate. Everything else in *text*
    (region/language tags included) is left untouched, unlike
    ``ra_checker._normalize_title``'s full bracket-stripping — that's what
    keeps two different regional releases from colliding here.
    """
    return _DISC_TAG_RE.sub("", text)
