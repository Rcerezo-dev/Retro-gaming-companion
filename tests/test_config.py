from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

from rom_manager.config import (
    _resolve_tool_path,
    build_cloud_sync_sources,
    get_adb_sync_sources,
    load_config,
)


def test_defaults_without_toml(tmp_path: Path) -> None:
    cfg = load_config(tmp_path)
    assert cfg.library_root is None
    assert cfg.sync.rclone_remote == ""
    assert cfg.rclone_binary == "rclone"
    assert cfg.chdman == "chdman"
    assert cfg.web_host == "0.0.0.0"
    assert cfg.web_port == 7777
    assert cfg.web_allow_lan is True


def test_default_tools_use_bundled_binaries(tmp_path: Path) -> None:
    (tmp_path / "tools").mkdir()
    for exe in ("rclone.exe", "adb.exe", "chdman.exe"):
        (tmp_path / "tools" / exe).write_bytes(b"")
    cfg = load_config(tmp_path)
    assert cfg.rclone_binary == str(tmp_path / "tools" / "rclone.exe")
    assert cfg.adb == str(tmp_path / "tools" / "adb.exe")
    assert cfg.chdman == str(tmp_path / "tools" / "chdman.exe")


def test_config_toml_overrides_bundled_tools(tmp_path: Path) -> None:
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "adb.exe").write_bytes(b"")
    (tmp_path / "config.toml").write_text('[tools]\nadb = "C:/otro/adb.exe"\n', encoding="utf-8")
    cfg = load_config(tmp_path)
    # VAL-FIX-3: normalizado a '\' — CreateProcess no acepta '/' en el exe
    assert cfg.adb == _resolve_tool_path("C:/otro/adb.exe")


def test_reads_library_root(tmp_path: Path) -> None:
    (tmp_path / "config.toml").write_text('[library]\nlibrary_root = "/roms"\n', encoding="utf-8")
    cfg = load_config(tmp_path)
    assert cfg.library_root == Path("/roms")


def test_reads_sync_section(tmp_path: Path) -> None:
    (tmp_path / "config.toml").write_text(
        '[sync]\nremote = "dropbox:/RetroArch/saves"\nrclone = "/usr/bin/rclone"\n',
        encoding="utf-8",
    )
    cfg = load_config(tmp_path)
    assert cfg.sync.rclone_remote == "dropbox:/RetroArch/saves"
    assert cfg.rclone_binary == _resolve_tool_path("/usr/bin/rclone")


def test_reads_tools_section(tmp_path: Path) -> None:
    (tmp_path / "config.toml").write_text(
        '[tools]\nchdman = "C:/tools/chdman.exe"\n', encoding="utf-8"
    )
    cfg = load_config(tmp_path)
    assert cfg.chdman == _resolve_tool_path("C:/tools/chdman.exe")


def test_reads_web_section(tmp_path: Path) -> None:
    (tmp_path / "config.toml").write_text(
        '[web]\nhost = "0.0.0.0"\nport = 8080\n', encoding="utf-8"
    )
    cfg = load_config(tmp_path)
    assert cfg.web_host == "0.0.0.0"
    assert cfg.web_port == 8080


def test_partial_toml_uses_defaults(tmp_path: Path) -> None:
    (tmp_path / "config.toml").write_text('[library]\nlibrary_root = "/roms"\n', encoding="utf-8")
    cfg = load_config(tmp_path)
    assert cfg.rclone_binary == "rclone"  # default preserved
    assert cfg.chdman == "chdman"  # default preserved
    assert cfg.web_port == 7777  # default preserved


def test_build_cloud_sync_sources_includes_all_optional_sources(tmp_path: Path) -> None:
    """REV43-52: one shared source-list builder for both the web sync job and
    the headless CLI 'sync' command — previously the CLI silently dropped the
    ra_config/cheats/playtime sources that the UI's sync already included."""
    ra_dir = tmp_path / "ra-config"
    cheats_dir = tmp_path / "cheats"
    (tmp_path / "config.toml").write_text(
        f"""
[library]
library_root = "{tmp_path.as_posix()}"

[sync]
ra_config_dir = "{ra_dir.as_posix()}"
ra_config_remote = "dropbox:/ra-config"
cheats_dir = "{cheats_dir.as_posix()}"
cheats_remote = "dropbox:/cheats"
playtime_remote = "dropbox:/playtime"

[[sync.sources]]
name = "RetroArch"
local_dir = "{tmp_path.as_posix()}"
remote = "dropbox:/saves"
""",
        encoding="utf-8",
    )
    cfg = load_config(tmp_path)

    names = [s.name for s in build_cloud_sync_sources(cfg)]

    assert "RetroArch" in names
    assert "RetroArch Config (.opt)" in names
    assert "RetroArch Cheats (.cht)" in names
    assert "Playtime Consola (.lrtl)" in names
    # Android playtime dir gets created so a later ingest step can find it.
    assert (tmp_path / ".rommgr" / "android_lrtl").is_dir()


def test_build_cloud_sync_sources_empty_without_config(tmp_path: Path) -> None:
    cfg = load_config(tmp_path)
    assert build_cloud_sync_sources(cfg) == []


def test_reads_cheats_sync_section(tmp_path: Path) -> None:
    """MEJ-4: .cht sync config, same dir+remote pair pattern as ra_config."""
    (tmp_path / "config.toml").write_text(
        '[sync]\ncheats_dir = "C:/RetroArch/cheats"\ncheats_remote = "dropbox:/RetroSync/cheats"\n',
        encoding="utf-8",
    )
    cfg = load_config(tmp_path)
    assert cfg.sync.cheats_dir == "C:/RetroArch/cheats"
    assert cfg.sync.cheats_remote == "dropbox:/RetroSync/cheats"


def test_get_adb_sync_sources_excludes_duckstation(tmp_path: Path) -> None:
    """VAL-FIX-4: DuckStation memcards are unreachable via ADB (scoped storage,
    Android 11+, no root) — must be excluded like Dolphin, not retried forever."""
    (tmp_path / "config.toml").write_text(
        f'[library]\nlibrary_root = "{tmp_path.as_posix()}"\n', encoding="utf-8"
    )
    cfg = load_config(tmp_path)
    packages = {src["package"] for src in get_adb_sync_sources(cfg)}
    assert "com.github.stenzek.duckstation" not in packages
    assert "org.dolphinemu.dolphinemu" not in packages
    assert "xyz.aethersx2.android" in packages  # sanity: accessible ones still included


def test_get_adb_sync_sources_excludes_emuex_families_with_no_real_path(tmp_path: Path) -> None:
    """GBA-SAVE-PATH-1c: verificado en hardware real (RG556006101273) que
    GBA.emu/GBC.emu/NES.emu/MD.emu nunca escriben en su árbol EmuEx
    (files/EmuEx/ vacío pese a estar instalados) -- sus saves reales viven
    junto a las ROMs (SAVES-FRAGMENT-8), ya cubiertos por el Cable Sync de
    carpeta normal. Snes9x EX+ sí tiene datos reales confirmados, debe seguir
    incluido."""
    (tmp_path / "config.toml").write_text(
        f'[library]\nlibrary_root = "{tmp_path.as_posix()}"\n', encoding="utf-8"
    )
    cfg = load_config(tmp_path)
    packages = {src["package"] for src in get_adb_sync_sources(cfg)}
    assert "com.explusalpha.GbaEmu" not in packages
    assert "com.explusalpha.GbcEmu" not in packages
    assert "com.explusalpha.NesEmu" not in packages
    assert "com.explusalpha.MdEmu" not in packages
    assert "com.explusalpha.Snes9xPlus" in packages  # sanity: verified-working one stays


def test_resolve_tool_path_normalizes_slashes_on_windows() -> None:
    """VAL-FIX-3: CreateProcess rejects '/' in the executable path itself."""
    with patch.object(sys, "platform", "win32"):
        assert _resolve_tool_path("tools/adb.exe") == "tools\\adb.exe"
        assert _resolve_tool_path("C:/otro/adb.exe") == "C:\\otro\\adb.exe"


def test_resolve_tool_path_bare_command_and_non_windows_untouched() -> None:
    assert _resolve_tool_path("rclone") == "rclone"  # bare command → PATH lookup
    with patch.object(sys, "platform", "linux"):
        assert _resolve_tool_path("tools/adb") == "tools/adb"  # native separator already
