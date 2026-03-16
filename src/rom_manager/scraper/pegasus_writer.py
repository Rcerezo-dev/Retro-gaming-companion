from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rom_manager.database.repository import LibraryRepository


def write_pegasus_metadata(
    library_root: Path,
    repository: "LibraryRepository",
    output_dir: Path | None = None,
) -> dict[str, int]:
    """Write Pegasus Metadata Format files (metadata.pegasus.txt) per platform.

    Returns {"platforms": N, "games": M}.
    """
    output_dir = output_dir or library_root
    with repository.connect() as conn:
        rows = conn.execute(
            """
            SELECT g.id, g.original_filename, g.source_path, g.platform,
                   g.canonical_title, g.region, g.extension,
                   m.title, m.year, m.genre, m.developer, m.publisher,
                   m.description, m.box_art_path
            FROM games g
            LEFT JOIN game_metadata m ON m.game_id = g.id
            WHERE g.file_type = 'rom' AND g.canonical_title IS NOT NULL
            ORDER BY g.platform, g.canonical_title
            """
        ).fetchall()

    # Group by platform
    by_platform: dict[str, list] = {}
    for row in rows:
        plat = row["platform"] or "Unknown"
        by_platform.setdefault(plat, []).append(row)

    games_written = 0
    for platform, games in by_platform.items():
        plat_dir = library_root / platform
        out_path = plat_dir / "metadata.pegasus.txt"
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            lines: list[str] = [
                f"collection: {platform}\n",
                f"shortname: {platform.lower().replace(' ', '')}\n",
                "\n",
            ]
            for g in games:
                title = g["canonical_title"] or g["original_filename"]
                rel = Path(g["source_path"]).name
                lines.append(f"game: {title}\n")
                lines.append(f"file: {rel}\n")
                if g["year"]:
                    lines.append(f"release: {g['year']}\n")
                if g["genre"]:
                    lines.append(f"genre: {g['genre']}\n")
                if g["developer"]:
                    lines.append(f"developer: {g['developer']}\n")
                if g["publisher"]:
                    lines.append(f"publisher: {g['publisher']}\n")
                if g["description"]:
                    desc = g["description"].replace("\n", " ")
                    lines.append(f"description: {desc}\n")
                if g["box_art_path"]:
                    try:
                        art_rel = Path(g["box_art_path"]).relative_to(plat_dir)
                        lines.append(f"assets.boxFront: {art_rel.as_posix()}\n")
                    except ValueError:
                        pass
                lines.append("\n")
            out_path.write_text("".join(lines), encoding="utf-8")
            games_written += len(games)
        except OSError:
            pass

    return {"platforms": len(by_platform), "games": games_written}
