from __future__ import annotations

import time


def _wait_job(client, key, timeout=5.0, on_tick=None):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = client.get_json("/api/job-status")
        if on_tick is not None:
            on_tick(status)
        if not status[f"{key}_running"]:
            return status
        time.sleep(0.02)
    raise TimeoutError(f"{key} job did not finish in {timeout}s")


def test_job_status_empty(client):
    status = client.get_json("/api/job-status")
    assert status["scan_running"] is False
    assert status["scan_result"] is None


def test_post_scan_empty_library(client, tmp_path):
    (tmp_path / "library").mkdir()
    resp = client.post_json("/api/scan", {})
    assert resp["status"] == "started"
    status = _wait_job(client, "scan")
    assert status["scan_result"] is not None


def test_post_match_empty_library(client):
    resp = client.post_json("/api/match", {})
    assert resp["status"] == "started"
    status = _wait_job(client, "match")
    assert status["match_result"] is not None


def test_match_progress_advances_row_by_row(client, repo, monkeypatch):
    """MATCH-HANG-CHDMAN-1: /api/job-status must expose match_progress
    (current/total/current_file) while the job is running, the same pattern
    already used by scan/convert_chd -- without it a real hang is only
    diagnosable by killing the server process."""
    from rom_manager.catalog.matcher import CatalogMatcher

    for i in range(4):
        repo.upsert_game(
            original_filename=f"game{i}.bin",
            source_path=f"/lib/game{i}.bin",
            platform="PlayStation",
            file_type="rom",
            relative_parent="",
            region="",
            extension=".bin",
            size_bytes=10,
            mtime=0,
            sha1=f"{i}" * 40,
            md5=f"{i}" * 32,
            crc32=f"{i}" * 8,
            set_type="single",
            timestamp="2026-09-15T00:00:00",
        )

    def _slow_match(self, sha1, filename, source_path):
        time.sleep(0.05)
        return None

    monkeypatch.setattr(CatalogMatcher, "match", _slow_match)

    resp = client.post_json("/api/match", {})
    assert resp["status"] == "started"

    seen: list[dict] = []
    status = _wait_job(client, "match", timeout=10.0, on_tick=lambda s: seen.append(s))

    assert status["match_result"]["total"] == 4
    progresses = [s["match_progress"] for s in seen if s.get("match_progress")]
    assert progresses, "no se observó match_progress mientras el job corría"
    assert all(p["total"] == 4 for p in progresses)
    assert max(p["current"] for p in progresses) >= 1
    assert all(p["current"] <= p["total"] for p in progresses)
