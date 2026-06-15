from __future__ import annotations

import time


def _wait_job(client, key, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = client.get_json("/api/job-status")
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
