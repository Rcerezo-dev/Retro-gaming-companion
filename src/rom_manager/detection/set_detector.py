from __future__ import annotations

from pathlib import Path


def detect_set_type(path: Path) -> str:
    extension = path.suffix.lower()
    if extension == ".cue":
        # B6-2: if a .chd sibling exists, this .cue is superseded — hide it
        if path.with_suffix(".chd").exists():
            return "disc_auxiliary"
        return "cue_sheet"
    if extension in {".bin", ".img"}:
        return "disc_image"
    if extension == ".iso":
        # Standalone .iso (PS2, Dreamcast, etc.) is a valid game file.
        # Only treat as disc_image if a .cue with the same stem references it.
        if path.with_suffix(".cue").exists():
            return "disc_image"
        return "single_file"
    if extension in {".ccd", ".sub", ".mds", ".mdf"}:
        return "disc_auxiliary"
    if extension == ".pbp":
        return "packed_disc"
    if extension == ".ecm":
        return "compressed_disc_image"
    return "single_file"
