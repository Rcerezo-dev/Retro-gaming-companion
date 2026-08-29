"""Regression test for HERR-FIX-1: /api/ra-check/discard-no-support used to
discard games with NO RA alternative at all -- exactly the ones that must
never be touched, since discarding them loses the only copy of that game.
Only "no_support_alternative" (a better copy already exists) is safe.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.retroachievements.ra_checker import RACheckSummary, RAGameResult
from rom_manager.retroachievements import ra_client
from rom_manager.web.handlers.sync import _do_ra_check
from rom_manager.web.jobs.manager import JobManager


@pytest.fixture
def repo(tmp_path: Path) -> LibraryRepository:
    return LibraryRepository(tmp_path / "library.db")


def test_no_support_entries_excludes_games_without_alternative(tmp_path, repo, monkeypatch):
    config = load_config(project_root=tmp_path)
    job_manager = JobManager()

    fake_alternative = ra_client.RAGame(
        id=1, title="Alt Title", achievements=12, leaderboards=0, points=100
    )
    summary = RACheckSummary(
        supported=0,
        no_support_alternative=1,
        no_support=1,
        no_md5=0,
        platform_unknown=0,
        check_failed=0,
        total=2,
        results=[
            RAGameResult(
                source_path="/lib/only-copy.nes",
                original_filename="only-copy.nes",
                platform="NES",
                our_md5="aaa",
                status="no_support",
            ),
            RAGameResult(
                source_path="/lib/has-better-copy.nes",
                original_filename="has-better-copy.nes",
                platform="NES",
                our_md5="bbb",
                status="no_support_alternative",
                alternative=fake_alternative,
            ),
        ],
    )

    monkeypatch.setattr(
        "rom_manager.retroachievements.ra_checker.check_library", lambda *a, **k: summary
    )

    _do_ra_check("fake-api-key", config, repo, job_manager)

    for _ in range(50):
        if not job_manager.get_status()["ra_check_running"]:
            break
        time.sleep(0.1)
    else:
        pytest.fail("ra_check job never finished")

    result = job_manager.get_status()["ra_check_result"]
    assert result is not None and "error" not in result
    entries = result["no_support_entries"]
    paths = {e["source_path"] for e in entries}
    assert paths == {"/lib/has-better-copy.nes"}, (
        "discard-no-support must only ever include games with a real "
        "alternative -- 'only-copy.nes' has none and would be lost forever"
    )
