"""CABLE-ROM-FIX-1/2: el sync de ROMs por cable (modo ADB) copiaba TODO sin
mirar nunca qué ya existía al otro lado — `skip_existing` se aceptaba pero
no se usaba en las ramas pc_to_anbernic/anbernic_to_pc, y no había guard de
espacio libre antes de escribir al dispositivo.
"""

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


def _run_sync(tmp_path, extra: dict) -> dict:
    router = Router()
    config = _config(tmp_path)
    register_cable(router, config=config, repository=None, job_manager=_state._job_manager)
    ctx = _FakeCtx(
        {
            "pc_path": str(tmp_path / "pc"),
            "use_adb": True,
            "adb_serial": "emulator-5554",
            "android_path": "/storage/emulated/0/Roms",
            "what": ["roms"],
            **extra,
        }
    )
    router.dispatch("POST", "/api/cable-sync", ctx)
    assert ctx.out.get("status") == "started", ctx.out
    for _ in range(100):
        if not _state._job_manager.get_status()["cable_sync_running"]:
            break
        time.sleep(0.02)
    return _state._job_manager.get_status()["cable_sync_result"]


def test_pc_to_anbernic_skips_file_already_on_device_with_same_size(tmp_path, monkeypatch):
    (tmp_path / "pc").mkdir()
    rom = tmp_path / "pc" / "mario.gba"
    rom.write_bytes(b"x" * 1024)

    monkeypatch.setattr(
        AdbTransport,
        "ls_recursive",
        lambda self, *a, **k: [
            AdbFileInfo(
                android_path="/storage/emulated/0/Roms/mario.gba", size=1024, mtime=time.time()
            )
        ],
    )

    def _boom_push(self, *a, **k):
        raise AssertionError("skip_existing=True no debería empujar un archivo ya idéntico")

    monkeypatch.setattr(AdbTransport, "push", _boom_push)

    res = _run_sync(
        tmp_path,
        {"direction": "pc_to_anbernic", "skip_existing": True, "dry_run": True},
    )
    assert res["copied"] == 0
    assert res["skipped"] == 1
    assert res["errors"] == 0


def test_pc_to_anbernic_still_pushes_by_default(tmp_path, monkeypatch):
    """Sin skip_existing (default False), sigue copiando -- comportamiento
    explícito, no una regresión silenciosa del fix."""
    (tmp_path / "pc").mkdir()
    (tmp_path / "pc" / "mario.gba").write_bytes(b"x" * 1024)

    monkeypatch.setattr(
        AdbTransport,
        "ls_recursive",
        lambda self, *a, **k: [
            AdbFileInfo(
                android_path="/storage/emulated/0/Roms/mario.gba", size=1024, mtime=time.time()
            )
        ],
    )
    monkeypatch.setattr(AdbTransport, "push", lambda self, local_src, dst, **k: 1024)

    res = _run_sync(tmp_path, {"direction": "pc_to_anbernic", "dry_run": True})
    assert res["copied"] == 1
    assert res["skipped"] == 0


def test_anbernic_to_pc_skips_file_already_on_pc_with_same_size(tmp_path, monkeypatch):
    (tmp_path / "pc").mkdir()
    (tmp_path / "pc" / "mario.gba").write_bytes(b"x" * 1024)

    monkeypatch.setattr(
        AdbTransport,
        "ls_recursive",
        lambda self, *a, **k: [
            AdbFileInfo(
                android_path="/storage/emulated/0/Roms/mario.gba", size=1024, mtime=time.time()
            )
        ],
    )

    def _boom_pull(self, *a, **k):
        raise AssertionError("skip_existing=True no debería tirar de un archivo ya idéntico")

    monkeypatch.setattr(AdbTransport, "pull", _boom_pull)

    res = _run_sync(
        tmp_path,
        {"direction": "anbernic_to_pc", "skip_existing": True, "dry_run": True},
    )
    assert res["copied"] == 0
    assert res["skipped"] == 1


def test_disk_space_guard_blocks_real_run_when_insufficient(tmp_path, monkeypatch):
    (tmp_path / "pc").mkdir()
    (tmp_path / "pc" / "big.gba").write_bytes(b"x" * 2048)

    monkeypatch.setattr(AdbTransport, "ls_recursive", lambda self, *a, **k: [])
    monkeypatch.setattr(AdbTransport, "free_bytes", lambda self, path: 1024)  # menos que 2048

    def _boom_push(self, *a, **k):
        raise AssertionError("no debe escribir nada si el guard de espacio ya rechazó el job")

    monkeypatch.setattr(AdbTransport, "push", _boom_push)

    res = _run_sync(
        tmp_path,
        {"direction": "pc_to_anbernic", "dry_run": False},
    )
    assert res is not None
    assert "error" in res
    assert "Espacio insuficiente" in res["error"]


def test_dry_run_does_not_trigger_space_guard(tmp_path, monkeypatch):
    """dry_run=True es solo previsualización -- no debe abortar por espacio."""
    (tmp_path / "pc").mkdir()
    (tmp_path / "pc" / "big.gba").write_bytes(b"x" * 2048)

    monkeypatch.setattr(AdbTransport, "ls_recursive", lambda self, *a, **k: [])
    monkeypatch.setattr(AdbTransport, "free_bytes", lambda self, path: 1024)
    monkeypatch.setattr(AdbTransport, "push", lambda self, local_src, dst, **k: 2048)

    res = _run_sync(tmp_path, {"direction": "pc_to_anbernic", "dry_run": True})
    assert "error" not in (res or {})
    assert res["copied"] == 1
