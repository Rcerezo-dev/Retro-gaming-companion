from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

# Directory names (case-insensitive) that are never ROM folders.
_EXCLUDED_DIR_NAMES = frozenset(
    {
        "bios",
        "system volume information",
        "_descartados",
    }
)


def _iter_files(root: Path) -> Iterator[Path]:
    """Yield files under *root*, skipping excluded and hidden directories."""
    try:
        entries = list(root.iterdir())
    except PermissionError:
        return
    for item in entries:
        if item.is_dir():
            if item.name.startswith(".") or item.name.lower() in _EXCLUDED_DIR_NAMES:
                continue
            yield from _iter_files(item)
        elif item.is_file():
            yield item


# Directory names (case-insensitive) that are never ROM folders.
_EXCLUDED_DIR_NAMES = frozenset(
    {
        "bios",
        "system volume information",
        "_descartados",
    }
)


def _iter_files(root: Path) -> Iterator[Path]:
    """Yield files under *root*, skipping excluded and hidden directories."""
    try:
        entries = list(root.iterdir())
    except PermissionError:
        return
    for item in entries:
        if item.is_dir():
            if item.name.startswith(".") or item.name.lower() in _EXCLUDED_DIR_NAMES:
                continue
            yield from _iter_files(item)
        elif item.is_file():
            yield item


@dataclass(slots=True)
class OrphanedSave:
    save_path: str
    stem: str
    extension: str
    size_bytes: int


def find_orphaned_saves(
    directory: Path,
    save_extensions: tuple[str, ...] | frozenset[str],
) -> list[OrphanedSave]:
    """Find save files that have no matching ROM in the same directory.

    A save is considered orphaned if no file with the same stem (and a
    non-save extension) exists alongside it.
    """
    exts = frozenset(e.lower() for e in save_extensions)
    orphans: list[OrphanedSave] = []

    for save_file in _iter_files(directory):
        if not save_file.is_file():
            continue
        if save_file.suffix.lower() not in exts:
            continue

        # Look for a sibling file with same stem but different (non-save) extension
        stem = save_file.stem
        siblings = [
            f
            for f in save_file.parent.iterdir()
            if f != save_file and f.stem == stem and f.suffix.lower() not in exts and f.is_file()
        ]
        if not siblings:
            try:
                size = save_file.stat().st_size
            except OSError:
                size = 0
            orphans.append(
                OrphanedSave(
                    save_path=str(save_file.resolve()),
                    stem=stem,
                    extension=save_file.suffix.lower(),
                    size_bytes=size,
                )
            )

    return sorted(orphans, key=lambda o: o.save_path)
