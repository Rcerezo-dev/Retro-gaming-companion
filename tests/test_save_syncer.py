from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

from rom_manager.database.repository import LibraryRepository
from rom_manager.sync.rclone_transport import RcloneTransport, RemoteEntry
from rom_manager.sync.save_syncer import list_local_saves, sync_saves
from rom_manager.sync.sync_log import log_sync_event

_SAVE_EXTS = (".sav", ".state")
_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


def _set_mtime(path: Path, when: datetime) -> None:
    ts = when.timestamp()
    os.utime(path, (ts, ts))


def _seed_last_sync(repo: LibraryRepository, local_path: Path, when: datetime) -> None:
    """Record a prior successful sync so ``decide`` can detect a conflict."""
    with repo.connect() as conn:
        log_sync_event(
            conn,
            local_path=str(local_path),
            remote_path="dropbox:/saves",
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
    _seed_last_sync(repo, save_file, _NOW)
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
