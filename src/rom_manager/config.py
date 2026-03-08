from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AppConfig:
    project_root: Path
    data_dir: Path
    database_path: Path
    logs_dir: Path
    catalogs_nointro_dir: Path
    catalogs_redump_dir: Path
    excluded_directories: tuple[str, ...]
    frontend_asset_extensions: tuple[str, ...]
    save_extensions: tuple[str, ...]
    # From config.toml (optional)
    saves_dir: Path | None
    rclone_remote: str
    rclone_binary: str
    chdman: str
    web_host: str
    web_port: int


_CONFIG_TOML_TEMPLATE = """\
# ROM Manager Local — user configuration
# Place this file at the root of your project folder (next to .rommgr/).
# All settings are optional; hardcoded defaults are used when omitted.

[library]
# Folder where your save files are stored on this PC.
# Used by 'rommgr sync-saves' and 'rommgr sync-status'.
# saves_dir = "D:/RetroArch/saves"

[sync]
# rclone remote path, e.g. "dropbox:/RetroArch/saves"
# remote = "dropbox:/RetroArch/saves"
# Path to the rclone binary (default: "rclone", assumes it is in PATH)
rclone = "rclone"

[tools]
# Path to the chdman binary (default: "chdman", assumes it is in PATH)
chdman = "chdman"

[web]
host = "127.0.0.1"
port = 7777
"""


def load_config(project_root: Path | None = None) -> AppConfig:
    root = (project_root or Path.cwd()).resolve()
    data_dir = root / ".rommgr"
    logs_dir = data_dir / "logs"
    database_path = data_dir / "library.sqlite"
    catalogs_dir = data_dir / "catalogs"

    toml: dict = {}
    toml_path = root / "config.toml"
    if toml_path.exists():
        with open(toml_path, "rb") as fh:
            toml = tomllib.load(fh)

    lib = toml.get("library", {})
    sync = toml.get("sync", {})
    tools = toml.get("tools", {})
    web = toml.get("web", {})

    saves_dir_raw = lib.get("saves_dir")
    saves_dir = Path(saves_dir_raw) if saves_dir_raw else None

    return AppConfig(
        project_root=root,
        data_dir=data_dir,
        database_path=database_path,
        logs_dir=logs_dir,
        catalogs_nointro_dir=catalogs_dir / "nointro",
        catalogs_redump_dir=catalogs_dir / "redump",
        saves_dir=saves_dir,
        rclone_remote=sync.get("remote", ""),
        rclone_binary=sync.get("rclone", "rclone"),
        chdman=tools.get("chdman", "chdman"),
        web_host=web.get("host", "127.0.0.1"),
        web_port=int(web.get("port", 7777)),
        excluded_directories=(  # noqa: E501
            "Android",
            "BIOS",
            "DCIM",
            "Documents",
            "Movies",
            "Music",
            "Notifications",
            "System Volume Information",
            "backup",
            "recovery_log",
        ),
        frontend_asset_extensions=(
            ".png",
            ".jpg",
            ".jpeg",
            ".mp4",
            ".xml",
        ),
        save_extensions=(
            ".sav",
            ".srm",
            ".state",
            ".st0",
            ".st1",
            ".st2",
            ".st3",
            ".st4",
            ".st5",
            ".fcs",
            ".dsv",
            ".sps",
            ".psv",
            ".mcr",
            ".mem",
            ".vmp",
            ".eep",
            ".fla",
            ".sra",
            ".dat",
            ".sgm",
            ".brm",
            ".nv",
            ".hi",
            ".fs",
            ".state1",
            ".state2",
        ),
    )
