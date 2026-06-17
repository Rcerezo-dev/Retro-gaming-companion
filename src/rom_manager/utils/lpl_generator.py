from __future__ import annotations

import json
from pathlib import Path

# RetroArch playlist format reference:
# https://docs.libretro.com/guides/roms-playlists-thumbnails/
# Each platform gets a <Platform Name>.lpl file that RetroArch reads directly.

_DEFAULT_CORE = "DETECT"


def _platform_db_name(platform: str) -> str:
    """Return the canonical RetroArch db_name for a platform (e.g. 'Sony - PlayStation.lpl')."""
    # Best-effort mapping — covers the most common platforms
    _MAP = {
        "Game Boy Advance": "Nintendo - Game Boy Advance",
        "Game Boy Color": "Nintendo - Game Boy Color",
        "Game Boy": "Nintendo - Game Boy",
        "Nintendo DS": "Nintendo - Nintendo DS",
        "Nintendo 3DS": "Nintendo - Nintendo 3DS",
        "NES": "Nintendo - Nintendo Entertainment System",
        "SNES": "Nintendo - Super Nintendo Entertainment System",
        "Nintendo 64": "Nintendo - Nintendo 64",
        "GameCube": "Nintendo - GameCube",
        "Wii": "Nintendo - Wii",
        "PlayStation": "Sony - PlayStation",
        "PlayStation 2": "Sony - PlayStation 2",
        "PSP": "Sony - PlayStation Portable",
        "Sega Mega Drive": "Sega - Mega Drive - Genesis",
        "Sega Genesis": "Sega - Mega Drive - Genesis",
        "Sega Master System": "Sega - Master System - Mark III",
        "Game Gear": "Sega - Game Gear",
        "Sega Saturn": "Sega - Saturn",
        "Dreamcast": "Sega - Dreamcast",
        "Sega CD": "Sega - Mega-CD",
        "Atari 2600": "Atari - 2600",
        "GBA": "Nintendo - Game Boy Advance",
        "GBC": "Nintendo - Game Boy Color",
        "GB": "Nintendo - Game Boy",
        "NDS": "Nintendo - Nintendo DS",
        "PSX": "Sony - PlayStation",
        "PS2": "Sony - PlayStation 2",
        "N64": "Nintendo - Nintendo 64",
        "MD": "Sega - Mega Drive - Genesis",
        "SMS": "Sega - Master System - Mark III",
        "GG": "Sega - Game Gear",
    }
    return _MAP.get(platform, platform)


def generate_lpl_playlists(
    library_root: Path,
    repository,
    *,
    output_dir: Path | None = None,
) -> dict:
    """Generate RetroArch .lpl playlist files, one per platform.

    Files are written to *output_dir* (defaults to library_root/.rommgr/playlists/).
    Returns {"platforms": N, "games": N, "output_dir": str}.
    """
    if output_dir is None:
        output_dir = library_root / ".rommgr" / "playlists"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Fetch all ROMs from the repository grouped by platform
    with repository.connect() as conn:
        rows = conn.execute(
            """
            SELECT platform, source_path, canonical_title, original_filename
            FROM games
            WHERE file_type = 'rom'
              AND platform IS NOT NULL
              AND (set_type IS NULL OR set_type NOT IN ('disc_image', 'disc_auxiliary'))
            ORDER BY platform, canonical_title, original_filename
            """
        ).fetchall()

    # Group by platform
    by_platform: dict[str, list[dict]] = {}
    for row in rows:
        plat = row["platform"] or "Unknown"
        by_platform.setdefault(plat, []).append(dict(row))

    total_games = 0
    for platform, games in by_platform.items():
        db_name = _platform_db_name(platform) + ".lpl"
        items = []
        for game in games:
            label = game["canonical_title"] or Path(game["original_filename"]).stem
            items.append({
                "path": game["source_path"],
                "label": label,
                "core_path": _DEFAULT_CORE,
                "core_name": _DEFAULT_CORE,
                "crc32": "",
                "db_name": db_name,
            })

        playlist = {
            "version": "1.4",
            "default_core_path": "",
            "default_core_name": "",
            "label_display_mode": 0,
            "right_thumbnail_mode": 0,
            "left_thumbnail_mode": 0,
            "sort_mode": 0,
            "items": items,
        }
        safe_name = platform.replace("/", "_").replace("\\", "_")
        lpl_path = output_dir / f"{safe_name}.lpl"
        lpl_path.write_text(json.dumps(playlist, indent=2, ensure_ascii=False), encoding="utf-8")
        total_games += len(items)

    return {
        "platforms": len(by_platform),
        "games": total_games,
        "output_dir": str(output_dir),
    }
