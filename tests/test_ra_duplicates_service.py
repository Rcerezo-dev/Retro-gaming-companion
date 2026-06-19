from __future__ import annotations

from pathlib import Path

from rom_manager.database.repository import LibraryRepository
from rom_manager.services.ra_duplicates_service import (
    discard_all_ra_duplicates,
    discard_no_support,
    discard_ra_duplicate,
    resolve_duplicate_ra,
)

_TS = "2024-01-01T00:00:00"


def _insert_game(repo: LibraryRepository, *, source_path: str) -> None:
    repo.upsert_game(
        original_filename="game.gb",
        source_path=source_path,
        platform="Game Boy",
        file_type="rom",
        relative_parent="",
        region="USA",
        extension=".gb",
        size_bytes=1024,
        mtime=0,
        sha1="S" * 40,
        md5="M" * 32,
        crc32="CCCCCCCC",
        set_type="single",
        timestamp=_TS,
    )


def _count(repo: LibraryRepository) -> int:
    with repo.connect() as conn:
        return int(conn.execute("SELECT COUNT(*) AS n FROM games").fetchone()["n"])


# ── discard_ra_duplicate ──────────────────────────────────────────────────────


def test_discard_ra_duplicate_moves_to_descartados(tmp_path: Path) -> None:
    rom = tmp_path / "dup.gb"
    rom.write_bytes(b"data")
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(rom))

    result = discard_ra_duplicate(repo, str(rom))

    assert result == {"ok": True}
    assert not rom.exists()
    assert (tmp_path / "_descartados" / "dup.gb").exists()
    assert _count(repo) == 0


def test_discard_ra_duplicate_file_already_gone(tmp_path: Path) -> None:
    rom = tmp_path / "ghost.gb"  # never created
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(rom))

    result = discard_ra_duplicate(repo, str(rom))

    assert result == {"ok": True, "note": "file already missing; removed from DB"}
    assert _count(repo) == 0


def test_discard_ra_duplicate_dest_collision_deletes_source(tmp_path: Path) -> None:
    rom = tmp_path / "dup.gb"
    rom.write_bytes(b"new")
    descartados = tmp_path / "_descartados"
    descartados.mkdir()
    (descartados / "dup.gb").write_bytes(b"old")  # name already taken
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(rom))

    result = discard_ra_duplicate(repo, str(rom))

    assert result == {"ok": True}
    # Source removed outright; the pre-existing discard is preserved
    assert not rom.exists()
    assert (descartados / "dup.gb").read_bytes() == b"old"
    assert _count(repo) == 0


# ── discard_all_ra_duplicates ─────────────────────────────────────────────────


def test_discard_all_ra_duplicates_only_unsupported(tmp_path: Path) -> None:
    supported = tmp_path / "keep.gb"
    unsupported = tmp_path / "drop.gb"
    supported.write_bytes(b"a")
    unsupported.write_bytes(b"b")
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(supported))
    _insert_game(repo, source_path=str(unsupported))

    ra_dups = {
        "groups": [
            {
                "entries": [
                    {"source_path": str(supported), "ra_supported": True},
                    {"source_path": str(unsupported), "ra_supported": False},
                ]
            }
        ]
    }
    result = discard_all_ra_duplicates(repo, ra_dups)

    assert result == {"discarded": 1, "failed": 0, "errors": []}
    assert supported.exists()
    assert not unsupported.exists()
    assert (tmp_path / "_descartados" / "drop.gb").exists()
    assert _count(repo) == 1


def test_discard_all_ra_duplicates_note_passthrough(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    result = discard_all_ra_duplicates(repo, {"note": "nothing"})
    assert result == {"discarded": 0, "failed": 0, "errors": [], "note": "nothing"}


# ── discard_no_support ────────────────────────────────────────────────────────


def test_discard_no_support_commits_db(tmp_path: Path) -> None:
    """Regression: the old handler forgot to commit, so rows survived. The
    service must actually persist the deletion."""
    rom = tmp_path / "ns.gb"
    rom.write_bytes(b"x")
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(rom))

    result = discard_no_support(repo, [{"source_path": str(rom)}])

    assert result == {"discarded": 1, "failed": 0, "errors": []}
    assert not rom.exists()
    assert (tmp_path / "_descartados" / "ns.gb").exists()
    # The row is gone AND committed (a fresh connection still sees it removed)
    assert _count(repo) == 0


def test_discard_no_support_empty(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    result = discard_no_support(repo, [])
    assert result == {"discarded": 0, "failed": 0, "errors": [], "note": "No games to discard."}


# ── resolve_duplicate_ra ──────────────────────────────────────────────────────


def test_resolve_duplicate_ra_discards_paths(tmp_path: Path) -> None:
    keep = tmp_path / "keep.gb"
    drop1 = tmp_path / "drop1.gb"
    drop2 = tmp_path / "drop2.gb"  # never created on disk
    keep.write_bytes(b"k")
    drop1.write_bytes(b"d")
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=str(keep))
    _insert_game(repo, source_path=str(drop1))
    _insert_game(repo, source_path=str(drop2))

    result = resolve_duplicate_ra(repo, str(keep), [str(drop1), str(drop2)])

    assert result == {"discarded": 2, "failed": 0, "errors": []}
    assert keep.exists()
    assert not drop1.exists()
    assert (tmp_path / "_descartados" / "drop1.gb").exists()
    assert _count(repo) == 1  # only keep survives
