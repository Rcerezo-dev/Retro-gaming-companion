from __future__ import annotations

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


def load_config(project_root: Path | None = None) -> AppConfig:
    root = (project_root or Path.cwd()).resolve()
    data_dir = root / ".rommgr"
    logs_dir = data_dir / "logs"
    database_path = data_dir / "library.sqlite"
    catalogs_dir = data_dir / "catalogs"
    return AppConfig(
        project_root=root,
        data_dir=data_dir,
        database_path=database_path,
        logs_dir=logs_dir,
        catalogs_nointro_dir=catalogs_dir / "nointro",
        catalogs_redump_dir=catalogs_dir / "redump",
        excluded_directories=(
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
