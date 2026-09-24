"""CFG-PORGAME-6: endpoint builder that pairs PC/Android override listings."""

from __future__ import annotations

from pathlib import Path

import pytest

from rom_manager.config import load_config
from rom_manager.sync.adb_transport import AdbFileInfo, AdbTransport
from rom_manager.web.builders.overrides import _build_overrides


@pytest.fixture
def config(tmp_path: Path):
    return load_config(tmp_path)


def test_no_android_transport_reports_message(config) -> None:
    result = _build_overrides(config, None)
    assert result["only_pc"] == []
    assert result["only_android"] == []
    assert result["in_both"] == []
    assert "ADB" in result["android_message"] or "dispositivo" in result["android_message"]


def test_pc_not_configured_flag(config) -> None:
    config.sync.ra_config_dir = ""
    result = _build_overrides(config, None)
    assert result["pc_configured"] is False


def test_exposes_shared_cores_for_the_copy_button(config) -> None:
    result = _build_overrides(config, None)
    assert "Gambatte" in result["shared_cores"]
    assert "Snes9x" not in result["shared_cores"]


def test_pc_only_override(config, tmp_path: Path) -> None:
    ra_dir = tmp_path / "ra-config"
    (ra_dir / "Snes9x").mkdir(parents=True)
    (ra_dir / "Snes9x" / "Super Mario World.opt").write_text("", encoding="utf-8")
    config.sync.ra_config_dir = str(ra_dir)

    result = _build_overrides(config, None)

    assert result["pc_configured"] is True
    assert result["only_pc"] == [{"rom": "Super Mario World", "cores": ["Snes9x"]}]
    assert result["only_android"] == []
    assert result["in_both"] == []


def test_android_only_override(config, monkeypatch) -> None:
    def fake_ls_recursive(self, android_path, *, wanted_extensions=None, **kw):
        return [
            AdbFileInfo(android_path=f"{android_path}/mGBA/Pokemon Emerald.opt", size=64, mtime=0.0)
        ]

    monkeypatch.setattr(AdbTransport, "ls_recursive", fake_ls_recursive)
    transport = AdbTransport(config.adb, "ABC123")

    result = _build_overrides(config, transport)

    assert result["only_android"] == [{"rom": "Pokemon Emerald", "cores": ["mGBA"]}]
    assert result["only_pc"] == []
    assert result["android_message"] is None


def test_same_rom_both_sides_reports_core_match(config, tmp_path: Path, monkeypatch) -> None:
    ra_dir = tmp_path / "ra-config"
    (ra_dir / "Gambatte").mkdir(parents=True)
    (ra_dir / "Gambatte" / "Tetris.opt").write_text("", encoding="utf-8")
    config.sync.ra_config_dir = str(ra_dir)

    def fake_ls_recursive(self, android_path, *, wanted_extensions=None, **kw):
        return [AdbFileInfo(android_path=f"{android_path}/Gambatte/Tetris.opt", size=1, mtime=0.0)]

    monkeypatch.setattr(AdbTransport, "ls_recursive", fake_ls_recursive)
    transport = AdbTransport(config.adb, "ABC123")

    result = _build_overrides(config, transport)

    assert result["in_both"] == [
        {
            "rom": "Tetris",
            "pc_cores": ["Gambatte"],
            "android_cores": ["Gambatte"],
            "core_match": True,
        }
    ]


def test_same_rom_different_cores_no_match(config, tmp_path: Path, monkeypatch) -> None:
    ra_dir = tmp_path / "ra-config"
    (ra_dir / "Snes9x").mkdir(parents=True)
    (ra_dir / "Snes9x" / "Chrono Trigger.opt").write_text("", encoding="utf-8")
    config.sync.ra_config_dir = str(ra_dir)

    def fake_ls_recursive(self, android_path, *, wanted_extensions=None, **kw):
        return [
            AdbFileInfo(
                android_path=f"{android_path}/Snes9x 2010/Chrono Trigger.opt", size=1, mtime=0.0
            )
        ]

    monkeypatch.setattr(AdbTransport, "ls_recursive", fake_ls_recursive)
    transport = AdbTransport(config.adb, "ABC123")

    result = _build_overrides(config, transport)

    assert result["in_both"][0]["core_match"] is False


def test_adb_transport_error_reports_message(config, monkeypatch) -> None:
    def raise_error(self, android_path, *, wanted_extensions=None, **kw):
        raise RuntimeError("device offline")

    monkeypatch.setattr(AdbTransport, "ls_recursive", raise_error)
    transport = AdbTransport(config.adb, "ABC123")

    result = _build_overrides(config, transport)

    assert result["only_android"] == []
    assert "device offline" in result["android_message"]
