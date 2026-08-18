"""Tests for _detect_android_ra_config_dir — B0-3c (auto-detección Android).

Mirrors test_detect_retroarch.py's style for the PC side, but the Android
probe goes through ADB (AdbTransport.test_path()) instead of the filesystem.
"""

from __future__ import annotations

from rom_manager.config import load_config
from rom_manager.web.handlers.config import _detect_android_ra_config_dir


class _FakeAdbTransport:
    def __init__(self, accessible: bool, error: str | None = None) -> None:
        self._accessible = accessible
        self._error = error

    def test_path(self, android_path: str) -> dict:
        if self._accessible:
            return {"accessible": True, "path": android_path, "entries": 3}
        return {"accessible": False, "error": self._error or "no existe"}


def test_no_device_reports_message(tmp_path) -> None:
    config = load_config(project_root=tmp_path)

    result = _detect_android_ra_config_dir(config, None)

    assert result == {
        "found": False,
        "ra_config_dir": None,
        "error": "conecta el dispositivo Android por ADB primero",
    }


def test_found_uses_auto_sync_android_path_as_candidate(tmp_path) -> None:
    config = load_config(project_root=tmp_path)
    config.sync.auto_sync_android_path = "/storage/emulated/0/RetroArch"
    transport = _FakeAdbTransport(accessible=True)

    result = _detect_android_ra_config_dir(config, transport)

    assert result == {
        "found": True,
        "ra_config_dir": "/storage/emulated/0/RetroArch/config",
    }


def test_not_found_surfaces_test_path_error(tmp_path) -> None:
    config = load_config(project_root=tmp_path)
    config.sync.auto_sync_android_path = "/storage/emulated/0/RetroArch"
    transport = _FakeAdbTransport(accessible=False, error="La ruta no existe en el dispositivo")

    result = _detect_android_ra_config_dir(config, transport)

    assert result["found"] is False
    assert result["ra_config_dir"] is None
    assert result["error"] == "La ruta no existe en el dispositivo"
