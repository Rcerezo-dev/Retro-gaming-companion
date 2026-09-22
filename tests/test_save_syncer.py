from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

from rom_manager.database.repository import LibraryRepository
from rom_manager.sync.rclone_transport import RcloneError, RcloneTransport, RemoteEntry
from rom_manager.sync.save_syncer import list_local_saves, sync_saves
from rom_manager.sync.sync_log import log_sync_event

_SAVE_EXTS = (".sav", ".state")
_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


def _set_mtime(path: Path, when: datetime) -> None:
    ts = when.timestamp()
    os.utime(path, (ts, ts))


def _seed_last_sync(
    repo: LibraryRepository,
    local_path: Path,
    when: datetime,
    remote_path: str = "dropbox:/saves",
) -> None:
    """Record a prior successful sync so ``decide`` can detect a conflict.

    REV43-35: *remote_path* must match what sync_saves() will actually resolve
    for this file (remote root + relative), since the watermark lookup now
    filters on it too — not just local_path.
    """
    with repo.connect() as conn:
        log_sync_event(
            conn,
            local_path=str(local_path),
            remote_path=remote_path,
            direction="upload",
            local_mtime=None,
            remote_mtime=None,
            result="ok",
            created_at=when.strftime("%Y-%m-%dT%H:%M:%S"),
        )
        conn.commit()


def _remote_entry(relative: str, offset_seconds: float = 0) -> RemoteEntry:
    return RemoteEntry(
        relative=relative,
        mtime=_NOW + timedelta(seconds=offset_seconds),
        size=512,
    )


def _mock_transport(remote_entries: list[RemoteEntry]) -> MagicMock:
    transport = MagicMock(spec=RcloneTransport)
    transport.list_remote.return_value = remote_entries
    return transport


# ---------------------------------------------------------------------------
# list_local_saves
# ---------------------------------------------------------------------------


def test_list_local_saves_finds_saves(tmp_path: Path) -> None:
    (tmp_path / "gb").mkdir()
    (tmp_path / "gb" / "tetris.sav").write_bytes(b"\x00" * 8)
    (tmp_path / "gb" / "tetris.state").write_bytes(b"\x00" * 16)
    (tmp_path / "gb" / "tetris.gb").write_bytes(b"\x00" * 1024)  # ROM — should be ignored

    saves = list_local_saves(tmp_path, _SAVE_EXTS)
    relatives = {s.relative for s in saves}
    assert "gb/tetris.sav" in relatives
    assert "gb/tetris.state" in relatives
    assert "gb/tetris.gb" not in relatives


def test_list_local_saves_empty_dir(tmp_path: Path) -> None:
    assert list_local_saves(tmp_path, _SAVE_EXTS) == []


def test_list_local_saves_include_glob_scopes_dolphin_wii_nand(tmp_path: Path) -> None:
    # SYNC-WII-SCOPE-1: only title/*/*/data/ is a real save; content/ is
    # installed-app/system data that must never leave the PC.
    game = tmp_path / "title" / "00010000" / "52334d50"
    (game / "content").mkdir(parents=True)
    (game / "content" / "title.tmd").write_bytes(b"\x00" * 4)
    (game / "data").mkdir()
    (game / "data" / "save.bin").write_bytes(b"\x00" * 8)
    (tmp_path / "shared1").mkdir()
    (tmp_path / "shared1" / "system.app").write_bytes(b"\x00" * 4)

    saves = list_local_saves(tmp_path, (), include_glob="title/*/*/data/**/*")
    relatives = {s.relative for s in saves}
    assert relatives == {"title/00010000/52334d50/data/save.bin"}


# ---------------------------------------------------------------------------
# sync_saves — dry run
# ---------------------------------------------------------------------------


def test_dry_run_upload(tmp_path: Path) -> None:
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()
    save_file = saves_dir / "tetris.sav"
    save_file.write_bytes(b"\x00" * 8)

    # Remote has no entry for this file.
    transport = _mock_transport([])
    repo = LibraryRepository(tmp_path / "lib.sqlite")

    result, decisions = sync_saves(
        saves_dir,
        "dropbox:/saves",
        transport=transport,
        repository=repo,
        save_extensions=_SAVE_EXTS,
        dry_run=True,
    )

    assert result.uploaded == 1
    assert result.downloaded == 0
    transport.upload.assert_not_called()  # dry run


def test_dry_run_download(tmp_path: Path) -> None:
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()
    # No local file; remote has one.
    transport = _mock_transport([_remote_entry("tetris.sav")])
    repo = LibraryRepository(tmp_path / "lib.sqlite")

    result, decisions = sync_saves(
        saves_dir,
        "dropbox:/saves",
        transport=transport,
        repository=repo,
        save_extensions=_SAVE_EXTS,
        dry_run=True,
    )

    assert result.downloaded == 1
    transport.download.assert_not_called()


def test_dry_run_up_to_date(tmp_path: Path) -> None:
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()
    save_file = saves_dir / "tetris.sav"
    save_file.write_bytes(b"\x00" * 8)
    # Force mtime to match remote exactly.
    import os

    ts = _NOW.timestamp()
    os.utime(save_file, (ts, ts))

    transport = _mock_transport([_remote_entry("tetris.sav", offset_seconds=0)])
    repo = LibraryRepository(tmp_path / "lib.sqlite")

    result, _ = sync_saves(
        saves_dir,
        "dropbox:/saves",
        transport=transport,
        repository=repo,
        save_extensions=_SAVE_EXTS,
        dry_run=True,
    )

    assert result.up_to_date == 1
    assert result.uploaded == 0
    assert result.downloaded == 0


def test_apply_upload_calls_transport(tmp_path: Path) -> None:
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()
    save_file = saves_dir / "tetris.sav"
    save_file.write_bytes(b"\x00" * 8)

    transport = _mock_transport([])
    repo = LibraryRepository(tmp_path / "lib.sqlite")

    result, _ = sync_saves(
        saves_dir,
        "dropbox:/saves",
        transport=transport,
        repository=repo,
        save_extensions=_SAVE_EXTS,
        dry_run=False,
    )

    assert result.uploaded == 1
    transport.upload.assert_called_once()


def test_upload_failure_on_first_file_does_not_raise_unbound(tmp_path: Path) -> None:
    """REV43-3: si transport.upload() falla en el primer archivo de la cola,
    remote_path debe estar definido para el log de error (antes: UnboundLocalError,
    porque remote_path solo se asignaba tras un upload exitoso)."""
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()
    save_file = saves_dir / "tetris.sav"
    save_file.write_bytes(b"\x00" * 8)

    transport = _mock_transport([])
    transport.upload.side_effect = RcloneError("network blip")
    repo = LibraryRepository(tmp_path / "lib.sqlite")

    result, _ = sync_saves(
        saves_dir,
        "dropbox:/saves",
        transport=transport,
        repository=repo,
        save_extensions=_SAVE_EXTS,
        dry_run=False,
    )

    assert result.errors == 1
    assert result.uploaded == 0


def test_apply_upload_with_matching_game_does_not_deadlock(tmp_path: Path) -> None:
    """Regression: record_play_session() must reuse sync_saves()'s open ``conn``
    (REV43-38 added the ``connection=`` param for exactly this) instead of
    opening its own — sync_saves() only commits ``conn`` once at the end of
    the loop, so a second writer connection to the same file self-deadlocks
    until sqlite's busy_timeout expires and raises "database is locked".
    Only reproduces when a games row actually matches the save's stem —
    other tests never insert one, so record_play_session's UPDATE (and thus
    the second connection) was never exercised."""
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()
    save_file = saves_dir / "tetris.sav"
    save_file.write_bytes(b"\x00" * 8)

    transport = _mock_transport([])
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    with repo.batch() as conn:
        conn.execute(
            "INSERT INTO games (source_path, original_filename, file_type, extension, "
            "size_bytes, mtime, sha1, md5, crc32, set_type, created_at, updated_at) "
            "VALUES (?, ?, 'rom', '.gb', 0, 0, ?, ?, 'x', 'single', ?, ?)",
            ("/roms/tetris.gb", "tetris.gb", "aa" * 20, "bb" * 16, "2024-01-01", "2024-01-01"),
        )

    result, _ = sync_saves(
        saves_dir,
        "dropbox:/saves",
        transport=transport,
        repository=repo,
        save_extensions=_SAVE_EXTS,
        dry_run=False,
    )

    assert result.uploaded == 1
    assert result.errors == 0
    with repo.connect() as conn:
        row = conn.execute("SELECT play_count FROM games").fetchone()
    assert row["play_count"] == 1


def test_apply_download_calls_transport(tmp_path: Path) -> None:
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()

    transport = _mock_transport([_remote_entry("mario.sav")])
    repo = LibraryRepository(tmp_path / "lib.sqlite")

    result, _ = sync_saves(
        saves_dir,
        "dropbox:/saves",
        transport=transport,
        repository=repo,
        save_extensions=_SAVE_EXTS,
        dry_run=False,
    )

    assert result.downloaded == 1
    transport.download.assert_called_once()


# ---------------------------------------------------------------------------
# TEST-1a — conflict resolution per conflict_policy
# ---------------------------------------------------------------------------


def _conflict_setup(tmp_path: Path) -> tuple[Path, MagicMock, LibraryRepository]:
    """Both sides changed after the last sync → decide() returns 'conflict'."""
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()
    save_file = saves_dir / "tetris.sav"
    save_file.write_bytes(b"\x00" * 8)
    # local changed +100s, remote changed +200s, both after last sync at _NOW.
    _set_mtime(save_file, _NOW + timedelta(seconds=100))
    transport = _mock_transport([_remote_entry("tetris.sav", offset_seconds=200)])
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _seed_last_sync(repo, save_file, _NOW, remote_path="dropbox:/saves/tetris.sav")
    return saves_dir, transport, repo


def test_conflict_keep_local_uploads_local(tmp_path: Path) -> None:
    saves_dir, transport, repo = _conflict_setup(tmp_path)

    result, decisions = sync_saves(
        saves_dir,
        "dropbox:/saves",
        transport=transport,
        repository=repo,
        save_extensions=_SAVE_EXTS,
        dry_run=False,
        conflict_policy="keep_local",
    )

    assert result.conflicts == 1
    assert decisions[0].action == "conflict"
    # Local wins: remote is backed up (download) and local is pushed (upload).
    transport.upload.assert_called_once()
    transport.download.assert_called_once()


def test_conflict_keep_remote_downloads_remote(tmp_path: Path) -> None:
    saves_dir, transport, repo = _conflict_setup(tmp_path)

    result, _ = sync_saves(
        saves_dir,
        "dropbox:/saves",
        transport=transport,
        repository=repo,
        save_extensions=_SAVE_EXTS,
        dry_run=False,
        conflict_policy="keep_remote",
    )

    assert result.conflicts == 1
    # Remote wins: local is backed up locally and remote is pulled (download).
    transport.download.assert_called_once()
    transport.upload.assert_not_called()
    # Local copy preserved with a .conflict-* suffix.
    backups = list((saves_dir).glob("tetris.sav.conflict-*"))
    assert len(backups) == 1


def test_conflict_newest_picks_newer_remote(tmp_path: Path) -> None:
    # Remote mtime (+200s) is newer than local (+100s) → remote wins under "newest".
    saves_dir, transport, repo = _conflict_setup(tmp_path)

    result, _ = sync_saves(
        saves_dir,
        "dropbox:/saves",
        transport=transport,
        repository=repo,
        save_extensions=_SAVE_EXTS,
        dry_run=False,
        conflict_policy="newest",
    )

    assert result.conflicts == 1
    transport.download.assert_called_once()
    transport.upload.assert_not_called()


def test_conflict_override_wins_over_global_policy(tmp_path: Path) -> None:
    """SYNC-CONFLICT-MANUAL-1: a per-file override beats conflict_policy."""
    saves_dir, transport, repo = _conflict_setup(tmp_path)

    result, _ = sync_saves(
        saves_dir,
        "dropbox:/saves",
        transport=transport,
        repository=repo,
        save_extensions=_SAVE_EXTS,
        dry_run=False,
        conflict_policy="keep_remote",  # would normally download, not upload
        conflict_overrides={"tetris.sav": "keep_local"},
    )

    assert result.conflicts == 1
    transport.upload.assert_called_once()  # local won, per the override


def test_conflict_override_skip_leaves_both_sides_untouched(tmp_path: Path) -> None:
    saves_dir, transport, repo = _conflict_setup(tmp_path)

    result, _ = sync_saves(
        saves_dir,
        "dropbox:/saves",
        transport=transport,
        repository=repo,
        save_extensions=_SAVE_EXTS,
        dry_run=False,
        conflict_policy="newest",
        conflict_overrides={"tetris.sav": "skip"},
    )

    assert result.conflicts == 1
    transport.upload.assert_not_called()
    transport.download.assert_not_called()
    # No conflict-suffixed backup either — nothing was touched.
    assert not list(saves_dir.glob("tetris.sav.conflict-*"))


def test_conflict_without_matching_override_uses_global_policy(tmp_path: Path) -> None:
    """A conflict whose relative path isn't in conflict_overrides is
    unaffected — only the explicitly listed files change behaviour."""
    saves_dir, transport, repo = _conflict_setup(tmp_path)

    result, _ = sync_saves(
        saves_dir,
        "dropbox:/saves",
        transport=transport,
        repository=repo,
        save_extensions=_SAVE_EXTS,
        dry_run=False,
        conflict_policy="keep_remote",
        conflict_overrides={"other/unrelated.sav": "keep_local"},
    )

    assert result.conflicts == 1
    transport.download.assert_called_once()
    transport.upload.assert_not_called()


def test_stale_watermark_from_old_remote_is_not_reused(tmp_path: Path) -> None:
    """REV43-35: a last_sync_at recorded against a since-changed saves_remote
    must not be treated as if it applied to the current one — otherwise a
    real conflict (both sides changed) could be missed."""
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()
    save_file = saves_dir / "tetris.sav"
    save_file.write_bytes(b"\x00" * 8)
    _set_mtime(save_file, _NOW + timedelta(seconds=100))
    transport = _mock_transport([_remote_entry("tetris.sav", offset_seconds=200)])
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    # Watermark recorded against a DIFFERENT (old) remote than the one used below.
    _seed_last_sync(repo, save_file, _NOW, remote_path="dropbox:/old-remote/tetris.sav")

    result, decisions = sync_saves(
        saves_dir,
        "dropbox:/saves",
        transport=transport,
        repository=repo,
        save_extensions=_SAVE_EXTS,
        dry_run=False,
        conflict_policy="newest",
    )

    # No matching watermark for the current remote → conflict-detection branch
    # is skipped, falls back to plain newest-wins (remote is newer here).
    assert result.conflicts == 0
    assert decisions[0].action == "download"
    assert decisions[0].last_sync_at is None


# ---------------------------------------------------------------------------
# TEST-1c — a backup failure must never block the sync
# ---------------------------------------------------------------------------


def test_backup_failure_does_not_block_download(tmp_path: Path, monkeypatch) -> None:
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()
    # Local exists and is OLDER than remote → decide() returns 'download',
    # and because backup_root is set the syncer backs it up before overwriting.
    save_file = saves_dir / "tetris.sav"
    save_file.write_bytes(b"local")
    _set_mtime(save_file, _NOW)
    transport = _mock_transport([_remote_entry("tetris.sav", offset_seconds=100)])
    repo = LibraryRepository(tmp_path / "lib.sqlite")

    def _boom(*_args, **_kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr("rom_manager.backup.save_backup.backup_save", _boom)

    result, _ = sync_saves(
        saves_dir,
        "dropbox:/saves",
        transport=transport,
        repository=repo,
        save_extensions=_SAVE_EXTS,
        dry_run=False,
        backup_root=tmp_path / "backups",
    )

    # Backup blew up, but the download still happened and no error was recorded.
    transport.download.assert_called_once()
    assert result.downloaded == 1
    assert result.errors == 0
