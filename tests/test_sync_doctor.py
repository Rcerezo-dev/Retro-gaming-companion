"""AUD-1 — Sync Doctor: clock skew + anomalous-save diagnostics.

Drives ``_build_sync_doctor`` with a fake ADB transport and a synthetic saves
tree, asserting the skew threshold, the future-mtime detection and the
local/remote join — the three signals that guard against mtime-based data loss.
"""

from __future__ import annotations

import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

import pytest

from rom_manager.config import load_config
from rom_manager.sync.adb_transport import AdbFileInfo
from rom_manager.web.handlers.sync_cable import _build_sync_doctor

_ANDROID_ROOT = "/storage/emulated/0/RetroArch"


class _FakeTransport:
    def __init__(self, adb_path, serial, **kwargs):
        pass

    def device_epoch(self) -> int:
        return int(time.time()) + _FakeTransport.skew

    def ls_recursive(self, android_path, *, wanted_extensions=None, **kwargs):
        return _FakeTransport.remote_files


class _FakeRepo:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()


@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.setattr("rom_manager.sync.adb_transport.AdbTransport", _FakeTransport)
    _FakeTransport.skew = 0
    _FakeTransport.remote_files = []

    cfg = load_config()
    cfg.save_extensions = (".sav",)
    cfg.sync.clock_skew_threshold_s = 120

    db = tmp_path / "test.db"
    with sqlite3.connect(db) as conn:
        conn.execute(
            "CREATE TABLE save_sync_log (id INTEGER PRIMARY KEY, local_path TEXT, "
            "remote_path TEXT, direction TEXT, result TEXT, message TEXT, created_at TEXT)"
        )
        conn.execute(
            "INSERT INTO save_sync_log (local_path, remote_path, direction, result, created_at) "
            "VALUES ('C:/pc/gba/both.sav', 'r/both.sav', 'upload', 'ok', '2026-07-01T10:00:00')"
        )

    pc_root = tmp_path / "pc"
    return cfg, _FakeRepo(db), pc_root


def _remote(rel: str, mtime: float) -> AdbFileInfo:
    return AdbFileInfo(android_path=f"{_ANDROID_ROOT}/{rel}", size=10, mtime=mtime)


def _write(root: Path, rel: str, mtime_offset: float = -3600) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"DATA")
    ts = time.time() + mtime_offset
    os.utime(p, (ts, ts))
    return p


def test_quick_skew_exceeded(env) -> None:
    cfg, repo, pc_root = env
    _FakeTransport.skew = 300
    r = _build_sync_doctor(cfg, repo, "SERIAL", _ANDROID_ROOT, str(pc_root), quick=True)
    assert r["skew_exceeded"] is True
    assert 295 <= r["skew_seconds"] <= 305
    assert "only_local" not in r  # quick mode skips the file join


def test_quick_skew_within_threshold(env) -> None:
    cfg, repo, pc_root = env
    _FakeTransport.skew = 30
    r = _build_sync_doctor(cfg, repo, "SERIAL", _ANDROID_ROOT, str(pc_root), quick=True)
    assert r["skew_exceeded"] is False


def test_full_report_join_and_anomalies(env) -> None:
    cfg, repo, pc_root = env
    now = time.time()
    _write(pc_root, "gba/both.sav")
    _write(pc_root, "gba/solo-pc.sav")
    _write(pc_root, "gba/futuro.sav", mtime_offset=99999)  # reloj mal puesto
    _FakeTransport.remote_files = [
        _remote("gba/both.sav", now - 3600),
        _remote("snes/solo-consola.sav", now - 3600),
        _remote("snes/futuro-remoto.sav", now + 99999),
    ]

    r = _build_sync_doctor(cfg, repo, "SERIAL", _ANDROID_ROOT, str(pc_root))

    assert r["local_total"] == 3 and r["remote_total"] == 3 and r["in_both"] == 1
    assert r["only_local"] == ["gba/futuro.sav", "gba/solo-pc.sav"]
    assert r["only_remote"] == ["snes/futuro-remoto.sav", "snes/solo-consola.sav"]
    assert r["future_local"] == ["gba/futuro.sav"]
    assert r["future_remote"] == ["snes/futuro-remoto.sav"]
    assert r["last_syncs"] == [
        {
            "file": "both.sav",
            "direction": "upload",
            "result": "ok",
            "created_at": "2026-07-01T10:00:00",
        }
    ]
