from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

from rom_manager.database.repository import LibraryRepository
from rom_manager.sync.rclone_transport import RcloneTransport, RemoteEntry
from rom_manager.sync.save_syncer import list_local_saves, sync_saves

_SAVE_EXTS = (".sav", ".state")
_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


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
