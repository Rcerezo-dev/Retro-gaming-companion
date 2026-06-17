from __future__ import annotations

from pathlib import Path

from rom_manager.database.repository import LibraryRepository

_TS = "2024-01-01T00:00:00"
_SHA1_A = "A" * 40
_SHA1_B = "B" * 40
_SHA1_C = "C" * 40


def _insert_game(
    repo: LibraryRepository,
    *,
    source_path: str,
    sha1: str,
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
        md5="M" * 32,
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


def test_no_duplicates(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path="/roms/a.gb", sha1=_SHA1_A)
    _insert_game(repo, source_path="/roms/b.gb", sha1=_SHA1_B)
    assert repo.get_duplicate_groups() == []


def test_one_duplicate_group(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path="/roms/a.gb", sha1=_SHA1_A, canonical_title="Tetris (World)")
    _insert_game(repo, source_path="/roms/backup/a.gb", sha1=_SHA1_A)
    _insert_game(repo, source_path="/roms/b.gb", sha1=_SHA1_B)  # unique

    groups = repo.get_duplicate_groups()
    assert len(groups) == 1
    group = groups[0]
    assert group.sha1 == _SHA1_A
    assert len(group.entries) == 2


def test_multiple_duplicate_groups(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    for i in range(3):
        _insert_game(repo, source_path=f"/roms/a{i}.gb", sha1=_SHA1_A)
    for i in range(2):
        _insert_game(repo, source_path=f"/roms/b{i}.gb", sha1=_SHA1_B)
    _insert_game(repo, source_path="/roms/c.gb", sha1=_SHA1_C)  # unique

    groups = repo.get_duplicate_groups()
    assert len(groups) == 2
    sizes = {len(g.entries) for g in groups}
    assert sizes == {3, 2}


def test_wasted_bytes(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path="/roms/a1.gb", sha1=_SHA1_A, size_bytes=2048)
    _insert_game(repo, source_path="/roms/a2.gb", sha1=_SHA1_A, size_bytes=2048)
    _insert_game(repo, source_path="/roms/a3.gb", sha1=_SHA1_A, size_bytes=2048)

    groups = repo.get_duplicate_groups()
    assert len(groups) == 1
    # 3 copies: 2 are "wasted"
    assert groups[0].wasted_bytes == 2048 * 2


def test_canonical_title_preserved(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(
        repo,
        source_path="/roms/a.gb",
        sha1=_SHA1_A,
        canonical_title="Tetris (World)",
    )
    _insert_game(repo, source_path="/roms/a2.gb", sha1=_SHA1_A)

    groups = repo.get_duplicate_groups()
    titles = {e.canonical_title for e in groups[0].entries}
    assert "Tetris (World)" in titles


def test_empty_library(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    assert repo.get_duplicate_groups() == []
