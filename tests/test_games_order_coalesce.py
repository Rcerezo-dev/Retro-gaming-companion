"""JUEGOS-FIX-4: SQLite orders NULL first in ASC, so the default "Título"
sort (ORDER BY canonical_title, ...) buried every identified game behind
unmatched ones (canonical_title IS NULL). ORDER BY must COALESCE to
original_filename so identified titles surface on page 1."""

from __future__ import annotations

from pathlib import Path

from rom_manager.database.repository import LibraryRepository


def _insert(
    repo: LibraryRepository,
    *,
    source_path: str,
    canonical_title: str | None,
    md5: str,
) -> None:
    repo.upsert_game(
        original_filename=Path(source_path).name,
        source_path=source_path,
        platform="gba",
        file_type="rom",
        relative_parent="",
        region="USA",
        extension=".gba",
        size_bytes=1,
        mtime=0,
        sha1=source_path,
        md5=md5,
        crc32="CCCCCCCC",
        set_type="single",
        timestamp="2024-01-01T00:00:00",
    )
    if canonical_title is not None:
        with repo.connect() as conn:
            conn.execute(
                "UPDATE games SET canonical_title = ? WHERE source_path = ?",
                (canonical_title, source_path),
            )
            conn.commit()


def test_title_sort_does_not_bury_matched_games_behind_unmatched(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    # Unmatched games sort before "Earthbound" alphabetically by filename
    # (SQLite puts NULL canonical_title first in ASC without COALESCE).
    for i in range(3):
        _insert(
            repo,
            source_path=str(tmp_path / f"aaa_unmatched_{i}.gba"),
            canonical_title=None,
            md5=f"{i}" * 32,
        )
    _insert(
        repo,
        source_path=str(tmp_path / "earthbound.gba"),
        canonical_title="Earthbound",
        md5="E" * 32,
    )

    games, total = repo.get_games_paginated(platform="gba", sort_by="title", limit=100)
    assert total == 4
    titles = [g["canonical_title"] or g["original_filename"] for g in games]
    assert titles[0] == "Earthbound"


def test_platform_sort_also_coalesces_title(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert(
        repo,
        source_path=str(tmp_path / "aaa_unmatched.gba"),
        canonical_title=None,
        md5="1" * 32,
    )
    _insert(
        repo,
        source_path=str(tmp_path / "earthbound.gba"),
        canonical_title="Earthbound",
        md5="2" * 32,
    )

    games, _ = repo.get_games_paginated(platform="gba", limit=100)
    titles = [g["canonical_title"] or g["original_filename"] for g in games]
    assert titles[0] == "Earthbound"
