"""Regression test for REV43-17: /api/stop-job (job=scan) canceled a regular
scan (_do_scan passes stop_event through) but had no effect on an ADB scan in
progress -- _do_adb_scan never checked the cancel flag in its per-file loop.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.sync.adb_transport import AdbFileInfo
from rom_manager.web.handlers.scan import _do_adb_scan
from rom_manager.web.jobs.manager import JobManager


class _FakeCtx:
    def __init__(self) -> None:
        self.sent: dict | None = None

    def _send_json(self, data: dict) -> None:
        self.sent = data

    def _send_error(self, code: int, message: str) -> None:
        self.sent = {"error": message}


class _FakeAdbTransport:
    """Stands in for AdbTransport: returns a canned file listing, no real ADB."""

    files: list[AdbFileInfo] = []

    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def ls_recursive(self, _android_path: str, **_kwargs) -> list[AdbFileInfo]:
        return self.files

    def iter_hashes(self, _files, **_kwargs):
        yield {}, {}


@pytest.fixture
def repo_android(tmp_path: Path) -> LibraryRepository:
    return LibraryRepository(tmp_path / "android.sqlite")


@pytest.fixture
def config(tmp_path: Path):
    return load_config(tmp_path)


def test_stop_job_cancels_adb_scan_in_progress(monkeypatch, repo_android, config):
    total_files = 10
    _FakeAdbTransport.files = [
        AdbFileInfo(android_path=f"/storage/emulated/0/roms/game{i}.gba", size=100, mtime=0.0)
        for i in range(total_files)
    ]
    monkeypatch.setattr("rom_manager.sync.adb_transport.AdbTransport", _FakeAdbTransport)

    job_manager = JobManager()
    call_count = {"n": 0}
    real_detect_platform = __import__(
        "rom_manager.detection.platform_detector", fromlist=["detect_platform"]
    ).detect_platform

    def _detect_platform_and_cancel_partway(fake_path):
        call_count["n"] += 1
        if call_count["n"] == 3:
            # Simulate /api/stop-job arriving mid-scan, after 3 of 10 files.
            job_manager.cancel("scan")
        return real_detect_platform(fake_path)

    monkeypatch.setattr(
        "rom_manager.detection.platform_detector.detect_platform",
        _detect_platform_and_cancel_partway,
    )

    ctx = _FakeCtx()
    _do_adb_scan(
        ctx,
        {"adb_serial": "emulator-5554", "android_path": "/storage/emulated/0"},
        config,
        repo_android,
        job_manager,
    )
    assert ctx.sent == {"status": "started"}

    for _ in range(50):
        if not job_manager.get_status()["scan_running"]:
            break
        time.sleep(0.1)
    else:
        pytest.fail("adb scan job never finished")

    result = job_manager.get_status()["scan_result"]
    assert result is not None
    assert result["cancelled"] is True
    assert result["roms_detected"] < total_files

    _, total = repo_android.get_games_paginated(file_type=None)
    assert total < total_files


def test_cancelled_adb_scan_does_not_prune(monkeypatch, repo_android, config):
    """ANDROID-SCAN-FIX-1a: a partial seen_paths must not delete the folder's rows."""
    stale = "/storage/emulated/0/roms/old.gba"
    repo_android.upsert_game(
        original_filename="old.gba",
        source_path=stale,
        platform="gba",
        file_type="rom",
        relative_parent="roms",
        region="",
        extension=".gba",
        size_bytes=1,
        mtime=0,
        sha1="",
        md5="",
        crc32="",
        set_type="single",
        timestamp="2026-01-01T00:00:00Z",
    )
    _FakeAdbTransport.files = [
        AdbFileInfo(android_path=f"/storage/emulated/0/roms/g{i}.gba", size=1, mtime=0.0)
        for i in range(3)
    ]
    monkeypatch.setattr("rom_manager.sync.adb_transport.AdbTransport", _FakeAdbTransport)
    job_manager = JobManager()
    monkeypatch.setattr(
        "rom_manager.detection.platform_detector.detect_platform",
        lambda _p: job_manager.cancel("scan") or "gba",
    )
    _do_adb_scan(
        _FakeCtx(),
        {"adb_serial": "emulator-5554", "android_path": "/storage/emulated/0"},
        config,
        repo_android,
        job_manager,
    )
    for _ in range(50):
        if not job_manager.get_status()["scan_running"]:
            break
        time.sleep(0.1)
    result = job_manager.get_status()["scan_result"]
    assert result["cancelled"] is True and result["pruned"] == 0
    _, total = repo_android.get_games_paginated(file_type=None)
    assert total >= 1
