"""Tests for _build_library_diff — STORAGE-MGR-1/2: size_bytes per entry + totals."""

from __future__ import annotations

from pathlib import Path

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.builders.diff import _build_library_diff

TS = "2026-01-01T00:00:00"


def _insert_game(repo: LibraryRepository, *, source_path: str, sha1: str, size_bytes: int) -> None:
    repo.upsert_game(
        original_filename=Path(source_path).name,
        source_path=source_path,
        platform="Game Boy Advance",
        file_type="rom",
        relative_parent="",
        region="USA",
        extension=".gba",
        size_bytes=size_bytes,
        mtime=0,
        sha1=sha1,
        md5=(sha1 * 32)[:32],
        crc32="deadbeef",
        set_type="single",
        timestamp=TS,
    )


def test_diff_includes_size_bytes_per_entry_and_totals(tmp_path: Path) -> None:
    repo_pc = LibraryRepository(tmp_path / "pc.db")
    repo_android = LibraryRepository(tmp_path / "android.db")
    config = load_config(tmp_path)

    _insert_game(repo_pc, source_path="/roms/OnlyPc.gba", sha1="a" * 40, size_bytes=1000)
    _insert_game(repo_android, source_path="/sd/OnlyAndroid.gba", sha1="b" * 40, size_bytes=2000)

    result = _build_library_diff(repo_pc, repo_android, config)

    assert result["only_pc"][0]["size_bytes"] == 1000
    assert result["only_android"][0]["size_bytes"] == 2000
    assert result["total_pc_bytes"] == 1000
    assert result["total_android_bytes"] == 2000
