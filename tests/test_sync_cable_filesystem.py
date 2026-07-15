"""CABLE-UX-9d — sync manual (modo filesystem) usa el motor compartido.

Cubre el camino que reemplazó `_copy`/los bucles por dirección propios por
`cable_engine.plan_direction`/`copy_item`: verifica que safe_mode y el
conteo de "Omitidos" en modo `newest` siguen comportándose igual que antes
de la migración.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from types import SimpleNamespace

import rom_manager.web.state as _state
from rom_manager.web.handlers.sync_cable import register_cable
from rom_manager.web.router import Router


def _config(tmp_path: Path, *, backup_saves_enabled: bool = False) -> SimpleNamespace:
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
        backup=SimpleNamespace(saves_enabled=backup_saves_enabled),
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


def _run_sync(tmp_path: Path, data: dict, *, config: SimpleNamespace | None = None) -> dict:
    _state._job_manager.finish("cable_sync", None)
    router = Router()
    register_cable(
        router,
        config=config or _config(tmp_path),
        repository=None,
        job_manager=_state._job_manager,
    )
    ctx = _FakeCtx(data)
    router.dispatch("POST", "/api/cable-sync", ctx)
    assert ctx.out.get("status") == "started", ctx.out

    for _ in range(100):
        if not _state._job_manager.get_status()["cable_sync_running"]:
            break
        time.sleep(0.02)
    return _state._job_manager.get_status()["cable_sync_result"]


def test_pc_to_anbernic_copies(tmp_path: Path) -> None:
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    _write(pc, "gba", "mario.sav")
    ab.mkdir()

    res = _run_sync(
        tmp_path,
        {
            "pc_path": str(pc),
            "anbernic_path": str(ab),
            "what": ["saves"],
            "direction": "pc_to_anbernic",
            "dry_run": False,
        },
    )

    assert res["copied"] == 1
    assert res["errors"] == 0
    assert (ab / "gba" / "mario.sav").exists()


def test_overwrite_backs_up_existing_save_when_enabled(tmp_path: Path) -> None:
    """REV43-2: sobrescribir un save existente por cable debe respaldarlo
    primero (backup_save), igual que ya hace el SD-auto daemon (CABLE-UX-9a) —
    la ruta manual no tenía red de seguridad."""
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    _write(pc, "mario.sav", content=b"NEW")
    _write(ab, "mario.sav", content=b"OLD")

    res = _run_sync(
        tmp_path,
        {
            "pc_path": str(pc),
            "anbernic_path": str(ab),
            "what": ["saves"],
            "direction": "pc_to_anbernic",
            "dry_run": False,
            "safe_mode": False,
        },
        config=_config(tmp_path, backup_saves_enabled=True),
    )

    assert res["copied"] == 1
    assert (ab / "mario.sav").read_bytes() == b"NEW"
    backups = list((tmp_path / ".rommgr" / "saves-backup").rglob("*.sav"))
    assert len(backups) == 1
    assert backups[0].read_bytes() == b"OLD"


def test_safe_mode_default_skips_existing_destination(tmp_path: Path) -> None:
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    _write(pc, "mario.sav", content=b"NEW")
    _write(ab, "mario.sav", content=b"OLD")

    res = _run_sync(
        tmp_path,
        {
            "pc_path": str(pc),
            "anbernic_path": str(ab),
            "what": ["saves"],
            "direction": "pc_to_anbernic",
            "dry_run": False,
        },
    )

    assert res["copied"] == 0
    assert res["safe_mode_skipped_overwrites"] == 1
    assert (ab / "mario.sav").read_bytes() == b"OLD"


def test_newest_ties_are_counted_as_skipped(tmp_path: Path) -> None:
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    pc_f = _write(pc, "mario.sav", content=b"SAME")
    ab_f = _write(ab, "mario.sav", content=b"SAME")
    os.utime(pc_f, (100, 100))
    os.utime(ab_f, (100, 100))

    res = _run_sync(
        tmp_path,
        {
            "pc_path": str(pc),
            "anbernic_path": str(ab),
            "what": ["saves"],
            "direction": "newest",
            "dry_run": False,
            "safe_mode": False,
        },
    )

    assert res["copied"] == 0
    assert res["skipped"] == 1
