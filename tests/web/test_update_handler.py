"""Tests for PHASE6-3b: web/handlers/update.py."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from rom_manager.config import load_config
from rom_manager.utils import update_checker as _uc
from rom_manager.web.handlers import update as _h_update
from rom_manager.web.router import Router


class _Ctx:
    def __init__(self) -> None:
        self.payload: dict | None = None

    def _send_json(self, data: dict) -> None:
        self.payload = data


@pytest.fixture(autouse=True)
def _reset_state():
    with _h_update._lock:
        _h_update._state.update(
            {
                "running": False,
                "done": False,
                "error": None,
                "bytes_done": 0,
                "bytes_total": 0,
                "downloaded_path": None,
            }
        )
    with _uc._lock:
        _uc._result.clear()
    yield


def _router(tmp_path: Path) -> Router:
    router = Router()
    config = load_config(tmp_path)
    _h_update.register(router, config=config)
    return router


def test_download_rejects_non_frozen(tmp_path: Path) -> None:
    router = _router(tmp_path)
    ctx = _Ctx()
    router.dispatch("POST", "/api/update/download", ctx)
    assert ctx.payload["status"] == "error"
    assert "código fuente" in ctx.payload["error"]


def test_download_rejects_when_no_exe_asset(tmp_path: Path) -> None:
    with _uc._lock:
        _uc._result.update({"assets": [{"name": "source.zip", "url": "https://x/s.zip"}]})
    router = _router(tmp_path)
    ctx = _Ctx()
    with patch.object(sys, "frozen", True, create=True):
        router.dispatch("POST", "/api/update/download", ctx)
    assert ctx.payload["status"] == "error"
    assert "instalador" in ctx.payload["error"]


def test_download_starts_and_status_reflects_progress(tmp_path: Path) -> None:
    with _uc._lock:
        _uc._result.update(
            {"assets": [{"name": "Setup.exe", "url": "https://x/Setup.exe", "size": 8}]}
        )
    router = _router(tmp_path)
    ctx = _Ctx()

    def _fake_download(url, dest_dir, filename, *, on_progress=None):
        if on_progress:
            on_progress(8, 8)
        dest = dest_dir / filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"x")
        return dest

    with (
        patch.object(sys, "frozen", True, create=True),
        patch("rom_manager.web.handlers.update.download_update", side_effect=_fake_download),
    ):
        router.dispatch("POST", "/api/update/download", ctx)
        assert ctx.payload["status"] == "started"

        for _ in range(50):
            if _h_update._state["done"]:
                break
            time.sleep(0.02)

    status_ctx = _Ctx()
    router.dispatch("GET", "/api/update/status", status_ctx)
    assert status_ctx.payload["done"] is True
    assert status_ctx.payload["error"] is None
    assert status_ctx.payload["downloaded_path"].endswith("Setup.exe")


def test_download_already_running_is_reported(tmp_path: Path) -> None:
    with _uc._lock:
        _uc._result.update({"assets": [{"name": "Setup.exe", "url": "https://x/Setup.exe"}]})
    router = _router(tmp_path)
    with _h_update._lock:
        _h_update._state["running"] = True
    ctx = _Ctx()
    with patch.object(sys, "frozen", True, create=True):
        router.dispatch("POST", "/api/update/download", ctx)
    assert ctx.payload["status"] == "already_running"


def test_apply_without_download_errors(tmp_path: Path) -> None:
    router = _router(tmp_path)
    ctx = _Ctx()
    router.dispatch("POST", "/api/update/apply", ctx)
    assert ctx.payload["status"] == "error"


def test_apply_launches_installer_and_shuts_down(tmp_path: Path) -> None:
    router = _router(tmp_path)
    with _h_update._lock:
        _h_update._state["downloaded_path"] = str(tmp_path / "Setup.exe")

    import rom_manager.web.state as _state_mod

    _state_mod._httpd_instance = type("FakeHttpd", (), {"shutdown": lambda self: None})()

    ctx = _Ctx()
    with patch("rom_manager.web.handlers.update.launch_installer") as launch:
        router.dispatch("POST", "/api/update/apply", ctx)
        time.sleep(0.05)
    launch.assert_called_once_with(Path(tmp_path / "Setup.exe"))
    assert ctx.payload["status"] == "launched"
