"""Versioned local backup of save files.

Structure on disk::

    <data_dir>/saves-backup/
        <platform>/              ← parent folder name of the save (e.g. "gba")
            <game_stem>/         ← save file stem (e.g. "Metroid Fusion (USA)")
                20260318T143022Z.sav   ← timestamped copy
                20260318T090000Z.sav
        saves-zips/
            backup-20260318T150000Z.zip   ← manual full-backup ZIPs

Backup files are named only by timestamp; the caller knows the original
save path and can restore back there.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(slots=True)
class BackupEntry:
    backup_path: Path
    timestamp: str        # ISO-8601 string  e.g. "2026-03-18T14:30:22Z"
    extension: str        # original save extension, e.g. ".sav"
    size: int


def _backup_dir_for_save(save_path: Path, backup_root: Path) -> Path:
    """Return the versioned directory for a specific save file.

    Uses ``save_path.parent.name`` as the platform folder and
    ``save_path.stem`` as the game folder, matching the typical ES-DE /
    RetroArch library layout where saves sit inside per-platform folders.
    """
    platform_folder = save_path.parent.name or "unknown"
    game_stem = save_path.stem or save_path.name
    return backup_root / "saves-backup" / platform_folder / game_stem


def _ts() -> str:
    """UTC timestamp formatted for filenames: ``20260318T143022Z``."""
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _ts_iso(ts_filename: str) -> str:
    """Convert filename timestamp ``20260318T143022Z`` → ISO ``2026-03-18T14:30:22Z``."""
    try:
        s = ts_filename.rstrip("Z")
        dt = datetime.strptime(s, "%Y%m%dT%H%M%S").replace(tzinfo=UTC)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return ts_filename


def backup_save(
    save_path: Path,
    backup_root: Path,
    keep_n: int = 5,
) -> Path | None:
    """Copy *save_path* to a versioned backup directory.

    Returns the path of the backup created, or None if the source does not
    exist.  After copying, prunes the oldest backups keeping at most
    *keep_n* copies.
    """
    if not save_path.exists():
        return None

    dest_dir = _backup_dir_for_save(save_path, backup_root)
    dest_dir.mkdir(parents=True, exist_ok=True)

    ts = _ts()
    dest = dest_dir / (ts + save_path.suffix.lower())
    shutil.copy2(save_path, dest)

    _prune_backups(dest_dir, save_path.suffix.lower(), keep_n)
    return dest


def list_backups(save_path: Path, backup_root: Path) -> list[BackupEntry]:
    """Return all backup entries for *save_path*, newest first."""
    backup_dir = _backup_dir_for_save(save_path, backup_root)
    if not backup_dir.exists():
        return []

    ext = save_path.suffix.lower()
    entries: list[BackupEntry] = []
    for f in sorted(backup_dir.iterdir(), reverse=True):
        if not f.is_file():
            continue
        if f.suffix.lower() != ext:
            continue
        ts_raw = f.stem   # e.g. "20260318T143022Z"
        entries.append(BackupEntry(
            backup_path=f,
            timestamp=_ts_iso(ts_raw),
            extension=ext,
            size=f.stat().st_size,
        ))
    return entries


def restore_backup(backup_path: Path, target_path: Path) -> bool:
    """Overwrite *target_path* with the contents of *backup_path*.

    Creates any missing parent directories.  Returns True on success.
    """
    if not backup_path.exists():
        return False
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup_path, target_path)
    return True


def _prune_backups(backup_dir: Path, ext: str, keep_n: int) -> int:
    """Remove oldest backups in *backup_dir* for extension *ext*.

    Keeps at most *keep_n* files.  Returns the number of files deleted.
    """
    if keep_n <= 0:
        return 0
    files = sorted(
        (f for f in backup_dir.iterdir() if f.is_file() and f.suffix.lower() == ext),
        reverse=True,   # newest first
    )
    deleted = 0
    for old in files[keep_n:]:
        try:
            old.unlink()
            deleted += 1
        except OSError:
            pass
    return deleted


def create_saves_zip(
    saves_dirs: list[Path],
    save_extensions: set[str],
    output_dir: Path,
) -> Path:
    """Create a timestamped ZIP of all save files in *saves_dirs*.

    Only files whose suffix is in *save_extensions* are included.
    The ZIP preserves the full relative structure from each saves_dir.

    Returns the path of the created ZIP.
    """
    import zipfile

    output_dir.mkdir(parents=True, exist_ok=True)
    ts = _ts()
    zip_path = output_dir / f"backup-{ts}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for saves_dir in saves_dirs:
            if not saves_dir.exists():
                continue
            for f in saves_dir.rglob("*"):
                if not f.is_file():
                    continue
                if save_extensions and f.suffix.lower() not in save_extensions:
                    continue
                arcname = str(f.relative_to(saves_dir.parent))
                zf.write(f, arcname)

    return zip_path


def list_manual_zips(backup_root: Path) -> list[dict]:
    """Return metadata for manual ZIP backups, newest first."""
    zips_dir = backup_root / "saves-backup" / "saves-zips"
    if not zips_dir.exists():
        return []
    result = []
    for f in sorted(zips_dir.iterdir(), reverse=True):
        if f.is_file() and f.suffix == ".zip":
            ts_raw = f.stem.replace("backup-", "")
            result.append({
                "filename": f.name,
                "path": str(f),
                "timestamp": _ts_iso(ts_raw),
                "size": f.stat().st_size,
            })
    return result
