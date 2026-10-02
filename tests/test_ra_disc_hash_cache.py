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


def test_get_saturn_dreamcast_disc_hash_routes_by_console_id(tmp_path: Path, monkeypatch) -> None:
    """DC-GDROM-FIRST-SECTOR-1 follow-up: 33=Saturn, 40=Dreamcast, same
    console-ID convention ra_checker._DISC_HASH_CONSOLE_IDS already keys by."""
    from rom_manager.retroachievements import ra_disc_hash_cache as m

    saturn_file = tmp_path / "game.bin"
    saturn_file.write_bytes(b"x" * 10)
    dreamcast_file = tmp_path / "game.gdi"
    dreamcast_file.write_bytes(b"y" * 10)

    monkeypatch.setattr(m, "compute_saturn_ra_hash", lambda p, chdman_path=None: "saturn-hash")
    monkeypatch.setattr(
        m, "compute_dreamcast_ra_hash", lambda p, chdman_path=None: "dreamcast-hash"
    )

    assert m.get_saturn_dreamcast_disc_hash(str(saturn_file), tmp_path, 33) == "saturn-hash"
    assert m.get_saturn_dreamcast_disc_hash(str(dreamcast_file), tmp_path, 40) == "dreamcast-hash"


def test_get_saturn_dreamcast_disc_hash_caches_by_sig(tmp_path: Path, monkeypatch) -> None:
    from rom_manager.retroachievements import ra_disc_hash_cache as m

    f = tmp_path / "game.bin"
    f.write_bytes(b"x" * 10)
    calls: list[Path] = []

    def fake_compute(p: Path, chdman_path: Path | None = None) -> str:
        calls.append(p)
        return "hash1"

    monkeypatch.setattr(m, "compute_saturn_ra_hash", fake_compute)

    assert m.get_saturn_dreamcast_disc_hash(str(f), tmp_path, 33) == "hash1"
    assert m.get_saturn_dreamcast_disc_hash(str(f), tmp_path, 33) == "hash1"
    assert len(calls) == 1  # second call was a cache hit, never recomputed


def test_get_saturn_dreamcast_disc_hash_unknown_console_returns_none(tmp_path: Path) -> None:
    from rom_manager.retroachievements.ra_disc_hash_cache import get_saturn_dreamcast_disc_hash

    f = tmp_path / "game.bin"
    f.write_bytes(b"x" * 10)

    assert get_saturn_dreamcast_disc_hash(str(f), tmp_path, 999) is None


def test_get_saturn_dreamcast_disc_hash_missing_file_returns_none(tmp_path: Path) -> None:
    from rom_manager.retroachievements.ra_disc_hash_cache import get_saturn_dreamcast_disc_hash

    assert get_saturn_dreamcast_disc_hash(str(tmp_path / "missing.bin"), tmp_path, 40) is None
