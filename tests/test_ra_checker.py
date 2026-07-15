"""Tests for ra_checker.py — RetroAchievements hash cross-referencing."""

from __future__ import annotations

from pathlib import Path

import pytest

from rom_manager.database.repository import LibraryRepository
from rom_manager.retroachievements import ra_checker

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
