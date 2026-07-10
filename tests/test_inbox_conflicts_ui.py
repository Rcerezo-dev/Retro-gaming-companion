"""RA-CONFLICT-2: read-only conflict listing + manual per-conflict resolution
from the UI (find_organize_conflicts / resolve_inbox_conflict)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from rom_manager.database.repository import LibraryRepository
from rom_manager.web.inbox_pipeline import find_organize_conflicts, resolve_inbox_conflict

_GB_CONSOLE_ID = 5  # RA console ID for "Game Boy"
_TS = "2024-01-01T00:00:00"


@dataclass
class _FakeInboxConfig:
    path: str = ""
    target_root: str = ""


@dataclass
class _FakeConfig:
    project_root: Path
    library_root: Path | None = None
    save_extensions: tuple[str, ...] = field(default_factory=tuple)
    inbox: _FakeInboxConfig = field(default_factory=_FakeInboxConfig)


def _insert_game(repo: LibraryRepository, *, source_path: Path, md5: str, platform: str) -> None:
    repo.upsert_game(
        original_filename=source_path.name,
        source_path=str(source_path),
        platform=platform,
        file_type="rom",
        relative_parent="",
        region="World",
        extension=source_path.suffix,
        size_bytes=1024,
        mtime=0,
        sha1="S" * 40,
        md5=md5,
        crc32="CCCCCCCC",
        set_type="single",
        timestamp=_TS,
    )


def _write_ra_cache(project_root: Path, games: list[dict]) -> None:
    cache_dir = project_root / ".rommgr" / "ra_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / f"ra_hashes_{_GB_CONSOLE_ID}.json").write_text(json.dumps(games), encoding="utf-8")


def _ra_entry(game_id: int, md5: str, achievements: int) -> dict:
    return {
        "ID": game_id,
        "Title": f"Game {game_id}",
        "NumAchievements": achievements,
        "NumLeaderboards": 0,
        "Points": achievements * 10,
        "Hashes": [md5.upper()],
    }


def _setup(tmp_path: Path) -> tuple[Path, Path, Path, LibraryRepository]:
    inbox = tmp_path / "Inbox"
    inbox.mkdir()
    dest_folder = tmp_path / "gb"
    dest_folder.mkdir()
    source_file = inbox / "Tetris (World).gb"
    dest_file = dest_folder / "Tetris (World).gb"
    source_file.write_bytes(b"SOURCE_CONTENT")
    dest_file.write_bytes(b"DEST_CONTENT")
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=source_file, md5="a" * 32, platform="Game Boy")
    return inbox, source_file, dest_file, repo


def test_find_organize_conflicts_lists_the_pair(tmp_path: Path) -> None:
    inbox, source_file, dest_file, repo = _setup(tmp_path)
    _write_ra_cache(tmp_path, [])
    config = _FakeConfig(project_root=tmp_path)

    conflicts = find_organize_conflicts(repo, config, str(inbox), str(tmp_path))

    assert len(conflicts) == 1
    c = conflicts[0]
    assert c["source_path"] == str(source_file)
    assert c["dest_path"] == str(dest_file)
    assert c["platform"] == "Game Boy"
    assert c["source_ra"] is None
    assert c["dest_ra"] is None


def test_find_organize_conflicts_empty_when_no_conflict(tmp_path: Path) -> None:
    inbox, source_file, dest_file, repo = _setup(tmp_path)
    dest_file.write_bytes(b"SOURCE_CONTENT")  # now identical to source
    _write_ra_cache(tmp_path, [])
    config = _FakeConfig(project_root=tmp_path)

    assert find_organize_conflicts(repo, config, str(inbox), str(tmp_path)) == []


def test_resolve_inbox_conflict_keep_source(tmp_path: Path) -> None:
    inbox, source_file, dest_file, repo = _setup(tmp_path)
    _write_ra_cache(tmp_path, [])
    config = _FakeConfig(
        project_root=tmp_path,
        library_root=tmp_path,
        inbox=_FakeInboxConfig(path=str(inbox), target_root=str(tmp_path)),
    )

    result = resolve_inbox_conflict(repo, config, str(source_file), "source")

    assert result == {"status": "kept_source", "error": None}
    assert dest_file.read_bytes() == b"SOURCE_CONTENT"
    assert not source_file.exists()


def test_resolve_inbox_conflict_keep_dest(tmp_path: Path) -> None:
    inbox, source_file, dest_file, repo = _setup(tmp_path)
    _write_ra_cache(tmp_path, [])
    config = _FakeConfig(
        project_root=tmp_path,
        library_root=tmp_path,
        inbox=_FakeInboxConfig(path=str(inbox), target_root=str(tmp_path)),
    )

    result = resolve_inbox_conflict(repo, config, str(source_file), "dest")

    assert result == {"status": "kept_dest", "error": None}
    assert dest_file.read_bytes() == b"DEST_CONTENT"
    assert not source_file.exists()


def test_resolve_inbox_conflict_no_longer_conflicting(tmp_path: Path) -> None:
    inbox, source_file, dest_file, repo = _setup(tmp_path)
    dest_file.unlink()  # conflict resolved by someone/something else already
    config = _FakeConfig(
        project_root=tmp_path,
        library_root=tmp_path,
        inbox=_FakeInboxConfig(path=str(inbox), target_root=str(tmp_path)),
    )

    result = resolve_inbox_conflict(repo, config, str(source_file), "source")

    assert "error" in result
    assert source_file.exists()  # untouched
