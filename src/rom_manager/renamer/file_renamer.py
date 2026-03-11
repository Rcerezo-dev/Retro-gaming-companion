from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class RenameOutcome:
    """Result of a single atomic ROM+saves rename."""
    success: bool
    source: Path
    target: Path
    saves_renamed: int = 0
    error: str = ""


def rename_rom_with_saves(
    source: Path,
    target: Path,
    save_extensions: frozenset[str],
) -> RenameOutcome:
    """Rename *source* → *target* and all companion save files atomically.

    Companion saves are files in the same directory that share the ROM's stem
    and have an extension in *save_extensions*.

    If the ROM rename succeeds but any save rename fails, **all** renames are
    rolled back so the directory is left in its original state.

    Returns a RenameOutcome describing what happened.
    """
    # Collect companion save files (same stem, save extension)
    stem = source.stem
    try:
        companions: list[Path] = [
            f for f in source.parent.iterdir()
            if f != source and f.stem == stem and f.suffix.lower() in save_extensions
        ]
    except OSError as exc:
        return RenameOutcome(
            success=False, source=source, target=target,
            error=f"Cannot list directory '{source.parent}': {exc}",
        )

    new_stem = target.stem

    # Step 1: rename the ROM
    try:
        os.rename(source, target)
    except OSError as exc:
        return RenameOutcome(success=False, source=source, target=target, error=str(exc))

    # Step 2: rename each companion save
    renamed_saves: list[tuple[Path, Path]] = []  # (new_path, original_path)
    try:
        for sav in companions:
            new_sav = sav.parent / (new_stem + sav.suffix)
            os.rename(sav, new_sav)
            renamed_saves.append((new_sav, sav))
    except OSError as exc:
        # Rollback: undo save renames already done
        for new_path, original_path in renamed_saves:
            try:
                os.rename(new_path, original_path)
            except OSError:
                pass
        # Rollback: undo the ROM rename
        try:
            os.rename(target, source)
        except OSError:
            pass
        return RenameOutcome(
            success=False,
            source=source,
            target=target,
            error=f"Save rename failed ({sav.name}): {exc} — all renames rolled back",
        )

    return RenameOutcome(
        success=True,
        source=source,
        target=target,
        saves_renamed=len(renamed_saves),
    )
