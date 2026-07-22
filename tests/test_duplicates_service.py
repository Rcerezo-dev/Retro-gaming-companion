from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from rom_manager.database.repository import LibraryRepository
from rom_manager.services.duplicates_service import (
    delete_all_duplicates,
    delete_duplicate,
)

# TABS-FIX-1's device-path detection only applies on Windows — a bare leading
# "/" is a normal, verifiable local path on POSIX (see utils/paths.is_device_path).
_windows_only = pytest.mark.skipif(os.name != "nt", reason="Windows-only device-path detection")

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


@_windows_only
def test_delete_duplicate_device_path_unreachable_does_not_touch_db(tmp_path: Path) -> None:
    """TABS-FIX-1: a device path (ADB scan) is never reachable via Path.exists()
    on Windows even when the file is alive on the console — must not silently
    delete the DB row and report success."""
    device_path = "/storage/emulated/0/RetroArch/roms/gb/dup.gb"
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=device_path, sha1=_SHA1_A)
    gid = _game_id(repo, device_path)

    result = delete_duplicate(repo, game_id=gid)

    assert "error" in result
    with repo.connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM games").fetchone()["n"] == 1


@_windows_only
def test_delete_duplicate_device_path_with_adb_transport_deletes_via_adb(tmp_path: Path) -> None:
    """TABS-FIX-1a: with a connected device, the file is deleted for real via
    ADB before the DB row is touched."""
    device_path = "/storage/emulated/0/RetroArch/roms/gb/dup.gb"
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=device_path, sha1=_SHA1_A)
    gid = _game_id(repo, device_path)
    adb = SimpleNamespace(remove=lambda path: None, removed=[])
    adb.remove = lambda path: adb.removed.append(path)

    result = delete_duplicate(repo, game_id=gid, adb_transport=adb)

    assert result == {"deleted": device_path}
    assert adb.removed == [device_path]
    with repo.connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM games").fetchone()["n"] == 0


@_windows_only
def test_delete_duplicate_device_path_adb_remove_fails_does_not_touch_db(tmp_path: Path) -> None:
    """If the ADB delete itself fails (device unplugged mid-op, permission
    denied…), the DB row must stay — no phantom-deleted duplicate."""
    device_path = "/storage/emulated/0/RetroArch/roms/gb/dup.gb"
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=device_path, sha1=_SHA1_A)
    gid = _game_id(repo, device_path)

    def _boom(path):
        raise RuntimeError("no se pudo borrar en el dispositivo")

    adb = SimpleNamespace(remove=_boom)

    result = delete_duplicate(repo, game_id=gid, adb_transport=adb)

    assert "error" in result
    with repo.connect() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM games").fetchone()["n"] == 1


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


@_windows_only
def test_delete_all_duplicates_device_path_counted_unreachable_not_deleted(
    tmp_path: Path,
) -> None:
    """TABS-FIX-1: a duplicate entry that's a device path (ADB scan) must not
    be silently cleaned from the DB — it's counted separately as
    'unreachable', not 'skipped' (which means 'genuinely gone from this PC').
    Both entries are device paths (alphabetically ordered: get_duplicate_groups
    orders by source_path, and any POSIX '/...' path sorts before a Windows
    drive-letter path, so a real local file could never land in entries[1:]
    alongside one — this reproduces the actual bug shape either way)."""
    device_canonical = "/storage/emulated/0/RetroArch/roms/gb/a1.gb"
    device_dup = "/storage/emulated/0/RetroArch/roms/gb/a2.gb"

    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=device_canonical, sha1=_SHA1_A, size_bytes=2048)
    _insert_game(repo, source_path=device_dup, sha1=_SHA1_A, size_bytes=2048)

    result = delete_all_duplicates(repo)

    assert result["deleted"] == 0
    assert result["skipped"] == 0
    assert result["unreachable"] == 1
    with repo.connect() as conn:
        remaining = {r["source_path"] for r in conn.execute("SELECT source_path FROM games")}
    assert device_dup in remaining  # row untouched, not phantom-deleted


@_windows_only
def test_delete_all_duplicates_device_path_with_adb_transport_deletes_via_adb(
    tmp_path: Path,
) -> None:
    """TABS-FIX-1a: with a connected device, on-device duplicates are deleted
    for real and counted as 'deleted', not 'unreachable'."""
    device_canonical = "/storage/emulated/0/RetroArch/roms/gb/a1.gb"
    device_dup = "/storage/emulated/0/RetroArch/roms/gb/a2.gb"

    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=device_canonical, sha1=_SHA1_A, size_bytes=2048)
    _insert_game(repo, source_path=device_dup, sha1=_SHA1_A, size_bytes=2048)
    adb = SimpleNamespace(removed=[])
    adb.remove = lambda path: adb.removed.append(path)

    result = delete_all_duplicates(repo, adb_transport=adb)

    assert result["deleted"] == 1
    assert result["unreachable"] == 0
    assert result["freed_bytes"] == 2048
    assert adb.removed == [device_dup]
    with repo.connect() as conn:
        remaining = {r["source_path"] for r in conn.execute("SELECT source_path FROM games")}
    assert device_dup not in remaining


@_windows_only
def test_delete_all_duplicates_device_path_adb_remove_fails_counted_as_failed(
    tmp_path: Path,
) -> None:
    device_canonical = "/storage/emulated/0/RetroArch/roms/gb/a1.gb"
    device_dup = "/storage/emulated/0/RetroArch/roms/gb/a2.gb"

    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=device_canonical, sha1=_SHA1_A, size_bytes=2048)
    _insert_game(repo, source_path=device_dup, sha1=_SHA1_A, size_bytes=2048)

    def _boom(path):
        raise RuntimeError("device offline")

    adb = SimpleNamespace(remove=_boom)

    result = delete_all_duplicates(repo, adb_transport=adb)

    assert result["deleted"] == 0
    assert result["failed"] == 1
    assert result["unreachable"] == 0
    with repo.connect() as conn:
        remaining = {r["source_path"] for r in conn.execute("SELECT source_path FROM games")}
    assert device_dup in remaining  # row untouched after a failed ADB delete


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
