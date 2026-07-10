"""RA-CONFLICT-1: the Inbox organize step resolves same-name/different-content
conflicts using RetroAchievements data, same tie-break rule as apply_ra_conflicts
(services/ra_duplicates_service.py) — higher achievement count wins."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from rom_manager.database.repository import LibraryRepository
from rom_manager.web.inbox_pipeline import _resolve_organize_conflict

# RA console ID for "Game Boy" = 5 (key "gameboy")
_GB_CONSOLE_ID = 5
_TS = "2024-01-01T00:00:00"


@dataclass
class _FakeConfig:
    project_root: Path
    save_extensions: tuple[str, ...] = field(default_factory=tuple)


def _insert_game(repo: LibraryRepository, *, source_path: Path, md5: str) -> int:
    repo.upsert_game(
        original_filename=source_path.name,
        source_path=str(source_path),
        platform="Game Boy",
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
    with repo.connect() as conn:
        return int(
            conn.execute(
                "SELECT id FROM games WHERE source_path=?", (str(source_path),)
            ).fetchone()["id"]
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


def test_source_wins_replaces_dest(tmp_path: Path) -> None:
    inbox = tmp_path / "Inbox"
    inbox.mkdir()
    dest_folder = tmp_path / "gb"
    dest_folder.mkdir()

    source_file = inbox / "Tetris (World).gb"
    dest_file = dest_folder / "Tetris (World).gb"
    source_file.write_bytes(b"SOURCE_WITH_RA")
    dest_file.write_bytes(b"DEST_NO_RA")

    md5_src, md5_dst = "a" * 32, "b" * 32
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    game_id = _insert_game(repo, source_path=source_file, md5=md5_src)
    _insert_game(repo, source_path=dest_file, md5=md5_dst)
    _write_ra_cache(tmp_path, [_ra_entry(1, md5_src, 50), _ra_entry(2, md5_dst, 5)])

    config = _FakeConfig(project_root=tmp_path)
    status, err = _resolve_organize_conflict(
        repo, config, source_file, dest_file, game_id, "Game Boy", {}
    )

    assert status == "kept_source"
    assert err is None
    assert dest_file.exists()
    assert dest_file.read_bytes() == b"SOURCE_WITH_RA"
    assert not source_file.exists()
    assert (dest_folder / "_descartados" / "Tetris (World).gb").exists()

    with repo.connect() as conn:
        rows = conn.execute("SELECT source_path FROM games").fetchall()
    assert [r["source_path"] for r in rows] == [str(dest_file.resolve())]


def test_dest_wins_discards_source(tmp_path: Path) -> None:
    inbox = tmp_path / "Inbox"
    inbox.mkdir()
    dest_folder = tmp_path / "gb"
    dest_folder.mkdir()

    source_file = inbox / "Tetris (World).gb"
    dest_file = dest_folder / "Tetris (World).gb"
    source_file.write_bytes(b"SOURCE_NO_RA")
    dest_file.write_bytes(b"DEST_WITH_RA")

    md5_src, md5_dst = "c" * 32, "d" * 32
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    game_id = _insert_game(repo, source_path=source_file, md5=md5_src)
    _insert_game(repo, source_path=dest_file, md5=md5_dst)
    _write_ra_cache(tmp_path, [_ra_entry(3, md5_src, 5), _ra_entry(4, md5_dst, 50)])

    config = _FakeConfig(project_root=tmp_path)
    status, err = _resolve_organize_conflict(
        repo, config, source_file, dest_file, game_id, "Game Boy", {}
    )

    assert status == "kept_dest"
    assert err is None
    assert dest_file.read_bytes() == b"DEST_WITH_RA"
    assert not source_file.exists()
    assert (inbox / "_descartados" / "Tetris (World).gb").exists()

    with repo.connect() as conn:
        rows = conn.execute("SELECT source_path FROM games").fetchall()
    assert [r["source_path"] for r in rows] == [str(dest_file)]


def test_no_ra_data_leaves_both_untouched(tmp_path: Path) -> None:
    inbox = tmp_path / "Inbox"
    inbox.mkdir()
    dest_folder = tmp_path / "gb"
    dest_folder.mkdir()

    source_file = inbox / "Tetris (World).gb"
    dest_file = dest_folder / "Tetris (World).gb"
    source_file.write_bytes(b"SOURCE")
    dest_file.write_bytes(b"DEST")

    repo = LibraryRepository(tmp_path / "lib.sqlite")
    game_id = _insert_game(repo, source_path=source_file, md5="1" * 32)
    _insert_game(repo, source_path=dest_file, md5="2" * 32)
    _write_ra_cache(tmp_path, [])  # no achievement data for anything

    config = _FakeConfig(project_root=tmp_path)
    status, err = _resolve_organize_conflict(
        repo, config, source_file, dest_file, game_id, "Game Boy", {}
    )

    assert status == "unresolved"
    assert err is None
    assert source_file.exists()
    assert dest_file.exists()
    assert not (inbox / "_descartados").exists()
    assert not (dest_folder / "_descartados").exists()
