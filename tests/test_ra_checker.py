"""Tests for ra_checker.py — RetroAchievements hash cross-referencing."""

from __future__ import annotations

from pathlib import Path

import pytest

from rom_manager.database.repository import LibraryRepository
from rom_manager.retroachievements import ra_checker
from tests.test_ra_hash_psx import _build_psx_image

TS = "2026-01-01T00:00:00"


@pytest.fixture
def repo(tmp_path: Path) -> LibraryRepository:
    return LibraryRepository(tmp_path / "library.db")


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


def test_network_failure_marks_check_failed_not_no_support(repo, monkeypatch) -> None:
    """REV43-27: a transient fetch_hash_library failure must not make every
    game on that platform look "no_support" — that status feeds
    discard_no_support's bulk-discard, so a network blip must never be
    indistinguishable from "confirmed, no RA support"."""
    _upsert(repo, source_path="/roms/gba/GameA.gba", original_filename="GameA.gba")
    _upsert(
        repo,
        source_path="/roms/gba/GameB.gba",
        original_filename="GameB.gba",
        md5="99887766" * 4,
    )

    def _boom(*_a, **_k):
        raise TimeoutError("simulated network failure")

    monkeypatch.setattr(ra_checker, "fetch_hash_library", _boom)

    summary = ra_checker.check_library(repo, api_key="fake-key")

    assert summary.no_support == 0
    assert summary.check_failed == 2
    assert all(r.status == "check_failed" for r in summary.results)


def test_genuinely_empty_hash_library_still_marks_no_support(repo, monkeypatch) -> None:
    """Control: a *successful* fetch that legitimately returns 0 games is not
    the bug in question — this must still fall through to no_support."""
    _upsert(repo)

    monkeypatch.setattr(ra_checker, "fetch_hash_library", lambda *_a, **_k: {})

    summary = ra_checker.check_library(repo, api_key="fake-key")

    assert summary.check_failed == 0
    assert summary.no_support == 1


def test_playstation_uses_disc_hash_not_stored_md5(repo, monkeypatch, tmp_path) -> None:
    """DUP-DISC-RA-1b: for PSX, the stored (whole-file) md5 never matches RA
    — check_library must compute/cache the disc-specific hash instead and
    use *that* to look up support, ignoring the games.md5 column entirely."""
    from rom_manager.retroachievements.ra_client import RAGame

    bin_path = _build_psx_image(tmp_path)
    from rom_manager.retroachievements.ra_hash_psx import compute_psx_ra_hash

    disc_hash = compute_psx_ra_hash(bin_path)
    assert disc_hash is not None

    _upsert(
        repo,
        source_path=str(bin_path),
        original_filename=bin_path.name,
        platform="PlayStation",
        md5="thiswillnevermatchanything0000",  # deliberately wrong/irrelevant
    )

    monkeypatch.setattr(
        ra_checker,
        "fetch_hash_library",
        lambda *_a, **_k: {
            disc_hash: RAGame(id=1, title="Test Game", achievements=10, leaderboards=0, points=100)
        },
    )

    summary = ra_checker.check_library(repo, api_key="fake-key", cache_dir=tmp_path / "ra_cache")

    assert summary.supported == 1
    assert summary.results[0].our_md5 == disc_hash
