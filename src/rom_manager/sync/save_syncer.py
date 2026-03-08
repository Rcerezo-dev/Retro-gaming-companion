from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from rom_manager.database.repository import LibraryRepository
from rom_manager.sync.conflict_resolver import SyncDecision, decide
from rom_manager.sync.rclone_transport import RemoteEntry, RcloneError, RcloneTransport
from rom_manager.sync.sync_log import get_last_sync, log_sync_event


@dataclass(slots=True)
class LocalSave:
    relative: str       # path relative to saves_dir, forward slashes
    absolute: Path
    mtime: datetime     # UTC
    size: int


@dataclass(slots=True)
class SyncResult:
    uploaded: int = 0
    downloaded: int = 0
    up_to_date: int = 0
    conflicts: int = 0
    errors: int = 0

    @property
    def total(self) -> int:
        return self.uploaded + self.downloaded + self.up_to_date + self.conflicts + self.errors


def list_local_saves(saves_dir: Path, save_extensions: tuple[str, ...]) -> list[LocalSave]:
    """Walk *saves_dir* and return all files whose extension is in *save_extensions*."""
    saves: list[LocalSave] = []
    ext_set = {e.lower() for e in save_extensions}
    for path in saves_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in ext_set:
            continue
        stat = path.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        relative = path.relative_to(saves_dir).as_posix()
        saves.append(LocalSave(relative=relative, absolute=path, mtime=mtime, size=stat.st_size))
    return saves


def sync_saves(
    saves_dir: Path,
    remote_root: str,
    *,
    transport: RcloneTransport,
    repository: LibraryRepository,
    save_extensions: tuple[str, ...],
    dry_run: bool = True,
) -> tuple[SyncResult, list[SyncDecision]]:
    """Synchronise local *saves_dir* with *remote_root* using rclone.

    Returns a SyncResult and the full list of decisions (for status display).
    """
    result = SyncResult()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    # Gather both sides.
    local_saves: dict[str, LocalSave] = {
        s.relative: s for s in list_local_saves(saves_dir, save_extensions)
    }
    try:
        remote_entries: dict[str, RemoteEntry] = {
            e.relative: e for e in transport.list_remote(remote_root)
        }
    except RcloneError as exc:
        raise

    all_relatives = sorted(set(local_saves) | set(remote_entries))

    decisions: list[SyncDecision] = []

    with repository.connect() as conn:
        for relative in all_relatives:
            local = local_saves.get(relative)
            remote = remote_entries.get(relative)

            local_path = saves_dir / Path(relative)
            remote_path = f"{remote_root.rstrip('/')}/{relative}"

            last_sync = get_last_sync(conn, str(local_path))

            decision = decide(
                relative,
                local_mtime=local.mtime if local else None,
                remote_mtime=remote.mtime if remote else None,
                last_sync_at=last_sync,
            )
            decisions.append(decision)

            if decision.action == "up_to_date":
                result.up_to_date += 1
                continue

            if dry_run:
                if decision.action == "upload":
                    result.uploaded += 1
                elif decision.action == "download":
                    result.downloaded += 1
                elif decision.action == "conflict":
                    result.conflicts += 1
                continue

            # --- Apply ---
            if decision.action == "upload":
                try:
                    transport.upload(local_path, remote_root, relative)
                    log_sync_event(
                        conn,
                        local_path=str(local_path),
                        remote_path=remote_path,
                        direction="upload",
                        local_mtime=decision.local_mtime,
                        remote_mtime=decision.remote_mtime,
                        result="ok",
                        created_at=timestamp,
                    )
                    result.uploaded += 1
                except RcloneError as exc:
                    log_sync_event(
                        conn,
                        local_path=str(local_path),
                        remote_path=remote_path,
                        direction="upload",
                        local_mtime=decision.local_mtime,
                        remote_mtime=decision.remote_mtime,
                        result="error",
                        message=str(exc),
                        created_at=timestamp,
                    )
                    result.errors += 1

            elif decision.action == "download":
                try:
                    transport.download(remote_root, relative, local_path)
                    log_sync_event(
                        conn,
                        local_path=str(local_path),
                        remote_path=remote_path,
                        direction="download",
                        local_mtime=decision.local_mtime,
                        remote_mtime=decision.remote_mtime,
                        result="ok",
                        created_at=timestamp,
                    )
                    result.downloaded += 1
                except RcloneError as exc:
                    log_sync_event(
                        conn,
                        local_path=str(local_path),
                        remote_path=remote_path,
                        direction="download",
                        local_mtime=decision.local_mtime,
                        remote_mtime=decision.remote_mtime,
                        result="error",
                        message=str(exc),
                        created_at=timestamp,
                    )
                    result.errors += 1

            elif decision.action == "conflict":
                # Back up both sides by appending a timestamp suffix, then upload local.
                backup_suffix = f".conflict-{timestamp.replace(':', '')}"
                backup_rel = relative + backup_suffix

                try:
                    # Keep remote copy with backup name.
                    transport.download(remote_root, relative, local_path.parent / (local_path.name + backup_suffix))
                    # Upload current local as the winner.
                    transport.upload(local_path, remote_root, relative)
                    log_sync_event(
                        conn,
                        local_path=str(local_path),
                        remote_path=remote_path,
                        direction="conflict",
                        local_mtime=decision.local_mtime,
                        remote_mtime=decision.remote_mtime,
                        result="ok",
                        message=f"Conflict resolved: local kept; remote backed up as {backup_rel}",
                        created_at=timestamp,
                    )
                    result.conflicts += 1
                except RcloneError as exc:
                    log_sync_event(
                        conn,
                        local_path=str(local_path),
                        remote_path=remote_path,
                        direction="conflict",
                        local_mtime=decision.local_mtime,
                        remote_mtime=decision.remote_mtime,
                        result="error",
                        message=str(exc),
                        created_at=timestamp,
                    )
                    result.errors += 1

        if not dry_run:
            conn.commit()

    return result, decisions
