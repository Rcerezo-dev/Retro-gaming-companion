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
    library_root: Path | None   # root of the ROM+saves library on this PC
    rclone_remote: str
    rclone_binary: str
    chdman: str
    web_host: str
    web_port: int
    screenscraper_user: str
    screenscraper_pass: str
    screenscraper_dev_id: str
    screenscraper_dev_pass: str
    ra_api_key: str


_CONFIG_TOML_TEMPLATE = """\
# ROM Manager Local — user configuration
# Place this file at the root of your project folder (next to .rommgr/).
# All settings are optional; hardcoded defaults are used when omitted.

[library]
# Root folder of your ROM library on this PC.
# Save files (.sav, .srm, .state, etc.) are expected to live alongside the ROMs.
# Used by 'rommgr sync-saves' and 'rommgr sync-status'.
# library_root = "E:/ROMs"

[sync]
# rclone remote path where saves will be mirrored in the cloud.
# The folder structure under library_root is preserved, but only save files are synced.
# remote = "dropbox:/RetroSync/saves"
# Path to the rclone binary (default: "rclone", assumes it is in PATH)
rclone = "rclone"

[screenscraper]
# Your ScreenScraper.fr account credentials (free registration at screenscraper.fr)
# user = "your_username"
# pass = "your_password"

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
    ss = toml.get("screenscraper", {})
    ra = toml.get("retroachievements", {})

    library_root_raw = lib.get("library_root")
    library_root = Path(library_root_raw) if library_root_raw else None

    return AppConfig(
        project_root=root,
        data_dir=data_dir,
        database_path=database_path,
        logs_dir=logs_dir,
        catalogs_nointro_dir=catalogs_dir / "nointro",
        catalogs_redump_dir=catalogs_dir / "redump",
        library_root=library_root,
        rclone_remote=sync.get("remote", ""),
        rclone_binary=sync.get("rclone", "rclone"),
        chdman=tools.get("chdman", "chdman"),
        web_host=web.get("host", "127.0.0.1"),
        web_port=int(web.get("port", 7777)),
        screenscraper_user=ss.get("user", ""),
        screenscraper_pass=ss.get("pass", ""),
        screenscraper_dev_id=ss.get("dev_id", ""),
        screenscraper_dev_pass=ss.get("dev_pass", ""),
        ra_api_key=ra.get("api_key", ""),
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
            ".brmc",
            ".ml1",
        ),
    )


def write_config_toml(project_root: Path, updates: dict) -> None:
    """Write (or update) config.toml with the given key→value pairs.

    *updates* is a flat dict of dotted keys, e.g.::

        {"library.library_root": "E:/ROMs", "sync.remote": "dropbox:/RetroSync/saves"}

    Sections/keys not present in *updates* are preserved as-is.
    """
    toml_path = project_root / "config.toml"

    # Read existing content (or empty dict)
    existing: dict = {}
    if toml_path.exists():
        with open(toml_path, "rb") as fh:
            existing = tomllib.load(fh)

    # Apply updates
    for dotted_key, value in updates.items():
        parts = dotted_key.split(".", 1)
        if len(parts) == 2:
            section, key = parts
            existing.setdefault(section, {})[key] = value
        else:
            existing[dotted_key] = value

    # Serialise back to TOML (simple writer — no comment preservation)
    lines: list[str] = ["# ROM Manager Local — user configuration\n"]
    for section, contents in existing.items():
        if isinstance(contents, dict):
            lines.append(f"\n[{section}]\n")
            for k, v in contents.items():
                if v is None or v == "":
                    lines.append(f"# {k} = \"\"\n")
                elif isinstance(v, bool):
                    lines.append(f"{k} = {'true' if v else 'false'}\n")
                elif isinstance(v, int):
                    lines.append(f"{k} = {v}\n")
                else:
                    escaped = str(v).replace("\\", "\\\\").replace('"', '\\"')
                    lines.append(f'{k} = "{escaped}"\n')
        else:
            if contents is None or contents == "":
                lines.append(f"# {section} = \"\"\n")
            else:
                escaped = str(contents).replace("\\", "\\\\").replace('"', '\\"')
                lines.append(f'{section} = "{escaped}"\n')

    toml_path.write_text("".join(lines), encoding="utf-8")
