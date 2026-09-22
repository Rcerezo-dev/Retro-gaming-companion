"""INBOX-METADATA-INLINE-1: tests for services/scrape_service.py — the shared
lookup+apply path reused by both the Colección single-game scrape endpoint
and the Inbox organize step."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from rom_manager.database.repository import LibraryRepository
from rom_manager.services.scrape_service import scrape_game_metadata

TS = "2026-01-01T00:00:00"


@pytest.fixture
def repo(tmp_path: Path) -> LibraryRepository:
    return LibraryRepository(tmp_path / "library.db")


def _add_game(repo: LibraryRepository, tmp_path: Path) -> int:
    source = tmp_path / "gba" / "mario.gba"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"\x00")
    repo.upsert_game(
        original_filename="mario.gba",
        source_path=str(source),
        platform="Game Boy Advance",
        file_type="rom",
        relative_parent="gba",
        region="USA",
        extension=".gba",
        size_bytes=1024,
        mtime=1700000000,
        sha1="a" * 40,
        md5="b" * 32,
        crc32="deadbeef",
        set_type="single",
        timestamp=TS,
    )
    with repo.connect() as conn:
        row = conn.execute("SELECT id FROM games WHERE original_filename = 'mario.gba'").fetchone()
    return row["id"]


def _config(**overrides) -> SimpleNamespace:
    cfg = SimpleNamespace(
        credentials=SimpleNamespace(
            screenscraper_user="user",
            screenscraper_pass="pass",
            screenscraper_dev_id="",
            screenscraper_dev_pass="",
        )
    )
    for key, value in overrides.items():
        setattr(cfg, key, value)
    return cfg


def _result(**overrides) -> SimpleNamespace:
    defaults = dict(
        ss_game_id="123",
        title="Super Mario Advance",
        year="2001",
        genre="Platform",
        publisher="Nintendo",
        developer="Nintendo",
        description="A platformer.",
        rating="8",
        box_art_url="",
        screenshot_url="",
        wheel_url="",
        genres_list="Platform",
        players="1",
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_no_credentials_returns_error(repo: LibraryRepository) -> None:
    cfg = _config()
    cfg.credentials.screenscraper_user = ""

    result = scrape_game_metadata(1, cfg, repo)

    assert result == {"error": "Credenciales de ScreenScraper no configuradas"}


def test_no_match_returns_found_false(repo: LibraryRepository, tmp_path: Path) -> None:
    game_id = _add_game(repo, tmp_path)
    client = MagicMock()
    client.search.return_value = None
    client.search_by_name.return_value = None
    client.last_quota = {}

    with patch("rom_manager.scraper.screenscraper.ScreenScraperClient", return_value=client):
        result = scrape_game_metadata(game_id, _config(), repo)

    assert result["found"] is False


def test_preview_does_not_write_to_db(repo: LibraryRepository, tmp_path: Path) -> None:
    game_id = _add_game(repo, tmp_path)
    client = MagicMock()
    client.search.return_value = _result()
    client.last_quota = {}

    with patch("rom_manager.scraper.screenscraper.ScreenScraperClient", return_value=client):
        result = scrape_game_metadata(game_id, _config(), repo, preview=True)

    assert result["found"] is True
    assert "applied" not in result
    with repo.connect() as conn:
        row = conn.execute("SELECT * FROM game_metadata WHERE game_id = ?", (game_id,)).fetchone()
    assert row is None


def test_apply_upserts_metadata_and_marks_scraped(repo: LibraryRepository, tmp_path: Path) -> None:
    game_id = _add_game(repo, tmp_path)
    client = MagicMock()
    client.search.return_value = _result()
    client.last_quota = {}

    with patch("rom_manager.scraper.screenscraper.ScreenScraperClient", return_value=client):
        result = scrape_game_metadata(game_id, _config(), repo, download_images=False)

    assert result["applied"] is True
    with repo.connect() as conn:
        meta = conn.execute(
            "SELECT title, genre FROM game_metadata WHERE game_id = ?", (game_id,)
        ).fetchone()
        game = conn.execute(
            "SELECT metadata_scraped FROM games WHERE id = ?", (game_id,)
        ).fetchone()
    assert meta["title"] == "Super Mario Advance"
    assert meta["genre"] == "Platform"
    assert game["metadata_scraped"] == 1


def test_reuses_provided_client_instead_of_building_a_new_one(
    repo: LibraryRepository, tmp_path: Path
) -> None:
    """A caller doing many games in one batch (Inbox) must be able to reuse a
    single client so its rate-limit throttle actually applies across calls."""
    game_id = _add_game(repo, tmp_path)
    shared_client = MagicMock()
    shared_client.search.return_value = _result()
    shared_client.last_quota = {}

    with patch("rom_manager.scraper.screenscraper.ScreenScraperClient") as ctor:
        result = scrape_game_metadata(game_id, _config(), repo, client=shared_client)

    ctor.assert_not_called()
    shared_client.search.assert_called_once()
    assert result["applied"] is True


def test_client_exception_is_caught_and_never_raises(
    repo: LibraryRepository, tmp_path: Path
) -> None:
    """A network failure must never blow up an Inbox organize batch."""
    game_id = _add_game(repo, tmp_path)

    with patch(
        "rom_manager.scraper.screenscraper.ScreenScraperClient",
        side_effect=RuntimeError("network down"),
    ):
        result = scrape_game_metadata(game_id, _config(), repo)

    assert "error" in result
