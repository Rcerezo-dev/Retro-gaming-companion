"""Tests for publish_retroarch_thumbnails() — RetroArch thumbnails/ publishing.

Covers hardlinking of PNG sources (zero-duplication path), JPG->PNG
conversion with mtime-keyed caching (conversion is mocked — real conversion
shells out to powershell.exe, Windows-only), and the skip conditions.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from rom_manager.database.repository import LibraryRepository
from rom_manager.utils import retroarch_thumbnails as rat

TS = "2026-01-01T00:00:00"


@pytest.fixture
def repo(tmp_path: Path) -> LibraryRepository:
    return LibraryRepository(tmp_path / "library.db")


def _add_game(
    repo: LibraryRepository,
    filename: str,
    *,
    platform: str = "Game Boy Advance",
    canonical_title: str | None = "Test Game (USA)",
    box_art_path: str = "",
    screenshot_path: str = "",
) -> int:
    repo.upsert_game(
        original_filename=filename,
        source_path=f"/roms/gba/{filename}",
        platform=platform,
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
        gid = conn.execute(
            "SELECT id FROM games WHERE original_filename = ?", (filename,)
        ).fetchone()["id"]
    if canonical_title is not None:
        repo.set_canonical_title(gid, canonical_title)
    with repo.batch() as conn:
        repo.upsert_metadata(
            game_id=gid,
            ss_game_id="1",
            title=canonical_title or "",
            year="",
            genre="",
            publisher="",
            developer="",
            description="",
            rating="",
            box_art_url="",
            box_art_path=box_art_path,
            screenshot_path=screenshot_path,
            scraped_at=TS,
            connection=conn,
        )
    return gid


def test_publishes_png_via_hardlink(tmp_path, repo):
    library_root = tmp_path / "library"
    src = library_root / "gba" / "media" / "images" / "game.png"
    src.parent.mkdir(parents=True)
    src.write_bytes(b"fake-png-bytes")
    _add_game(repo, "game.gba", box_art_path=str(src))

    retroarch_root = tmp_path / "RetroArch"
    result = rat.publish_retroarch_thumbnails(library_root, repo, retroarch_root)

    dest = (
        retroarch_root
        / "thumbnails"
        / "Nintendo - Game Boy Advance"
        / "Named_Boxarts"
        / "Test Game (USA).png"
    )
    assert dest.exists()
    assert dest.samefile(src)
    assert result == {
        "published": 1,
        "converted": 0,
        "skipped_no_title": 0,
        "missing_source": 0,
        "errors": [],
    }


def test_rerun_is_idempotent_and_skips_relinking(tmp_path, repo):
    library_root = tmp_path / "library"
    src = library_root / "gba" / "media" / "images" / "game.png"
    src.parent.mkdir(parents=True)
    src.write_bytes(b"fake-png-bytes")
    _add_game(repo, "game.gba", box_art_path=str(src))
    retroarch_root = tmp_path / "RetroArch"

    rat.publish_retroarch_thumbnails(library_root, repo, retroarch_root)
    result = rat.publish_retroarch_thumbnails(library_root, repo, retroarch_root)

    assert result["published"] == 1
    assert result["errors"] == []


def test_converts_jpg_and_caches_across_runs(tmp_path, repo, monkeypatch):
    library_root = tmp_path / "library"
    src = library_root / "gba" / "media" / "images" / "game.jpg"
    src.parent.mkdir(parents=True)
    src.write_bytes(b"fake-jpg-bytes")
    _add_game(repo, "game.gba", box_art_path=str(src))
    retroarch_root = tmp_path / "RetroArch"

    calls = []

    def _fake_convert(source: Path, dest_png: Path) -> bool:
        calls.append(source)
        dest_png.parent.mkdir(parents=True, exist_ok=True)
        dest_png.write_bytes(b"converted-png-bytes")
        return True

    monkeypatch.setattr(rat, "_convert_to_png", _fake_convert)

    first = rat.publish_retroarch_thumbnails(library_root, repo, retroarch_root)
    second = rat.publish_retroarch_thumbnails(library_root, repo, retroarch_root)

    assert first["converted"] == 1
    assert first["published"] == 1
    assert second["converted"] == 0  # cache hit, not reconverted
    assert second["published"] == 1
    assert len(calls) == 1

    dest = (
        retroarch_root
        / "thumbnails"
        / "Nintendo - Game Boy Advance"
        / "Named_Boxarts"
        / "Test Game (USA).png"
    )
    assert dest.read_bytes() == b"converted-png-bytes"


def test_conversion_failure_is_reported_as_error(tmp_path, repo, monkeypatch):
    library_root = tmp_path / "library"
    src = library_root / "gba" / "media" / "images" / "game.jpg"
    src.parent.mkdir(parents=True)
    src.write_bytes(b"fake-jpg-bytes")
    _add_game(repo, "game.gba", box_art_path=str(src))
    retroarch_root = tmp_path / "RetroArch"

    monkeypatch.setattr(rat, "_convert_to_png", lambda source, dest_png: False)

    result = rat.publish_retroarch_thumbnails(library_root, repo, retroarch_root)

    assert result["published"] == 0
    assert result["converted"] == 0
    assert len(result["errors"]) == 1


def test_skips_games_without_canonical_title(tmp_path, repo):
    library_root = tmp_path / "library"
    src = library_root / "gba" / "media" / "images" / "game.png"
    src.parent.mkdir(parents=True)
    src.write_bytes(b"fake-png-bytes")
    _add_game(repo, "game.gba", canonical_title=None, box_art_path=str(src))
    retroarch_root = tmp_path / "RetroArch"

    result = rat.publish_retroarch_thumbnails(library_root, repo, retroarch_root)

    assert result["skipped_no_title"] == 1
    assert result["published"] == 0
    assert not (retroarch_root / "thumbnails").exists()


def test_missing_source_file_is_counted(tmp_path, repo):
    library_root = tmp_path / "library"
    missing = library_root / "gba" / "media" / "images" / "gone.png"
    _add_game(repo, "game.gba", box_art_path=str(missing))
    retroarch_root = tmp_path / "RetroArch"

    result = rat.publish_retroarch_thumbnails(library_root, repo, retroarch_root)

    assert result["missing_source"] == 1
    assert result["published"] == 0


def test_publishes_both_boxart_and_screenshot(tmp_path, repo):
    library_root = tmp_path / "library"
    box = library_root / "gba" / "media" / "images" / "game.png"
    shot = library_root / "gba" / "media" / "screenshots" / "game.png"
    box.parent.mkdir(parents=True)
    shot.parent.mkdir(parents=True)
    box.write_bytes(b"box")
    shot.write_bytes(b"shot")
    _add_game(repo, "game.gba", box_art_path=str(box), screenshot_path=str(shot))
    retroarch_root = tmp_path / "RetroArch"

    result = rat.publish_retroarch_thumbnails(library_root, repo, retroarch_root)

    assert result["published"] == 2
    assert (
        retroarch_root
        / "thumbnails"
        / "Nintendo - Game Boy Advance"
        / "Named_Boxarts"
        / "Test Game (USA).png"
    ).exists()
    assert (
        retroarch_root
        / "thumbnails"
        / "Nintendo - Game Boy Advance"
        / "Named_Snaps"
        / "Test Game (USA).png"
    ).exists()
