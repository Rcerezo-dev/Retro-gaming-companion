"""ANBERNIC-BULK-SEND dedup: before pushing a filtered group of games to the
Anbernic, same-title duplicates collapse to one winner — RA achievements
first, then whichever extension already dominates that platform in the
library.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from rom_manager.database.repository import LibraryRepository
from rom_manager.retroachievements.ra_platform_ids import get_ra_console_id
from rom_manager.services.ra_duplicates_service import filter_duplicate_winners


def _insert(repo: LibraryRepository, *, source_path: str, canonical_title: str, extension: str, md5: str) -> None:
    repo.upsert_game(
        original_filename=Path(source_path).name,
        source_path=source_path,
        platform="gba",
        file_type="rom",
        relative_parent="",
        region="USA",
        extension=extension,
        size_bytes=1,
        mtime=0,
        sha1=source_path,
        md5=md5,
        crc32="CCCCCCCC",
        set_type="single",
        timestamp="2024-01-01T00:00:00",
    )
    with repo.connect() as conn:
        conn.execute(
            "UPDATE games SET canonical_title = ? WHERE source_path = ?",
            (canonical_title, source_path),
        )
        conn.commit()


def _write_ra_cache(project_root: Path, console_id: int, md5_with_achievements: str) -> None:
    cache_dir = project_root / ".rommgr" / "ra_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    data = [
        {
            "ID": 1,
            "Title": "Test Game",
            "NumAchievements": 12,
            "NumLeaderboards": 0,
            "Points": 100,
            "Hashes": [md5_with_achievements],
        }
    ]
    (cache_dir / f"ra_hashes_{console_id}.json").write_text(json.dumps(data), encoding="utf-8")


def test_filter_duplicate_winners_keeps_ra_copy(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert(repo, source_path=str(tmp_path / "a.gba"), canonical_title="Test Game", extension=".gba", md5="A" * 32)
    _insert(repo, source_path=str(tmp_path / "b.zip"), canonical_title="Test Game", extension=".zip", md5="B" * 32)
    _write_ra_cache(tmp_path, get_ra_console_id("gba"), "b" * 32)

    config = SimpleNamespace(project_root=tmp_path)
    games, _total = repo.get_games_paginated(platform="gba", limit=100)
    winners = filter_duplicate_winners(repo, config, games)

    assert [w["source_path"] for w in winners] == [str(tmp_path / "b.zip")]


def test_filter_duplicate_winners_falls_back_to_dominant_format(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    # Two .gba files already establish the platform's dominant format.
    _insert(repo, source_path=str(tmp_path / "other.gba"), canonical_title="Other Game", extension=".gba", md5="C" * 32)
    _insert(repo, source_path=str(tmp_path / "another.gba"), canonical_title="Another", extension=".gba", md5="E" * 32)
    # Duplicate pair with no RA data at all -> tie-break on format.
    _insert(repo, source_path=str(tmp_path / "a.gba"), canonical_title="Test Game", extension=".gba", md5="A" * 32)
    _insert(repo, source_path=str(tmp_path / "a.zip"), canonical_title="Test Game", extension=".zip", md5="D" * 32)

    config = SimpleNamespace(project_root=tmp_path)
    games, _total = repo.get_games_paginated(platform="gba", limit=100)
    winners = filter_duplicate_winners(repo, config, games)

    paths = {w["source_path"] for w in winners}
    assert str(tmp_path / "a.gba") in paths
    assert str(tmp_path / "a.zip") not in paths
    assert len(winners) == 3  # other.gba + another.gba + a.gba
