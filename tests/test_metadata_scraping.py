"""Tests for SAGE-1: batch description scraping support in the metadata repository.

Covers get_games_for_scraping(missing_descriptions=), update_description()
and get_description_coverage().
"""

from __future__ import annotations

from pathlib import Path

import pytest

from rom_manager.database.repository import LibraryRepository

TS = "2026-01-01T00:00:00"


@pytest.fixture
def repo(tmp_path: Path) -> LibraryRepository:
    return LibraryRepository(tmp_path / "library.db")


def _add_game(repo: LibraryRepository, filename: str, **overrides) -> int:
    defaults = dict(
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
    defaults.update(overrides)
    repo.upsert_game(**defaults)
    with repo.connect() as conn:
        row = conn.execute(
            "SELECT id FROM games WHERE original_filename = ?", (filename,)
        ).fetchone()
    return row["id"]


def _add_metadata(repo: LibraryRepository, game_id: int, description: str) -> None:
    with repo.batch() as conn:
        repo.upsert_metadata(
            game_id=game_id,
            ss_game_id="123",
            title="Some Game",
            year="1999",
            genre="Platform",
            publisher="Pub",
            developer="Dev",
            description=description,
            rating="4",
            box_art_url="http://example/box.png",
            box_art_path="/media/box.png",
            scraped_at=TS,
            connection=conn,
        )


def test_default_excludes_games_with_metadata(repo):
    gid_no_meta = _add_game(repo, "NoMeta.gba")
    gid_empty_desc = _add_game(repo, "EmptyDesc.gba")
    _add_metadata(repo, gid_empty_desc, description="")

    ids = {g["id"] for g in repo.get_games_for_scraping()}
    assert gid_no_meta in ids
    assert gid_empty_desc not in ids


def test_missing_descriptions_includes_empty_desc_games(repo):
    gid_no_meta = _add_game(repo, "NoMeta.gba")
    gid_empty_desc = _add_game(repo, "EmptyDesc.gba")
    gid_with_desc = _add_game(repo, "WithDesc.gba")
    _add_metadata(repo, gid_empty_desc, description="")
    _add_metadata(repo, gid_with_desc, description="A great game.")

    games = repo.get_games_for_scraping(missing_descriptions=True)
    by_id = {g["id"]: g for g in games}
    assert gid_no_meta in by_id and not by_id[gid_no_meta]["has_metadata"]
    assert gid_empty_desc in by_id and by_id[gid_empty_desc]["has_metadata"]
    assert gid_with_desc not in by_id


def test_missing_descriptions_skips_checked_unmatched_games(repo):
    gid = _add_game(repo, "Unmatched.gba")
    with repo.batch() as conn:
        repo.mark_metadata_scraped(gid, conn)

    assert repo.get_games_for_scraping(missing_descriptions=True) == []


def test_update_description_preserves_image_paths(repo):
    gid = _add_game(repo, "EmptyDesc.gba")
    _add_metadata(repo, gid, description="")

    with repo.batch() as conn:
        repo.update_description(
            game_id=gid, description="Filled in.", scraped_at=TS, connection=conn
        )

    with repo.connect() as conn:
        row = conn.execute(
            "SELECT description, box_art_path FROM game_metadata WHERE game_id = ?", (gid,)
        ).fetchone()
    assert row["description"] == "Filled in."
    assert row["box_art_path"] == "/media/box.png"


def test_description_coverage(repo):
    assert repo.get_description_coverage() == {
        "total": 0,
        "with_description": 0,
        "pct": 0.0,
    }

    gid_with = _add_game(repo, "WithDesc.gba")
    gid_empty = _add_game(repo, "EmptyDesc.gba")
    _add_game(repo, "NoMeta.gba")
    _add_metadata(repo, gid_with, description="A great game.")
    _add_metadata(repo, gid_empty, description="")

    cov = repo.get_description_coverage()
    assert cov["total"] == 3
    assert cov["with_description"] == 1
    assert cov["pct"] == 33.3
