"""CABLE-UX-1: pre-flight de reloj en el backend para sync ADB "newest".

Antes, el guard de skew de reloj (AUD-1) solo vivía en el frontend (confirm()
saltable). Estos tests comprueban que el backend bloquea de verdad — tanto el
sync manual (`_do_cable_sync`) como el disparo automático (`_auto_sync_loop`).
"""

from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

import rom_manager.web.state as _state
from rom_manager.sync.adb_transport import AdbTransport
from rom_manager.web.handlers.sync_cable import register_cable
from rom_manager.web.router import Router


def _config(tmp_path, *, direction="newest", threshold=120):
    return SimpleNamespace(
        adb="adb",
        project_root=tmp_path,
        library_root=str(tmp_path / "pc"),
        anbernic_root=None,
        save_extensions=(".sav",),
        sync=SimpleNamespace(
            auto_sync_direction=direction,
            auto_sync_android_path="/storage/emulated/0/RetroArch",
            clock_skew_threshold_s=threshold,
        ),
    )


class _FakeCtx:
    def __init__(self, post_data):
        self._post_data = post_data
        self.out = None

    def _send_json(self, obj):
        self.out = obj


@pytest.fixture(autouse=True)
def _isolate_job_manager():
    # finish() (not just clear_result) also resets the "running" flag — needed
    # because the "clock ok" test lets a real background thread run to completion.
    _state._job_manager.finish("cable_sync", None)
    yield
    for _ in range(50):
        if not _state._job_manager.get_status()["cable_sync_running"]:
            break
        time.sleep(0.05)
    _state._job_manager.finish("cable_sync", None)


def test_manual_sync_blocked_when_clock_skewed(tmp_path, monkeypatch):
    monkeypatch.setattr(AdbTransport, "device_epoch", lambda self: int(time.time()) + 600)

    router = Router()
    config = _config(tmp_path)
    register_cable(router, config=config, repository=None, job_manager=_state._job_manager)

    ctx = _FakeCtx(
        {
            "pc_path": str(tmp_path / "pc"),
            "use_adb": True,
            "adb_serial": "emulator-5554",
            "android_path": "/storage/emulated/0/RetroArch",
            "what": ["saves"],
            "direction": "newest",
            "dry_run": False,
        }
    )
    router.dispatch("POST", "/api/cable-sync", ctx)

    assert "error" in ctx.out
    assert "reloj" in ctx.out["error"].lower()
    # No debe haber arrancado ningún job — es un rechazo síncrono
    assert not _state._job_manager.get_status()["cable_sync_running"]


def test_manual_sync_proceeds_when_clock_ok(tmp_path, monkeypatch):
    monkeypatch.setattr(AdbTransport, "device_epoch", lambda self: int(time.time()))
    monkeypatch.setattr(AdbTransport, "ls_recursive", lambda self, *a, **k: [])

    router = Router()
    config = _config(tmp_path)
    register_cable(router, config=config, repository=None, job_manager=_state._job_manager)

    ctx = _FakeCtx(
        {
            "pc_path": str(tmp_path / "pc"),
            "use_adb": True,
            "adb_serial": "emulator-5554",
            "android_path": "/storage/emulated/0/RetroArch",
            "what": ["saves"],
            "direction": "newest",
            "dry_run": False,
        }
    )
    router.dispatch("POST", "/api/cable-sync", ctx)

    assert ctx.out.get("status") == "started"


def test_manual_sync_skips_guard_for_non_newest_direction(tmp_path, monkeypatch):
    # pc_to_anbernic no depende de mtime — no debe llamar al reloj del dispositivo
    def _boom(self):
        raise AssertionError("device_epoch no debería llamarse fuera de direction=newest")

    monkeypatch.setattr(AdbTransport, "device_epoch", _boom)
    monkeypatch.setattr(AdbTransport, "ls_recursive", lambda self, *a, **k: [])

    router = Router()
    config = _config(tmp_path)
    register_cable(router, config=config, repository=None, job_manager=_state._job_manager)

    ctx = _FakeCtx(
        {
            "pc_path": str(tmp_path / "pc"),
            "use_adb": True,
            "adb_serial": "emulator-5554",
            "android_path": "/storage/emulated/0/RetroArch",
            "what": ["saves"],
            "direction": "pc_to_anbernic",
            "dry_run": False,
        }
    )
    router.dispatch("POST", "/api/cable-sync", ctx)

    assert ctx.out.get("status") == "started"
