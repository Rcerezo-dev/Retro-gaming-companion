"""Tests for JUEGOS-UX-5/6: .lrtl scanner and per-origin playtime upsert.

Same conventions as test_repository.py: real SQLite in tmp_path, no mocks.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rom_manager.database.repository import LibraryRepository
from rom_manager.utils.lrtl_scanner import parse_lrtl, parse_runtime, scan_lrtl_dir

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def repo(tmp_path: Path) -> LibraryRepository:
    return LibraryRepository(tmp_path / "library.db")


TS = "2026-01-01T00:00:00"


def _upsert(repo: LibraryRepository, **overrides) -> None:
    defaults = dict(
        original_filename="Game.gba",
        source_path="/roms/gba/Game.gba",
        platform="Game Boy Advance",
        file_type="rom",
        relative_parent="gba",
        region="USA",
        extension=".gba",
        size_bytes=1024,
        mtime=1700000000,
        sha1="aabbccdd" * 5,
        md5="11223344" * 4,
        crc32="deadbeef",
        set_type="single",
        timestamp=TS,
    )
    defaults.update(overrides)
    repo.upsert_game(**defaults)


def _write_lrtl(path: Path, runtime: str, last_played: str = "2026-01-01 12:00:00") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"version": "1.0", "runtime": runtime, "last_played": last_played}),
        encoding="utf-8",
    )
    return path


def _playtime_row(repo: LibraryRepository) -> dict:
    with repo.connect() as conn:
        row = conn.execute(
            "SELECT playtime_minutes_pc, playtime_minutes_android,"
            " first_played_at, last_played_at FROM games"
        ).fetchone()
    return dict(row)


# ── parse_runtime ─────────────────────────────────────────────────────────────


def test_parse_runtime_rounds_seconds():
    assert parse_runtime("0:31:37") == 32  # 37s redondea hacia arriba
    assert parse_runtime("0:31:29") == 31  # 29s trunca
    assert parse_runtime("1:00:00") == 60


def test_parse_runtime_hours_over_24():
    assert parse_runtime("25:10:30") == 25 * 60 + 10 + 1


def test_parse_runtime_invalid_raises():
    with pytest.raises(ValueError):
        parse_runtime("31:37")
    with pytest.raises(ValueError):
        parse_runtime("a:b:c")
    with pytest.raises(ValueError):
        parse_runtime("")


# ── parse_lrtl ────────────────────────────────────────────────────────────────


def test_parse_lrtl_valid(tmp_path: Path):
    f = _write_lrtl(tmp_path / "Super Game (USA).lrtl", "0:31:37")
    entry = parse_lrtl(f)
    assert entry is not None
    assert entry.stem == "Super Game (USA)"
    assert entry.minutes == 32
    assert entry.last_played == "2026-01-01T12:00:00"


def test_parse_lrtl_corrupt_json_returns_none(tmp_path: Path):
    f = tmp_path / "bad.lrtl"
    f.write_text("{not json", encoding="utf-8")
    assert parse_lrtl(f) is None


def test_parse_lrtl_missing_runtime_returns_none(tmp_path: Path):
    f = tmp_path / "empty.lrtl"
    f.write_text('{"version": "1.0"}', encoding="utf-8")
    assert parse_lrtl(f) is None


def test_parse_lrtl_no_last_played(tmp_path: Path):
    f = tmp_path / "g.lrtl"
    f.write_text('{"runtime": "0:10:00", "last_played": ""}', encoding="utf-8")
    entry = parse_lrtl(f)
    assert entry is not None
    assert entry.last_played is None


# ── scan_lrtl_dir ─────────────────────────────────────────────────────────────


def test_scan_lrtl_dir_recurses_per_core(tmp_path: Path):
    _write_lrtl(tmp_path / "CoreA" / "Game One.lrtl", "0:10:00")
    _write_lrtl(tmp_path / "CoreB" / "Game Two.lrtl", "0:20:00")
    entries = {e.stem: e.minutes for e in scan_lrtl_dir(tmp_path)}
    assert entries == {"Game One": 10, "Game Two": 20}


def test_scan_lrtl_dir_same_stem_keeps_max(tmp_path: Path):
    """Mismo juego bajo dos cores: gana el runtime mayor (semántica MAX)."""
    _write_lrtl(tmp_path / "CoreA" / "Game.lrtl", "0:30:00")
    _write_lrtl(tmp_path / "CoreB" / "Game.lrtl", "1:00:00")
    entries = scan_lrtl_dir(tmp_path)
    assert len(entries) == 1
    assert entries[0].minutes == 60


def test_scan_lrtl_dir_skips_corrupt(tmp_path: Path):
    _write_lrtl(tmp_path / "CoreA" / "Good.lrtl", "0:05:00")
    (tmp_path / "CoreA" / "Bad.lrtl").write_text("{oops", encoding="utf-8")
    entries = scan_lrtl_dir(tmp_path)
    assert [e.stem for e in entries] == ["Good"]


# ── set_playtime_minutes ──────────────────────────────────────────────────────


def test_set_playtime_matches_by_filename_stem(repo):
    _upsert(repo)
    assert repo.set_playtime_minutes("game", 45, "pc", "2026-01-02T10:00:00") is True
    row = _playtime_row(repo)
    assert row["playtime_minutes_pc"] == 45
    assert row["playtime_minutes_android"] is None
    assert row["last_played_at"] == "2026-01-02T10:00:00"
    assert row["first_played_at"] == "2026-01-02T10:00:00"


def test_set_playtime_matches_by_canonical_title(repo):
    _upsert(repo)
    repo.update_match(
        "/roms/gba/Game.gba",
        canonical_title="Super Game (USA)",
        match_confidence="high",
        catalog_source="nointro",
    )
    assert repo.set_playtime_minutes("super game (usa)", 10, "pc") is True
    assert _playtime_row(repo)["playtime_minutes_pc"] == 10


def test_set_playtime_no_match_returns_false(repo):
    _upsert(repo)
    assert repo.set_playtime_minutes("Other Game", 10, "pc") is False


def test_set_playtime_never_decreases(repo):
    """Los .lrtl traen totales acumulados: MAX, nunca sobreescribir a menos."""
    _upsert(repo)
    repo.set_playtime_minutes("Game", 100, "pc")
    repo.set_playtime_minutes("Game", 50, "pc")
    assert _playtime_row(repo)["playtime_minutes_pc"] == 100
    repo.set_playtime_minutes("Game", 120, "pc")
    assert _playtime_row(repo)["playtime_minutes_pc"] == 120


def test_set_playtime_origins_are_independent(repo):
    """JUEGOS-UX-5: cada origen es dueño de su contador — el de Android nunca
    pisa el de PC ni al revés."""
    _upsert(repo)
    repo.set_playtime_minutes("Game", 100, "pc")
    repo.set_playtime_minutes("Game", 40, "android")
    row = _playtime_row(repo)
    assert row["playtime_minutes_pc"] == 100
    assert row["playtime_minutes_android"] == 40


def test_set_playtime_last_played_only_moves_forward(repo):
    _upsert(repo)
    repo.set_playtime_minutes("Game", 10, "pc", "2026-01-05T00:00:00")
    repo.set_playtime_minutes("Game", 20, "pc", "2026-01-03T00:00:00")
    assert _playtime_row(repo)["last_played_at"] == "2026-01-05T00:00:00"


def test_set_playtime_null_last_played_keeps_null(repo):
    _upsert(repo)
    repo.set_playtime_minutes("Game", 10, "pc", None)
    assert _playtime_row(repo)["last_played_at"] is None


def test_set_playtime_invalid_origin_raises(repo):
    _upsert(repo)
    with pytest.raises(ValueError):
        repo.set_playtime_minutes("Game", 10, "cloud")
