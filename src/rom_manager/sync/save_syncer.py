from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from rom_manager.database.repository import LibraryRepository
from rom_manager.sync.conflict_resolver import SyncDecision, decide
from rom_manager.sync.delta_cache import DeltaCache
from rom_manager.sync.rclone_transport import (
    RcloneError,
    RcloneTransport,
    RemoteEntry,
    _resolve_remote,
)
from rom_manager.sync.sync_log import get_last_sync, log_sync_event

_logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LocalSave:
    relative: str  # path relative to saves_dir, forward slashes
    absolute: Path
    mtime: datetime  # UTC
    size: int


@dataclass(slots=True)
class SyncResult:
    uploaded: int = 0
    downloaded: int = 0
    up_to_date: int = 0
    conflicts: int = 0
    errors: int = 0
    delta_skipped: int = 0  # files skipped because content hash unchanged

    @property
    def total(self) -> int:
        return (
            self.uploaded
            + self.downloaded
            + self.up_to_date
            + self.conflicts
            + self.errors
            + self.delta_skipped
        )


def list_local_saves(
    saves_dir: Path, save_extensions: tuple[str, ...], include_glob: str = "**/*"
) -> list[LocalSave]:
    """Walk *saves_dir* and return all files whose extension is in *save_extensions*.

    Pass an empty tuple to include every file regardless of extension (useful for
    emulators like PPSSPP/Dolphin whose save directories contain only save data).

    *include_glob* narrows which subtree of *saves_dir* is walked (e.g. Dolphin's
    Wii NAND has real saves only under ``title/*/*/data/`` — the rest is emulated
    system content that shouldn't leave the PC).
    """
    saves: list[LocalSave] = []
    ext_set = {e.lower() for e in save_extensions} if save_extensions else None
    for path in saves_dir.glob(include_glob):
        if not path.is_file():
            continue
        if ext_set is not None and path.suffix.lower() not in ext_set:
            continue
        stat = path.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=UTC)
        relative = path.relative_to(saves_dir).as_posix()
        saves.append(LocalSave(relative=relative, absolute=path, mtime=mtime, size=stat.st_size))
    return saves


def sync_saves(
    saves_dir: Path,
    saves_remote: str,
    *,
    transport: RcloneTransport,
    repository: LibraryRepository,
    save_extensions: tuple[str, ...],
    state_extensions: tuple[str, ...] = (),
    states_remote: str | None = None,
    dry_run: bool = True,
    backup_root: Path | None = None,
    backup_keep_n: int = 5,
    delta_cache: DeltaCache | None = None,
    conflict_policy: str = "newest",
    include_glob: str = "**/*",
) -> tuple[SyncResult, list[SyncDecision]]:
    """Synchronise local *saves_dir* with *saves_remote* and *states_remote* using rclone.

    Files are routed to the correct remote based on extension:
    - state_extensions → states_remote
    - save_extensions → saves_remote

    Returns a SyncResult and the full list of decisions (for status display).
    """
    result = SyncResult()
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S")

    # Gather both sides.
    local_saves: dict[str, LocalSave] = {
        s.relative: s for s in list_local_saves(saves_dir, save_extensions, include_glob)
    }
    try:
        # List from both remotes (combine results)
        remote_entries: dict[str, RemoteEntry] = {}
        try:
            remote_entries.update({e.relative: e for e in transport.list_remote(saves_remote)})
        except RcloneError:
            pass  # saves_remote may be empty or unavailable
        if states_remote:
            try:
                remote_entries.update({e.relative: e for e in transport.list_remote(states_remote)})
            except RcloneError:
                pass  # states_remote may be empty or unavailable
    except RcloneError:
        raise

    all_relatives = sorted(set(local_saves) | set(remote_entries))

    decisions: list[SyncDecision] = []

    # REV43-35: el watermark de conflicto ahora se busca por (local_path, remote_path)
    # real, no solo local_path — si saves_remote/states_remote cambian en config, un
    # last_sync_at de la ruta anterior ya no se confunde con el remoto actual.
    saves_remote_clean = (saves_remote or "").strip() or None
    states_remote_clean = (states_remote or "").strip() or None

    with repository.connect() as conn:
        for relative in all_relatives:
            local = local_saves.get(relative)
            remote = remote_entries.get(relative)

            local_path = saves_dir / Path(relative)
            # REV43-3: computado aquí (antes de cualquier transport.upload/download)
            # para que quede definido incluso si la transferencia falla en el
            # primer intento — evita UnboundLocalError en el except y que el log
            # de auditoría arrastre la ruta de una iteración anterior.
            # REV43-35: misma decisión de enrutado que usará transport.upload/download,
            # así el watermark y el log de auditoría reflejan el remoto real, no un
            # placeholder fijo.
            file_ext = Path(relative).suffix.lower()
            chosen_remote, _category, _configured = _resolve_remote(
                file_ext,
                saves_remote_clean,
                states_remote_clean,
                None,
                save_extensions,
                state_extensions,
            )
            remote_path = (
                f"{chosen_remote.rstrip('/')}/{relative}"
                if chosen_remote
                else f"<no remote configured>/{relative}"
            )

            last_sync = get_last_sync(conn, str(local_path), remote_path=remote_path)

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

            # S37-2 delta cache: skip upload if content hash is unchanged
            # (mtime may differ, e.g. emulator opened file without writing new data)
            if (
                decision.action == "upload"
                and delta_cache is not None
                and local is not None
                and not delta_cache.content_changed(relative, local_path)
            ):
                result.delta_skipped += 1
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
                    transport.upload(
                        local_path,
                        relative,
                        saves_remote=saves_remote,
                        states_remote=states_remote,
                        save_extensions=save_extensions,
                        state_extensions=state_extensions,
                    )
                    log_sync_event(
                        conn,
                        local_path=str(local_path),
                        remote_path=remote_path,
                        direction="upload",
                        local_mtime=decision.local_mtime,
                        remote_mtime=decision.remote_mtime,
                        result="ok",
                        created_at=timestamp,
                        # AUD-2: rclone copyto verifica checksums tras cada transferencia
                        verified=True,
                    )
                    if delta_cache is not None:
                        delta_cache.mark_synced(relative, local_path, "upload")
                    repository.record_play_session(local_path, timestamp, connection=conn)
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
                    # S29: backup local save before overwriting with remote version
                    if backup_root and local_path.exists():
                        try:
                            from rom_manager.backup.save_backup import backup_save

                            backup_save(local_path, backup_root, keep_n=backup_keep_n)
                        except Exception:
                            # backup failure must never block sync
                            _logger.warning(
                                "Save backup failed before download (continuing)", exc_info=True
                            )
                    transport.download(
                        relative,
                        local_path,
                        saves_remote=saves_remote,
                        states_remote=states_remote,
                        save_extensions=save_extensions,
                        state_extensions=state_extensions,
                    )
                    log_sync_event(
                        conn,
                        local_path=str(local_path),
                        remote_path=remote_path,
                        direction="download",
                        local_mtime=decision.local_mtime,
                        remote_mtime=decision.remote_mtime,
                        result="ok",
                        created_at=timestamp,
                        verified=True,
                    )
                    if delta_cache is not None:
                        delta_cache.mark_synced(relative, local_path, "download")
                    repository.record_play_session(local_path, timestamp, connection=conn)
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
                # P4: auto-resolve conflict using configured policy
                if backup_root and local_path.exists():
                    try:
                        from rom_manager.backup.save_backup import backup_save

                        backup_save(local_path, backup_root, keep_n=backup_keep_n)
                    except Exception:
                        # backup failure must never block sync
                        _logger.warning(
                            "Save backup failed before conflict resolution (continuing)",
                            exc_info=True,
                        )

                backup_suffix = f".conflict-{timestamp.replace(':', '')}"

                # Determine winner
                if conflict_policy in ("keep_pc", "keep_local"):
                    local_wins = True
                    policy_reason = "policy=keep_local"
                elif conflict_policy in ("keep_android", "keep_remote"):
                    local_wins = False
                    policy_reason = "policy=keep_remote"
                else:  # "newest" or "ask" (can't prompt in background, fall back to newest)
                    local_wins = (
                        decision.local_mtime is None
                        or decision.remote_mtime is None
                        or decision.local_mtime >= decision.remote_mtime
                    )
                    policy_reason = "policy=newest;" + (" local" if local_wins else " remote")

                try:
                    if local_wins:
                        # Backup remote copy locally with conflict suffix, then upload local as winner
                        transport.download(
                            relative,
                            local_path.parent / (local_path.name + backup_suffix),
                            saves_remote=saves_remote,
                            states_remote=states_remote,
                            save_extensions=save_extensions,
                            state_extensions=state_extensions,
                        )
                        transport.upload(
                            local_path,
                            relative,
                            saves_remote=saves_remote,
                            states_remote=states_remote,
                            save_extensions=save_extensions,
                            state_extensions=state_extensions,
                        )
                        msg = (
                            f"Conflict resolved ({policy_reason}): local kept; "
                            f"remote backed up as {relative}{backup_suffix}"
                        )
                        if delta_cache is not None:
                            delta_cache.mark_synced(relative, local_path, "upload")
                    else:
                        # Backup local file with conflict suffix, then download remote as winner
                        import shutil as _shutil

                        _shutil.copy2(
                            local_path, local_path.parent / (local_path.name + backup_suffix)
                        )
                        transport.download(
                            relative,
                            local_path,
                            saves_remote=saves_remote,
                            states_remote=states_remote,
                            save_extensions=save_extensions,
                            state_extensions=state_extensions,
                        )
                        msg = (
                            f"Conflict resolved ({policy_reason}): remote kept; "
                            f"local backed up as {relative}{backup_suffix}"
                        )
                        if delta_cache is not None:
                            delta_cache.mark_synced(relative, local_path, "download")

                    log_sync_event(
                        conn,
                        local_path=str(local_path),
                        remote_path=remote_path,
                        direction="conflict",
                        local_mtime=decision.local_mtime,
                        remote_mtime=decision.remote_mtime,
                        result="ok",
                        message=msg,
                        created_at=timestamp,
                        verified=True,
                    )
                    repository.record_play_session(local_path, timestamp, connection=conn)
                    result.conflicts += 1
                except RcloneError as exc:
                    if delta_cache is not None:
                        delta_cache.invalidate(relative)
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


def sync_single_file(
    local_path: Path,
    remote: str,
    *,
    transport: RcloneTransport,
    dry_run: bool = True,
) -> tuple[SyncResult, list[SyncDecision]]:
    """DEVPROFILE-8b/9: restore-style sync for a single file (a whole SQLite
    DB, a RetroArch playlist) -- unlike ``sync_saves()``, there's only one
    file, so per-file merge/conflict tracking doesn't apply: newest mtime
    wins. Reuses ``decide()`` with ``last_sync_at=None``, which never returns
    "conflict" -- exactly the "restore, don't merge" behaviour this needs.

    *remote* is the full remote path to the file itself (not a directory),
    e.g. ``"dropbox:RetroSync/data/library_pc.db"``.

    # ponytail: no audit log (sync_log)/delta_cache here, unlike sync_saves --
    # add if Sync Doctor needs per-file-source history for these too.
    """
    result = SyncResult()
    remote = remote.rstrip("/")
    remote_dir, _, filename = remote.rpartition("/")

    remote_mtime = None
    try:
        for entry in transport.list_remote(remote_dir):
            if entry.relative == filename:
                remote_mtime = entry.mtime
                break
    except RcloneError:
        pass  # remote dir may not exist yet

    local_mtime = (
        datetime.fromtimestamp(local_path.stat().st_mtime, tz=UTC) if local_path.exists() else None
    )
    decision = decide(filename, local_mtime, remote_mtime, last_sync_at=None)

    if decision.action == "upload":
        result.uploaded += 1
    elif decision.action == "download":
        result.downloaded += 1
    else:
        result.up_to_date += 1

    if decision.action == "up_to_date" or dry_run:
        return result, [decision]

    try:
        if decision.action == "upload":
            transport.upload(local_path, filename, fallback_remote=remote_dir)
        else:
            transport.download(filename, local_path, fallback_remote=remote_dir)
    except RcloneError:
        if decision.action == "upload":
            result.uploaded -= 1
        else:
            result.downloaded -= 1
        result.errors += 1

    return result, [decision]
