from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from rom_manager.config import AppConfig
from rom_manager.detection.platform_detector import is_rom_file


class FileCategory(StrEnum):
    ROM = "rom"
    SAVE = "save"
    FRONTEND_ASSET = "frontend_asset"
    SYSTEM_SUPPORT = "system_support"
    UNKNOWN = "unknown"


def classify_path(path: Path, config: AppConfig, source_root: Path | None = None) -> FileCategory:
    if _is_in_excluded_directory(path, config, source_root):
        return FileCategory.SYSTEM_SUPPORT

    extension = path.suffix.lower()
    if is_rom_file(path):
        return FileCategory.ROM
    if extension in config.save_extensions:
        return FileCategory.SAVE
    if extension in config.frontend_asset_extensions or path.name.lower() == "gamelist.xml":
        return FileCategory.FRONTEND_ASSET
    return FileCategory.UNKNOWN


def _is_in_excluded_directory(
    path: Path,
    config: AppConfig,
    source_root: Path | None,
) -> bool:
    relative_parts = _relevant_parts(path, source_root)
    names = {part.casefold() for part in relative_parts}
    return any(excluded.casefold() in names for excluded in config.excluded_directories)


def _relevant_parts(path: Path, source_root: Path | None) -> tuple[str, ...]:
    if source_root is None:
        return path.parts

    try:
        relative = path.resolve().relative_to(source_root.resolve())
    except ValueError:
        return path.parts
    return relative.parts
