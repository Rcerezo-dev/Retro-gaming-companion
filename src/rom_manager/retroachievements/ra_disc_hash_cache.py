"""File-backed cache for disc-image RA hashes (PS1, GameCube, Wii).

Computing one requires decompressing a whole .chd via ``chdman`` (~7s each)
or scanning a raw .bin/.cue/.iso -- recomputing on every RA check / duplicates
review would make both features unusably slow. Keyed by
(source_path, mtime_ns, size), same signature pattern already used by
``load_arcade_crc_index`` (catalog/mame_loader.py) -- a re-ripped/replaced
file at the same path invalidates its own cache entry automatically.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from rom_manager.retroachievements.ra_hash_gamecube_wii import (
    compute_gamecube_ra_hash,
    compute_wii_ra_hash,
)
from rom_manager.retroachievements.ra_hash_psx import compute_psx_ra_hash

_logger = logging.getLogger(__name__)

_CACHE_FILENAME = "psx_disc_hashes.json"
_GAMECUBE_WII_CACHE_FILENAME = "gamecube_wii_disc_hashes.json"


def _cache_path(cache_dir: Path, filename: str = _CACHE_FILENAME) -> Path:
    return cache_dir / filename


def _load(cache_dir: Path, filename: str = _CACHE_FILENAME) -> dict[str, dict[str, str]]:
    p = _cache_path(cache_dir, filename)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _logger.warning("Caché de hashes de disco corrupta o ilegible: %s", p, exc_info=True)
        return {}


def _save(
    cache_dir: Path, data: dict[str, dict[str, str]], filename: str = _CACHE_FILENAME
) -> None:
    p = _cache_path(cache_dir, filename)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data), encoding="utf-8")


def get_psx_disc_hash(source_path: str, cache_dir: Path, chdman_path: Path | None) -> str | None:
    """RA-compatible MD5 for a PS1 disc image at *source_path*, cached by
    (mtime, size). Returns None if the file is missing or the format/content
    isn't supported yet (see ``ra_hash_psx.compute_psx_ra_hash``) -- a miss
    is cached too, so an unsupported file isn't retried every call."""
    p = Path(source_path)
    try:
        st = p.stat()
    except OSError:
        return None
    sig = f"{st.st_mtime_ns}:{st.st_size}"

    cache = _load(cache_dir)
    entry = cache.get(source_path)
    if entry and entry.get("sig") == sig:
        return entry.get("hash") or None

    computed = compute_psx_ra_hash(p, chdman_path=chdman_path)
    cache[source_path] = {"sig": sig, "hash": computed or ""}
    _save(cache_dir, cache)
    return computed


_GAMECUBE_RA_CONSOLE_ID = 16
_WII_RA_CONSOLE_ID = 20


def get_gamecube_wii_disc_hash(source_path: str, cache_dir: Path, console_id: int) -> str | None:
    """RA-compatible MD5 for a raw GameCube/Wii disc image at *source_path*,
    cached by (mtime, size). *console_id* picks the algorithm (RA's own IDs:
    16=GameCube, 20=Wii -- see ``ra_hash_gamecube_wii.py``), same convention
    ``ra_checker._DISC_HASH_CONSOLE_IDS`` already keys by. Returns None if the
    file is missing, *console_id* isn't one of the two, or the format/content
    isn't a raw disc image this module can hash yet (e.g. ``.rvz``) -- a miss
    is cached too, so an unsupported file isn't retried every call."""
    p = Path(source_path)
    try:
        st = p.stat()
    except OSError:
        return None
    sig = f"{st.st_mtime_ns}:{st.st_size}"

    cache = _load(cache_dir, _GAMECUBE_WII_CACHE_FILENAME)
    entry = cache.get(source_path)
    if entry and entry.get("sig") == sig:
        return entry.get("hash") or None

    if console_id == _GAMECUBE_RA_CONSOLE_ID:
        computed = compute_gamecube_ra_hash(p)
    elif console_id == _WII_RA_CONSOLE_ID:
        computed = compute_wii_ra_hash(p)
    else:
        computed = None
    cache[source_path] = {"sig": sig, "hash": computed or ""}
    _save(cache_dir, cache, _GAMECUBE_WII_CACHE_FILENAME)
    return computed
