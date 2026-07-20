from __future__ import annotations

import os
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


def is_device_path(source_path: str, *, anbernic_root: str | None = None) -> bool:
    """Return True if *source_path* is an Android-console path, not a local
    file that ``Path(source_path).exists()`` can verify from Windows.

    ADB scans store paths in POSIX form (``/storage/emulated/0/...``), which
    is never a valid absolute path on Windows — ``Path.exists()`` on it is
    always False, even when the file is alive on the device. Treating that as
    "file genuinely gone" silently deletes the DB row for a duplicate that
    still exists (TABS-FIX-1) and misclassifies rows during the two-DB
    migration (VAL-FIX-2).

    The bare "starts with /" check only means "unreachable local path" on
    Windows (the app's actual runtime, per CLAUDE.md) — on POSIX, a leading
    "/" is a perfectly normal local path that ``Path.exists()`` verifies
    correctly, so it must not be treated as a device-path signal there.
    """
    p = source_path.lower()
    if anbernic_root:
        root = anbernic_root.lower().rstrip("/\\")
        if root and p.startswith(root):
            return True
    return os.name == "nt" and p.startswith("/")
