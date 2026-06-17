from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import types

    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.jobs.manager import JobManager
    from rom_manager.web.router import Router


# ── Public entry point ────────────────────────────────────────────────────────

def register(
    router: Router,
    *,
    config: AppConfig,
    repository: LibraryRepository,
    srv_mod: types.ModuleType,
    job_manager: JobManager,
) -> None:
    """Register scraper / gamelist / ScreenScraper routes on *router*."""

    # ── GET /api/ss-quota ────────────────────────────────────────────────────
    @router.get("/api/ss-quota")
    def get_ss_quota(ctx) -> None:
        has_dev = bool(config.screenscraper_dev_id and config.screenscraper_dev_pass)
        ctx._send_json({**srv_mod._ss_last_quota, "has_dev_account": has_dev})

    # ── POST /api/scrape ─────────────────────────────────────────────────────
    @router.post("/api/scrape")
    def post_scrape(ctx) -> None:
        _do_scrape(ctx, ctx._post_data, config, repository, job_manager)

    # ── POST /api/scrape-single ──────────────────────────────────────────────
    @router.post("/api/scrape-single")
    def post_scrape_single(ctx) -> None:
        _do_scrape_single(ctx, ctx._post_data, config, repository, srv_mod)

    # ── POST /api/export-gamelists ───────────────────────────────────────────
    @router.post("/api/export-gamelists")
    def post_export_gamelists(ctx) -> None:
        _do_export_gamelists(ctx, ctx._post_data, config, repository, srv_mod)

    # ── GET /api/export-metadata-nlp ────────────────────────────────────────
    @router.get("/api/export-metadata-nlp")
    def get_export_metadata_nlp(ctx) -> None:
        import csv as _csv
        import io as _io
        rows = repository.get_metadata_for_nlp()
        buf = _io.StringIO()
        writer = _csv.writer(buf)
        if rows:
            writer.writerow(rows[0].keys())
            for r in rows:
                writer.writerow(r.values())
        body = buf.getvalue().encode("utf-8-sig")
        ctx._send(200, "text/csv; charset=utf-8", body,
                  extra_headers={"Content-Disposition": 'attachment; filename="metadata_nlp.csv"'})

    # ── POST /api/export-pegasus ─────────────────────────────────────────────
    @router.post("/api/export-pegasus")
    def post_export_pegasus(ctx) -> None:
        if not config.library_root:
            ctx._send_json({"error": "library_root not configured"})
            return
        try:
            from rom_manager.scraper.pegasus_writer import write_pegasus_metadata
            result_peg = write_pegasus_metadata(config.library_root, repository)
            ctx._send_json({"ok": True, "platforms": result_peg["platforms"], "games": result_peg["games"]})
        except Exception as exc:
            ctx._send_json({"error": str(exc)})


# ── Handler logic ─────────────────────────────────────────────────────────────

def _do_scrape(ctx, data: dict, config: AppConfig, repository: LibraryRepository, job_manager: JobManager) -> None:
    platform        = data.get("platform") or None
    download_images = bool(data.get("images", False))
    limit           = int(data.get("limit", 0))

    _cancel = job_manager.cancel_event("scrape")

    def run() -> None:
        import rom_manager.web.server as _srv
        job_result = None
        try:
            from rom_manager.scanner.rom_scanner import utc_now
            from rom_manager.scraper.platform_ids import get_system_id
            from rom_manager.scraper.screenscraper import ScreenScraperClient, download_image

            if not config.screenscraper_user:
                job_result = {"error": "screenscraper credentials not configured"}
                return

            client = ScreenScraperClient(
                user=config.screenscraper_user,
                password=config.screenscraper_pass,
                dev_id=config.screenscraper_dev_id,
                dev_password=config.screenscraper_dev_pass,
            )
            games = repository.get_games_for_scraping(platform=platform)
            if limit:
                games = games[:limit]
            total = len(games)
            found = skipped = network_errors = images_filled = 0
            failed_games: list[str] = []
            _RETRY_DELAYS = [5, 15, 30]
            job_manager.update_progress("scrape", {"current": 0, "total": total, "found": 0, "network_errors": 0, "current_game": ""})
            # B6-3: use connect() + per-game commit instead of batch() so a single
            # network error mid-scrape doesn't lose all previously scraped metadata.
            with repository.connect() as conn:
                for idx, game in enumerate(games, 1):
                    if _cancel.is_set():
                        break
                    job_manager.update_progress("scrape", {
                        "current": idx, "total": total,
                        "found": found, "network_errors": network_errors,
                        "current_game": game["original_filename"],
                    })
                    sys_id = get_system_id(game["platform"])
                    result = None
                    last_error = ""
                    for attempt in range(3):
                        if _cancel.is_set():
                            break
                        try:
                            result = client.search(
                                crc32=game["crc32"], md5=game["md5"], sha1=game["sha1"],
                                filename=game["original_filename"], size_bytes=game["size_bytes"],
                                system_id=sys_id,
                            )
                            if result is None:
                                name_hint = game.get("canonical_title") or game["original_filename"]
                                result = client.search_by_name(name_hint, system_id=sys_id)
                            last_error = ""
                            break
                        except PermissionError:
                            raise
                        except Exception as exc:
                            last_error = str(exc)
                            if attempt < 2 and not _cancel.is_set():
                                time.sleep(_RETRY_DELAYS[attempt])
                    if _cancel.is_set():
                        break
                    if client.last_quota:
                        _srv._ss_last_quota.update(client.last_quota)
                    if last_error:
                        network_errors += 1
                        failed_games.append(game["original_filename"])
                        continue
                    if result is None:
                        skipped += 1
                        repository.mark_metadata_scraped(game["id"], conn)  # DB-1: mark as checked
                        conn.commit()
                        continue
                    box_art_path = screenshot_path = wheel_path = ""
                    if download_images:
                        _src_parent = Path(game["source_path"]).parent
                        _stem       = Path(game["original_filename"]).stem
                        if result.box_art_url:
                            _ext  = ".png" if ".png" in result.box_art_url.lower() else ".jpg"
                            _dest = _src_parent / "media" / "images" / f"{_stem}{_ext}"
                            if not _dest.exists():
                                try:
                                    download_image(result.box_art_url, _dest)
                                except Exception:
                                    pass
                            if _dest.exists():
                                box_art_path = str(_dest)
                        if result.screenshot_url:
                            _ext  = ".png" if ".png" in result.screenshot_url.lower() else ".jpg"
                            _dest = _src_parent / "media" / "screenshots" / f"{_stem}{_ext}"
                            if not _dest.exists():
                                try:
                                    download_image(result.screenshot_url, _dest)
                                except Exception:
                                    pass
                            if _dest.exists():
                                screenshot_path = str(_dest)
                        if result.wheel_url:
                            _ext  = ".png" if ".png" in result.wheel_url.lower() else ".jpg"
                            _dest = _src_parent / "media" / "wheels" / f"{_stem}{_ext}"
                            if not _dest.exists():
                                try:
                                    download_image(result.wheel_url, _dest)
                                except Exception:
                                    pass
                            if _dest.exists():
                                wheel_path = str(_dest)
                    repository.upsert_metadata(
                        game_id=game["id"],
                        ss_game_id=result.ss_game_id,
                        title=result.title, year=result.year,
                        genre=result.genre, publisher=result.publisher,
                        developer=result.developer, description=result.description,
                        rating=result.rating, box_art_url=result.box_art_url,
                        box_art_path=box_art_path,
                        screenshot_path=screenshot_path,
                        wheel_path=wheel_path,
                        scraped_at=utc_now(),
                        connection=conn,
                    )
                    repository.mark_metadata_scraped(game["id"], conn)  # DB-1: mark as checked
                    conn.commit()
                    found += 1

            # ── Pasada 2: descargar portadas desde URLs almacenadas (sin llamada API) ──
            if download_images and not _cancel.is_set():
                missing_img = repository.get_games_missing_images(platform=platform)
                img_total = len(missing_img)
                with repository.connect() as conn:
                    for img_idx, img_game in enumerate(missing_img, 1):
                        if _cancel.is_set():
                            break
                        job_manager.update_progress("scrape", {
                            "current": img_idx, "total": img_total,
                            "found": images_filled, "network_errors": 0,
                            "current_game": f"[portadas] {img_game['original_filename']}",
                        })
                        _ext  = ".png" if ".png" in img_game["box_art_url"].lower() else ".jpg"
                        _dest = Path(img_game["source_path"]).parent / "media" / "images" / f"{Path(img_game['original_filename']).stem}{_ext}"
                        if not _dest.exists():
                            try:
                                download_image(img_game["box_art_url"], _dest)
                            except Exception:
                                pass
                        if _dest.exists():
                            repository.update_image_paths(
                                game_id=img_game["id"],
                                box_art_path=str(_dest),
                                connection=conn,
                            )
                            conn.commit()
                            images_filled += 1

            # Auto-export gamelists after scrape (best-effort)
            _gamelist_written: list[str] = []
            try:
                from rom_manager.scraper.gamelist_writer import write_gamelist
                _out_root    = Path(config.library_root) if config.library_root else None
                _es_folders  = _srv._ES_PLATFORM_FOLDERS
                if _out_root:
                    _plat_filter = platform
                    _plats = repository.get_scraped_platform_summary()
                    if _plat_filter:
                        _plats = [p for p in _plats if p["platform"] == _plat_filter]
                    for _plat in _plats:
                        if _plat["scraped"] == 0:
                            continue
                        _entries = repository.get_metadata_for_platform(_plat["platform"])
                        if not _entries:
                            continue
                        _slug = _es_folders.get(_plat["platform"], _plat["platform"].lower().replace(" ", "").replace("/", "_"))
                        _pdir = _out_root / _slug
                        _pdir.mkdir(parents=True, exist_ok=True)
                        write_gamelist(_pdir, _entries)
                        _gamelist_written.append(_plat["platform"])
            except Exception:
                pass

            job_result = {
                "total": total, "found": found, "skipped": skipped,
                "network_errors": network_errors,
                "images_filled": images_filled,
                "failed_games": failed_games[:20],
                "cancelled": _cancel.is_set(),
                "gamelists_written": _gamelist_written,
                "result_ts": utc_now(),
            }
        except Exception as exc:
            job_result = {"error": str(exc)}
        finally:
            job_manager.finish("scrape", job_result)

    ctx._send_json(job_manager.start("scrape", run))


def _do_scrape_single(ctx, data: dict, config: AppConfig, repository: LibraryRepository, srv_mod) -> None:
    game_id         = data.get("game_id")
    preview         = bool(data.get("preview", False))
    download_images = bool(data.get("images", False))
    if not game_id:
        ctx._send_json({"error": "game_id required"})
        return
    if not config.screenscraper_user:
        ctx._send_json({"error": "Credenciales de ScreenScraper no configuradas"})
        return
    try:
        from rom_manager.scanner.rom_scanner import utc_now
        from rom_manager.scraper.platform_ids import get_system_id
        from rom_manager.scraper.screenscraper import ScreenScraperClient, download_image
        with repository.connect() as _conn:
            _grow = _conn.execute(
                "SELECT g.id, g.original_filename, g.source_path, g.platform, "
                "g.crc32, g.md5, g.sha1, g.size_bytes, g.canonical_title "
                "FROM games g WHERE g.id = ?", (int(game_id),)
            ).fetchone()
        if not _grow:
            ctx._send_json({"error": "Juego no encontrado"})
            return
        _game   = dict(_grow)
        _client = ScreenScraperClient(
            user=config.screenscraper_user, password=config.screenscraper_pass,
            dev_id=config.screenscraper_dev_id, dev_password=config.screenscraper_dev_pass,
        )
        _sys_id = get_system_id(_game["platform"])
        _result = _client.search(
            crc32=_game["crc32"], md5=_game["md5"], sha1=_game["sha1"],
            filename=_game["original_filename"], size_bytes=_game["size_bytes"],
            system_id=_sys_id,
        )
        if _result is None:
            _name_hint = _game.get("canonical_title") or _game["original_filename"]
            _result    = _client.search_by_name(_name_hint, system_id=_sys_id)
        if _client.last_quota:
            srv_mod._ss_last_quota.update(_client.last_quota)
        if _result is None:
            ctx._send_json({"found": False, "error": "No encontrado en ScreenScraper"})
            return
        _preview_data = {
            "found": True,
            "ss_game_id":   _result.ss_game_id,
            "title":        _result.title,
            "year":         _result.year,
            "genre":        _result.genre,
            "publisher":    _result.publisher,
            "developer":    _result.developer,
            "description":  _result.description,
            "rating":       _result.rating,
            "box_art_url":  _result.box_art_url,
        }
        if preview:
            ctx._send_json(_preview_data)
            return
        _box_art_path = _screenshot_path = _wheel_path = ""
        if download_images:
            _src_parent = Path(_game["source_path"]).parent
            _stem       = Path(_game["original_filename"]).stem
            if _result.box_art_url:
                _ext  = ".png" if ".png" in _result.box_art_url.lower() else ".jpg"
                _dest = _src_parent / "media" / "images" / f"{_stem}{_ext}"
                download_image(_result.box_art_url, _dest)
                _box_art_path = str(_dest)
            if _result.screenshot_url:
                _ext  = ".png" if ".png" in _result.screenshot_url.lower() else ".jpg"
                _dest = _src_parent / "media" / "screenshots" / f"{_stem}{_ext}"
                try:
                    download_image(_result.screenshot_url, _dest)
                    _screenshot_path = str(_dest)
                except Exception:
                    pass
            if _result.wheel_url:
                _ext  = ".png" if ".png" in _result.wheel_url.lower() else ".jpg"
                _dest = _src_parent / "media" / "wheels" / f"{_stem}{_ext}"
                try:
                    download_image(_result.wheel_url, _dest)
                    _wheel_path = str(_dest)
                except Exception:
                    pass
        with repository.batch() as _bconn:
            repository.upsert_metadata(
                game_id=int(game_id),
                ss_game_id=_result.ss_game_id,
                title=_result.title, year=_result.year,
                genre=_result.genre, publisher=_result.publisher,
                developer=_result.developer, description=_result.description,
                rating=_result.rating, box_art_url=_result.box_art_url,
                box_art_path=_box_art_path,
                screenshot_path=_screenshot_path,
                wheel_path=_wheel_path,
                scraped_at=utc_now(),
                connection=_bconn,
            )
            repository.mark_metadata_scraped(int(game_id), _bconn)  # DB-1: mark as checked
        ctx._send_json({**_preview_data, "applied": True})
    except Exception as _exc:
        ctx._send_json({"error": str(_exc)})


def _do_export_gamelists(ctx, data: dict, config: AppConfig, repository: LibraryRepository, srv_mod) -> None:
    from rom_manager.scraper.gamelist_writer import write_gamelist
    output_root = (
        Path(data.get("output_dir") or "").resolve()
        if data.get("output_dir")
        else config.library_root
    )
    if output_root is None:
        ctx._send_json({"error": "library_root not configured"})
        return
    platform_filter = data.get("platform") or None
    platforms = repository.get_scraped_platform_summary()
    if platform_filter:
        platforms = [p for p in platforms if p["platform"] == platform_filter]

    es_folders = srv_mod._ES_PLATFORM_FOLDERS
    written    = []
    for plat in platforms:
        if plat["scraped"] == 0:
            continue
        entries = repository.get_metadata_for_platform(plat["platform"])
        if not entries:
            continue
        slug         = es_folders.get(plat["platform"], plat["platform"].lower().replace(" ", "").replace("/", "_"))
        platform_dir = Path(output_root) / slug
        platform_dir.mkdir(parents=True, exist_ok=True)
        out = write_gamelist(platform_dir, entries)
        written.append({"platform": plat["platform"], "path": str(out), "entries": len(entries)})
    ctx._send_json({"written": written})
