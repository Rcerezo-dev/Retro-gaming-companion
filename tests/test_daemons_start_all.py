"""Regresión: start_all() debe pasar un get_repo_fn de 1 argumento a los
daemons de cable sync (mismo contrato que el resto de la app, ver
web/builders/common.py::_repo_for_path). Bug real detectado en producción:
"start_all.<locals>.<lambda>() takes 0 positional arguments but 1 was given"
en cada intento de auto-sync al conectar la consola.
"""

from __future__ import annotations

import threading
from pathlib import Path

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web import cable_sync_daemon, daemons


def test_start_all_wires_one_arg_get_repo_fn(tmp_path: Path, monkeypatch) -> None:
    cfg = load_config()
    cfg.project_root = tmp_path
    cfg.library_root = tmp_path / "pc"
    (tmp_path / "pc").mkdir()
    cfg.sync.auto_sync_enabled = True

    pc_repo = LibraryRepository(tmp_path / "pc.sqlite")
    android_repo = LibraryRepository(tmp_path / "android.sqlite")

    done = threading.Event()
    captured: dict[str, LibraryRepository] = {}

    def fake_auto_sync_loop(config, get_repo_fn) -> None:
        # La línea que fallaba en producción: get_repo_fn(path), no get_repo_fn().
        captured["pc"] = get_repo_fn(str(cfg.library_root / "psx" / "game.cue"))
        captured["android"] = get_repo_fn(str(tmp_path / "android_sd" / "game.cue"))
        done.set()

    monkeypatch.setattr(cable_sync_daemon, "_auto_sync_loop", fake_auto_sync_loop)
    monkeypatch.setattr(cable_sync_daemon, "_sd_card_sync_loop", lambda *a: None)
    monkeypatch.setattr(daemons, "_inbox_watcher_loop", lambda *a: None)
    monkeypatch.setattr(daemons, "_health_scheduler_loop", lambda *a: None)

    daemons.start_all(cfg, pc_repo, repository_android=android_repo)

    assert done.wait(timeout=2), "_auto_sync_loop nunca se invocó"
    assert captured["pc"] is pc_repo
    assert captured["android"] is android_repo
