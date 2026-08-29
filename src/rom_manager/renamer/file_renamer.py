from __future__ import annotations

import logging
import os
import re
import shutil
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from rom_manager.utils.paths import same_file as _same_file

_logger = logging.getLogger(__name__)

# TABS-FIX-7: savestates de RetroArch que el chequeo simple de sufijo no ve —
# slots numerados sin límite (.state3, .state12) y el auto-save (.state.auto).
_STATE_SUFFIX_RE = re.compile(r"\.state\d*(\.auto)?$", re.IGNORECASE)


def central_save_dirs(config) -> list[Path]:
    """Carpetas centrales donde pueden vivir saves/states fuera de la del ROM.

    RetroArch con Savefile/Savestate Directory configurado (su default) guarda
    en ``saves/``/``states/`` junto al exe, y el sync usa ``local_dir`` por
    fuente. Renombrar el ROM sin renombrar esos archivos los deja huérfanos
    (TABS-FIX-7). Solo devuelve las que existen.
    """
    dirs: list[Path] = []
    ra = getattr(config, "retroarch_path", "")
    if ra:
        base = Path(ra).parent
        dirs.extend((base / "saves", base / "states"))
    sync = getattr(config, "sync", None)
    for src in getattr(sync, "sync_sources", None) or []:
        dirs.append(Path(src.local_dir))
    return [d for d in dirs if d.is_dir()]


def _companion_remainder(name: str, stem: str, save_extensions: frozenset[str]) -> str | None:
    """Si *name* es compañero de un ROM con *stem*, devuelve su parte de extensión.

    Casa ``<stem><ext>`` con ext en *save_extensions*, más los patrones de
    savestate que el sufijo simple no cubre (``.state3``, ``.state.auto``).
    Devuelve ``None`` si no es compañero (p. ej. "Game 2.srm" para stem "Game").
    """
    if not name.startswith(stem):
        return None
    rest = name[len(stem) :]
    if not rest.startswith("."):
        return None
    if rest.lower() in save_extensions or _STATE_SUFFIX_RE.match(rest):
        return rest
    return None


def _collect_companions(
    source: Path,
    stem: str,
    save_extensions: frozenset[str],
    extra_dirs: Iterable[Path] = (),
) -> list[tuple[Path, str]]:
    """``(ruta, extensión)`` de cada save/state compañero del ROM *source*.

    Busca en la carpeta del ROM y en *extra_dirs* (carpetas centrales de
    RetroArch/sync). Lanza OSError si la carpeta del ROM no se puede listar;
    las extra_dirs ilegibles se ignoran.
    """
    companions: list[tuple[Path, str]] = []
    seen_dirs: set[Path] = set()
    for i, d in enumerate([source.parent, *extra_dirs]):
        if d in seen_dirs:
            continue
        seen_dirs.add(d)
        try:
            entries = list(d.iterdir())
        except OSError:
            if i == 0:
                raise
            continue
        for f in entries:
            if f == source or not f.is_file():
                continue
            rest = _companion_remainder(f.name, stem, save_extensions)
            if rest is not None:
                companions.append((f, rest))
    return companions


def _cleanup_empty_source_dir(source_dir: Path, target_dir: Path) -> None:
    """INBOX-ORPHAN-3: a per-game subfolder rename (psx/saturn/dreamcast/wii)
    moves everything out of *source_dir* into a differently-named *target_dir*
    but never deletes the now-empty original — os.rmdir only succeeds when the
    directory is truly empty, so this is a no-op for the platform-root folder
    (never empty after a single move) and for any dir still holding a file
    the move didn't touch (e.g. a manual leftover).
    """
    if source_dir == target_dir or source_dir.parent != target_dir.parent:
        return
    try:
        source_dir.rmdir()
    except OSError:
        pass


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
    backup_root: Path | None = None,
    backup_keep_n: int = 5,
    extra_dirs: Iterable[Path] = (),
) -> RenameOutcome:
    """Rename *source* → *target* and all companion save files atomically.

    Companion saves share the ROM's stem and live either next to the ROM or in
    one of *extra_dirs* (central RetroArch/sync folders — see
    :func:`central_save_dirs`). Same-dir companions follow the ROM to the
    target directory; central-dir companions are renamed in place.

    If the ROM rename succeeds but any save rename fails, **all** renames are
    rolled back so the directory is left in its original state.

    Returns a RenameOutcome describing what happened.
    """
    stem = source.stem
    try:
        companions = _collect_companions(source, stem, save_extensions, extra_dirs)
    except OSError as exc:
        return RenameOutcome(
            success=False,
            source=source,
            target=target,
            error=f"Cannot list directory '{source.parent}': {exc}",
        )

    new_stem = target.stem

    # S29: backup companion saves before renaming/moving them
    if backup_root:
        try:
            from rom_manager.backup.save_backup import backup_save

            for sav, _rest in companions:
                backup_save(sav, backup_root, keep_n=backup_keep_n)
        except Exception:
            # backup failure must never block rename
            _logger.warning("Save backup failed before rename (continuing)", exc_info=True)

    # Step 1: rename the ROM
    try:
        # ZIP-ROUTE-FIX-1: the plan can send a ROM into a subfolder that
        # doesn't exist yet (e.g. "Virtual Console") — os.rename fails with
        # WinError 3 unless the target directory already exists.
        target.parent.mkdir(parents=True, exist_ok=True)
        os.rename(source, target)
    except OSError as exc:
        return RenameOutcome(success=False, source=source, target=target, error=str(exc))

    # Step 2: rename each companion save. Same-dir companions follow the ROM
    # to target.parent; central-dir companions keep their directory.
    renamed_saves: list[tuple[Path, Path]] = []  # (new_path, original_path)
    try:
        for sav, rest in companions:
            new_dir = target.parent if sav.parent == source.parent else sav.parent
            new_sav = new_dir / (new_stem + rest)
            # On Windows os.rename raises WinError 183 if the target already exists.
            # If the destination is the same file (NTFS case-only rename) just proceed.
            # If it is a different file, back it up with a .bak suffix before overwriting.
            if new_sav.exists() and not _same_file(sav, new_sav):
                bak = new_sav.with_suffix(new_sav.suffix + ".bak")
                n = 1
                # A leftover .bak from a previous attempt must never make this a
                # no-op (os.replace(bak, bak)) — that would leave new_sav's
                # current content unbacked-up right before it gets overwritten.
                while bak.exists():
                    bak = new_sav.with_suffix(new_sav.suffix + f".bak{n}")
                    n += 1
                os.replace(new_sav, bak)
            if not (new_sav.exists() and _same_file(sav, new_sav)):
                shutil.move(str(sav), str(new_sav))
            else:
                os.replace(sav, new_sav)  # case-only rename on NTFS
            renamed_saves.append((new_sav, sav))
    except OSError as exc:
        # Rollback: undo save renames already done
        rollback_failures: list[str] = []
        for new_path, original_path in renamed_saves:
            try:
                shutil.move(str(new_path), str(original_path))
            except OSError as rb_exc:
                rollback_failures.append(f"{new_path.name} → {original_path.name}: {rb_exc}")
        # Rollback: undo the ROM rename
        try:
            os.rename(target, source)
        except OSError as rb_exc:
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

    _cleanup_empty_source_dir(source.parent, target.parent)
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
    extra_dirs: Iterable[Path] = (),
) -> RenameOutcome:
    """Move a CUE sheet + all referenced BIN tracks (and saves) into a subfolder.

    Creates target_cue.parent, moves the BIN tracks (keeping their original names),
    renames the CUE to target_cue.  The BIN references inside the CUE remain valid
    because both CUE and BINs end up in the same directory.
    Companion saves next to the CUE move into the subfolder; saves in
    *extra_dirs* (central RetroArch/sync folders) are renamed in place.
    All moves are rolled back atomically on any failure.
    """
    from rom_manager.converters.chd_converter import parse_bins_from_cue, parse_tracks_from_gdi

    target_dir = target_cue.parent
    _ext = source_cue.suffix.lower()
    if _ext == ".gdi":
        bin_files = [p for p in parse_tracks_from_gdi(source_cue) if p.exists()]
    else:  # .cue
        bin_files = [p for p in parse_bins_from_cue(source_cue) if p.exists()]

    stem = source_cue.stem
    new_stem = target_cue.stem
    try:
        companions = _collect_companions(source_cue, stem, save_extensions, extra_dirs)
    except OSError:
        companions = []

    if backup_root and companions:
        try:
            from rom_manager.backup.save_backup import backup_save

            for sav, _rest in companions:
                backup_save(sav, backup_root, keep_n=backup_keep_n)
        except Exception:
            # backup failure must never block rename
            _logger.warning("Save backup failed before rename (continuing)", exc_info=True)

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return RenameOutcome(
            success=False,
            source=source_cue,
            target=target_cue,
            error=f"Cannot create directory '{target_dir}': {exc}",
        )

    moved: list[tuple[Path, Path]] = []  # (new_path, original_path)

    def _rollback() -> list[str]:
        """Undo moves already done. Returns per-file failures (empty if clean)."""
        failures: list[str] = []
        for new_p, orig_p in reversed(moved):
            try:
                shutil.move(str(new_p), str(orig_p))
            except OSError as rb_exc:
                failures.append(f"{new_p.name} → {orig_p.name}: {rb_exc}")
        try:
            target_dir.rmdir()
        except OSError:
            pass  # non-critical: dir may be non-empty (rollback above failed) or already gone
        return failures

    def _rollback_detail() -> str:
        failures = _rollback()
        if not failures:
            return ""
        return "; rollback INCOMPLETE — manual fix needed: " + " | ".join(failures)

    # Move BIN tracks (keeping original names)
    for bin_path in bin_files:
        bin_dest = target_dir / bin_path.name
        try:
            os.rename(bin_path, bin_dest)
            moved.append((bin_dest, bin_path))
        except OSError as exc:
            detail = _rollback_detail()
            return RenameOutcome(
                success=False,
                source=source_cue,
                target=target_cue,
                error=f"Failed to move track '{bin_path.name}': {exc}{detail}",
            )

    # Move saves (renaming stem to match new CUE name); central-dir saves
    # stay in their directory, same-dir saves follow the set into the subfolder.
    saves_moved = 0
    for sav, rest in companions:
        dest_dir = target_dir if sav.parent == source_cue.parent else sav.parent
        sav_dest = dest_dir / (new_stem + rest)
        try:
            shutil.move(str(sav), str(sav_dest))
            moved.append((sav_dest, sav))
            saves_moved += 1
        except OSError as exc:
            detail = _rollback_detail()
            return RenameOutcome(
                success=False,
                source=source_cue,
                target=target_cue,
                error=f"Failed to move save '{sav.name}': {exc}{detail}",
            )

    # Move and rename the CUE itself
    try:
        os.rename(source_cue, target_cue)
    except OSError as exc:
        detail = _rollback_detail()
        return RenameOutcome(
            success=False,
            source=source_cue,
            target=target_cue,
            error=f"Failed to move CUE '{source_cue.name}': {exc}{detail}",
        )

    _cleanup_empty_source_dir(source_cue.parent, target_cue.parent)
    return RenameOutcome(
        success=True, source=source_cue, target=target_cue, saves_renamed=saves_moved
    )
