"""VAL-FIX-5: cable-sync preview must count remote saves over ADB instead of
always reporting "no accesible en modo ADB"."""

from __future__ import annotations

from pathlib import Path

import pytest

from rom_manager.config import load_config
from rom_manager.sync.adb_transport import AdbFileInfo, AdbTransport
from rom_manager.web.builders.misc import _build_cable_sync_preview


@pytest.fixture
def config(tmp_path: Path):
    return load_config(tmp_path)


def test_adb_mode_without_serial_reports_message(config) -> None:
    result = _build_cable_sync_preview({"mode": ["adb"]}, config)
    assert result["android_saves"] is None
    assert "dispositivo" in result["android_message"]


def test_adb_mode_with_serial_counts_remote_saves(config, monkeypatch) -> None:
    def fake_ls_recursive(self, android_path, *, wanted_extensions=None, **kw):
        return [
            AdbFileInfo(android_path=f"{android_path}/a.srm", size=10, mtime=1.0),
            AdbFileInfo(android_path=f"{android_path}/b.srm", size=20, mtime=2.0),
        ]

    monkeypatch.setattr(AdbTransport, "ls_recursive", fake_ls_recursive)

    result = _build_cable_sync_preview(
        {"mode": ["adb"], "serial": ["ABC123"], "android_path": ["/storage/emulated/0/RetroArch"]},
        config,
    )
    assert result["android_saves"] == 2
    assert result["android_message"] is None


def test_adb_mode_transport_error_reports_message(config, monkeypatch) -> None:
    def raise_error(self, android_path, *, wanted_extensions=None, **kw):
        raise RuntimeError("device offline")

    monkeypatch.setattr(AdbTransport, "ls_recursive", raise_error)

    result = _build_cable_sync_preview({"mode": ["adb"], "serial": ["ABC123"]}, config)
    assert result["android_saves"] is None
    assert "device offline" in result["android_message"]
