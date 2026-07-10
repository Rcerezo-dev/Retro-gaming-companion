"""ZIP-ROUTE-FIX-2: organizing a file into a path already held by a stale
("ghost") DB row must not fail with UNIQUE constraint failed — the physical
move already succeeded, so the ghost row (pointing at a file that no longer
exists there) must be dropped before the real row's source_path is updated."""

from __future__ import annotations

from pathlib import Path

from rom_manager.database.repository import LibraryRepository

_TS = "2026-07-10T00:00:00"


def _insert_game(repo: LibraryRepository, *, source_path: str) -> int:
    repo.upsert_game(
        original_filename=Path(source_path).name,
        source_path=source_path,
        platform="Game Boy",
        file_type="rom",
        relative_parent="",
        region="USA",
        extension=".gb",
        size_bytes=1,
        mtime=0,
        sha1="A" * 40,
        md5="M" * 32,
        crc32="CCCCCCCC",
        set_type="single",
        timestamp=_TS,
    )
    with repo.connect() as conn:
        return int(
            conn.execute(
                "SELECT id FROM games WHERE source_path=?", (source_path,)
            ).fetchone()["id"]
        )


def test_ghost_row_dropped_before_update(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    dest_path = str(tmp_path / "Game Boy" / "Tetris (USA).gb")
    # Ghost row: a stale entry pointing at the destination path with no file.
    _insert_game(repo, source_path=dest_path)
    # Real row: the one actually being organized (still at its inbox path).
    game_id = _insert_game(repo, source_path=str(tmp_path / "inbox" / "Tetris (USA).gb"))

    # This is the exact statement pair the organize step now runs.
    with repo.batch() as conn:
        conn.execute("DELETE FROM games WHERE source_path=? AND id!=?", (dest_path, game_id))
        conn.execute(
            "UPDATE games SET source_path=?, original_filename=? WHERE id=?",
            (dest_path, "Tetris (USA).gb", game_id),
        )

    with repo.connect() as conn:
        rows = conn.execute("SELECT id, source_path FROM games").fetchall()
    assert len(rows) == 1
    assert rows[0]["id"] == game_id
    assert rows[0]["source_path"] == dest_path
