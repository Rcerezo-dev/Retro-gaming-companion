"""CABLE-ROM-FIX-4: Cable Sync respeta `exclude_platform_folders` — con la
allowlist activa, ningún archivo bajo una carpeta de plataforma excluida (PC
o consola) se copia, se cuenta como "extra" en el espejo, ni se borra. Antes
había que apuntar `pc_path`/`anbernic_path` a una subcarpeta a mano (script
ad-hoc de CABLE-ROM-FIX-3, sesión 2026-08-26) cada vez que la SD no tenía
espacio para toda la biblioteca. Por defecto (lista vacía) el comportamiento
no cambia respecto a antes.
"""

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


def test_platform_folders_endpoint_lists_standard_folders(tmp_path: Path) -> None:
    router = Router()
    register_cable(
        router, config=_config(tmp_path), repository=None, job_manager=_state._job_manager
    )
    ctx = _FakeCtx({})
    router.dispatch("GET", "/api/platform-folders", ctx)

    assert "arcade" in ctx.out["folders"]
    assert "psx" in ctx.out["folders"]
    assert ctx.out["folders"] == sorted(ctx.out["folders"])


def test_exclude_platform_folders_skips_excluded_platform_pc_to_anbernic(tmp_path: Path) -> None:
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    _write(pc, "arcade", "sf2.zip")
    _write(pc, "psx", "game.chd")
    ab.mkdir()

    res = _run_sync(
        tmp_path,
        {
            "pc_path": str(pc),
            "anbernic_path": str(ab),
            "what": ["roms"],
            "direction": "pc_to_anbernic",
            "dry_run": False,
            "exclude_platform_folders": ["arcade"],
        },
    )

    assert res["copied"] == 1
    assert not (ab / "arcade" / "sf2.zip").exists()
    assert (ab / "psx" / "game.chd").exists()


def test_exclude_platform_folders_is_case_insensitive(tmp_path: Path) -> None:
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    _write(pc, "Arcade", "sf2.zip")
    ab.mkdir()

    res = _run_sync(
        tmp_path,
        {
            "pc_path": str(pc),
            "anbernic_path": str(ab),
            "what": ["roms"],
            "direction": "pc_to_anbernic",
            "dry_run": False,
            "exclude_platform_folders": ["ARCADE"],
        },
    )

    assert res["copied"] == 0
    assert not (ab / "Arcade" / "sf2.zip").exists()


def test_exclude_platform_folders_empty_copies_everything_as_before(tmp_path: Path) -> None:
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    _write(pc, "arcade", "sf2.zip")
    _write(pc, "psx", "game.chd")
    ab.mkdir()

    res = _run_sync(
        tmp_path,
        {
            "pc_path": str(pc),
            "anbernic_path": str(ab),
            "what": ["roms"],
            "direction": "pc_to_anbernic",
            "dry_run": False,
        },
    )

    assert res["copied"] == 2


def test_exclude_platform_folders_anbernic_to_pc(tmp_path: Path) -> None:
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    pc.mkdir()
    _write(ab, "arcade", "sf2.zip")
    _write(ab, "psx", "game.chd")

    res = _run_sync(
        tmp_path,
        {
            "pc_path": str(pc),
            "anbernic_path": str(ab),
            "what": ["roms"],
            "direction": "anbernic_to_pc",
            "dry_run": False,
            "exclude_platform_folders": ["arcade"],
        },
    )

    assert res["copied"] == 1
    assert not (pc / "arcade" / "sf2.zip").exists()
    assert (pc / "psx" / "game.chd").exists()


def test_exclude_platform_folders_with_mirror_does_not_touch_excluded_platform(
    tmp_path: Path,
) -> None:
    """Con "Espejo completo" activo, una plataforma excluida no debe tratarse
    como "extra" y borrarse del destino — nunca se sincronizó, así que no
    debe verse afectada por el espejo (misma lógica que ANBERNIC-PICK-4 con
    el tag, pero para la exclusión por plataforma)."""
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    _write(pc, "psx", "game.chd")
    _write(ab, "arcade", "sf2.zip")  # solo en la consola, plataforma excluida
    _write(ab, "psx", "old.chd")  # solo en la consola, plataforma sincronizada — sí es "extra"

    res = _run_sync(
        tmp_path,
        {
            "pc_path": str(pc),
            "anbernic_path": str(ab),
            "what": ["roms"],
            "direction": "pc_to_anbernic",
            "dry_run": False,
            "delete_extra": True,
            "exclude_platform_folders": ["arcade"],
        },
    )

    assert (ab / "arcade" / "sf2.zip").exists()
    assert not (ab / "psx" / "old.chd").exists()
    assert res["deleted_extra"] == 1
