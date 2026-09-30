"""Cache corruption found live 2026-09-29: two writers (ra_check + a
review-queue build) racing on psx_disc_hashes.json left a torn, invalid JSON
file on disk -- _save() now writes to a temp file and os.replace()s it in,
atomic on both POSIX and Windows."""

from __future__ import annotations

from pathlib import Path

from rom_manager.retroachievements.ra_disc_hash_cache import _CACHE_FILENAME, _load, _save


def test_save_then_load_roundtrip(tmp_path: Path) -> None:
    data = {"C:/Game.chd": {"sig": "123:456", "hash": "abc"}}

    _save(tmp_path, data)
    loaded = _load(tmp_path)

    assert loaded == data


def test_save_leaves_no_temp_files_behind(tmp_path: Path) -> None:
    _save(tmp_path, {"a": {"sig": "1:1", "hash": "x"}})

    entries = list(tmp_path.iterdir())
    assert entries == [tmp_path / _CACHE_FILENAME]


def test_load_recovers_from_corrupt_file(tmp_path: Path) -> None:
    (tmp_path / _CACHE_FILENAME).write_text("not valid json{{{", encoding="utf-8")

    assert _load(tmp_path) == {}


def test_load_missing_file_returns_empty(tmp_path: Path) -> None:
    assert _load(tmp_path) == {}
