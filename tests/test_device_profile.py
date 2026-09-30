"""Tests for services/device_profile.py (DEVPROFILE-4a/4b)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from rom_manager.config import SyncSource, load_config
from rom_manager.services.device_profile import (
    detect_data_sources,
    detect_tier_a_sources,
    export_profile_sources,
    import_profile_sources,
    save_profile_manifest,
)
from rom_manager.sync.rclone_transport import RcloneTransport
from rom_manager.web.handlers.system import (
    _handle_device_profile_detect,
    _handle_save_device_profile_manifest,
)


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


# ── DEVPROFILE-8: services/device_profile.py::detect_data_sources ─────────────


def test_detect_data_sources_only_returns_existing_dirs(tmp_path: Path) -> None:
    (tmp_path / ".rommgr" / "catalogs").mkdir(parents=True)

    sources = detect_data_sources(tmp_path, "dropbox:RetroSync")

    assert len(sources) == 1
    assert sources[0].local_dir == str(tmp_path / ".rommgr" / "catalogs")
    assert sources[0].remote == "dropbox:RetroSync/catalogs"
    assert sources[0].sync_all is True


def test_detect_data_sources_empty_when_nothing_exists(tmp_path: Path) -> None:
    assert detect_data_sources(tmp_path, "dropbox:RetroSync") == []


def test_detect_data_sources_includes_dbs_as_single_file(tmp_path: Path) -> None:
    """DEVPROFILE-8b: library_pc.db/library_android.db are single files under
    .rommgr, unlike "catalogs" (a whole directory) -- detected the same way
    but marked single_file=True so they route to sync_single_file()."""
    (tmp_path / ".rommgr").mkdir(parents=True)
    (tmp_path / ".rommgr" / "library_pc.db").write_bytes(b"")
    (tmp_path / ".rommgr" / "library_android.db").write_bytes(b"")

    sources = detect_data_sources(tmp_path, "dropbox:RetroSync")

    by_name = {s.name: s for s in sources}
    pc_db = by_name["Base de datos PC (library_pc.db)"]
    assert pc_db.single_file is True
    assert pc_db.remote == "dropbox:RetroSync/library_pc.db"
    assert by_name["Base de datos Android (library_android.db)"].single_file is True


def test_detect_tier_a_sources_includes_playlists_as_single_file(tmp_path: Path) -> None:
    """DEVPROFILE-9: RetroArch's recent/favorites playlists -- only the ones
    that actually exist are returned, same rule as the whole-directory
    sources above."""
    ra_dir = tmp_path / "RetroArch"
    (ra_dir / "playlists").mkdir(parents=True)
    (ra_dir / "playlists" / "content_history.lpl").write_bytes(b"")

    sources = detect_tier_a_sources(ra_dir, "dropbox:RetroSync")

    by_name = {s.name: s for s in sources}
    recientes = by_name["RetroArch Recientes"]
    assert recientes.single_file is True
    assert recientes.remote == "dropbox:RetroSync/content_history.lpl"
    assert "RetroArch Favoritos" not in by_name  # content_favorites.lpl not created


def test_export_import_roundtrips_single_file_flag(tmp_path: Path) -> None:
    roms = tmp_path / "roms"
    saves = tmp_path / "roms" / "saves"
    system = tmp_path / "RetroArch" / "system"
    db = tmp_path / ".rommgr" / "library_pc.db"
    for d in (roms, saves, system, db.parent):
        d.mkdir(parents=True)
    db.write_bytes(b"")

    sources = [
        SyncSource(
            name="Base de datos PC",
            local_dir=str(db),
            remote="dropbox:RetroSync/library_pc.db",
            single_file=True,
        )
    ]

    exported = export_profile_sources(sources, roms, saves, system, project_root=tmp_path)
    assert exported[0]["single_file"] is True
    assert exported[0]["local_dir"] == "{PROJECT_ROOT}/.rommgr/library_pc.db"

    other_root = tmp_path / "other-device"
    imported = import_profile_sources(exported, roms, saves, system, project_root=other_root)
    assert imported[0].single_file is True
    assert imported[0].local_dir == str(other_root / ".rommgr" / "library_pc.db")


def test_export_import_roundtrips_project_root_token(tmp_path: Path) -> None:
    """DEVPROFILE-8: a source outside ROMS/SAVES/SYSTEM but under project_root
    (e.g. .rommgr/catalogs) must still re-root to the *new* device's project
    root on restore, not stay pinned to the old device's absolute path."""
    roms = tmp_path / "roms"
    saves = tmp_path / "roms" / "saves"
    system = tmp_path / "RetroArch" / "system"
    catalogs = tmp_path / ".rommgr" / "catalogs"
    for d in (roms, saves, system, catalogs):
        d.mkdir(parents=True)

    sources = [
        SyncSource(name="DATs", local_dir=str(catalogs), remote="dropbox:RetroSync/catalogs")
    ]

    exported = export_profile_sources(sources, roms, saves, system, project_root=tmp_path)
    assert exported[0]["local_dir"] == "{PROJECT_ROOT}/.rommgr/catalogs"

    other_root = tmp_path / "other-device"
    imported = import_profile_sources(exported, roms, saves, system, project_root=other_root)
    assert imported[0].local_dir == str(other_root / ".rommgr" / "catalogs")


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


def test_handle_device_profile_detect_no_retroarch_configured(tmp_path: Path) -> None:
    # DEVPROFILE-8: project_root must be an isolated tmp_path, not the real
    # cwd -- this repo's own .rommgr/catalogs would otherwise be detected and
    # the "no RetroArch configured" error path would never trigger.
    cfg = load_config(tmp_path)
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

    cfg = load_config(tmp_path)
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


# ── DEVPROFILE-5a: services/device_profile.py::save_profile_manifest ──────────


def test_save_profile_manifest_uploads_tokenized_json(tmp_path: Path) -> None:
    roms = tmp_path / "roms"
    saves = tmp_path / "roms" / "saves"
    system = tmp_path / "RetroArch" / "system"
    for d in (roms, saves, system):
        d.mkdir(parents=True)

    sources = [
        SyncSource(name="BIOS / System", local_dir=str(system), remote="dropbox:RetroSync/system")
    ]

    captured: dict = {}

    def _capture(args):
        # save_profile_manifest deletes the temp file right after upload()
        # returns, so the content has to be read while _run is still "in flight".
        captured["args"] = args
        captured["content"] = json.loads(Path(args[1]).read_text(encoding="utf-8"))
        return ""

    transport = RcloneTransport()
    transport._run = MagicMock(side_effect=_capture)

    remote_path = save_profile_manifest(
        sources, roms, saves, system, transport, remote_base="dropbox:RetroSync/"
    )

    assert remote_path == "dropbox:RetroSync/device-profile.json"
    args = captured["args"]
    assert args[0] == "copyto"
    assert args[2] == "dropbox:RetroSync/device-profile.json"
    assert captured["content"] == [
        {
            "name": "BIOS / System",
            "local_dir": "{SYSTEM}",
            "remote": "dropbox:RetroSync/system",
            "sync_all": False,
            "single_file": False,
        }
    ]


def test_save_profile_manifest_cleans_up_temp_file(tmp_path: Path) -> None:
    roms = saves = system = tmp_path
    transport = RcloneTransport()
    captured: dict = {}

    def _capture(args):
        captured["tmp_path"] = Path(args[1])
        return ""

    transport._run = MagicMock(side_effect=_capture)

    save_profile_manifest([], roms, saves, system, transport, remote_base="dropbox:RetroSync")

    assert not captured["tmp_path"].exists()


# ── DEVPROFILE-5a: web/handlers/system.py::_handle_save_device_profile_manifest


def test_handle_save_manifest_requires_library_root(tmp_path: Path) -> None:
    cfg = load_config()
    cfg.library_root = None

    result = _handle_save_device_profile_manifest(cfg)

    assert result["saved"] is False
    assert "library_root" in result["error"]


def test_handle_save_manifest_requires_confirmed_sources(tmp_path: Path) -> None:
    cfg = load_config()
    cfg.library_root = tmp_path
    cfg.sync.sync_sources = []

    result = _handle_save_device_profile_manifest(cfg)

    assert result["saved"] is False
    assert "fuentes de sync" in result["error"]


def test_handle_save_manifest_requires_remote(tmp_path: Path) -> None:
    cfg = load_config()
    cfg.library_root = tmp_path
    cfg.sync.saves_remote = ""
    cfg.sync.states_remote = ""
    cfg.sync.sync_sources = [
        SyncSource(name="X", local_dir=str(tmp_path), remote="dropbox:RetroSync/x")
    ]

    result = _handle_save_device_profile_manifest(cfg)

    assert result["saved"] is False
    assert "remoto" in result["error"]


def test_handle_save_manifest_reports_rclone_error(tmp_path: Path) -> None:
    """No mocking — a nonexistent rclone binary exercises the real upload
    path end-to-end (remote_base derivation, temp file, RcloneError catch)
    without needing a real cloud remote."""
    cfg = load_config()
    cfg.library_root = tmp_path
    cfg.rclone_binary = "nonexistent-rclone-binary-xyz"
    cfg.sync.saves_remote = "dropbox:RetroSync/saves"
    cfg.sync.sync_sources = [
        SyncSource(name="X", local_dir=str(tmp_path), remote="dropbox:RetroSync/x")
    ]

    result = _handle_save_device_profile_manifest(cfg)

    assert result["saved"] is False
    assert "rclone" in result["error"].lower()
