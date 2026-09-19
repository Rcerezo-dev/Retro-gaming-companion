"""ANDROID-DUP-2: _do_adb_scan used to hard-code sha1="" md5="" for every
row -- the Android repo's SHA1-based duplicate union and RA-support lookup
never had anything to work with. Now it calls AdbTransport.sha1_recursive/
md5_recursive (computed on the device, see their docstrings) and stores the
real hashes, with an opt-out for a caller that only wants a fast
file-listing refresh.
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
    """Stands in for AdbTransport: canned listing + hash maps, no real ADB."""

    files: list[AdbFileInfo] = []
    sha1_map: dict[str, str] = {}
    md5_map: dict[str, str] = {}
    sha1_calls: int = 0
    md5_calls: int = 0

    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def ls_recursive(self, _android_path: str, **_kwargs) -> list[AdbFileInfo]:
        return self.files

    def sha1_recursive(self, _android_path: str, **_kwargs) -> dict[str, str]:
        type(self).sha1_calls += 1
        return self.sha1_map

    def md5_recursive(self, _android_path: str, **_kwargs) -> dict[str, str]:
        type(self).md5_calls += 1
        return self.md5_map


@pytest.fixture(autouse=True)
def _reset_fake_transport():
    _FakeAdbTransport.sha1_calls = 0
    _FakeAdbTransport.md5_calls = 0
    yield


@pytest.fixture
def repo_android(tmp_path: Path) -> LibraryRepository:
    return LibraryRepository(tmp_path / "android.sqlite")


@pytest.fixture
def config(tmp_path: Path):
    return load_config(tmp_path)


def _run_scan(monkeypatch, repo_android, config, data: dict) -> dict:
    job_manager = JobManager()
    monkeypatch.setattr("rom_manager.sync.adb_transport.AdbTransport", _FakeAdbTransport)
    ctx = _FakeCtx()
    _do_adb_scan(ctx, data, config, repo_android, job_manager)
    assert ctx.sent == {"status": "started"}
    for _ in range(50):
        if not job_manager.get_status()["scan_running"]:
            break
        time.sleep(0.1)
    else:
        pytest.fail("adb scan job never finished")
    return job_manager.get_status()["scan_result"]


def _hashes_by_path(repo_android: LibraryRepository) -> dict[str, tuple[str, str]]:
    with repo_android.connect() as conn:
        rows = conn.execute("SELECT source_path, sha1, md5 FROM games").fetchall()
    return {r["source_path"]: (r["sha1"], r["md5"]) for r in rows}


def test_adb_scan_stores_real_hashes_by_default(monkeypatch, repo_android, config) -> None:
    path = "/storage/521D-04EA/ROMs/gba/Final Fantasy Tactics [E].gba"
    _FakeAdbTransport.files = [AdbFileInfo(android_path=path, size=16777216, mtime=0.0)]
    # Real AdbTransport.sha1_recursive/md5_recursive always lowercase (see
    # _hash_recursive) -- the fake mirrors that contract.
    _FakeAdbTransport.sha1_map = {path: "a" * 40}
    _FakeAdbTransport.md5_map = {path: "b" * 32}

    result = _run_scan(
        monkeypatch,
        repo_android,
        config,
        {"adb_serial": "SERIAL", "android_path": "/storage/521D-04EA/ROMs"},
    )

    assert result["hashes_computed"] is True
    assert result["sha1_hashed"] == 1
    assert result["md5_hashed"] == 1
    assert _FakeAdbTransport.sha1_calls == 1
    assert _FakeAdbTransport.md5_calls == 1
    hashes = _hashes_by_path(repo_android)
    assert hashes[path] == ("a" * 40, "b" * 32)


def test_adb_scan_compute_hashes_false_skips_hashing(monkeypatch, repo_android, config) -> None:
    path = "/storage/521D-04EA/ROMs/gba/Final Fantasy Tactics [E].gba"
    _FakeAdbTransport.files = [AdbFileInfo(android_path=path, size=16777216, mtime=0.0)]
    # Present but must never be consulted when compute_hashes is False.
    _FakeAdbTransport.sha1_map = {path: "a" * 40}
    _FakeAdbTransport.md5_map = {path: "b" * 32}

    result = _run_scan(
        monkeypatch,
        repo_android,
        config,
        {
            "adb_serial": "SERIAL",
            "android_path": "/storage/521D-04EA/ROMs",
            "compute_hashes": False,
        },
    )

    assert result["hashes_computed"] is False
    assert result["sha1_hashed"] == 0
    assert result["md5_hashed"] == 0
    assert _FakeAdbTransport.sha1_calls == 0
    assert _FakeAdbTransport.md5_calls == 0
    hashes = _hashes_by_path(repo_android)
    assert hashes[path] == ("", "")


def test_adb_scan_missing_hash_falls_back_to_empty_string(
    monkeypatch, repo_android, config
) -> None:
    """A file the hash pass couldn't reach (unreadable, gone mid-scan) must
    still get scanned -- just without a hash, same as before this existed."""
    path = "/storage/521D-04EA/ROMs/gba/game.gba"
    _FakeAdbTransport.files = [AdbFileInfo(android_path=path, size=1024, mtime=0.0)]
    _FakeAdbTransport.sha1_map = {}
    _FakeAdbTransport.md5_map = {}

    _run_scan(
        monkeypatch,
        repo_android,
        config,
        {"adb_serial": "SERIAL", "android_path": "/storage/521D-04EA/ROMs"},
    )

    hashes = _hashes_by_path(repo_android)
    assert hashes[path] == ("", "")
