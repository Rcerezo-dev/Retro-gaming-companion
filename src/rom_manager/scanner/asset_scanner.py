from __future__ import annotations

from pathlib import Path

from rom_manager.detection.platform_detector import detect_platform


def inspect_asset(path: Path) -> tuple[str | None, str]:
    asset_type = (
        "gamelist" if path.name.lower() == "gamelist.xml" else path.suffix.lower().lstrip(".")
    )
    return detect_platform(path), asset_type
