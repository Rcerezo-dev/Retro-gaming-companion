"""Tests for pegasus_writer.write_pegasus_metadata."""

from __future__ import annotations

from pathlib import Path

from rom_manager.database.repository import LibraryRepository
from rom_manager.scraper.pegasus_writer import write_pegasus_metadata

TS = "2026-01-01T00:00:00"


def _insert_matched_game(repo: LibraryRepository, *, platform: str, source_path: str) -> None:
    repo.upsert_game(
        original_filename=Path(source_path).name,
        source_path=source_path,
        platform=platform,
        file_type="rom",
        relative_parent="",
        region="USA",
        extension=Path(source_path).suffix,
        size_bytes=1024,
        mtime=0,
        sha1="a" * 40,
        md5="b" * 32,
        crc32="deadbeef",
        set_type="single",
        timestamp=TS,
    )
    repo.update_match(
        source_path,
        canonical_title=Path(source_path).stem,
        match_confidence="high",
        catalog_source="nointro",
    )


def test_writes_metadata_for_each_platform(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_matched_game(repo, platform="GBA", source_path=str(tmp_path / "GBA" / "game.gba"))

    result = write_pegasus_metadata(tmp_path, repo)

    assert result == {"platforms": 1, "games": 1, "errors": []}
    assert (tmp_path / "GBA" / "metadata.pegasus.txt").exists()


def test_platform_write_failure_is_reported_not_silent(tmp_path: Path) -> None:
    """REV43-30: a platform whose write fails must be reported in "errors",
    not silently dropped while the caller still thinks everything wrote."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_matched_game(repo, platform="GBA", source_path=str(tmp_path / "GBA" / "game.gba"))
    _insert_matched_game(repo, platform="PSX", source_path=str(tmp_path / "PSX" / "game.cue"))

    # Block PSX's directory creation: a plain file already occupies that path.
    (tmp_path / "PSX").write_bytes(b"not a directory")

    result = write_pegasus_metadata(tmp_path, repo)

    assert result["platforms"] == 1  # only GBA succeeded
    assert result["games"] == 1
    assert len(result["errors"]) == 1
    assert "PSX" in result["errors"][0]
    assert (tmp_path / "GBA" / "metadata.pegasus.txt").exists()
