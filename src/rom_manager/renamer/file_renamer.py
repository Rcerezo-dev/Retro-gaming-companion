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


def _same_file(a: Path, b: Path) -> bool:
    try:
        return a.samefile(b)
    except OSError:
        return False


def rename_rom_with_saves(
    source: Path,
    target: Path,
    save_extensions: frozenset[str],
    backup_root: Path | None = None,
    backup_keep_n: int = 5,
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

    # S29: backup companion saves before renaming/moving them
    if backup_root:
        try:
            from rom_manager.backup.save_backup import backup_save
            for sav in companions:
                backup_save(sav, backup_root, keep_n=backup_keep_n)
        except Exception:
            pass  # backup failure must never block rename

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
            # On Windows os.rename raises WinError 183 if the target already exists.
            # If the destination is the same file (NTFS case-only rename) just proceed.
            # If it is a different file, back it up with a .bak suffix before overwriting.
            if new_sav.exists() and not _same_file(sav, new_sav):
                bak = new_sav.with_suffix(new_sav.suffix + ".bak")
                os.replace(bak if bak.exists() else new_sav, bak)
            os.replace(sav, new_sav)
            renamed_saves.append((new_sav, sav))
    except OSError as exc:
        # Rollback: undo save renames already done
        rollback_failures: list[str] = []
        for new_path, original_path in renamed_saves:
            try:
                os.rename(new_path, original_path)
            except OSError as rb_exc:
                rollback_failures.append(f"{new_path.name} → {original_path.name}: {rb_exc}")
        # Rollback: undo the ROM rename
        rom_rb_failed = False
        try:
            os.rename(target, source)
        except OSError as rb_exc:
            rom_rb_failed = True
            rollback_failures.append(f"ROM {target.name} → {source.name}: {rb_exc}")
        if rollback_failures:
            detail = "; rollback INCOMPLETE — manual fix needed: " + " | ".join(rollback_failures)
        else:
            detail = " — all renames rolled back"
        return RenameOutcome(
            success=False,
            source=source,
            target=target,
            error=f"Save rename failed ({sav.name}): {exc}{detail}",
        )

    return RenameOutcome(
        success=True,
        source=source,
        target=target,
        saves_renamed=len(renamed_saves),
    )


def move_disc_set_to_subfolder(
    source_cue: Path,
    target_cue: Path,
    save_extensions: frozenset[str],
    backup_root: Path | None = None,
    backup_keep_n: int = 5,
) -> RenameOutcome:
    """Move a CUE sheet + all referenced BIN tracks (and saves) into a subfolder.

    Creates target_cue.parent, moves the BIN tracks (keeping their original names),
    renames the CUE to target_cue.  The BIN references inside the CUE remain valid
    because both CUE and BINs end up in the same directory.
    All moves are rolled back atomically on any failure.
    """
    from rom_manager.converters.chd_converter import parse_bins_from_cue, parse_tracks_from_gdi

    target_dir = target_cue.parent
    _ext = source_cue.suffix.lower()
    if _ext == ".gdi":
        bin_files = [p for p in parse_tracks_from_gdi(source_cue) if p.exists()]
    else:  # .cue
        bin_files = [p for p in parse_bins_from_cue(source_cue) if p.exists()]

    # Companion save files (same stem as CUE, save extension)
    stem = source_cue.stem
    new_stem = target_cue.stem
    try:
        companions: list[Path] = [
            f for f in source_cue.parent.iterdir()
            if f != source_cue and f.stem == stem and f.suffix.lower() in save_extensions
        ]
    except OSError:
        companions = []

    if backup_root and companions:
        try:
            from rom_manager.backup.save_backup import backup_save
            for sav in companions:
                backup_save(sav, backup_root, keep_n=backup_keep_n)
        except Exception:
            pass

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return RenameOutcome(success=False, source=source_cue, target=target_cue,
                             error=f"Cannot create directory '{target_dir}': {exc}")

    moved: list[tuple[Path, Path]] = []  # (new_path, original_path)

    def _rollback() -> None:
        for new_p, orig_p in reversed(moved):
            try:
                os.rename(new_p, orig_p)
            except OSError:
                pass
        try:
            target_dir.rmdir()
        except OSError:
            pass

    # Move BIN tracks (keeping original names)
    for bin_path in bin_files:
        bin_dest = target_dir / bin_path.name
        try:
            os.rename(bin_path, bin_dest)
            moved.append((bin_dest, bin_path))
        except OSError as exc:
            _rollback()
            return RenameOutcome(success=False, source=source_cue, target=target_cue,
                                 error=f"Failed to move track '{bin_path.name}': {exc}")

    # Move saves (renaming stem to match new CUE name)
    saves_moved = 0
    for sav in companions:
        sav_dest = target_dir / (new_stem + sav.suffix)
        try:
            os.replace(sav, sav_dest)
            moved.append((sav_dest, sav))
            saves_moved += 1
        except OSError as exc:
            _rollback()
            return RenameOutcome(success=False, source=source_cue, target=target_cue,
                                 error=f"Failed to move save '{sav.name}': {exc}")

    # Move and rename the CUE itself
    try:
        os.rename(source_cue, target_cue)
    except OSError as exc:
        _rollback()
        return RenameOutcome(success=False, source=source_cue, target=target_cue,
                             error=f"Failed to move CUE '{source_cue.name}': {exc}")

    return RenameOutcome(success=True, source=source_cue, target=target_cue,
                         saves_renamed=saves_moved)
