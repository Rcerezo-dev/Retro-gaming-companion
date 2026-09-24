"""CABLE-ROOT-1c/1d — roadmap 11 (fix/cable-sync-android-root-canonical).

Un Cable Sync ADB apuntando por error a un root vacío (almacenamiento
interno en vez de la SD real que vigila el launcher) "tenía éxito" sin
ninguna señal de que algo estaba mal (errors=0, tamaño exacto) — hallazgo
real 2026-09-13 (`CABLE-ROOT-1`, Dark Cloud/Viewtiful Joe 2/Sonic Adventure/
Crazy Taxi 2 aterrizaron en `/storage/emulated/0/RetroArch/...` en vez de
`/storage/521D-04EA/ROMs/...`). Dos fixes cubiertos aquí:

1. `rel_posix` se traduce a su slug canónico de Android antes de construir
   el destino ADB (mismo mecanismo que ya usa el Inbox, roadmap 05) — una
   carpeta del PC con nombre viejo (`PlayStation 2`) ya no se espeja tal
   cual.
2. Antes de una corrida real (`dry_run=False`, `pc_to_anbernic`), se avisa
   (no bloquea) si el destino de una plataforma con volumen real en el PC
   aparece sospechosamente vacío en el dispositivo.
"""

from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

import rom_manager.web.state as _state
from rom_manager.sync.adb_transport import AdbTransport
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
        notify_desktop=False,
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
            "android_path": "/storage/emulated/0/RetroArch",
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


def test_pc_to_anbernic_adb_translates_non_canonical_folder(tmp_path, monkeypatch):
    (tmp_path / "pc" / "PlayStation 2").mkdir(parents=True)
    (tmp_path / "pc" / "PlayStation 2" / "Dark Cloud (USA).iso").write_bytes(b"x" * 1024)

    monkeypatch.setattr(AdbTransport, "ls_recursive", lambda self, *a, **k: [])
    monkeypatch.setattr(AdbTransport, "free_bytes", lambda self, path: 10**9)

    pushed: list[str] = []
    monkeypatch.setattr(
        AdbTransport,
        "push",
        lambda self, local_src, dst, **k: pushed.append(dst) or 1024,
    )

    res = _run_sync(tmp_path, {"direction": "pc_to_anbernic", "dry_run": False})

    assert res["copied"] == 1
    assert pushed == ["/storage/emulated/0/RetroArch/ps2/Dark Cloud (USA).iso"]


def test_pc_to_anbernic_adb_warns_when_device_platform_folder_is_suspiciously_empty(
    tmp_path, monkeypatch
):
    pc_platform = tmp_path / "pc" / "gba"
    pc_platform.mkdir(parents=True)
    for i in range(20):
        (pc_platform / f"game{i}.gba").write_bytes(b"x")

    monkeypatch.setattr(AdbTransport, "ls_recursive", lambda self, *a, **k: [])
    monkeypatch.setattr(AdbTransport, "free_bytes", lambda self, path: 10**9)
    monkeypatch.setattr(AdbTransport, "push", lambda self, local_src, dst, **k: 1)

    res = _run_sync(tmp_path, {"direction": "pc_to_anbernic", "dry_run": False})

    assert res["copied"] == 20
    log_path = tmp_path / ".rommgr" / "cable_sync_ops.log"
    log_text = log_path.read_text(encoding="utf-8")
    assert "[WARN ]" in log_text
    assert "gba/ (20 archivos en PC)" in log_text
    assert "destino vacío" in log_text


def test_pc_to_anbernic_adb_no_warning_below_threshold(tmp_path, monkeypatch):
    pc_platform = tmp_path / "pc" / "gba"
    pc_platform.mkdir(parents=True)
    for i in range(3):
        (pc_platform / f"game{i}.gba").write_bytes(b"x")

    monkeypatch.setattr(AdbTransport, "ls_recursive", lambda self, *a, **k: [])
    monkeypatch.setattr(AdbTransport, "free_bytes", lambda self, path: 10**9)
    monkeypatch.setattr(AdbTransport, "push", lambda self, local_src, dst, **k: 1)

    res = _run_sync(tmp_path, {"direction": "pc_to_anbernic", "dry_run": False})

    assert res["copied"] == 3
    log_path = tmp_path / ".rommgr" / "cable_sync_ops.log"
    log_text = log_path.read_text(encoding="utf-8")
    assert "[WARN ]" not in log_text


def test_pc_to_anbernic_adb_no_warning_when_device_already_has_files(tmp_path, monkeypatch):
    pc_platform = tmp_path / "pc" / "gba"
    pc_platform.mkdir(parents=True)
    for i in range(20):
        (pc_platform / f"game{i}.gba").write_bytes(b"x")

    from rom_manager.sync.adb_transport import AdbFileInfo

    monkeypatch.setattr(
        AdbTransport,
        "ls_recursive",
        lambda self, *a, **k: [
            AdbFileInfo(
                android_path="/storage/emulated/0/RetroArch/gba/existing.gba",
                size=1,
                mtime=time.time(),
            )
        ],
    )
    monkeypatch.setattr(AdbTransport, "free_bytes", lambda self, path: 10**9)
    monkeypatch.setattr(AdbTransport, "push", lambda self, local_src, dst, **k: 1)

    res = _run_sync(
        tmp_path, {"direction": "pc_to_anbernic", "dry_run": False, "skip_existing": False}
    )

    assert res["copied"] == 20
    log_path = tmp_path / ".rommgr" / "cable_sync_ops.log"
    log_text = log_path.read_text(encoding="utf-8")
    assert "[WARN ]" not in log_text
