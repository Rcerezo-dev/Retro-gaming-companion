"""CABLE-ROM-FIX-6: el espejo de Cable Sync (delete_extra) no debe tratar un
disco como "extra a borrar" cuando el otro lado ya lo tiene en un formato de
imagen de disco distinto (.chd == .cue/.bin/.gdi/.ccd del mismo título) —
antes de este fix, comparar solo por ruta/nombre exacto marcaba para borrar
el .cue del dispositivo cuando el PC ya lo tenía convertido a .chd (o
viceversa), el mismo patrón de incidente que TRASH-FIX-5."""

from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace

import rom_manager.web.state as _state
from rom_manager.web.handlers.sync_cable import register_cable
from rom_manager.web.router import Router


def _config(tmp_path: Path) -> SimpleNamespace:
    return SimpleNamespace(
        adb="adb",
        project_root=tmp_path,
        data_dir=tmp_path / ".rommgr",
        library_root=None,
        anbernic_root=None,
        save_extensions=(".sav",),
        excluded_directories=frozenset(),
        notify_desktop=False,
        sync=SimpleNamespace(clock_skew_threshold_s=120),
        backup=SimpleNamespace(saves_enabled=False),
    )


class _FakeCtx:
    def __init__(self, post_data: dict) -> None:
        self._post_data = post_data
        self.out: dict | None = None

    def _send_json(self, obj: dict) -> None:
        self.out = obj


def _write(root: Path, *parts: str, content: bytes = b"x") -> Path:
    p = root.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return p


def _run_sync(tmp_path: Path, data: dict) -> dict:
    _state._job_manager.finish("cable_sync", None)
    router = Router()
    register_cable(
        router, config=_config(tmp_path), repository=None, job_manager=_state._job_manager
    )
    ctx = _FakeCtx(data)
    router.dispatch("POST", "/api/cable-sync", ctx)
    assert ctx.out.get("status") == "started", ctx.out

    for _ in range(100):
        if not _state._job_manager.get_status()["cable_sync_running"]:
            break
        time.sleep(0.02)
    return _state._job_manager.get_status()["cable_sync_result"]


def test_pc_to_anbernic_mirror_keeps_device_cue_matching_pc_chd(tmp_path: Path) -> None:
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    _write(pc, "psx", "Xenogears (USA).chd")
    _write(ab, "psx", "Xenogears (USA).cue")  # mismo disco, formato distinto
    _write(ab, "psx", "Old Game (USA).cue")  # sin equivalente en el PC -- sí es extra

    res = _run_sync(
        tmp_path,
        {
            "pc_path": str(pc),
            "anbernic_path": str(ab),
            "what": ["roms"],
            "direction": "pc_to_anbernic",
            "dry_run": False,
            "delete_extra": True,
        },
    )

    assert (ab / "psx" / "Xenogears (USA).cue").exists()
    assert not (ab / "psx" / "Old Game (USA).cue").exists()
    assert res["deleted_extra"] == 1


def test_anbernic_to_pc_mirror_keeps_pc_chd_matching_device_cue(tmp_path: Path) -> None:
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    _write(ab, "psx", "Xenogears (USA).cue")
    _write(pc, "psx", "Xenogears (USA).chd")  # mismo disco, formato distinto
    _write(pc, "psx", "Old Game (USA).chd")  # sin equivalente en el dispositivo -- sí es extra

    res = _run_sync(
        tmp_path,
        {
            "pc_path": str(pc),
            "anbernic_path": str(ab),
            "what": ["roms"],
            "direction": "anbernic_to_pc",
            "dry_run": False,
            "delete_extra": True,
        },
    )

    assert (pc / "psx" / "Xenogears (USA).chd").exists()
    assert not (pc / "psx" / "Old Game (USA).chd").exists()
    assert res["deleted_extra"] == 1
