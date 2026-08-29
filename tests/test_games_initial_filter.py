"""Alphabet filter for the Games tab: get_games_paginated(initial=...) narrows
to titles whose first letter matches (or, for "#", to titles that don't start
with A-Z)."""

from __future__ import annotations

from pathlib import Path

from rom_manager.database.repository import LibraryRepository


def _insert(
    repo: LibraryRepository, *, source_path: str, canonical_title: str, extension: str, md5: str
) -> None:
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


def test_get_games_paginated_initial_filter(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert(
        repo,
        source_path=str(tmp_path / "e.gba"),
        canonical_title="Earthbound",
        extension=".gba",
        md5="A" * 32,
    )
    _insert(
        repo,
        source_path=str(tmp_path / "z.gba"),
        canonical_title="Zelda",
        extension=".gba",
        md5="B" * 32,
    )

    games_e, total_e = repo.get_games_paginated(platform="gba", initial="E", limit=100)
    assert total_e == 1
    assert games_e[0]["canonical_title"] == "Earthbound"

    games_z, total_z = repo.get_games_paginated(platform="gba", initial="Z", limit=100)
    assert total_z == 1
    assert games_z[0]["canonical_title"] == "Zelda"


def test_get_games_paginated_initial_hash_matches_non_alpha(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert(
        repo,
        source_path=str(tmp_path / "3.gba"),
        canonical_title="3 Ninjas",
        extension=".gba",
        md5="C" * 32,
    )
    _insert(
        repo,
        source_path=str(tmp_path / "z.gba"),
        canonical_title="Zelda",
        extension=".gba",
        md5="D" * 32,
    )

    games_hash, total_hash = repo.get_games_paginated(platform="gba", initial="#", limit=100)
    assert total_hash == 1
    assert games_hash[0]["canonical_title"] == "3 Ninjas"
