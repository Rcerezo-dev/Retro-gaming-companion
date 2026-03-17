"""Tests for LibraryRepository (S20).

Uses a real SQLite database in a pytest tmp_path — no mocks, no :memory: tricks.
All state is isolated per test via the `repo` fixture.
"""
from __future__ import annotations

import pytest
from pathlib import Path

from rom_manager.database.repository import LibraryRepository, DuplicateGroup


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def repo(tmp_path: Path) -> LibraryRepository:
    """Fresh repository backed by a temp file. Schema initialised automatically."""
    return LibraryRepository(tmp_path / "library.db")


TS = "2026-01-01T00:00:00"  # stable timestamp for all tests


def _upsert(repo: LibraryRepository, **overrides) -> None:
    """Insert a game row with sensible defaults; caller can override any field."""
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
        sha1="aabbccdd" * 5,   # 40 hex chars
        md5="11223344" * 4,
        crc32="deadbeef",
        set_type="single",
        timestamp=TS,
    )
    defaults.update(overrides)
    repo.upsert_game(**defaults)


# ── Schema initialisation ─────────────────────────────────────────────────────

def test_fresh_repo_has_empty_summary(repo):
    s = repo.get_summary()
    assert s.total_games == 0
    assert s.total_saves == 0
    assert s.total_assets == 0


# ── upsert_game ───────────────────────────────────────────────────────────────

def test_upsert_game_inserts(repo):
    _upsert(repo)
    assert repo.get_summary().total_games == 1


def test_upsert_game_updates_on_conflict(repo):
    """Second upsert on same source_path must update, not insert a duplicate."""
    _upsert(repo, original_filename="Old.gba", size_bytes=512)
    _upsert(repo, original_filename="New.gba", size_bytes=1024)

    assert repo.get_summary().total_games == 1

    with repo.connect() as conn:
        row = conn.execute("SELECT original_filename, size_bytes FROM games").fetchone()
    assert row["original_filename"] == "New.gba"
    assert row["size_bytes"] == 1024


def test_upsert_game_via_batch(repo):
    """upsert_game accepts an existing connection (batch mode)."""
    with repo.batch() as conn:
        repo.upsert_game(
            original_filename="Batch.gba",
            source_path="/roms/Batch.gba",
            platform="Game Boy Advance",
            file_type="rom",
            relative_parent="gba",
            region=None,
            extension=".gba",
            size_bytes=256,
            mtime=1700000001,
            sha1="cc" * 20,
            md5="dd" * 16,
            crc32="cafebabe",
            set_type="single",
            timestamp=TS,
            connection=conn,
        )
    assert repo.get_summary().total_games == 1


# ── upsert_save / upsert_asset ────────────────────────────────────────────────

def test_upsert_save(repo):
    repo.upsert_save(
        original_path="/roms/gba/Game.sav",
        relative_parent="gba",
        extension=".sav",
        size_bytes=8192,
        timestamp=TS,
    )
    assert repo.get_summary().total_saves == 1


def test_upsert_asset(repo):
    repo.upsert_asset(
        source_path="/roms/gba/Game.png",
        relative_parent="gba",
        platform="Game Boy Advance",
        asset_type="image",
        timestamp=TS,
    )
    assert repo.get_summary().total_assets == 1


# ── get_unresolved_games / update_match / get_matched_games ───────────────────

def test_get_unresolved_returns_unmatched(repo):
    _upsert(repo, source_path="/roms/A.gba", sha1="aa" * 20)
    _upsert(repo, source_path="/roms/B.gba", sha1="bb" * 20)

    # Match one of them
    repo.update_match(
        "/roms/A.gba",
        canonical_title="Game A",
        match_confidence="high",
        catalog_source="nointro",
    )

    unresolved = repo.get_unresolved_games()
    assert len(unresolved) == 1
    assert unresolved[0].source_path == "/roms/B.gba"


def test_update_match_and_get_matched(repo):
    _upsert(repo, source_path="/roms/C.gba", sha1="cc" * 20)
    repo.update_match(
        "/roms/C.gba",
        canonical_title="My Game",
        match_confidence="high",
        catalog_source="nointro",
    )

    matched = repo.get_matched_games()
    assert len(matched) == 1
    assert matched[0].canonical_title == "My Game"
    assert matched[0].match_confidence == "high"


# ── get_duplicate_groups / exclude_duplicate_sha1 ────────────────────────────

def test_duplicate_groups_same_sha1(repo):
    sha = "deadbeef" * 5
    _upsert(repo, source_path="/roms/Copy1.gba", sha1=sha, size_bytes=1024)
    _upsert(repo, source_path="/roms/Copy2.gba", sha1=sha, size_bytes=1024)

    groups = repo.get_duplicate_groups()
    assert len(groups) == 1
    assert groups[0].sha1 == sha
    assert len(groups[0].entries) == 2
    assert groups[0].wasted_bytes == 1024   # one copy is "wasted"


def test_unique_sha1_not_a_duplicate(repo):
    _upsert(repo, source_path="/roms/Unique.gba", sha1="aa" * 20)
    assert repo.get_duplicate_groups() == []


def test_exclude_duplicate_sha1_hides_group(repo):
    sha = "cafebabe" * 5
    _upsert(repo, source_path="/roms/D1.gba", sha1=sha)
    _upsert(repo, source_path="/roms/D2.gba", sha1=sha)

    repo.exclude_duplicate_sha1(sha)
    assert repo.get_duplicate_groups() == []


# ── apply_rename ──────────────────────────────────────────────────────────────

def test_apply_rename_updates_path(repo):
    _upsert(repo, source_path="/roms/Old.gba", original_filename="Old.gba")

    with repo.connect() as conn:
        game_id = conn.execute("SELECT id FROM games").fetchone()["id"]

    repo.apply_rename(
        game_id=game_id,
        old_source_path="/roms/Old.gba",
        new_source_path="/roms/New (USA).gba",
        new_filename="New (USA).gba",
        timestamp=TS,
    )

    with repo.connect() as conn:
        row = conn.execute("SELECT source_path, original_filename FROM games").fetchone()
    assert row["source_path"] == "/roms/New (USA).gba"
    assert row["original_filename"] == "New (USA).gba"


def test_apply_rename_logs_file_operation(repo):
    _upsert(repo, source_path="/roms/Orig.gba")
    with repo.connect() as conn:
        game_id = conn.execute("SELECT id FROM games").fetchone()["id"]

    repo.apply_rename(
        game_id=game_id,
        old_source_path="/roms/Orig.gba",
        new_source_path="/roms/Renamed.gba",
        new_filename="Renamed.gba",
        timestamp=TS,
    )

    with repo.connect() as conn:
        ops = conn.execute("SELECT * FROM file_operations").fetchall()
    assert len(ops) == 1
    assert ops[0]["operation_type"] == "rename"


# ── prune_stale_entries ───────────────────────────────────────────────────────

def test_prune_stale_removes_missing(repo, tmp_path):
    root = str(tmp_path / "roms")
    keep = str(tmp_path / "roms" / "keep.gba")
    gone = str(tmp_path / "roms" / "gone.gba")

    _upsert(repo, source_path=keep)
    _upsert(repo, source_path=gone, sha1="ff" * 20)

    deleted = repo.prune_stale_entries(root, seen_paths={keep})

    assert deleted == 1
    assert repo.get_summary().total_games == 1
    with repo.connect() as conn:
        paths = [r[0] for r in conn.execute("SELECT source_path FROM games").fetchall()]
    assert keep in paths
    assert gone not in paths


def test_prune_stale_ignores_other_roots(repo, tmp_path):
    root_a = str(tmp_path / "a")
    root_b = str(tmp_path / "b")
    path_a = str(tmp_path / "a" / "game.gba")
    path_b = str(tmp_path / "b" / "game.gba")

    _upsert(repo, source_path=path_a)
    _upsert(repo, source_path=path_b, sha1="ee" * 20)

    # Prune root_a with no seen paths — only path_a should be removed
    deleted = repo.prune_stale_entries(root_a, seen_paths=set())

    assert deleted == 1
    assert repo.get_summary().total_games == 1


# ── scan run lifecycle ────────────────────────────────────────────────────────

def test_scan_run_lifecycle(repo):
    root = "/roms/gba"
    run_id = repo.create_scan_run(root, started_at=TS)
    assert isinstance(run_id, int) and run_id > 0

    repo.complete_scan_run(
        run_id,
        finished_at="2026-01-01T00:01:00",
        files_seen=10,
        roms_detected=8,
        saves_detected=2,
        assets_detected=0,
        system_files_detected=0,
        unknown_files_detected=0,
        errors=0,
    )

    last = repo.get_last_scan_by_root()
    assert root in last
    assert last[root] == "2026-01-01T00:01:00"


# ── batch rollback on error ───────────────────────────────────────────────────

def test_batch_rollback_on_error(repo):
    """If an exception is raised inside batch(), the transaction is rolled back."""
    try:
        with repo.batch() as conn:
            conn.execute(
                "INSERT INTO games (source_path, original_filename, file_type, extension, "
                "size_bytes, mtime, sha1, md5, crc32, set_type, created_at, updated_at) "
                "VALUES (?, ?, 'rom', '.gba', 0, 0, ?, ?, 'x', 'single', ?, ?)",
                ("/roms/rollback.gba", "rollback.gba", "aa" * 20, "bb" * 16, TS, TS),
            )
            raise RuntimeError("simulated failure")
    except RuntimeError:
        pass

    assert repo.get_summary().total_games == 0


# ── get_known_roms ────────────────────────────────────────────────────────────

def test_get_known_roms_returns_mtime_and_size(repo):
    _upsert(repo, source_path="/roms/Known.gba", mtime=999, size_bytes=2048)
    known = repo.get_known_roms()
    assert "/roms/Known.gba" in known
    assert known["/roms/Known.gba"] == (999, 2048)


# ── delete_game ───────────────────────────────────────────────────────────────

def test_delete_game_removes_row(repo):
    _upsert(repo)
    with repo.connect() as conn:
        game_id = conn.execute("SELECT id FROM games").fetchone()["id"]

    repo.delete_game(game_id)
    assert repo.get_summary().total_games == 0


# ── sha1_exists ───────────────────────────────────────────────────────────────

def test_sha1_exists(repo):
    sha = "12345678" * 5
    assert not repo.sha1_exists(sha)
    _upsert(repo, sha1=sha)
    assert repo.sha1_exists(sha)
