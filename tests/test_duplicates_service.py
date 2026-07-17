from __future__ import annotations

from pathlib import Path

from rom_manager.database.repository import LibraryRepository
from rom_manager.services.duplicates_service import (
    delete_all_duplicates,
    delete_duplicate,
)

_TS = "2024-01-01T00:00:00"
_SHA1_A = "A" * 40
_SHA1_B = "B" * 40


def _insert_game(
    repo: LibraryRepository,
    *,
    source_path: str,
    sha1: str,
    size_bytes: int = 1024,
    platform: str = "Game Boy",
) -> None:
    repo.upsert_game(
        original_filename="game.gb",
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


def _game_id(repo: LibraryRepository, source_path: str) -> int:
    with repo.connect() as conn:
        row = conn.execute("SELECT id FROM games WHERE source_path = ?", (source_path,)).fetchone()
    return int(row["id"])


def test_delete_duplicate_removes_file_and_db_record(tmp_path: Path) -> None:
    rom = tmp_path / "dup.gb"
    rom.write_bytes(b"data")
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(rom), sha1=_SHA1_A)
    gid = _game_id(repo, str(rom))

    result = delete_duplicate(repo, game_id=gid)

    assert result == {"deleted": str(rom)}
    assert not rom.exists()
    with repo.connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM games").fetchone()["n"] == 0


def test_delete_duplicate_derives_source_path_from_db(tmp_path: Path) -> None:
    rom = tmp_path / "dup.gb"
    rom.write_bytes(b"data")
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(rom), sha1=_SHA1_A)
    gid = _game_id(repo, str(rom))

    # No source_path passed → derived from DB
    result = delete_duplicate(repo, game_id=gid, source_path="")

    assert result == {"deleted": str(rom)}
    assert not rom.exists()


def test_delete_duplicate_missing_game_id(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    result = delete_duplicate(repo, game_id=None)
    assert "error" in result


def test_delete_duplicate_file_already_gone_still_cleans_db(tmp_path: Path) -> None:
    rom = tmp_path / "ghost.gb"  # never created on disk
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(rom), sha1=_SHA1_A)
    gid = _game_id(repo, str(rom))

    result = delete_duplicate(repo, game_id=gid)

    assert result == {"deleted": str(rom)}
    with repo.connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM games").fetchone()["n"] == 0


def test_delete_all_duplicates_keeps_canonical_deletes_rest(tmp_path: Path) -> None:
    canonical = tmp_path / "a1.gb"
    dup = tmp_path / "a2.gb"
    canonical.write_bytes(b"data")
    dup.write_bytes(b"data")
    unique = tmp_path / "b.gb"
    unique.write_bytes(b"other")

    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(canonical), sha1=_SHA1_A, size_bytes=2048)
    _insert_game(repo, source_path=str(dup), sha1=_SHA1_A, size_bytes=2048)
    _insert_game(repo, source_path=str(unique), sha1=_SHA1_B)

    result = delete_all_duplicates(repo)

    assert result["deleted"] == 1
    assert result["skipped"] == 0
    assert result["failed"] == 0
    assert result["freed_bytes"] == 2048
    # First entry of the group is kept; the second is removed
    assert canonical.exists()
    assert not dup.exists()
    assert unique.exists()


def test_delete_all_duplicates_respects_platform_filter(tmp_path: Path) -> None:
    # DUPLICADOS-UX-1: con filtro de plataforma solo se borra esa plataforma
    gb_keep, gb_dup = tmp_path / "gb1.gb", tmp_path / "gb2.gb"
    snes_keep, snes_dup = tmp_path / "sn1.sfc", tmp_path / "sn2.sfc"
    for f in (gb_keep, gb_dup, snes_keep, snes_dup):
        f.write_bytes(b"data")

    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(gb_keep), sha1=_SHA1_A)
    _insert_game(repo, source_path=str(gb_dup), sha1=_SHA1_A)
    _insert_game(repo, source_path=str(snes_keep), sha1=_SHA1_B, platform="SNES")
    _insert_game(repo, source_path=str(snes_dup), sha1=_SHA1_B, platform="SNES")

    result = delete_all_duplicates(repo, platform="SNES")

    assert result["deleted"] == 1
    assert not snes_dup.exists()
    # El grupo Game Boy queda intacto
    assert gb_keep.exists() and gb_dup.exists()


def test_excluded_duplicates_list_and_remove(tmp_path: Path) -> None:
    # DUPLICADOS-UX-5: listar exclusiones y quitarlas devuelve el grupo a duplicados
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(tmp_path / "a1.gb"), sha1=_SHA1_A)
    _insert_game(repo, source_path=str(tmp_path / "a2.gb"), sha1=_SHA1_A)

    repo.exclude_duplicate_sha1(_SHA1_A)
    assert repo.get_duplicate_groups() == []
    excluded = repo.get_excluded_duplicates()
    assert len(excluded) == 1
    assert excluded[0]["sha1"] == _SHA1_A
    assert excluded[0]["platform"] == "Game Boy"

    repo.remove_excluded_duplicate(_SHA1_A)
    assert repo.get_excluded_duplicates() == []
    assert len(repo.get_duplicate_groups()) == 1


def test_delete_all_duplicates_no_groups(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(tmp_path / "only.gb"), sha1=_SHA1_A)
    result = delete_all_duplicates(repo)
    assert result["deleted"] == 0
    assert result["summary"].startswith("0 movidos a _descartados/")
