"""Tests for _apply_ra_conflicts — B-test-4.

Synthetic data scenarios:
  1. Disk conflict  — two files mapped to the same canonical name; the file
     already at the canonical path has more RA achievements → the other one
     should land in _descartados/.
  2. Disk conflict  — the incoming source has MORE achievements → it should
     be renamed to the canonical path; the blocker moves to _descartados/.
  3. Collision      — two files not yet renamed both target the same canonical
     name; the one with more achievements wins; the loser lands in _descartados/.
  4. No-RA skip     — neither file has achievements in the cache → both kept,
     nothing moved.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from rom_manager.database.repository import LibraryRepository
from rom_manager.services.ra_duplicates_service import apply_ra_conflicts

# ---------------------------------------------------------------------------
# RA console ID for "Game Boy" = 5  (key "gameboy")
# ---------------------------------------------------------------------------
_GB_CONSOLE_ID = 5

_TS = "2024-01-01T00:00:00"


# ---------------------------------------------------------------------------
# Minimal stubs
# ---------------------------------------------------------------------------


@dataclass
class _FakeConfig:
    project_root: Path
    save_extensions: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _insert_game(
    repo: LibraryRepository,
    *,
    source_path: Path,
    md5: str,
    canonical_title: str,
    platform: str = "Game Boy",
) -> None:
    repo.upsert_game(
        original_filename=source_path.name,
        source_path=str(source_path),
        platform=platform,
        file_type="rom",
        relative_parent="",
        region="World",
        extension=source_path.suffix,
        size_bytes=1024,
        mtime=0,
        sha1="S" * 40,
        md5=md5,
        crc32="CCCCCCCC",
        set_type="single",
        timestamp=_TS,
    )
    repo.update_match(
        str(source_path),
        canonical_title=canonical_title,
        match_confidence="high",
        catalog_source="test.dat",
    )


def _write_ra_cache(project_root: Path, games: list[dict]) -> None:
    """Write a fake RA cache JSON for Game Boy (console ID 5)."""
    cache_dir = project_root / ".rommgr" / "ra_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"ra_hashes_{_GB_CONSOLE_ID}.json"
    cache_file.write_text(json.dumps(games), encoding="utf-8")


def _ra_entry(game_id: int, md5: str, achievements: int) -> dict:
    return {
        "ID": game_id,
        "Title": f"Game {game_id}",
        "NumAchievements": achievements,
        "NumLeaderboards": 0,
        "Points": achievements * 10,
        "Hashes": [md5.upper()],  # API returns upper-case; parser lowercases
    }


# ---------------------------------------------------------------------------
# Scenario 1 — Disk conflict: target wins (higher RA)
# ---------------------------------------------------------------------------


def test_disk_conflict_target_wins(tmp_path: Path) -> None:
    """
    Setup
    -----
    tetris_old.gb  (md5=aaa, 5 RA)  → wants to rename to Tetris (World).gb
    Tetris (World).gb  (md5=bbb, 50 RA)  already at canonical path

    Expected
    --------
    tetris_old.gb  → _descartados/tetris_old.gb  (loser)
    Tetris (World).gb  stays untouched            (winner)
    DB: tetris_old.gb removed
    """
    roms = tmp_path / "roms"
    roms.mkdir()

    loser_file = roms / "tetris_old.gb"
    winner_file = roms / "Tetris (World).gb"
    loser_file.write_bytes(b"LOSER_ROM")
    winner_file.write_bytes(b"WINNER_ROM")

    md5_loser = "a" * 32
    md5_winner = "b" * 32

    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=loser_file, md5=md5_loser, canonical_title="Tetris (World)")
    _insert_game(repo, source_path=winner_file, md5=md5_winner, canonical_title="Tetris (World)")

    _write_ra_cache(
        tmp_path,
        [
            _ra_entry(1, md5_loser, 5),
            _ra_entry(2, md5_winner, 50),
        ],
    )

    config = _FakeConfig(project_root=tmp_path)
    response = apply_ra_conflicts(repo, config)

    # loser must be in _descartados/
    assert (roms / "_descartados" / "tetris_old.gb").exists(), "loser not in _descartados"
    assert not loser_file.exists(), "loser still at original path"

    # winner untouched
    assert winner_file.exists(), "winner was incorrectly moved"

    # DB: loser row removed
    with repo.connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM games WHERE source_path = ?", (str(loser_file),)
        ).fetchone()
    assert row is None, "loser still in DB"

    assert response["resolved"] == 1
    assert response["errors"] == []


# ---------------------------------------------------------------------------
# Scenario 2 — Disk conflict: source wins (higher RA)
# ---------------------------------------------------------------------------


def test_disk_conflict_source_wins(tmp_path: Path) -> None:
    """
    Setup
    -----
    tetris_new.gb  (md5=ccc, 50 RA)  → wants to rename to Tetris (World).gb
    Tetris (World).gb  (md5=ddd, 5 RA)  already at canonical path

    Expected
    --------
    Tetris (World).gb  → _descartados/Tetris (World).gb  (loser)
    tetris_new.gb      → renamed to Tetris (World).gb    (winner)
    DB: winner updated to new path; loser removed
    """
    roms = tmp_path / "roms"
    roms.mkdir()

    winner_src = roms / "tetris_new.gb"
    blocker_file = roms / "Tetris (World).gb"
    winner_src.write_bytes(b"WINNER_ROM")
    blocker_file.write_bytes(b"BLOCKER_ROM")

    md5_winner = "c" * 32
    md5_blocker = "d" * 32

    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=winner_src, md5=md5_winner, canonical_title="Tetris (World)")
    _insert_game(repo, source_path=blocker_file, md5=md5_blocker, canonical_title="Tetris (World)")

    _write_ra_cache(
        tmp_path,
        [
            _ra_entry(3, md5_winner, 50),
            _ra_entry(4, md5_blocker, 5),
        ],
    )

    config = _FakeConfig(project_root=tmp_path)
    response = apply_ra_conflicts(repo, config)

    canonical = roms / "Tetris (World).gb"

    # blocker in _descartados/
    assert (roms / "_descartados" / "Tetris (World).gb").exists(), "blocker not in _descartados"

    # winner renamed to canonical path
    assert canonical.exists(), "winner not renamed to canonical path"
    assert not winner_src.exists(), "winner still at old source path"
    assert canonical.read_bytes() == b"WINNER_ROM", "wrong file at canonical path"

    # DB: winner's source_path updated
    with repo.connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM games WHERE source_path = ?", (str(canonical),)
        ).fetchone()
    assert row is not None, "winner path not updated in DB"

    assert response["resolved"] == 1
    assert response["errors"] == []


# ---------------------------------------------------------------------------
# Scenario 3 — Collision: two sources → same canonical name
# ---------------------------------------------------------------------------


def test_collision_conflict(tmp_path: Path) -> None:
    """
    Setup
    -----
    mario_v1.gb  (md5=eee, 30 RA)  → wants Super Mario Land (World).gb
    mario_v2.gb  (md5=fff, 5 RA)   → wants Super Mario Land (World).gb
    Neither file exists at the canonical path.

    Expected
    --------
    mario_v1.gb  → renamed to Super Mario Land (World).gb   (winner)
    mario_v2.gb  → _descartados/mario_v2.gb                 (loser)
    """
    roms = tmp_path / "roms"
    roms.mkdir()

    winner_src = roms / "mario_v1.gb"
    loser_src = roms / "mario_v2.gb"
    winner_src.write_bytes(b"WINNER_MARIO")
    loser_src.write_bytes(b"LOSER_MARIO")

    md5_winner = "e" * 32
    md5_loser = "f" * 32

    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(
        repo, source_path=winner_src, md5=md5_winner, canonical_title="Super Mario Land (World)"
    )
    _insert_game(
        repo, source_path=loser_src, md5=md5_loser, canonical_title="Super Mario Land (World)"
    )

    _write_ra_cache(
        tmp_path,
        [
            _ra_entry(5, md5_winner, 30),
            _ra_entry(6, md5_loser, 5),
        ],
    )

    config = _FakeConfig(project_root=tmp_path)
    response = apply_ra_conflicts(repo, config)

    canonical = roms / "Super Mario Land (World).gb"

    assert canonical.exists(), "winner not renamed to canonical path"
    assert canonical.read_bytes() == b"WINNER_MARIO", "wrong file at canonical path"
    assert not winner_src.exists(), "winner still at old path"

    assert (roms / "_descartados" / "mario_v2.gb").exists(), "loser not in _descartados"
    assert not loser_src.exists(), "loser still at original path"

    assert response["errors"] == []


# ---------------------------------------------------------------------------
# Scenario 4 — No RA data: both files skipped
# ---------------------------------------------------------------------------


def test_no_ra_data_skips_conflict(tmp_path: Path) -> None:
    """When neither conflicting file has RA data, both files are left untouched."""
    roms = tmp_path / "roms"
    roms.mkdir()

    file_a = roms / "game_a.gb"
    file_b = roms / "Game Title (World).gb"
    file_a.write_bytes(b"GAME_A")
    file_b.write_bytes(b"GAME_B")

    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path=file_a, md5="1" * 32, canonical_title="Game Title (World)")
    _insert_game(repo, source_path=file_b, md5="2" * 32, canonical_title="Game Title (World)")

    # Empty RA cache (no achievements for any hash)
    _write_ra_cache(tmp_path, [])

    config = _FakeConfig(project_root=tmp_path)
    response = apply_ra_conflicts(repo, config)

    # Nothing moved
    assert file_a.exists(), "file_a was incorrectly moved despite no RA data"
    assert file_b.exists(), "file_b was incorrectly moved despite no RA data"
    assert not (roms / "_descartados").exists(), "_descartados created unexpectedly"

    assert response["resolved"] == 0
    assert response["skipped_no_ra"] == 1
