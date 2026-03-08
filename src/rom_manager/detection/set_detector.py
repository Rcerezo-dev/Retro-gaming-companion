from __future__ import annotations

from pathlib import Path


def detect_set_type(path: Path) -> str:
    extension = path.suffix.lower()
    if extension == ".cue":
        return "cue_sheet"
    if extension in {".bin", ".img", ".iso"}:
        return "disc_image"
    if extension in {".ccd", ".sub", ".mds", ".mdf"}:
        return "disc_auxiliary"
    if extension == ".pbp":
        return "packed_disc"
    if extension == ".ecm":
        return "compressed_disc_image"
    return "single_file"
