from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


def write_gamelist(
    platform_dir: Path,
    entries: list[dict],
    *,
    media_subdir: str = "media/images",
    es_config_dir: Path | None = None,
) -> Path:
    """Generate a gamelist.xml in *platform_dir* for EmulationStation / ES-DE.

    Each entry in *entries* is a dict with keys:
        filename, title, year, genre, publisher, developer,
        description, rating, box_art_path (local path or empty)

    Always writes ``platform_dir/gamelist.xml`` with paths relative to the ROM dir.
    If *es_config_dir* is given (e.g. ~/.emulationstation/gamelists/{system}/),
    also writes a copy there using absolute paths — required for classic EmulationStation
    which looks for gamelists outside the ROM directory.

    Returns the path to the primary written file (alongside ROMs).
    """

    def _build_tree(use_absolute: bool) -> ET.ElementTree:
        root = ET.Element("gameList")
        for entry in entries:
            game_el = ET.SubElement(root, "game")

            rom_path = platform_dir / entry["filename"]
            _sub(game_el, "path", str(rom_path) if use_absolute else f"./{entry['filename']}")
            _sub(game_el, "name", entry.get("title") or _stem(entry["filename"]))

            if entry.get("description"):
                _sub(game_el, "desc", entry["description"])

            box_art = entry.get("box_art_path", "")
            if box_art:
                if use_absolute:
                    _sub(game_el, "image", str(Path(box_art).resolve()))
                else:
                    try:
                        rel = Path(box_art).relative_to(platform_dir)
                        _sub(game_el, "image", f"./{rel.as_posix()}")
                    except ValueError:
                        _sub(game_el, "image", box_art)

            if entry.get("rating"):
                try:
                    rating_norm = float(entry["rating"]) / 20.0  # SS uses 0–20 scale
                    _sub(game_el, "rating", f"{rating_norm:.2f}")
                except (ValueError, TypeError):
                    pass

            if entry.get("year"):
                _sub(game_el, "releasedate", f"{entry['year']}0101T000000")

            if entry.get("developer"):
                _sub(game_el, "developer", entry["developer"])
            if entry.get("publisher"):
                _sub(game_el, "publisher", entry["publisher"])
            if entry.get("genre"):
                _sub(game_el, "genre", entry["genre"])

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        return tree

    # Primary gamelist alongside ROMs (relative paths — ES-DE, Pegasus)
    out_path = platform_dir / "gamelist.xml"
    _build_tree(use_absolute=False).write(out_path, encoding="utf-8", xml_declaration=True)

    # Secondary gamelist in ES config dir (absolute paths — classic EmulationStation)
    if es_config_dir is not None:
        es_config_dir.mkdir(parents=True, exist_ok=True)
        es_out = es_config_dir / "gamelist.xml"
        _build_tree(use_absolute=True).write(es_out, encoding="utf-8", xml_declaration=True)

    return out_path


def _sub(parent: ET.Element, tag: str, text: str) -> ET.Element:
    el = ET.SubElement(parent, tag)
    el.text = text
    return el


def _stem(filename: str) -> str:
    return Path(filename).stem
