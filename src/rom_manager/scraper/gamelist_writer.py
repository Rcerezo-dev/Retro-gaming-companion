from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

_DISC_RE = re.compile(r"\(Dis[ck]\s*(\d+)\)", re.IGNORECASE)

# Priority order when deduplicating entries with the same scraped title.
# Lower index = higher priority.
_EXT_PRIORITY: dict[str, int] = {
    ".m3u": 0,  # playlist covers all discs → always preferred
    ".chd": 1,  # converted disc image (single file, clean)
    ".pbp": 2,  # PSP packed disc
    ".cue": 3,  # cue sheet (valid, but inferior to m3u/chd)
    ".gdi": 4,
    ".iso": 5,
}
_EXT_PRIORITY_DEFAULT = 10


def write_gamelist(
    platform_dir: Path,
    entries: list[dict],
    *,
    media_subdir: str = "media/images",
    es_config_dir: Path | None = None,
) -> Path:
    """Genera gamelist.xml en *platform_dir* para EmulationStation / ES-DE.

    Cada entrada en *entries* es un dict con las claves:
        filename, source_path (opcional), title, year, genre, publisher, developer,
        description, rating, box_art_path, screenshot_path, wheel_path

    Siempre escribe ``platform_dir/gamelist.xml`` con rutas relativas al dir de ROMs.
    Si *es_config_dir* se proporciona, también escribe una copia con rutas absolutas.

    Correcciones aplicadas:
    - **Subcarpetas de disco** (PSX/Saturn): si *source_path* está disponible, la
      ruta relativa se calcula a partir de él en lugar de usar solo *filename*.
      Esto evita que ES-DE muestre la carpeta como ítem navegable en vez del juego.
    - **Deduplicación**: si dos entradas tienen el mismo título scrapeado, se conserva
      solo la de mayor prioridad (.m3u > .chd > .pbp > .cue …). Evita que aparezcan
      tanto el .m3u como los .cue individuales de un set multi-disco.

    Devuelve la ruta al archivo principal generado (junto a los ROMs).
    """
    deduped = _deduplicate(entries)

    def _rom_rel(entry: dict) -> str:
        """Ruta relativa del ROM respecto a platform_dir, con soporte para subcarpetas."""
        src = entry.get("source_path", "")
        if src:
            try:
                rel = Path(src).relative_to(platform_dir)
                return rel.as_posix()
            except ValueError:
                pass
        return entry["filename"]

    def _media_path(path_str: str, use_absolute: bool) -> str:
        if not path_str:
            return ""
        if use_absolute:
            return str(Path(path_str).resolve())
        try:
            rel = Path(path_str).relative_to(platform_dir)
            return f"./{rel.as_posix()}"
        except ValueError:
            return path_str

    def _build_tree(use_absolute: bool) -> ET.ElementTree:
        root_el = ET.Element("gameList")
        for entry in deduped:
            game_el = ET.SubElement(root_el, "game")

            rel = _rom_rel(entry)
            path_val = str(platform_dir / rel) if use_absolute else f"./{rel}"
            _sub(game_el, "path", path_val)

            title = entry.get("title") or _stem(entry["filename"])
            m = _DISC_RE.search(entry["filename"])
            if m and f"Disc {m.group(1)}" not in title and f"Disk {m.group(1)}" not in title:
                title = f"{title} (Disc {m.group(1)})"
            _sub(game_el, "name", title)

            if entry.get("description"):
                _sub(game_el, "desc", entry["description"])

            _img = _media_path(entry.get("box_art_path", ""), use_absolute)
            if _img:
                _sub(game_el, "image", _img)

            _wheel = _media_path(entry.get("wheel_path", ""), use_absolute)
            if _wheel:
                _sub(game_el, "thumbnail", _wheel)
                _sub(game_el, "marquee", _wheel)

            _shot = _media_path(entry.get("screenshot_path", ""), use_absolute)
            if _shot:
                _sub(game_el, "screenshot", _shot)

            if entry.get("rating"):
                try:
                    rating_norm = float(entry["rating"]) / 20.0
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

        tree = ET.ElementTree(root_el)
        ET.indent(tree, space="  ")
        return tree

    out_path = platform_dir / "gamelist.xml"
    _build_tree(use_absolute=False).write(out_path, encoding="utf-8", xml_declaration=True)

    if es_config_dir is not None:
        es_config_dir.mkdir(parents=True, exist_ok=True)
        es_out = es_config_dir / "gamelist.xml"
        _build_tree(use_absolute=True).write(es_out, encoding="utf-8", xml_declaration=True)

    return out_path


def _best(candidates: list[dict]) -> dict:
    """Highest-priority entry by extension (.m3u > .chd > .pbp > .cue …)."""
    return min(
        candidates,
        key=lambda e: _EXT_PRIORITY.get(Path(e["filename"]).suffix.lower(), _EXT_PRIORITY_DEFAULT),
    )


def _deduplicate(entries: list[dict]) -> list[dict]:
    """Devuelve una lista deduplicada por título scrapeado.

    Dos niveles de colapso, ambos solo dentro del mismo título:
    - Si hay un .m3u (playlist que cubre todo el set), gana él solo —
      colapsa TODOS los discos individuales del set en una sola entrada.
    - Si no hay .m3u, se deduplica por número de disco (extraído del
      nombre de archivo): dos representaciones del *mismo* disco colapsan
      (mayor prioridad de extensión gana), pero discos *distintos* del
      mismo set (Disc 1, Disc 2, …) se mantienen como entradas separadas.
    """
    groups: dict[str, list[dict]] = {}
    for entry in entries:
        title_key = (entry.get("title") or _stem(entry["filename"])).lower().strip()
        groups.setdefault(title_key, []).append(entry)

    result: list[dict] = []
    for group in groups.values():
        m3u_entries = [e for e in group if Path(e["filename"]).suffix.lower() == ".m3u"]
        if m3u_entries:
            result.append(_best(m3u_entries))
            continue

        by_disc: dict[str | None, list[dict]] = {}
        for entry in group:
            m = _DISC_RE.search(entry["filename"])
            disc_num = m.group(1) if m else None
            by_disc.setdefault(disc_num, []).append(entry)
        for disc_group in by_disc.values():
            result.append(_best(disc_group))
    return result


def _sub(parent: ET.Element, tag: str, text: str) -> ET.Element:
    el = ET.SubElement(parent, tag)
    el.text = text
    return el


def _stem(filename: str) -> str:
    return Path(filename).stem
