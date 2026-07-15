"""Tests for the shared RA hash-cache reader in web/builders/duplicates.py
(REV43-53: 3 independent readers of the same cache all bypassed the TTL)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.builders.duplicates import (
    _annotate_duplicates_with_ra,
    _build_ra_duplicates,
    _load_ra_hash_map,
)

TS = "2026-01-01T00:00:00"


def _write_ra_cache(tmp_path: Path, console_id: int, *, age_seconds: float) -> None:
    cache_dir = tmp_path / ".rommgr" / "ra_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"ra_hashes_{console_id}.json"
    cache_file.write_text(
        json.dumps([{"ID": 1, "Title": "Game", "NumAchievements": 10, "Hashes": ["m" * 32]}]),
        encoding="utf-8",
    )
    stale_time = time.time() - age_seconds
    os.utime(cache_file, (stale_time, stale_time))


def test_load_ra_hash_map_ignores_stale_cache(tmp_path: Path) -> None:
    _write_ra_cache(tmp_path, console_id=4, age_seconds=8 * 24 * 3600)  # 8 days old
    result = _load_ra_hash_map(tmp_path / ".rommgr" / "ra_cache", "Game Boy Advance", {})
    assert result == {}


def test_load_ra_hash_map_uses_fresh_cache(tmp_path: Path) -> None:
    _write_ra_cache(tmp_path, console_id=4, age_seconds=3600)
    result = _load_ra_hash_map(tmp_path / ".rommgr" / "ra_cache", "Game Boy Advance", {})
    assert result == {"m" * 32: 10}


def test_annotate_duplicates_with_ra_uses_fresh_cache(tmp_path: Path) -> None:
    _write_ra_cache(tmp_path, console_id=4, age_seconds=3600)
    config = load_config(tmp_path)
    title_groups = [
        {
            "platform": "Game Boy Advance",
            "entries": [{"id": 1}],
        }
    ]
    id_to_md5_repo = LibraryRepository(config.database_path)
    id_to_md5_repo.upsert_game(
        original_filename="game.gba",
        source_path=str(tmp_path / "game.gba"),
        platform="Game Boy Advance",
        file_type="rom",
        relative_parent="",
        region="USA",
        extension=".gba",
        size_bytes=1,
        mtime=0,
        sha1="a" * 40,
        md5="m" * 32,
        crc32="deadbeef",
        set_type="single",
        timestamp=TS,
    )
    with id_to_md5_repo.connect() as conn:
        game_id = conn.execute("SELECT id FROM games").fetchone()["id"]
    title_groups[0]["entries"][0]["id"] = game_id

    result = _annotate_duplicates_with_ra(title_groups, config, id_to_md5_repo)

    assert result[0]["entries"][0]["ra_achievements"] == 10


def test_build_ra_duplicates_reports_no_cache_note(tmp_path: Path) -> None:
    """No cache at all -> the "note" fallback must still trigger, even though
    _load_ra_hash_map now always inserts a (possibly-empty) dict per platform."""
    config = load_config(tmp_path)
    repo = LibraryRepository(config.database_path)
    repo.upsert_game(
        original_filename="game.gba",
        source_path=str(tmp_path / "game.gba"),
        platform="Game Boy Advance",
        file_type="rom",
        relative_parent="",
        region="USA",
        extension=".gba",
        size_bytes=1,
        mtime=0,
        sha1="a" * 40,
        md5="m" * 32,
        crc32="deadbeef",
        set_type="single",
        timestamp=TS,
    )

    result = _build_ra_duplicates(repo, config)

    assert result["groups"] == []
    assert "note" in result
