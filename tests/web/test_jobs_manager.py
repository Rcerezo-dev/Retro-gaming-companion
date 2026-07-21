from __future__ import annotations

import threading

from rom_manager.web.jobs.manager import JobManager


def test_start_returns_started():
    jm = JobManager()
    result = jm.start("scan", lambda: None)
    assert result == {"status": "started"}


def test_start_while_running_returns_already_running():
    jm = JobManager()
    gate = threading.Event()
    jm.start("scan", gate.wait)  # bloquea hasta que se libere
    assert jm.start("scan", lambda: None) == {"status": "already_running"}
    gate.set()


def test_update_progress_and_finish():
    jm = JobManager()
    jm.update_progress("scan", {"files_seen": 10})
    status = jm.get_status()
    assert status["scan_progress"] == {"files_seen": 10}
    jm.finish("scan", {"ok": True})
    status = jm.get_status()
    assert status["scan_progress"] is None
    assert status["scan_result"] == {"ok": True}


def test_cancel_event():
    jm = JobManager()
    assert jm.is_cancel_requested("scan") is False
    jm.cancel("scan")
    assert jm.is_cancel_requested("scan") is True


def test_get_status_shape_has_all_job_names():
    jm = JobManager()
    status = jm.get_status()
    for name in ("scan", "match", "sync", "cable_sync", "apply", "inbox"):
        assert f"{name}_running" in status


def test_get_job_default_shape():
    jm = JobManager()
    job = jm.get_job("download_dats")
    assert job == {"running": False, "progress": None, "result": None}


def test_get_job_reflects_lifecycle():
    jm = JobManager()
    jm.start("download_dats", lambda: None)
    assert jm.get_job("download_dats")["running"] is True
    jm.update_progress("download_dats", {"done": 1, "total": 3})
    assert jm.get_job("download_dats")["progress"] == {"done": 1, "total": 3}
    jm.finish("download_dats", {"downloaded": ["x"]})
    job = jm.get_job("download_dats")
    assert job["running"] is False
    assert job["progress"] is None
    assert job["result"] == {"downloaded": ["x"]}
