from __future__ import annotations

import re
from pathlib import Path

_FILE_LINE_RE = re.compile(r'^\s*FILE\s+"(.+?)"\s+', re.IGNORECASE)


def validate_cue(cue_path: Path) -> list[str]:
    """Parse a .cue sheet and return a list of error strings.

    Each error names a referenced .bin (or other data file) that is missing
    from the same directory as the .cue.  Returns an empty list if the set is
    complete or the .cue cannot be read.
    """
    errors: list[str] = []
    try:
        text = cue_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    parent = cue_path.parent
    for line in text.splitlines():
        m = _FILE_LINE_RE.match(line)
        if not m:
            continue
        referenced = m.group(1)
        if not (parent / referenced).exists():
            errors.append(f"missing: {referenced}")

    return errors
