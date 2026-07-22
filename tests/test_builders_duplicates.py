"""Tests for _build_review_queue (TABS-FIX-6): fuses SHA1/title/RA duplicates
and plan conflicts into a single queue grouped by game."""

from __future__ import annotations

import json
from pathlib import Path

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.builders.duplicates import _build_review_queue

_TS = "2026-01-01T00:00:00"


def _insert_game(
    repo: LibraryRepository,
    *,
    source_path: str,
    sha1: str,
    md5: str = "m" * 32,
    original_filename: str = "game.gb",
    platform: str | None = "Game Boy",
    canonical_title: str | None = None,
    size_bytes: int = 1024,
) -> None:
    repo.upsert_game(
        original_filename=original_filename,
        source_path=source_path,
        platform=platform,
        file_type="rom",
        relative_parent="",
        region="USA",
        extension=".gb",
        size_bytes=size_bytes,
        mtime=0,
        sha1=sha1,
        md5=md5,
        crc32="CCCCCCCC",
        set_type="single",
        timestamp=_TS,
    )
    if canonical_title:
        repo.update_match(
            source_path,
            canonical_title=canonical_title,
            match_confidence="high",
            catalog_source="test.dat",
        )


def _write_ra_cache(project_root: Path, console_id: int, hashes: dict[str, int]) -> None:
    cache_dir = project_root / ".rommgr" / "ra_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    games = [
        {"ID": i, "Title": f"g{i}", "NumAchievements": n, "Hashes": [h]}
        for i, (h, n) in enumerate(hashes.items(), start=1)
    ]
    (cache_dir / f"ra_hashes_{console_id}.json").write_text(json.dumps(games), encoding="utf-8")


def test_sha1_duplicate_group(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path="/roms/a.gb", sha1="A" * 40, original_filename="tetris.gb")
    _insert_game(
        repo, source_path="/roms/backup/a.gb", sha1="A" * 40, original_filename="tetris.gb"
    )

    result = _build_review_queue(repo, repo, None)

    assert result["total_groups"] == 1
    group = result["groups"][0]
    assert group["reasons"] == ["sha1"]
    assert len(group["entries"]) == 2


def test_no_duplicates_no_groups(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path="/roms/a.gb", sha1="A" * 40)
    _insert_game(repo, source_path="/roms/b.gb", sha1="B" * 40, original_filename="other.gb")

    result = _build_review_queue(repo, repo, None)

    assert result["groups"] == []


def test_title_duplicate_across_region_tags(tmp_path: Path) -> None:
    """Same normalized title (region tag differs) but different sha1 → 'title'."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(
        repo,
        source_path="/roms/tetris_usa.gb",
        sha1="A" * 40,
        canonical_title="Tetris (USA)",
    )
    _insert_game(
        repo,
        source_path="/roms/tetris_eu.gb",
        sha1="B" * 40,
        canonical_title="Tetris (Europe)",
    )

    result = _build_review_queue(repo, repo, None)

    assert result["total_groups"] == 1
    group = result["groups"][0]
    assert group["reasons"] == ["title"]
    assert {e["source_path"] for e in group["entries"]} == {
        "/roms/tetris_usa.gb",
        "/roms/tetris_eu.gb",
    }


def test_ra_mixed_reason_and_recommendation(tmp_path: Path) -> None:
    """One entry has RA achievements, the other doesn't -> reason 'ra' and the
    RA-supported entry is recommended, matching the criterion the old
    '/api/ra-duplicates' view already used."""
    config = load_config(tmp_path)
    _write_ra_cache(tmp_path, console_id=4, hashes={"m" * 32: 10})
    repo = LibraryRepository(config.database_path)
    _insert_game(
        repo,
        source_path="/roms/tetris_a.gb",
        sha1="A" * 40,
        md5="m" * 32,
        canonical_title="Tetris (USA)",
        platform="Game Boy Advance",
    )
    _insert_game(
        repo,
        source_path="/roms/tetris_b.gb",
        sha1="B" * 40,
        md5="n" * 32,
        canonical_title="Tetris (Europe)",
        platform="Game Boy Advance",
    )

    result = _build_review_queue(repo, repo, config)

    assert result["total_groups"] == 1
    group = result["groups"][0]
    assert "ra" in group["reasons"]
    assert "title" in group["reasons"]  # distinct sha1 + canonical_title also flags "title"
    recommended = next(e for e in group["entries"] if e["recommended"])
    assert recommended["source_path"] == "/roms/tetris_a.gb"


def test_excluded_group_is_hidden(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path="/roms/a.gb", sha1="A" * 40, original_filename="tetris.gb")
    _insert_game(
        repo, source_path="/roms/backup/a.gb", sha1="A" * 40, original_filename="tetris.gb"
    )

    before = _build_review_queue(repo, repo, None)
    assert before["total_groups"] == 1
    group_key = before["groups"][0]["group_key"]

    repo.exclude_duplicate_group(group_key)
    after = _build_review_queue(repo, repo, None)

    assert after["groups"] == []


def test_plan_disk_conflict_single_entry_group(tmp_path: Path) -> None:
    """A 'disk' conflict has only one tracked DB row (the blocker on disk isn't
    a games row) — it must still surface, unlike sha1/title/ra groups which
    need >=2 entries to mean anything."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    (tmp_path / "Tetris (World).gb").touch()  # blocker: untracked file on disk
    messy = tmp_path / "messy_tetris.gb"
    messy.touch()
    _insert_game(
        repo,
        source_path=str(messy),
        sha1="A" * 40,
        canonical_title="Tetris (World)",
        platform="Game Boy",
    )

    result = _build_review_queue(repo, repo, None)

    disk_groups = [g for g in result["groups"] if "disk" in g["reasons"]]
    assert len(disk_groups) == 1
    assert len(disk_groups[0]["entries"]) == 1
    assert disk_groups[0]["entries"][0]["source_path"] == str(messy)
    assert disk_groups[0]["entries"][0]["target_name"] == "Tetris (World).gb"
