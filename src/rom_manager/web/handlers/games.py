from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.jobs.manager import JobManager
    from rom_manager.web.router import Router


_logger = logging.getLogger(__name__)

_ra_progress_cache: dict = {}  # (ra_game_id, username) → {unlocked, total, ...}
_ra_hash_cache: dict = {}  # (cid, mtime) → (hash_map, title_index)


def _state_search_dirs(rom_path: Path, config) -> list[Path]:
    """Build the list of directories to search for save-state files."""
    dirs: list[Path] = [rom_path.parent]
    ra = getattr(config, "retroarch_path", None)
    if ra:
        states_dir = Path(ra).parent / "states"
        if states_dir not in dirs:
            dirs.append(states_dir)
    lib = getattr(config, "library_root", None)
    if lib:
        lib_path = Path(lib)
        if lib_path not in dirs:
            dirs.append(lib_path)
    return dirs


def _dat_title_index(config) -> dict[str, tuple[int, dict[str, str]]]:
    """AUD-5: por DAT, ``dat_filename → (total_dumps, {clave_1g1r: título})``.

    La clave 1G1R es ``normalize_for_match`` (quita región/revisión/tags), así
    "Sonic (USA)" y "Sonic (Europe)" cuentan como un solo título base. El
    título guardado es el primero visto, solo para mostrar en los faltantes.
    """
    from rom_manager.catalog.catalog_loader import (
        _detect_dat_format,
        load_clrmamepro_dat,
        load_nointro_dat_with_header,
    )
    from rom_manager.detection.filename_normalizer import normalize_for_match

    out: dict[str, tuple[int, dict[str, str]]] = {}
    for dat_dir in (
        config.catalogs_nointro_dir,
        config.catalogs_redump_dir,
        config.catalogs_arcade_dir,
    ):
        if not dat_dir or not dat_dir.exists():
            continue
        for dat_file in dat_dir.glob("*.dat"):
            try:
                if _detect_dat_format(dat_file) == "clrmamepro":
                    entries = load_clrmamepro_dat(dat_file)
                else:
                    _label, entries = load_nointro_dat_with_header(dat_file)
            except Exception:  # noqa: S112 — DAT corrupto: se ignora, igual que el resto de loaders
                continue
            titles: dict[str, str] = {}
            for entry in entries.values():
                key = normalize_for_match(entry.title)
                if key and key not in titles:
                    titles[key] = entry.title
            out[dat_file.name] = (len(entries), titles)
    return out


def _owned_title_keys(repo) -> dict[str, set[str]]:
    """AUD-5: ``catalog_source → claves 1G1R`` de los títulos que ya tienes."""
    from rom_manager.detection.filename_normalizer import normalize_for_match

    with repo.connect() as conn:
        rows = conn.execute(
            """
            SELECT catalog_source, COALESCE(canonical_title, original_filename) AS t
            FROM games
            WHERE file_type = 'rom' AND catalog_source IS NOT NULL
            """
        ).fetchall()
    owned: dict[str, set[str]] = {}
    for r in rows:
        key = normalize_for_match(r["t"] or "")
        if key:
            owned.setdefault(r["catalog_source"], set()).add(key)
    return owned


def _lookup_ra_game(platform: str, md5: str, config: AppConfig):
    """Return the RAGame matching *platform*/*md5* from the local RA cache, or None.

    Shared by the bulk (_enrich_games_with_ra) and individual (/api/game) lookups
    so there is one cache-reading implementation, not two (REV43-43). Memoized in
    the module-level _ra_hash_cache, keyed by (console_id, cache file mtime) so a
    refreshed cache is picked up without a server restart.
    """
    if not platform or not md5:
        return None
    import json as _json

    from rom_manager.retroachievements.ra_client import _parse_game_list
    from rom_manager.retroachievements.ra_platform_ids import get_ra_console_id

    cid = get_ra_console_id(platform)
    if not cid:
        return None
    cache_file = config.project_root / ".rommgr" / "ra_cache" / f"ra_hashes_{cid}.json"
    if not cache_file.exists():
        return None
    key = (cid, cache_file.stat().st_mtime)
    if key not in _ra_hash_cache:
        try:
            _ra_hash_cache[key] = _parse_game_list(
                _json.loads(cache_file.read_text(encoding="utf-8"))
            )
        except Exception:
            _logger.warning("Caché RA corrupta o ilegible: %s", cache_file, exc_info=True)
            _ra_hash_cache[key] = {}
    return _ra_hash_cache[key].get(md5.lower())


def _enrich_games_with_ra(games: list[dict], config: AppConfig) -> None:
    """Add ra_game_id and ra_achievements to each game dict using local RA cache files.

    MD5-only match, consistent with the /api/game detail endpoint.
    """
    for g in games:
        try:
            rg = _lookup_ra_game(g.get("platform") or "", g.get("md5") or "", config)
            if rg:
                g["ra_game_id"] = rg.id
                g["ra_achievements"] = rg.achievements
        except Exception:
            _logger.debug("Anotación RA de un juego falló; se omite", exc_info=True)
            continue


# ── Public entry point ────────────────────────────────────────────────────────


def register(
    router: Router,
    *,
    config: AppConfig,
    repository: LibraryRepository,
    get_repo_fn,
    job_manager: JobManager,
) -> None:
    """Register game library / backup / launch routes on *router*."""

    # ── GET /api/games ───────────────────────────────────────────────────────
    @router.get("/api/games")
    def get_games(ctx) -> None:
        from rom_manager.web.builders.library import _build_games

        qs = getattr(ctx, "_qs", {})
        offset = int(qs.get("offset", ["0"])[0])
        limit = min(int(qs.get("limit", ["100"])[0]), 5000)
        plat = qs.get("platform", [None])[0] or None
        st = qs.get("status", [None])[0] or None
        root = qs.get("root", [None])[0] or None
        ft = qs.get("filetype", ["rom"])[0]
        file_type = ft if ft in ("rom", "", "save") else None
        search = qs.get("search", [None])[0] or None
        play_status = qs.get("play_status", [None])[0] or None
        favorite = qs.get("favorite", ["0"])[0] == "1"
        tag_filter = qs.get("tag", [None])[0] or None
        genre_filter = qs.get("genre", [None])[0] or None
        year_filter = qs.get("year", [None])[0] or None
        region_filter = qs.get("region", [None])[0] or None
        sort_by = qs.get("sort_by", [None])[0] or None
        _games_repo = get_repo_fn(root or "")
        _result = _build_games(
            _games_repo,
            offset=offset,
            limit=limit,
            platform=plat,
            status=st,
            source_root=root,
            file_type=file_type,
            search=search,
            play_status=play_status,
            favorite=favorite,
            tag=tag_filter,
            genre=genre_filter,
            year=year_filter,
            region=region_filter,
            sort_by=sort_by,
        )
        _enrich_games_with_ra(_result["games"], config)
        _ni = config.catalogs_nointro_dir
        _rd = config.catalogs_redump_dir
        _result["dat_count"] = (
            sum(1 for f in _ni.iterdir() if f.suffix.lower() == ".dat") if _ni.exists() else 0
        ) + (sum(1 for f in _rd.iterdir() if f.suffix.lower() == ".dat") if _rd.exists() else 0)
        ctx._send_json(_result)

    # ── GET /api/games/filter-options ────────────────────────────────────────
    @router.get("/api/games/filter-options")
    def get_filter_options(ctx) -> None:
        ctx._send_json(repository.get_filter_options())

    # ── GET /api/tags ────────────────────────────────────────────────────────
    @router.get("/api/tags")
    def get_tags(ctx) -> None:
        ctx._send_json({"tags": repository.get_all_tags()})

    # ── GET /api/game-tags ───────────────────────────────────────────────────
    @router.get("/api/game-tags")
    def get_game_tags(ctx) -> None:
        qs = getattr(ctx, "_qs", {})
        game_id = qs.get("id", [None])[0]
        if not game_id:
            ctx._send_json({"error": "id required"})
        else:
            ctx._send_json({"tags": repository.get_tags(int(game_id))})

    # ── GET /api/export-m3u ──────────────────────────────────────────────────
    @router.get("/api/export-m3u")
    def get_export_m3u(ctx) -> None:
        """Return a RetroArch-compatible .m3u playlist for all ROMs with a given tag."""
        qs = getattr(ctx, "_qs", {})
        tag = qs.get("tag", [None])[0]
        if not tag:
            ctx._send_json({"error": "tag required"})
            return
        with repository.connect() as conn:
            rows = conn.execute(
                """
                SELECT g.source_path, g.title
                FROM games g
                JOIN game_tags gt ON gt.game_id = g.id
                WHERE gt.tag = ? AND g.file_type = 'rom'
                ORDER BY g.title COLLATE NOCASE
                """,
                (tag,),
            ).fetchall()
        lines = ["#EXTM3U"]
        for r in rows:
            lines.append(f"#EXTINF:-1,{r['title'] or Path(r['source_path']).stem}")
            lines.append(r["source_path"])
        body = "\n".join(lines).encode("utf-8")
        safe_tag = tag.replace("/", "_").replace("\\", "_")
        ctx._send(
            200,
            "audio/x-mpegurl",
            body,
            extra_headers={"Content-Disposition": f'attachment; filename="{safe_tag}.m3u"'},
        )

    # ── GET /api/stateshot ───────────────────────────────────────────────────
    @router.get("/api/stateshot")
    def get_stateshot(ctx) -> None:
        import base64

        from rom_manager.utils.state_reader import find_state_thumbnails

        qs = getattr(ctx, "_qs", {})
        game_id = qs.get("id", [None])[0]
        if not game_id:
            ctx._send_json({"error": "id required"})
            return
        with repository.connect() as conn:
            row = conn.execute(
                "SELECT source_path FROM games WHERE id = ?", (int(game_id),)
            ).fetchone()
        if not row:
            ctx._send_json({"found": False})
            return
        rom_path = Path(row["source_path"])
        search_dirs = _state_search_dirs(rom_path, config)
        results = find_state_thumbnails(rom_path.stem, search_dirs, max_results=1)
        if results:
            _, png = results[0]
            ctx._send_json({"found": True, "data": base64.b64encode(png).decode()})
        else:
            ctx._send_json({"found": False})

    # ── GET /api/stateshots ──────────────────────────────────────────────────
    @router.get("/api/stateshots")
    def get_stateshots(ctx) -> None:
        """Return all save-state thumbnails for a game (for the grid view)."""
        import base64

        from rom_manager.utils.state_reader import find_state_thumbnails

        qs = getattr(ctx, "_qs", {})
        game_id = qs.get("id", [None])[0]
        if not game_id:
            ctx._send_json({"error": "id required"})
            return
        with repository.connect() as conn:
            row = conn.execute(
                "SELECT source_path FROM games WHERE id = ?", (int(game_id),)
            ).fetchone()
        if not row:
            ctx._send_json({"slots": []})
            return
        rom_path = Path(row["source_path"])
        search_dirs = _state_search_dirs(rom_path, config)
        results = find_state_thumbnails(rom_path.stem, search_dirs, max_results=8)
        ctx._send_json(
            {
                "slots": [
                    {"slot": slot, "data": base64.b64encode(png).decode()} for slot, png in results
                ]
            }
        )

    # ── GET /api/save-backups ────────────────────────────────────────────────
    @router.get("/api/save-backups")
    def get_save_backups(ctx) -> None:
        from rom_manager.backup.save_backup import list_backups

        qs = getattr(ctx, "_qs", {})
        game_id = qs.get("id", [None])[0]
        if not game_id:
            ctx._send_json({"error": "id required"})
            return
        with repository.connect() as conn:
            row = conn.execute(
                "SELECT source_path FROM games WHERE id = ?", (int(game_id),)
            ).fetchone()
        if not row:
            ctx._send_json({"backups": []})
            return
        rom_path = Path(row["source_path"])
        all_entries = []
        for ext in config.save_extensions:
            save_path = rom_path.parent / (rom_path.stem + ext)
            entries = list_backups(save_path, config.data_dir)
            for e in entries:
                all_entries.append(
                    {
                        "backup_path": str(e.backup_path),
                        "timestamp": e.timestamp,
                        "extension": e.extension,
                        "size": e.size,
                        "original_save": str(save_path),
                    }
                )
        all_entries.sort(key=lambda x: x["timestamp"], reverse=True)
        ctx._send_json(
            {
                "backups": all_entries,
                "backup_enabled": config.backup.saves_enabled,
                "keep_n": config.backup.saves_keep_n,
            }
        )

    # ── GET /api/manual-backups ──────────────────────────────────────────────
    @router.get("/api/manual-backups")
    def get_manual_backups(ctx) -> None:
        from rom_manager.backup.save_backup import list_manual_zips

        ctx._send_json({"zips": list_manual_zips(config.data_dir)})

    # ── GET /api/save-comparison ─────────────────────────────────────────────
    @router.get("/api/save-comparison")
    def get_save_comparison(ctx) -> None:
        ctx._send_json({"saves": repository.get_save_comparison()})

    # ── GET /api/game-sync-history ───────────────────────────────────────────
    @router.get("/api/game-sync-history")
    def get_game_sync_history(ctx) -> None:
        qs = getattr(ctx, "_qs", {})
        sp = qs.get("source_path", [""])[0]
        if not sp:
            ctx._send_json({"error": "source_path required"})
        else:
            ctx._send_json({"history": repository.get_save_sync_history(sp)})

    # ── GET /api/game ────────────────────────────────────────────────────────
    @router.get("/api/game")
    def get_game(ctx) -> None:
        qs = getattr(ctx, "_qs", {})
        game_id = qs.get("id", [None])[0]
        if not game_id:
            ctx._send_json({"error": "id required"})
            return
        with repository.connect() as conn:
            row = conn.execute(
                """
                SELECT g.id, g.original_filename, g.source_path, g.platform,
                       g.region, g.extension, g.size_bytes, g.sha1, g.md5, g.crc32,
                       g.canonical_title, g.match_confidence, g.catalog_source,
                       g.play_status, g.last_played_at, g.file_type,
                       g.notes, g.is_favorite,
                       g.user_rating, g.play_count, g.first_played_at,
                       m.title AS ss_title, m.year, m.genre, m.publisher,
                       m.developer, m.description, m.rating, m.box_art_url,
                       m.box_art_path, m.scraped_at, m.ss_game_id
                FROM games g
                LEFT JOIN game_metadata m ON m.game_id = g.id
                WHERE g.id = ?
            """,
                (int(game_id),),
            ).fetchone()
        if not row:
            ctx._send_json({"error": "not found"})
            return
        result = dict(row)
        # RA data lookup from local cache
        try:
            rg = _lookup_ra_game(result.get("platform") or "", result.get("md5") or "", config)
            if rg:
                result["ra_game_id"] = rg.id
                result["ra_title"] = rg.title
                result["ra_achievements"] = rg.achievements
                result["ra_points"] = rg.points
        except Exception:
            _logger.debug("Anotación RA en detalle de juego falló", exc_info=True)
        # saves count by stem matching
        try:
            import os as _os2

            _sp = result.get("source_path") or ""
            _stem = _os2.path.splitext(_os2.path.basename(_sp))[0]
            if _stem:
                with repository.connect() as _sc2:
                    _row2 = _sc2.execute(
                        "SELECT COUNT(*) FROM saves WHERE original_path LIKE ?",
                        (f"%{_stem}%",),
                    ).fetchone()
                    result["saves_count"] = _row2[0] if _row2 else 0
        except Exception:
            _logger.warning("Conteo de saves por stem falló", exc_info=True)
            result["saves_count"] = 0
        ctx._send_json(result)

    # ── GET /api/ra-user-progress ─────────────────────────────────────────────
    @router.get("/api/ra-user-progress")
    def get_ra_user_progress(ctx) -> None:
        qs = getattr(ctx, "_qs", {})
        ra_game_id = qs.get("ra_game_id", [None])[0]
        if not ra_game_id:
            ctx._send_json({"error": "ra_game_id required"})
            return
        try:
            ra_game_id = int(ra_game_id)
        except (ValueError, TypeError):
            ctx._send_json({"error": "ra_game_id must be integer"})
            return

        api_key = config.credentials.ra_api_key
        username = config.credentials.ra_username
        if not api_key or not username:
            ctx._send_json(
                {
                    "error": "retroachievements.api_key and retroachievements.username must be configured"
                }
            )
            return

        # 1-hour in-memory cache
        cache_key = (ra_game_id, username)
        cached = _ra_progress_cache.get(cache_key)
        if cached and time.time() - cached["_ts"] < 3600:
            ctx._send_json(cached)
            return

        try:
            import json as _json
            import urllib.request as _req

            url = (
                f"https://retroachievements.org/API/API_GetGameInfoAndUserProgress.php"
                f"?g={ra_game_id}&u={username}&y={api_key}"
            )
            request = _req.Request(url, headers={"User-Agent": "ROMManagerLocal/1.0"})
            with _req.urlopen(request, timeout=15) as resp:
                data = _json.loads(resp.read())
        except Exception as exc:
            ctx._send_json({"error": str(exc)})
            return

        result = {
            "total": int(data.get("NumAchievements", 0) or 0),
            "unlocked": int(data.get("NumAwardedToUser", 0) or 0),
            "hardcore": int(data.get("NumAwardedToUserHardcore", 0) or 0),
            "points_earned": int(data.get("ScoreAchieved", 0) or 0),
            "points_total": int(data.get("PossibleScore", 0) or 0),
            "_ts": time.time(),
        }
        _ra_progress_cache[cache_key] = result
        ctx._send_json(result)

    # ── POST /api/set-play-status ────────────────────────────────────────────
    @router.post("/api/set-play-status")
    def post_set_play_status(ctx) -> None:
        data = ctx._post_data
        game_id = data.get("game_id")
        status = data.get("status") or None
        if not game_id:
            ctx._send_json({"error": "game_id required"})
            return
        _status_repo = get_repo_fn(data.get("source_path", ""))
        _status_repo.set_play_status(int(game_id), status)
        ctx._send_json({"ok": True})

    # ── POST /api/set-metadata ───────────────────────────────────────────────
    @router.post("/api/set-metadata")
    def post_set_metadata(ctx) -> None:
        data = ctx._post_data
        game_id = data.get("game_id")
        if not game_id:
            ctx._send_json({"error": "game_id required"})
            return
        gid = int(game_id)
        _meta_repo = get_repo_fn(data.get("source_path", ""))
        if "notes" in data:
            _meta_repo.set_notes(gid, data["notes"] or None)
        if "canonical_title" in data:
            _meta_repo.set_canonical_title(gid, data["canonical_title"])
        _meta_fields = {
            k: v
            for k, v in data.items()
            if k in {"year", "genre", "publisher", "developer", "description", "rating"}
        }
        if _meta_fields:
            _meta_repo.upsert_metadata_manual(gid, **_meta_fields)
        ctx._send_json({"ok": True})

    # ── POST /api/toggle-favorite ────────────────────────────────────────────
    @router.post("/api/toggle-favorite")
    def post_toggle_favorite(ctx) -> None:
        data = ctx._post_data
        game_id = data.get("game_id")
        if not game_id:
            ctx._send_json({"error": "game_id required"})
            return
        _fav_repo = get_repo_fn(data.get("source_path", ""))
        new_val = _fav_repo.toggle_favorite(int(game_id))
        ctx._send_json({"ok": True, "is_favorite": new_val})

    # ── POST /api/tag ────────────────────────────────────────────────────────
    @router.post("/api/tag")
    def post_tag(ctx) -> None:
        data = ctx._post_data
        game_id = data.get("game_id")
        tag = str(data.get("tag", "")).strip()
        action = data.get("action", "add")  # "add" | "remove"
        if not game_id or not tag:
            ctx._send_json({"error": "game_id and tag required"})
            return
        _tag_repo = get_repo_fn(data.get("source_path", ""))
        if action == "remove":
            _tag_repo.remove_tag(int(game_id), tag)
        else:
            _tag_repo.add_tag(int(game_id), tag)
        ctx._send_json({"ok": True, "tags": _tag_repo.get_tags(int(game_id))})

    # ── POST /api/open-folder ────────────────────────────────────────────────
    @router.post("/api/open-folder")
    def post_open_folder(ctx) -> None:
        import os as _os_of
        import subprocess as _sp_of

        folder_path = ctx._post_data.get("path", "").strip()
        if not folder_path:
            ctx._send_json({"ok": False, "error": "path required"})
            return
        try:
            p = _os_of.path.abspath(folder_path)
            folder = p if _os_of.path.isdir(p) else _os_of.path.dirname(p)
            if sys.platform == "win32":
                _sp_of.Popen(["explorer", folder])
            else:
                _sp_of.Popen(["xdg-open", folder])
            ctx._send_json({"ok": True})
        except Exception as _exc_of:
            ctx._send_json({"ok": False, "error": str(_exc_of)})

    # ── POST /api/launch ─────────────────────────────────────────────────────
    @router.post("/api/launch")
    def post_launch(ctx) -> None:
        import subprocess

        data = ctx._post_data
        game_id = data.get("game_id")
        if not game_id:
            ctx._send_json({"error": "game_id required"})
            return
        with repository.connect() as conn:
            row = conn.execute(
                "SELECT source_path, platform FROM games WHERE id = ?", (int(game_id),)
            ).fetchone()
        if not row:
            ctx._send_json({"error": "game not found"})
            return
        retroarch_exe = config.retroarch_path or ""
        if not retroarch_exe or not Path(retroarch_exe).exists():
            ctx._send_json(
                {"error": "RetroArch no configurado. Ajusta retroarch_path en Settings."}
            )
            return
        platform = row["platform"] or ""
        core = (config.launcher_cores or {}).get(platform, "")
        rom = row["source_path"]
        cmd = [retroarch_exe]
        if core:
            cmd += ["--libretro", core]
        cmd.append(rom)
        try:
            subprocess.Popen(cmd)
            ctx._send_json({"ok": True, "cmd": cmd})
        except Exception as exc:
            ctx._send_json({"error": str(exc)})

    # ── POST /api/restore-backup ─────────────────────────────────────────────
    @router.post("/api/restore-backup")
    def post_restore_backup(ctx) -> None:
        data = ctx._post_data
        backup_path_str = data.get("backup_path", "").strip()
        original_save_str = data.get("original_save", "").strip()
        if not backup_path_str or not original_save_str:
            ctx._send_json({"error": "backup_path and original_save required"})
            return
        from rom_manager.backup.save_backup import restore_backup

        bp = Path(backup_path_str)
        tp = Path(original_save_str)
        if config.library_root:
            resolved_root = config.library_root.resolve()
            resolved_target = tp.resolve()
            if not resolved_target.is_relative_to(resolved_root):
                ctx._send_json({"error": "La ruta destino está fuera de la biblioteca"})
                return
        ok = restore_backup(bp, tp)
        if ok:
            ctx._send_json({"ok": True, "restored_to": str(tp)})
        else:
            ctx._send_json({"error": f"Backup no encontrado: {bp.name}"})

    # ── POST /api/backup-now ─────────────────────────────────────────────────
    @router.post("/api/backup-now")
    def post_backup_now(ctx) -> None:
        def _do_backup_now() -> None:
            import time as _t

            job_result = None
            try:
                from rom_manager.backup.save_backup import create_saves_zip

                saves_dirs = []
                if config.library_root and config.library_root.exists():
                    saves_dirs.append(config.library_root)
                for src in config.sync.sync_sources:
                    p = Path(src.local_dir)
                    if p.exists() and p not in saves_dirs:
                        saves_dirs.append(p)
                zip_path = create_saves_zip(
                    saves_dirs,
                    set(config.save_extensions),
                    config.data_dir / "saves-backup" / "saves-zips",
                )
                job_result = {
                    "ok": True,
                    "zip": str(zip_path),
                    "size": zip_path.stat().st_size,
                    "result_ts": str(_t.time()),
                }
            except Exception as exc:
                job_result = {"ok": False, "error": str(exc), "result_ts": str(_t.time())}
            finally:
                job_manager.finish("backup_now", job_result)

        ctx._send_json(job_manager.start("backup_now", _do_backup_now))

    # ── GET /api/unmatched-by-platform ───────────────────────────────────────
    @router.get("/api/unmatched-by-platform")
    def get_unmatched_by_platform(ctx) -> None:
        qs = getattr(ctx, "_qs", {})
        root = qs.get("root", [None])[0] or ""
        _repo = get_repo_fn(root)

        with _repo.connect() as conn:
            rows = conn.execute(
                """
                SELECT COALESCE(platform, '(sin plataforma)') AS platform,
                       COUNT(*) AS cnt,
                       GROUP_CONCAT(original_filename, '|||') AS filenames
                FROM games
                WHERE canonical_title IS NULL AND file_type = 'rom'
                GROUP BY platform
                ORDER BY cnt DESC
                """
            ).fetchall()

        total_unmatched = sum(r["cnt"] for r in rows)

        # List loaded DAT files so the user knows which catalogs are present
        loaded_dats: list[str] = []
        project_root = config.project_root
        if project_root:
            for dat_dir in (
                Path(project_root) / ".rommgr" / "dats",
                Path(project_root) / ".rommgr" / "catalogs" / "nointro",
                Path(project_root) / ".rommgr" / "catalogs" / "redump",
            ):
                try:
                    loaded_dats.extend(
                        f.name for f in dat_dir.iterdir() if f.suffix.lower() in {".dat", ".xml"}
                    )
                except (OSError, FileNotFoundError):
                    pass

        platforms = [
            {
                "platform": row["platform"],
                "count": row["cnt"],
                "examples": (row["filenames"] or "").split("|||")[:5],
            }
            for row in rows
        ]

        ctx._send_json(
            {
                "total_unmatched": total_unmatched,
                "loaded_dats": sorted(loaded_dats),
                "platforms": platforms,
            }
        )

    # ── GET /api/collection-completeness ─────────────────────────────────────
    @router.get("/api/collection-completeness")
    def get_collection_completeness(ctx) -> None:
        qs = getattr(ctx, "_qs", {})
        root = qs.get("root", [None])[0] or ""
        _repo = get_repo_fn(root)

        with _repo.connect() as conn:
            rows = conn.execute(
                """
                SELECT catalog_source, COUNT(*) AS owned
                FROM games
                WHERE file_type = 'rom' AND catalog_source IS NOT NULL
                GROUP BY catalog_source
                ORDER BY owned DESC
                """
            ).fetchall()

        owned_by_source = {r["catalog_source"]: r["owned"] for r in rows}
        dat_index = _dat_title_index(config)
        owned_keys = _owned_title_keys(_repo)

        def _row(source: str, owned: int) -> dict:
            raw_total, titles = dat_index.get(source, (None, {}))
            owned_1g1r = len(owned_keys.get(source, set()) & set(titles)) if titles else None
            total_1g1r = len(titles) if titles else None
            return {
                "label": Path(source).stem,
                "source": source,
                "owned": owned,
                "total": raw_total,
                "pct": round(owned / raw_total * 100, 1) if raw_total else None,
                # AUD-5: modo 1G1R — títulos base, agrupando región/revisión
                "owned_1g1r": owned_1g1r,
                "total_1g1r": total_1g1r,
                "pct_1g1r": (
                    round(owned_1g1r / total_1g1r * 100, 1)
                    if owned_1g1r is not None and total_1g1r
                    else None
                ),
            }

        results = [_row(source, owned) for source, owned in owned_by_source.items()]
        seen = set(owned_by_source)
        results.extend(_row(dat_name, 0) for dat_name in dat_index if dat_name not in seen)

        results.sort(key=lambda r: (r["owned"] == 0, -(r["owned"] or 0)))
        ctx._send_json({"platforms": results})

    # ── GET /api/collection-missing.csv (AUD-5) ───────────────────────────────
    @router.get("/api/collection-missing.csv")
    def get_collection_missing_csv(ctx) -> None:
        """CSV de títulos base (1G1R) presentes en los DATs pero no en tu biblioteca."""
        import csv as _csv
        import io as _io

        qs = getattr(ctx, "_qs", {})
        root = qs.get("root", [None])[0] or ""
        source_filter = qs.get("source", [""])[0]
        _repo = get_repo_fn(root)

        dat_index = _dat_title_index(config)
        owned_keys = _owned_title_keys(_repo)

        buf = _io.StringIO()
        writer = _csv.writer(buf)
        writer.writerow(["Plataforma (DAT)", "Título faltante"])
        for dat_name in sorted(dat_index):
            if source_filter and dat_name != source_filter:
                continue
            # sin filtro: solo plataformas donde ya tienes algo (si no, el CSV
            # sería el volcado completo de todos los DATs)
            if not source_filter and dat_name not in owned_keys:
                continue
            _raw, titles = dat_index[dat_name]
            have = owned_keys.get(dat_name, set())
            label = Path(dat_name).stem
            for key in sorted(set(titles) - have, key=lambda k: titles[k].lower()):
                writer.writerow([label, titles[key]])
        body = buf.getvalue().encode("utf-8-sig")
        ctx._send(
            200,
            "text/csv; charset=utf-8",
            body,
            extra_headers={"Content-Disposition": 'attachment; filename="faltantes.csv"'},
        )

    # ── GET /api/screenshots ─────────────────────────────────────────────────────
    @router.get("/api/screenshots")
    def get_screenshots(ctx) -> None:
        """List RetroArch screenshots matching a ROM stem."""
        stem = (ctx._qs.get("stem", [None])[0] or "").strip()
        if not config.retroarch_path:
            ctx._send_json({"screenshots": [], "error": "retroarch_path no configurado"})
            return
        shots_dir = Path(config.retroarch_path).parent / "screenshots"
        if not shots_dir.is_dir():
            ctx._send_json({"screenshots": []})
            return
        files = []
        for f in shots_dir.iterdir():
            if f.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
                continue
            if stem and not f.stem.startswith(stem):
                continue
            try:
                mtime = f.stat().st_mtime
            except OSError:
                mtime = 0.0
            files.append({"filename": f.name, "taken_at": int(mtime)})
        files.sort(key=lambda x: x["taken_at"], reverse=True)
        ctx._send_json({"screenshots": files})

    # ── GET /api/screenshot-file ──────────────────────────────────────────────────
    @router.get("/api/screenshot-file")
    def get_screenshot_file(ctx) -> None:
        """Serve a single RetroArch screenshot PNG by filename (no path traversal)."""
        import mimetypes

        name = (ctx._qs.get("name", [None])[0] or "").strip()
        if not name or "/" in name or "\\" in name or name.startswith("."):
            ctx._send_error(400, "Nombre de archivo inválido")
            return
        if not config.retroarch_path:
            ctx._send_error(404, "retroarch_path no configurado")
            return
        shots_dir = Path(config.retroarch_path).parent / "screenshots"
        img_path = (shots_dir / name).resolve()
        if not str(img_path).startswith(str(shots_dir.resolve())):
            ctx._send_error(403, "Ruta fuera del directorio de screenshots")
            return
        if not img_path.exists():
            ctx._send_error(404, "Screenshot no encontrado")
            return
        try:
            body = img_path.read_bytes()
            mime, _ = mimetypes.guess_type(str(img_path))
            ctx._send(200, mime or "image/png", body)
        except OSError as exc:
            ctx._send_error(500, str(exc))

    # ── GET /api/activity-heatmap ────────────────────────────────────────────
    @router.get("/api/activity-heatmap")
    def get_activity_heatmap(ctx) -> None:
        """Return daily game counts for the last 52 weeks for a GitHub-style heatmap."""
        with repository.connect() as conn:
            rows = conn.execute(
                """
                SELECT DATE(last_played_at) AS day, COUNT(DISTINCT id) AS cnt
                FROM games
                WHERE last_played_at IS NOT NULL
                  AND last_played_at >= DATE('now', '-364 days')
                GROUP BY day
                ORDER BY day
                """
            ).fetchall()
        ctx._send_json({"days": [{"date": r["day"], "count": r["cnt"]} for r in rows]})
