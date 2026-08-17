"""Tests for STORAGE-MGR-3: bulk delete of selected /api/library-diff entries."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from rom_manager.database.repository import LibraryRepository
from rom_manager.services.storage_service import delete_storage_items

TS = "2026-01-01T00:00:00"


def _insert_game(repo: LibraryRepository, *, source_path: str, sha1: str) -> None:
    repo.upsert_game(
        original_filename=Path(source_path).name,
        source_path=source_path,
        platform="Game Boy Advance",
        file_type="rom",
        relative_parent="",
        region="USA",
        extension=".gba",
        size_bytes=1024,
        mtime=0,
        sha1=sha1,
        md5=(sha1 * 32)[:32],
        crc32="deadbeef",
        set_type="single",
        timestamp=TS,
    )


def _count(repo: LibraryRepository) -> int:
    with repo.connect() as conn:
        return int(conn.execute("SELECT COUNT(*) AS n FROM games").fetchone()["n"])


def test_deletes_pc_item_to_trash(tmp_path: Path) -> None:
    roms = tmp_path / "roms"
    roms.mkdir()
    rom = roms / "Game.gba"
    rom.write_bytes(b"data")

    repo_pc = LibraryRepository(tmp_path / "pc.db")
    repo_android = LibraryRepository(tmp_path / "android.db")
    _insert_game(repo_pc, source_path=str(rom), sha1="A" * 40)

    result = delete_storage_items(repo_pc, repo_android, [{"sha1": "A" * 40, "location": "pc"}])

    assert result == {"trashed": 1, "deleted_device": 0, "errors": []}
    assert not rom.exists()
    assert (roms / "_descartados" / "Game.gba").exists()
    assert _count(repo_pc) == 0


def test_android_item_without_transport_errors_and_keeps_row(tmp_path: Path) -> None:
    repo_pc = LibraryRepository(tmp_path / "pc.db")
    repo_android = LibraryRepository(tmp_path / "android.db")
    device_path = "/storage/emulated/0/RetroArch/roms/gba/Game.gba"
    _insert_game(repo_android, source_path=device_path, sha1="B" * 40)

    result = delete_storage_items(
        repo_pc, repo_android, [{"sha1": "B" * 40, "location": "android"}], adb_transport=None
    )

    assert result["trashed"] == 0
    assert result["deleted_device"] == 0
    assert len(result["errors"]) == 1
    assert _count(repo_android) == 1


def test_android_item_with_transport_deletes_via_adb(tmp_path: Path) -> None:
    repo_pc = LibraryRepository(tmp_path / "pc.db")
    repo_android = LibraryRepository(tmp_path / "android.db")
    device_path = "/storage/emulated/0/RetroArch/roms/gba/Game.gba"
    _insert_game(repo_android, source_path=device_path, sha1="C" * 40)
    adb = SimpleNamespace(removed=[])
    adb.remove = lambda p: adb.removed.append(p)

    result = delete_storage_items(
        repo_pc, repo_android, [{"sha1": "C" * 40, "location": "android"}], adb_transport=adb
    )

    assert result == {"trashed": 0, "deleted_device": 1, "errors": []}
    assert adb.removed == [device_path]
    assert _count(repo_android) == 0


def test_unknown_sha1_reports_error(tmp_path: Path) -> None:
    repo_pc = LibraryRepository(tmp_path / "pc.db")
    repo_android = LibraryRepository(tmp_path / "android.db")

    result = delete_storage_items(repo_pc, repo_android, [{"sha1": "F" * 40, "location": "pc"}])

    assert result["trashed"] == 0
    assert len(result["errors"]) == 1


def test_invalid_item_is_reported_not_raised(tmp_path: Path) -> None:
    repo_pc = LibraryRepository(tmp_path / "pc.db")
    repo_android = LibraryRepository(tmp_path / "android.db")

    result = delete_storage_items(repo_pc, repo_android, [{"sha1": "", "location": "pc"}])

    assert result["trashed"] == 0
    assert len(result["errors"]) == 1


@pytest.mark.parametrize("location", ["pc", "android"])
def test_mixed_selection_only_touches_matching_repo(tmp_path: Path, location: str) -> None:
    """Deleting a PC item must never touch the Android DB/repo, and vice versa."""
    roms = tmp_path / "roms"
    roms.mkdir()
    rom = roms / "Game.gba"
    rom.write_bytes(b"data")

    repo_pc = LibraryRepository(tmp_path / "pc.db")
    repo_android = LibraryRepository(tmp_path / "android.db")
    _insert_game(repo_pc, source_path=str(rom), sha1="D" * 40)
    _insert_game(repo_android, source_path="/storage/x/Other.gba", sha1="E" * 40)

    sha1 = "D" * 40 if location == "pc" else "E" * 40
    adb = SimpleNamespace(remove=lambda p: None)
    delete_storage_items(
        repo_pc, repo_android, [{"sha1": sha1, "location": location}], adb_transport=adb
    )

    if location == "pc":
        assert _count(repo_pc) == 0
        assert _count(repo_android) == 1
    else:
        assert _count(repo_pc) == 1
        assert _count(repo_android) == 0
