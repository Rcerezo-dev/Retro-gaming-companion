"""REV43-6: en modo ADB con skip_sha1_dups, un dry_run no debe disparar
transferencias ADB reales (antes: transport.pull(..., dry_run=False) estaba
hardcodeado para poder hashear el archivo, ignorando el dry_run pedido)."""

from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

import rom_manager.web.state as _state
from rom_manager.sync.adb_transport import AdbFileInfo, AdbTransport
from rom_manager.web.handlers.sync_cable import register_cable
from rom_manager.web.router import Router


def _config(tmp_path):
    return SimpleNamespace(
        adb="adb",
        project_root=tmp_path,
        data_dir=tmp_path / ".rommgr",
        library_root=str(tmp_path / "pc"),
        anbernic_root=None,
        save_extensions=(".sav",),
        sync=SimpleNamespace(clock_skew_threshold_s=120),
        backup=SimpleNamespace(saves_enabled=False),
    )


class _FakeCtx:
    def __init__(self, post_data):
        self._post_data = post_data
        self.out = None

    def _send_json(self, obj):
        self.out = obj


@pytest.fixture(autouse=True)
def _isolate_job_manager():
    _state._job_manager.finish("cable_sync", None)
    yield
    for _ in range(50):
        if not _state._job_manager.get_status()["cable_sync_running"]:
            break
        time.sleep(0.05)
    _state._job_manager.finish("cable_sync", None)


def test_dry_run_skips_real_pull_even_with_sha1_dedup(tmp_path, monkeypatch):
    monkeypatch.setattr(AdbTransport, "device_epoch", lambda self: int(time.time()))
    monkeypatch.setattr(
        AdbTransport,
        "ls_recursive",
        lambda self, *a, **k: [
            AdbFileInfo(
                android_path="/storage/emulated/0/RetroArch/roms/gba/mario.gba",
                size=1024,
                mtime=time.time(),
            )
        ],
    )

    def _boom_pull(self, *a, **k):
        raise AssertionError("dry_run no debe disparar un pull ADB real")

    monkeypatch.setattr(AdbTransport, "pull", _boom_pull)

    router = Router()
    config = _config(tmp_path)
    register_cable(router, config=config, repository=None, job_manager=_state._job_manager)

    ctx = _FakeCtx(
        {
            "pc_path": str(tmp_path / "pc"),
            "use_adb": True,
            "adb_serial": "emulator-5554",
            "android_path": "/storage/emulated/0/RetroArch",
            "what": ["roms"],
            "direction": "anbernic_to_pc",
            "skip_sha1_dups": True,
            "dry_run": True,
        }
    )
    router.dispatch("POST", "/api/cable-sync", ctx)
    assert ctx.out.get("status") == "started", ctx.out

    for _ in range(100):
        if not _state._job_manager.get_status()["cable_sync_running"]:
            break
        time.sleep(0.02)

    res = _state._job_manager.get_status()["cable_sync_result"]
    assert res["copied"] == 1
    assert res["errors"] == 0
    assert not (tmp_path / "pc" / "gba" / "mario.gba").exists()  # dry-run: nada tocado en disco
