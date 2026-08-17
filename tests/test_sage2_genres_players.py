"""Tests for SAGE-2: persist genres_list/players from ScreenScraper.

Covers the schema migration + backfill, upsert_metadata() persisting both
fields, and GET /api/export-history exposing them.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from rom_manager.database.repository import LibraryRepository
from rom_manager.database.schema import initialize_database
from rom_manager.web.handlers import play_history as _h_play_history
from rom_manager.web.jobs.manager import JobManager
from rom_manager.web.router import Router

TS = "2026-01-01T00:00:00"


@pytest.fixture
def repo(tmp_path: Path) -> LibraryRepository:
    return LibraryRepository(tmp_path / "library.db")


def _add_game(repo: LibraryRepository, filename: str) -> int:
    repo.upsert_game(
        original_filename=filename,
        source_path=f"/roms/gba/{filename}",
        platform="Game Boy Advance",
        file_type="rom",
        relative_parent="gba",
        region="USA",
        extension=".gba",
        size_bytes=1024,
        mtime=1700000000,
        sha1=(filename * 40)[:40],
        md5=(filename * 32)[:32],
        crc32="deadbeef",
        set_type="single",
        timestamp=TS,
    )
    with repo.connect() as conn:
        row = conn.execute(
            "SELECT id FROM games WHERE original_filename = ?", (filename,)
        ).fetchone()
    return row["id"]


class _Ctx:
    def __init__(self) -> None:
        self.status: int | None = None
        self.body: bytes | None = None

    def _send(self, status: int, content_type: str, body: bytes) -> None:
        self.status = status
        self.body = body


def test_upsert_metadata_persists_genres_list_and_players(repo):
    gid = _add_game(repo, "Sonic.gba")
    with repo.batch() as conn:
        repo.upsert_metadata(
            game_id=gid,
            ss_game_id="1",
            title="Sonic Advance",
            year="2001",
            genre="Platform",
            publisher="Sega",
            developer="Sonic Team",
            description="",
            rating="4",
            box_art_url="",
            box_art_path="",
            genres_list="Platform, Action",
            players="1-2",
            scraped_at=TS,
            connection=conn,
        )

    with repo.connect() as conn:
        row = conn.execute(
            "SELECT genres_list, players FROM game_metadata WHERE game_id = ?", (gid,)
        ).fetchone()
    assert row["genres_list"] == "Platform, Action"
    assert row["players"] == "1-2"


def test_upsert_metadata_conflict_updates_genres_list_and_players(repo):
    gid = _add_game(repo, "Sonic.gba")
    with repo.batch() as conn:
        repo.upsert_metadata(
            game_id=gid,
            ss_game_id="1",
            title="Sonic Advance",
            year="2001",
            genre="Platform",
            publisher="Sega",
            developer="Sonic Team",
            description="",
            rating="4",
            box_art_url="",
            box_art_path="",
            genres_list="Platform",
            players="1",
            scraped_at=TS,
            connection=conn,
        )
    with repo.batch() as conn:
        repo.upsert_metadata(
            game_id=gid,
            ss_game_id="1",
            title="Sonic Advance",
            year="2001",
            genre="Platform",
            publisher="Sega",
            developer="Sonic Team",
            description="",
            rating="4",
            box_art_url="",
            box_art_path="",
            genres_list="Platform, Action",
            players="1-2",
            scraped_at=TS,
            connection=conn,
        )

    with repo.connect() as conn:
        row = conn.execute(
            "SELECT genres_list, players FROM game_metadata WHERE game_id = ?", (gid,)
        ).fetchone()
    assert row["genres_list"] == "Platform, Action"
    assert row["players"] == "1-2"


def test_backfill_seeds_genres_list_from_existing_genre(tmp_path: Path):
    """Rows scraped before the migration get genres_list backfilled from genre;
    players has no source to backfill from and stays NULL."""
    db_path = tmp_path / "library.db"

    # Simulate a pre-SAGE-2 database: create it, then drop the two new
    # columns to reproduce a row that predates this migration.
    repo = LibraryRepository(db_path)
    gid = _add_game(repo, "Old.gba")
    with repo.batch() as conn:
        repo.upsert_metadata(
            game_id=gid,
            ss_game_id="1",
            title="Old Game",
            year="1999",
            genre="RPG",
            publisher="Pub",
            developer="Dev",
            description="",
            rating="",
            box_art_url="",
            box_art_path="",
            scraped_at=TS,
            connection=conn,
        )
    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE game_metadata SET genres_list = NULL, players = NULL")
        conn.commit()

    # Re-running the migration (as happens on every connect) must backfill
    # genres_list from genre without touching players.
    with sqlite3.connect(db_path) as conn:
        initialize_database(conn)
        row = conn.execute(
            "SELECT genres_list, players FROM game_metadata WHERE game_id = ?", (gid,)
        ).fetchone()
    assert row[0] == "RPG"
    assert row[1] is None


def test_export_history_includes_genres_list_and_players(repo):
    import json

    gid = _add_game(repo, "Sonic.gba")
    with repo.batch() as conn:
        repo.upsert_metadata(
            game_id=gid,
            ss_game_id="1",
            title="Sonic Advance",
            year="2001",
            genre="Platform",
            publisher="Sega",
            developer="Sonic Team",
            description="",
            rating="4",
            box_art_url="",
            box_art_path="",
            genres_list="Platform, Action",
            players="1-2",
            scraped_at=TS,
            connection=conn,
        )

    router = Router()
    _h_play_history.register(router, repository=repo, config=object(), job_manager=JobManager())
    ctx = _Ctx()
    router.dispatch("GET", "/api/export-history", ctx)

    payload = json.loads(ctx.body)
    game = next(g for g in payload["games"] if g["id"] == gid)
    assert game["genres_list"] == "Platform, Action"
    assert game["players"] == "1-2"
