"""Roadmap 08 (fix/error-handling) — hallazgos 1 y 5: los catch-all de más
alto nivel de varios job runners guardaban el error en job_result (visible
en la UI) pero nunca dejaban traceback en el log del servidor. Si el mensaje
de str(exc) no basta para diagnosticar, no queda nada que buscar en logs.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

import rom_manager.web.state as _state
from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.handlers.sync import _do_ra_check
from rom_manager.web.handlers.sync_cable import _do_cable_sync, _do_tree_diff
from rom_manager.web.jobs.manager import JobManager


class _FakeCtx:
    def __init__(self, post_data: dict | None = None) -> None:
        self._post_data = post_data or {}
        self.out: dict | None = None

    def _send_json(self, obj: dict) -> None:
        self.out = obj


@pytest.fixture(autouse=True)
def _isolate_job_manager():
    _state._job_manager.finish("cable_sync", None)
    _state._job_manager.finish("tree_diff", None)
    yield
    for name in ("cable_sync", "tree_diff"):
        for _ in range(50):
            if not _state._job_manager.get_status()[f"{name}_running"]:
                break
            time.sleep(0.05)
        _state._job_manager.finish(name, None)


def _wait_until_finished(job_manager: JobManager, name: str) -> dict:
    for _ in range(100):
        if not job_manager.get_status()[f"{name}_running"]:
            break
        time.sleep(0.02)
    else:
        pytest.fail(f"job {name} nunca terminó")
    return job_manager.get_status()[f"{name}_result"]


def test_cable_sync_logs_traceback_on_uncaught_error(tmp_path: Path, caplog) -> None:
    config = SimpleNamespace(
        adb="adb",
        project_root=tmp_path,
        data_dir=tmp_path / ".rommgr",
        library_root=None,
        anbernic_root=None,
        save_extensions=(".sav",),
        notify_desktop=False,
        sync=SimpleNamespace(clock_skew_threshold_s=120),
        backup=SimpleNamespace(saves_enabled=False),
    )
    ctx = _FakeCtx()

    with caplog.at_level(logging.ERROR, logger="rom_manager.web.handlers.sync_cable"):
        _do_cable_sync(
            ctx,
            {
                "pc_path": str(tmp_path / "no-existe"),
                "anbernic_path": str(tmp_path / "ab"),
                "direction": "pc_to_anbernic",
                "dry_run": True,
            },
            config,
            repository=None,
            job_manager=_state._job_manager,
        )

    result = _wait_until_finished(_state._job_manager, "cable_sync")
    assert "error" in result
    assert any(
        r.name == "rom_manager.web.handlers.sync_cable" and r.exc_info for r in caplog.records
    ), "el catch-all de Cable Sync debe loggear con traceback (logger.exception)"


def test_ra_check_logs_traceback_on_uncaught_error(tmp_path: Path, caplog, monkeypatch) -> None:
    config = load_config(project_root=tmp_path)
    repo = LibraryRepository(tmp_path / "library.db")
    job_manager = JobManager()

    def _boom(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr("rom_manager.retroachievements.ra_checker.check_library", _boom)

    with caplog.at_level(logging.ERROR, logger="rom_manager.web.handlers.sync"):
        _do_ra_check("fake-api-key", config, repo, job_manager)

    result = _wait_until_finished(job_manager, "ra_check")
    assert "error" in result
    assert any(r.name == "rom_manager.web.handlers.sync" and r.exc_info for r in caplog.records), (
        "el catch-all de RA check debe loggear con traceback (logger.exception)"
    )


def test_tree_diff_logs_traceback_on_uncaught_error(tmp_path: Path, caplog, monkeypatch) -> None:
    config = SimpleNamespace(
        library_root=str(tmp_path),
        anbernic_root=None,
        sync=SimpleNamespace(auto_sync_android_path=""),
    )
    job_manager = _state._job_manager
    ctx = _FakeCtx()

    def _boom(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr("rom_manager.utils.dir_diff.get_local_tree", _boom)

    with caplog.at_level(logging.ERROR, logger="rom_manager.web.handlers.sync_cable"):
        _do_tree_diff(ctx, {"pc_path": str(tmp_path)}, config, job_manager)

    result = _wait_until_finished(job_manager, "tree_diff")
    assert "error" in result
    assert any(
        r.name == "rom_manager.web.handlers.sync_cable" and r.exc_info for r in caplog.records
    ), "el catch-all de tree diff debe loggear con traceback (logger.exception)"
