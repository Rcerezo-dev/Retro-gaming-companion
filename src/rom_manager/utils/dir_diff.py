"""Filesystem tree diff — compares two directory trees and returns what differs.

Works for local paths (PC, SD card mounted as drive letter) and for ADB devices
(passing an AdbTransport instance).  All paths are normalised to lowercase
forward-slash strings so Windows and Android file systems are compared correctly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

# Dirs that are never ROMs — skip them on any platform
_OS_SKIP: frozenset[str] = frozenset(
    {
        "System Volume Information",
        ".Trashes",
        ".fseventsd",
        ".Spotlight-V100",
        "$RECYCLE.BIN",
        "RECYCLER",
        "LOST.DIR",
    }
)


@dataclass(slots=True)
class DiffResult:
    only_a: list[str]  # relative paths present only in tree A
    only_b: list[str]  # relative paths present only in tree B
    in_both: int  # count of paths present in both trees
    total_a: int  # total files in tree A
    total_b: int  # total files in tree B


def get_local_tree(
    root: Path,
    skip_dirs: frozenset[str] = frozenset(),
) -> set[str]:
    """Walk *root* and return a set of relative paths (lowercase, forward slashes).

    Hidden files/dirs (starting with ``"."``) and the OS-reserved dirs in
    ``_OS_SKIP`` are always excluded.  Pass *skip_dirs* to add more names
    (e.g. ``config.excluded_directories``).
    """
    skip = _OS_SKIP | skip_dirs
    result: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]
        rel_dir = Path(dirpath).relative_to(root)
        for fname in filenames:
            if fname.startswith("."):
                continue
            rel = (rel_dir / fname).as_posix().lower()
            result.add(rel)
    return result


def get_adb_tree(
    transport,
    android_root: str,
    *,
    timeout: int = 300,
) -> set[str]:
    """List files on an ADB device and return relative paths (lowercase, forward slashes).

    *transport* must be an ``AdbTransport`` instance.  *android_root* is the
    absolute path on the device (e.g. ``/storage/emulated/0/Roms``).
    """
    root_posix = android_root.rstrip("/")
    files = transport.ls_recursive(android_root, exclude_hidden=True, timeout=timeout)
    result: set[str] = set()
    for fi in files:
        try:
            rel = PurePosixPath(fi.android_path).relative_to(root_posix)
        except ValueError:
            continue
        result.add(str(rel).lower())
    return result


def diff_trees(tree_a: set[str], tree_b: set[str]) -> DiffResult:
    """Return what is only in A, only in B, and how many are in both."""
    only_a = sorted(tree_a - tree_b)
    only_b = sorted(tree_b - tree_a)
    return DiffResult(
        only_a=only_a,
        only_b=only_b,
        in_both=len(tree_a & tree_b),
        total_a=len(tree_a),
        total_b=len(tree_b),
    )
