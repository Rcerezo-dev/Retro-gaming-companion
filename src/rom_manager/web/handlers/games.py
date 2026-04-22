from __future__ import annotations

import sys
import time
import threading
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import parse_qs

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.router import Router
    import types


_ra_progress_cache: dict = {}  # (ra_game_id, username) → {unlocked, total, ...}
_ra_hash_cache: dict = {}     # (cid, mtime) → (hash_map, title_index)


def _enrich_games_with_ra(games: list[dict], config: "AppConfig") -> None:
    """Add ra_game_id and ra_achievements to each game dict using local RA cache files.

    MD5-only match, consistent with the /api/game detail endpoint.
    """
    if not games:
        return
    import json as _json
    from rom_manager.retroachievements.ra_platform_ids import get_ra_console_id
    from rom_manager.retroachievements.ra_client import _parse_game_list
    cache_dir = config.project_root / ".rommgr" / "ra_cache"
    hl_by_cid: dict = {}

    for g in games:
        try:
            plat = g.get("platform") or ""
            if not plat:
                continue
            cid = get_ra_console_id(plat)
            if not cid:
                continue
            if cid not in hl_by_cid:
                cf = cache_dir / f"ra_hashes_{cid}.json"
                if cf.exists():
                    key = (cid, cf.stat().st_mtime)
                    if key not in _ra_hash_cache:
                        try:
                            hl = _parse_game_list(_json.loads(cf.read_text("utf-8")))
                        except Exception:
                            hl = {}
                        _ra_hash_cache[key] = hl
                    hl = _ra_hash_cache[key]
                else:
                    hl = {}
                hl_by_cid[cid] = hl

            md5 = g.get("md5") or ""
            rg = hl_by_cid[cid].get(md5.lower()) if md5 else None
            if rg:
                g["ra_game_id"] = rg.id
                g["ra_achievements"] = rg.achievements
        except Exception:
            continue

# ── Public entry point ────────────────────────────────────────────────────────

def register(
    router: "Router",
    *,
    config: "AppConfig",
    repository: "LibraryRepository",
    get_repo_fn,
    srv_mod: "types.ModuleType",
) -> None:
    """Register game library / backup / launch routes on *router*."""

    # ── GET /api/games ───────────────────────────────────────────────────────
    @router.get("/api/games")
    def get_games(ctx) -> None:
        from rom_manager.web.response_builders import _build_games
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
            _games_repo, offset=offset, limit=limit, platform=plat, status=st,
            source_root=root, file_type=file_type, search=search,
            play_status=play_status, favorite=favorite, tag=tag_filter,
            genre=genre_filter, year=year_filter, region=region_filter,
            sort_by=sort_by,
        )
        _enrich_games_with_ra(_result["games"], config)
        _ni = config.catalogs_nointro_dir
        _rd = config.catalogs_redump_dir
        _result["dat_count"] = (
            sum(1 for f in _ni.iterdir() if f.suffix.lower() == ".dat") if _ni.exists() else 0
        ) + (
            sum(1 for f in _rd.iterdir() if f.suffix.lower() == ".dat") if _rd.exists() else 0
        )
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

    # ── GET /api/stateshot ───────────────────────────────────────────────────
    @router.get("/api/stateshot")
    def get_stateshot(ctx) -> None:
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
        candidates = list(rom_path.parent.glob(rom_path.stem + ".state*.png"))
        if not candidates and config.library_root:
            candidates = list(Path(config.library_root).rglob(rom_path.stem + ".state*.png"))
        if candidates:
            import base64
            png = sorted(candidates)[-1]
            img_b64 = base64.b64encode(png.read_bytes()).decode()
            ctx._send_json({"found": True, "data": img_b64, "filename": png.name})
        else:
            ctx._send_json({"found": False})

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
                all_entries.append({
                    "backup_path": str(e.backup_path),
                    "timestamp": e.timestamp,
                    "extension": e.extension,
                    "size": e.size,
                    "original_save": str(save_path),
                })
        all_entries.sort(key=lambda x: x["timestamp"], reverse=True)
        ctx._send_json({
            "backups": all_entries,
            "backup_enabled": config.backup_saves_enabled,
            "keep_n": config.backup_saves_keep_n,
        })

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
            row = conn.execute("""
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
            """, (int(game_id),)).fetchone()
        if not row:
            ctx._send_json({"error": "not found"})
            return
        result = dict(row)
        # RA data lookup from local cache
        try:
            import json as _json
            from rom_manager.retroachievements.ra_platform_ids import get_ra_console_id
            from rom_manager.retroachievements.ra_client import _parse_game_list
            _plat = result.get("platform") or ""
            _md5  = result.get("md5") or ""
            if _plat and _md5:
                _cid = get_ra_console_id(_plat)
                if _cid:
                    _cf = config.project_root / ".rommgr" / "ra_cache" / f"ra_hashes_{_cid}.json"
                    if _cf.exists():
                        _key = (_cid, _cf.stat().st_mtime)
                        if _key not in _ra_hash_cache:
                            try:
                                _hl = _parse_game_list(_json.loads(_cf.read_text(encoding="utf-8")))
                            except Exception:
                                _hl = {}
                            _ra_hash_cache[_key] = _hl
                        _rg = _ra_hash_cache[_key].get(_md5.lower())
                        if _rg:
                            result["ra_game_id"]      = _rg.id
                            result["ra_title"]        = _rg.title
                            result["ra_achievements"] = _rg.achievements
                            result["ra_points"]       = _rg.points
        except Exception:
            pass
        # saves count by stem matching
        try:
            import os as _os2
            _sp  = result.get("source_path") or ""
            _stem = _os2.path.splitext(_os2.path.basename(_sp))[0]
            if _stem:
                with repository.connect() as _sc2:
                    _row2 = _sc2.execute(
                        "SELECT COUNT(*) FROM saves WHERE original_path LIKE ?",
                        (f"%{_stem}%",),
                    ).fetchone()
                    result["saves_count"] = _row2[0] if _row2 else 0
        except Exception:
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

        api_key  = config.ra_api_key
        username = config.ra_username
        if not api_key or not username:
            ctx._send_json({"error": "retroachievements.api_key and retroachievements.username must be configured"})
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
            "total":          int(data.get("NumAchievements", 0) or 0),
            "unlocked":       int(data.get("NumAwardedToUser", 0) or 0),
            "hardcore":       int(data.get("NumAwardedToUserHardcore", 0) or 0),
            "points_earned":  int(data.get("ScoreAchieved", 0) or 0),
            "points_total":   int(data.get("PossibleScore", 0) or 0),
            "_ts":            time.time(),
        }
        _ra_progress_cache[cache_key] = result
        ctx._send_json(result)

    # ── POST /api/set-play-status ────────────────────────────────────────────
    @router.post("/api/set-play-status")
    def post_set_play_status(ctx) -> None:
        data = ctx._post_data
        game_id = data.get("game_id")
        status  = data.get("status") or None
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
        if "notes" in data:
            repository.set_notes(gid, data["notes"] or None)
        if "canonical_title" in data:
            repository.set_canonical_title(gid, data["canonical_title"])
        _meta_fields = {k: v for k, v in data.items()
                        if k in {"year", "genre", "publisher", "developer", "description", "rating"}}
        if _meta_fields:
            repository.upsert_metadata_manual(gid, **_meta_fields)
        ctx._send_json({"ok": True})

    # ── POST /api/toggle-favorite ────────────────────────────────────────────
    @router.post("/api/toggle-favorite")
    def post_toggle_favorite(ctx) -> None:
        data = ctx._post_data
        game_id = data.get("game_id")
        if not game_id:
            ctx._send_json({"error": "game_id required"})
            return
        new_val = repository.toggle_favorite(int(game_id))
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
        if action == "remove":
            repository.remove_tag(int(game_id), tag)
        else:
            repository.add_tag(int(game_id), tag)
        ctx._send_json({"ok": True, "tags": repository.get_tags(int(game_id))})

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
            ctx._send_json({"error": "RetroArch no configurado. Ajusta retroarch_path en Settings."})
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
        backup_path_str   = data.get("backup_path", "").strip()
        original_save_str = data.get("original_save", "").strip()
        if not backup_path_str or not original_save_str:
            ctx._send_json({"error": "backup_path and original_save required"})
            return
        from rom_manager.backup.save_backup import restore_backup
        bp = Path(backup_path_str)
        tp = Path(original_save_str)
        if config.library_root and not str(tp).startswith(str(config.library_root)):
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
        m = srv_mod

        def _do_backup_now() -> None:
            try:
                import rom_manager.web.server as _srv
                from rom_manager.backup.save_backup import create_saves_zip
                saves_dirs = []
                if config.library_root and config.library_root.exists():
                    saves_dirs.append(config.library_root)
                for src in config.sync_sources:
                    p = Path(src.local_dir)
                    if p.exists() and p not in saves_dirs:
                        saves_dirs.append(p)
                zip_path = create_saves_zip(
                    saves_dirs,
                    set(config.save_extensions),
                    config.data_dir / "saves-backup" / "saves-zips",
                )
                import time as _t
                _srv._job_results["backup_now"] = {
                    "ok": True,
                    "zip": str(zip_path),
                    "size": zip_path.stat().st_size,
                    "result_ts": str(_t.time()),
                }
            except Exception as exc:
                import time as _t
                import rom_manager.web.server as _srv
                _srv._job_results["backup_now"] = {
                    "ok": False, "error": str(exc), "result_ts": str(_t.time()),
                }
            finally:
                import rom_manager.web.server as _srv
                with _srv._job_lock:
                    _srv._jobs["backup_now"] = False

        with m._job_lock:
            if m._jobs.get("backup_now"):
                ctx._send_json({"status": "already_running"})
                return
            m._jobs["backup_now"] = True
        threading.Thread(target=_do_backup_now, daemon=True).start()
        ctx._send_json({"status": "started"})

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
                        f.name for f in dat_dir.iterdir()
                        if f.suffix.lower() in {".dat", ".xml"}
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

        ctx._send_json({
            "total_unmatched": total_unmatched,
            "loaded_dats": sorted(loaded_dats),
            "platforms": platforms,
        })
