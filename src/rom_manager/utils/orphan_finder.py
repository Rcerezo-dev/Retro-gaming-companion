from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# RPT-A2: directories that never hold user ROMs/saves — BIOS, OS internals, the app's
# own discard bin, and ES-DE asset/media folders. Files under any of these are skipped
# so the orphan report doesn't flag e.g. `BIOS\scummvm\theme\*.dat` (project rule:
# "BIOS, assets and Android folders are never treated as ROMs").
_EXCLUDED_DIRS = frozenset(
    n.lower()
    for n in (
        "BIOS",
        "System Volume Information",
        "$RECYCLE.BIN",
        "downloaded_media",
        "media",
        "assets",
        "gamelists",
    )
)

# RPT-A3: extensions that appear in the save set but are emulator data/assets, not user
# saves (e.g. scummvm theme `.dat`, FBNeo split-data `.fs`). Never reported as orphans.
_NON_SAVE_EXTS = frozenset({".dat", ".fs"})


@dataclass(slots=True)
class OrphanedSave:
    save_path: str
    stem: str
    extension: str
    size_bytes: int


def _in_excluded_dir(rel_dirs: tuple[str, ...]) -> bool:
    """True if any directory component is excluded (named, hidden `.`, or app `_`)."""
    for part in rel_dirs:
        if part.lower() in _EXCLUDED_DIRS or part.startswith((".", "_")):
            return True
    return False


def find_orphaned_saves(
    directory: Path,
    save_extensions: tuple[str, ...] | frozenset[str],
) -> list[OrphanedSave]:
    """Find save files that have no matching ROM in the same directory.

    A save is considered orphaned if no file with the same stem (and a
    non-save extension) exists alongside it. Excluded directories (BIOS, OS
    internals, assets…) and non-save extensions (.dat/.fs) are ignored.
    """
    exts = frozenset(e.lower() for e in save_extensions) - _NON_SAVE_EXTS
    orphans: list[OrphanedSave] = []

    for save_file in directory.rglob("*"):
        if not save_file.is_file():
            continue
        if save_file.suffix.lower() not in exts:
            continue
        if _in_excluded_dir(save_file.relative_to(directory).parts[:-1]):
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
