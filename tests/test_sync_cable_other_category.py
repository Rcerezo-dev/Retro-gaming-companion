"""ANBERNIC-PICK-5: `_cat_name()` reconoce una tercera categoría "other" para
archivos que no son ni un save ni un ROM reconocido (carátulas, metadatos).
Antes, cualquier extensión que no fuera un save se clasificaba como "rom" a
ciegas, así que con "Espejo completo" (`delete_extra`) activo, carátulas de
`media/` (.jpg) y metadatos sueltos (.txt, .xml, .ini) que nunca están en la
BD como juego se listaban como "extra" y se borraban junto a los ROMs de
verdad. Caso real: 204 .jpg + 4 archivos detectados en una validación con
`what=["roms"]` (sin "assets" marcado). Ver backlog.md:932-948.
"""

from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace

import rom_manager.web.state as _state
from rom_manager.web.handlers.sync_cable import register_cable
from rom_manager.web.router import Router

_TS = "2024-01-01T00:00:00"


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


def test_mirror_does_not_delete_unrecognized_extras_without_assets(tmp_path: Path) -> None:
    """Reproduce el incidente real: carátulas/metadatos que quedaron en la
    Anbernic de una sync anterior con "assets" marcado no deben desaparecer
    al hacer "Espejo completo" con solo "roms", aunque no existan en el PC
    (nunca están en la BD como juego, así que antes nada los protegía)."""
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    _write(pc, "arcade", "sf2.zip")
    _write(ab, "arcade", "sf2.zip")
    _write(ab, "media", "wheels", "sf2.jpg")
    _write(ab, "media", "wheels", "notes.txt")
    _write(ab, "media", "wheels", "gamelist.xml")
    _write(ab, "media", "wheels", "config.ini")

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

    assert res["deleted_extra"] == 0
    assert (ab / "media" / "wheels" / "sf2.jpg").exists()
    assert (ab / "media" / "wheels" / "notes.txt").exists()
    assert (ab / "media" / "wheels" / "gamelist.xml").exists()
    assert (ab / "media" / "wheels" / "config.ini").exists()


def test_mirror_still_deletes_real_extra_roms(tmp_path: Path) -> None:
    """El fix no debe romper el "espejo" real: un ROM de verdad que ya no
    está en el PC sigue borrándose de la consola."""
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    pc.mkdir()
    _write(ab, "arcade", "old_game.zip")

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

    assert res["deleted_extra"] == 1
    assert not (ab / "arcade" / "old_game.zip").exists()


def test_other_category_still_deletable_with_assets_explicit(tmp_path: Path) -> None:
    """Si el usuario sí pide sincronizar "assets" explícitamente, el espejo
    de carátulas/metadatos vuelve a aplicar (comportamiento intencional, no
    el bug — el punto es que "roms" solo no debe arrastrar "other")."""
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    pc.mkdir()
    _write(ab, "media", "wheels", "orphan.jpg")

    res = _run_sync(
        tmp_path,
        {
            "pc_path": str(pc),
            "anbernic_path": str(ab),
            "what": ["assets"],
            "direction": "pc_to_anbernic",
            "dry_run": False,
            "delete_extra": True,
        },
    )

    assert res["deleted_extra"] == 1
    assert not (ab / "media" / "wheels" / "orphan.jpg").exists()
