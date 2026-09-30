"""Business logic for scraping metadata/box art for a single game.

Extracted from ``web/handlers/scraper.py::_do_scrape_single`` (INBOX-METADATA-INLINE-1)
so the Inbox pipeline can reuse the exact same ScreenScraper lookup + apply path
used for a single game from Colección, instead of a second implementation. No web
``ctx`` here: callers pass plain inputs and get a result dict back.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository

_log = logging.getLogger(__name__)


def scrape_game_metadata(
    game_id: int,
    config: AppConfig,
    repository: LibraryRepository,
    *,
    preview: bool = False,
    download_images: bool = True,
    client: object | None = None,
) -> dict:
    """Look up *game_id* on ScreenScraper and, unless *preview*, apply the result.

    Same lookup order as the Colección single-game scrape: hash match first
    (crc32/md5/sha1), name fallback second.

    - ``preview=True`` (or no match found): returns the lookup dict, no DB
      writes, no image downloads.
    - ``preview=False``: also downloads images and upserts metadata, adding
      ``applied: True`` to the returned dict.

    *client* lets a caller processing many games in one batch (the Inbox
    organize loop) reuse a single ``ScreenScraperClient`` — its rate-limit
    throttle (``min_interval``) is per-instance, so a fresh client per call
    would silently skip it. Omit it for a one-off single-game call (a new
    client is built internally, same as before).

    Never raises — a failure (network, no credentials, no match) comes back
    as ``{"error": str}`` (or ``{"found": False, ...}``), so a caller
    processing many games can skip one and keep going without aborting the
    whole batch.
    """
    if not config.credentials.screenscraper_user:
        return {"error": "Credenciales de ScreenScraper no configuradas"}
    try:
        from rom_manager.scanner.rom_scanner import utc_now
        from rom_manager.scraper.platform_ids import get_system_id
        from rom_manager.scraper.screenscraper import ScreenScraperClient, download_image

        with repository.connect() as conn:
            row = conn.execute(
                "SELECT g.id, g.original_filename, g.source_path, g.platform, "
                "g.crc32, g.md5, g.sha1, g.size_bytes, g.canonical_title "
                "FROM games g WHERE g.id = ?",
                (int(game_id),),
            ).fetchone()
        if not row:
            return {"error": "Juego no encontrado"}
        game = dict(row)
        if client is None:
            client = ScreenScraperClient(
                user=config.credentials.screenscraper_user,
                password=config.credentials.screenscraper_pass,
                dev_id=config.credentials.screenscraper_dev_id,
                dev_password=config.credentials.screenscraper_dev_pass,
            )
        sys_id = get_system_id(game["platform"])
        result = client.search(
            crc32=game["crc32"],
            md5=game["md5"],
            sha1=game["sha1"],
            filename=game["original_filename"],
            size_bytes=game["size_bytes"],
            system_id=sys_id,
        )
        if result is None:
            name_hint = game.get("canonical_title") or game["original_filename"]
            result = client.search_by_name(name_hint, system_id=sys_id)
        # No dependencia de web.state aquí (esto es capa de servicio, sin UI) —
        # el caller HTTP decide qué hacer con la cuota si le importa.
        last_quota = client.last_quota or None
        if result is None:
            return {
                "found": False,
                "error": "No encontrado en ScreenScraper",
                "last_quota": last_quota,
            }

        preview_data = {
            "found": True,
            "ss_game_id": result.ss_game_id,
            "title": result.title,
            "year": result.year,
            "genre": result.genre,
            "publisher": result.publisher,
            "developer": result.developer,
            "description": result.description,
            "rating": result.rating,
            "box_art_url": result.box_art_url,
            "last_quota": last_quota,
        }
        if preview:
            return preview_data

        box_art_path = screenshot_path = wheel_path = ""
        if download_images:
            src_parent = Path(game["source_path"]).parent
            stem = Path(game["original_filename"]).stem
            if result.box_art_url:
                ext = ".png" if ".png" in result.box_art_url.lower() else ".jpg"
                dest = src_parent / "media" / "images" / f"{stem}{ext}"
                download_image(result.box_art_url, dest)
                box_art_path = str(dest)
            if result.screenshot_url:
                ext = ".png" if ".png" in result.screenshot_url.lower() else ".jpg"
                dest = src_parent / "media" / "screenshots" / f"{stem}{ext}"
                try:
                    download_image(result.screenshot_url, dest)
                    screenshot_path = str(dest)
                except Exception:
                    _log.warning(
                        "Descarga de captura falló: %s", result.screenshot_url, exc_info=True
                    )
            if result.wheel_url:
                ext = ".png" if ".png" in result.wheel_url.lower() else ".jpg"
                dest = src_parent / "media" / "wheels" / f"{stem}{ext}"
                try:
                    download_image(result.wheel_url, dest)
                    wheel_path = str(dest)
                except Exception:
                    _log.warning("Descarga de wheel falló: %s", result.wheel_url, exc_info=True)

        with repository.batch() as bconn:
            repository.upsert_metadata(
                game_id=int(game_id),
                ss_game_id=result.ss_game_id,
                title=result.title,
                year=result.year,
                genre=result.genre,
                publisher=result.publisher,
                developer=result.developer,
                description=result.description,
                rating=result.rating,
                box_art_url=result.box_art_url,
                box_art_path=box_art_path,
                screenshot_path=screenshot_path,
                wheel_path=wheel_path,
                genres_list=result.genres_list,
                players=result.players,
                scraped_at=utc_now(),
                connection=bconn,
            )
            repository.mark_metadata_scraped(int(game_id), bconn)
        return {**preview_data, "applied": True}
    except Exception as exc:
        _log.warning("Scrape de game_id=%s falló (no fatal)", game_id, exc_info=True)
        return {"error": str(exc)}
