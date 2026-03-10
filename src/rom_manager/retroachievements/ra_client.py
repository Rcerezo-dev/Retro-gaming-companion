from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

_RA_BASE = "https://retroachievements.org/API"
_CACHE_TTL_SECONDS = 7 * 24 * 3600  # 1 week


@dataclass(slots=True)
class RAGame:
    id: int
    title: str
    achievements: int
    leaderboards: int
    points: int
    hashes: list[str] = field(default_factory=list)  # MD5 hashes, lowercase


def fetch_hash_library(
    console_id: int,
    api_key: str,
    *,
    cache_dir: Path | None = None,
) -> dict[str, RAGame]:
    """Fetch all games with achievements for *console_id* and return MD5 → RAGame.

    Results are cached to *cache_dir* (if given) for one week.
    """
    cache_file: Path | None = None
    if cache_dir:
        cache_file = cache_dir / f"ra_hashes_{console_id}.json"
        if cache_file.exists():
            age = time.time() - cache_file.stat().st_mtime
            if age < _CACHE_TTL_SECONDS:
                data = json.loads(cache_file.read_text(encoding="utf-8"))
                return _parse_game_list(data)

    url = f"{_RA_BASE}/API_GetGameList.php?i={console_id}&h=1&f=1&y={api_key}"
    req = urllib.request.Request(url, headers={"User-Agent": "ROMManagerLocal/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    data = json.loads(raw)

    if cache_dir and cache_file:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(data), encoding="utf-8")

    return _parse_game_list(data)


def _parse_game_list(data: list[dict]) -> dict[str, RAGame]:
    """Parse the API response into a MD5 → RAGame mapping."""
    result: dict[str, RAGame] = {}
    if not isinstance(data, list):
        return result
    for entry in data:
        if not isinstance(entry, dict):
            continue
        game_id = entry.get("ID") or entry.get("GameID")
        if not game_id:
            continue
        hashes_raw = entry.get("Hashes") or []
        hashes = [h.lower() for h in hashes_raw if isinstance(h, str)]
        game = RAGame(
            id=int(game_id),
            title=entry.get("Title", ""),
            achievements=int(entry.get("NumAchievements", 0) or 0),
            leaderboards=int(entry.get("NumLeaderboards", 0) or 0),
            points=int(entry.get("Points", 0) or 0),
            hashes=hashes,
        )
        for h in hashes:
            result[h] = game
    return result
