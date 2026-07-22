from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

from rom_manager.config import _resolve_tool_path, load_config


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


def test_resolve_tool_path_normalizes_slashes_on_windows() -> None:
    """VAL-FIX-3: CreateProcess rejects '/' in the executable path itself."""
    with patch.object(sys, "platform", "win32"):
        assert _resolve_tool_path("tools/adb.exe") == "tools\\adb.exe"
        assert _resolve_tool_path("C:/otro/adb.exe") == "C:\\otro\\adb.exe"


def test_resolve_tool_path_bare_command_and_non_windows_untouched() -> None:
    assert _resolve_tool_path("rclone") == "rclone"  # bare command → PATH lookup
    with patch.object(sys, "platform", "linux"):
        assert _resolve_tool_path("tools/adb") == "tools/adb"  # native separator already
