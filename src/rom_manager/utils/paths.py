from __future__ import annotations

from pathlib import Path


def same_file(a: Path, b: Path) -> bool:
    """Return True if *a* and *b* refer to the same file on disk.

    On Windows (case-insensitive FS) ``Path("game.gba").exists()`` returns
    True even when ``Path("Game.gba")`` is the only file, so callers must
    distinguish a *case-only* rename from a true conflict.
    """
    try:
        return a.samefile(b)
    except OSError:
        return False
