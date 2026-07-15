"""Tests for the `scrape` CLI command's error counting (REV43-31)."""

from __future__ import annotations

from pathlib import Path

from rom_manager import cli
from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.scraper.screenscraper import ScraperResult

TS = "2026-01-01T00:00:00"


def _insert_unscraped_game(repo: LibraryRepository, *, source_path: str) -> None:
    repo.upsert_game(
        original_filename=Path(source_path).name,
        source_path=source_path,
        platform="Game Boy Advance",
        file_type="rom",
        relative_parent="",
        region="USA",
        extension=".gba",
        size_bytes=1024,
        mtime=0,
        sha1="a" * 40,
        md5="b" * 32,
        crc32="deadbeef",
        set_type="single",
        timestamp=TS,
    )


class _FakeScreenScraperClient:
    def __init__(self, **_kwargs) -> None:
        pass

    def search(self, **_kwargs) -> ScraperResult:
        return ScraperResult(
            ss_game_id="1",
            title="Game",
            year="2000",
            genre="Platform",
            publisher="Pub",
            developer="Dev",
            description="",
            rating="",
            box_art_url="http://example.invalid/box.png",
        )


def test_scrape_counts_image_download_failure_as_error(tmp_path, monkeypatch, capsys) -> None:
    """REV43-31: the `errors` counter never incremented, even when downloading
    the box art failed — the CLI always printed "Errors: 0" while silently
    keeping a box_art_path that pointed at a file that was never written."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.toml").write_text(
        '[screenscraper]\nuser = "u"\npass = "p"\n', encoding="utf-8"
    )

    config = load_config(tmp_path)
    repo = LibraryRepository(config.database_path)
    rom_path = tmp_path / "gba" / "Game.gba"
    _insert_unscraped_game(repo, source_path=str(rom_path))

    monkeypatch.setattr(
        "rom_manager.scraper.screenscraper.ScreenScraperClient", _FakeScreenScraperClient
    )
    monkeypatch.setattr("rom_manager.scraper.screenscraper.download_image", lambda *_a, **_k: False)

    exit_code = cli.main(["scrape", "--images"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Errors: 1" in out
    assert "fallo al descargar la carátula" in out

    with repo.connect() as conn:
        row = conn.execute(
            "SELECT box_art_path FROM game_metadata gm JOIN games g ON g.id = gm.game_id"
        ).fetchone()
    assert row["box_art_path"] == ""
