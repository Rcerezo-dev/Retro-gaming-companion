from __future__ import annotations

from pathlib import Path

from rom_manager.config import load_config


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
    assert cfg.adb == "C:/otro/adb.exe"


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
    assert cfg.rclone_binary == "/usr/bin/rclone"


def test_reads_tools_section(tmp_path: Path) -> None:
    (tmp_path / "config.toml").write_text(
        '[tools]\nchdman = "C:/tools/chdman.exe"\n', encoding="utf-8"
    )
    cfg = load_config(tmp_path)
    assert cfg.chdman == "C:/tools/chdman.exe"


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
