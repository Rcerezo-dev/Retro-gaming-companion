"""Tests for services/device_profile.py (DEVPROFILE-4a/4b)."""

from __future__ import annotations

from pathlib import Path

from rom_manager.config import SyncSource, load_config
from rom_manager.services.device_profile import (
    detect_tier_a_sources,
    export_profile_sources,
    import_profile_sources,
)
from rom_manager.web.handlers.system import _handle_device_profile_detect


def test_detect_tier_a_sources_only_returns_existing_dirs(tmp_path: Path) -> None:
    ra_dir = tmp_path / "RetroArch"
    (ra_dir / "autoconfig").mkdir(parents=True)
    (ra_dir / "shaders").mkdir(parents=True)
    # "system" deliberately not created

    sources = detect_tier_a_sources(ra_dir, "dropbox:RetroSync")

    names = {Path(s.local_dir).name for s in sources}
    assert names == {"autoconfig", "shaders"}
    assert all(s.sync_all for s in sources)


def test_detect_tier_a_sources_builds_remote_from_base(tmp_path: Path) -> None:
    ra_dir = tmp_path / "RetroArch"
    (ra_dir / "system").mkdir(parents=True)

    sources = detect_tier_a_sources(ra_dir, "dropbox:RetroSync/")

    assert sources[0].remote == "dropbox:RetroSync/system"


def test_detect_tier_a_sources_empty_when_nothing_exists(tmp_path: Path) -> None:
    assert detect_tier_a_sources(tmp_path / "RetroArch", "dropbox:RetroSync") == []


def test_export_import_roundtrips_tokenized_paths(tmp_path: Path) -> None:
    roms = tmp_path / "roms"
    saves = tmp_path / "roms" / "saves"
    system = tmp_path / "RetroArch" / "system"
    for d in (roms, saves, system):
        d.mkdir(parents=True)

    sources = [
        SyncSource(name="BIOS / System", local_dir=str(system), remote="dropbox:RetroSync/system")
    ]

    exported = export_profile_sources(sources, roms, saves, system)
    assert exported[0]["local_dir"] == "{SYSTEM}"

    # Different target device, different absolute roots — token resolves to the new device's path.
    other_system = tmp_path / "other-device" / "system"
    imported = import_profile_sources(exported, roms, saves, other_system)
    assert imported[0].local_dir == str(other_system)
    assert imported[0].remote == "dropbox:RetroSync/system"


def test_export_leaves_paths_outside_roots_untouched(tmp_path: Path) -> None:
    roms = tmp_path / "roms"
    saves = tmp_path / "roms" / "saves"
    system = tmp_path / "system"
    for d in (roms, saves, system):
        d.mkdir(parents=True)
    standalone = tmp_path / "Dolphin" / "Config"
    standalone.mkdir(parents=True)

    sources = [
        SyncSource(
            name="Dolphin",
            local_dir=str(standalone),
            remote="dropbox:RetroSync/dolphin",
            sync_all=True,
        )
    ]

    exported = export_profile_sources(sources, roms, saves, system)
    assert exported[0]["local_dir"] == str(standalone)


# ── DEVPROFILE-4a: web/handlers/system.py::_handle_device_profile_detect ──────


def test_handle_device_profile_detect_no_retroarch_configured() -> None:
    cfg = load_config()
    cfg.retroarch_path = ""

    result = _handle_device_profile_detect(cfg)

    assert result["candidates"] == []
    assert "error" in result


def test_handle_device_profile_detect_builds_remote_and_excludes_existing(
    tmp_path: Path,
) -> None:
    ra_dir = tmp_path / "RetroArch"
    (ra_dir / "shaders").mkdir(parents=True)
    (ra_dir / "system").mkdir(parents=True)

    cfg = load_config()
    cfg.retroarch_path = str(ra_dir / "retroarch.exe")
    cfg.sync.saves_remote = "dropbox:RetroSync/saves"
    cfg.sync.sync_sources = [
        SyncSource(
            name="BIOS / System",
            local_dir=str(ra_dir / "system"),
            remote="dropbox:RetroSync/system",
            sync_all=True,
        )
    ]

    result = _handle_device_profile_detect(cfg)

    names = {c["name"] for c in result["candidates"]}
    assert names == {"RetroArch Shaders"}
    assert result["candidates"][0]["remote"] == "dropbox:RetroSync/shaders"
    assert result["existing"][0]["name"] == "BIOS / System"
