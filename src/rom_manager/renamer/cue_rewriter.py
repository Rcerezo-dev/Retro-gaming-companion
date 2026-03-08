from __future__ import annotations

import re
from pathlib import Path


_FILE_LINE_RE = re.compile(
    r"(^\s*FILE\s+\")(.+?)(\"\s*\S*.*)",
    re.IGNORECASE | re.MULTILINE,
)


def rewrite_cue(cue_path: Path, old_bin: str, new_bin: str) -> bool:
    """Replace ``FILE "old_bin"`` references with ``FILE "new_bin"`` inside a .cue sheet.

    Only acts when *old_bin* has no directory component (i.e. the .bin lives
    in the same directory as the .cue).  Returns ``True`` if the file was
    modified, ``False`` if no changes were needed or the file could not be read.
    """
    # Guard: only handle same-directory bins
    if Path(old_bin).parent != Path("."):
        return False

    try:
        original = cue_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False

    lines = original.splitlines(keepends=True)
    new_lines: list[str] = []
    changed = False

    for line in lines:
        m = _FILE_LINE_RE.match(line)
        if m and m.group(2).lower() == old_bin.lower():
            # Preserve everything after the match (e.g. trailing newline)
            tail = line[m.end():]
            line = m.group(1) + new_bin + m.group(3) + tail
            changed = True
        new_lines.append(line)

    if not changed:
        return False

    cue_path.write_text("".join(new_lines), encoding="utf-8")
    return True
