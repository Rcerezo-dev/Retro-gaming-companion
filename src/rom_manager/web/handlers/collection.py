from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.router import Router

_logger = logging.getLogger(__name__)


# ── Public entry point ────────────────────────────────────────────────────────


def register(
    router: Router,
    *,
    config: AppConfig,
    repository: LibraryRepository,
    repo_android: LibraryRepository,
    get_repo_fn,
) -> None:
    """Register collection / library-data routes on *router*."""
    from rom_manager.services.storage_service import delete_storage_items
    from rom_manager.sync.adb_transport import resolve_single_device_transport
    from rom_manager.web.builders.diff import _build_library_diff
    from rom_manager.web.builders.misc import _build_assets
    from rom_manager.web.builders.overrides import _build_overrides

    _logger.debug("Starting registration, router=%s", router)

    def _adb_transport():
        # TABS-FIX-1a: resuelto por request (no cacheado) — el dispositivo puede
        # conectarse/desconectarse entre cargar el diff y pulsar "Borrar".
        return resolve_single_device_transport(config.adb)

    # ── GET /api/platform-stats ───────────────────────────────────────────────
    @router.get("/api/platform-stats")
    def get_platform_stats(ctx) -> None:
        # ANBERNIC-PICK-7: size_bytes/tagged_cnt añadidos para el asistente
        # guiado — reutiliza esta misma agregación en vez de una nueva.
        qs = getattr(ctx, "_qs", {})
        src_root = qs.get("root", [None])[0] or None
        ps_repo = get_repo_fn(src_root or "")
        tagged_sql = (
            "SUM(CASE WHEN id IN (SELECT game_id FROM game_tags WHERE tag = 'anbernic')"
            " THEN 1 ELSE 0 END) AS tagged_cnt"
        )
        with ps_repo.connect() as conn:
            if src_root:
                rows = conn.execute(
                    f"SELECT platform, COUNT(*) AS cnt, SUM(size_bytes) AS total_size, {tagged_sql}"
                    " FROM games WHERE source_path LIKE ? AND file_type = 'rom' "
                    "GROUP BY platform ORDER BY cnt DESC",
                    [src_root.rstrip("/\\") + "%"],
                ).fetchall()
            else:
                rows = conn.execute(
                    f"SELECT platform, COUNT(*) AS cnt, SUM(size_bytes) AS total_size, {tagged_sql}"
                    " FROM games WHERE file_type = 'rom' "
                    "GROUP BY platform ORDER BY cnt DESC"
                ).fetchall()
        ctx._send_json(
            {
                "platforms": [
                    {
                        "platform": r["platform"] or "?",
                        "total_games": r["cnt"],
                        "total_size": r["total_size"] or 0,
                        "tagged_count": r["tagged_cnt"] or 0,
                    }
                    for r in rows
                ]
            }
        )

    # ── GET /api/collection-stats-v2 ──────────────────────────────────────────
    @router.get("/api/collection-stats-v2")
    def get_collection_stats_v2(ctx) -> None:
        """Agregados del panel Stats de Análisis (COLECCION-UX: restaurado).

        Existía antes del refactor 487aa91 (server.py monolítico) y se perdió
        al trocearlo — mismo destino que /api/junk-scan (MEJ-6). El frontend
        (loadCollectionStatsV2) siguió llamándolo contra un 404 silencioso.
        """
        qs = getattr(ctx, "_qs", {})
        src_root = qs.get("root", [None])[0] or None
        stats_repo = get_repo_fn(src_root or "")
        where = "WHERE file_type = 'rom'"
        params: list = []
        if src_root:
            where += " AND source_path LIKE ?"
            params.append(src_root.rstrip("/\\") + "%")
        with stats_repo.connect() as conn:
            by_plat = conn.execute(
                f"SELECT COALESCE(platform,'?') AS p, COUNT(*) AS n FROM games {where}"
                " GROUP BY p ORDER BY n DESC",
                params,
            ).fetchall()
            by_status = conn.execute(
                f"SELECT COALESCE(play_status,'Sin estado') AS s, COUNT(*) AS n"
                f" FROM games {where} GROUP BY s ORDER BY n DESC",
                params,
            ).fetchall()
            by_region = conn.execute(
                f"SELECT COALESCE(region,'?') AS r, COUNT(*) AS n FROM games {where}"
                " GROUP BY r ORDER BY n DESC",
                params,
            ).fetchall()
            favs = conn.execute(
                f"SELECT COUNT(*) AS n FROM games {where} AND is_favorite = 1",
                params,
            ).fetchone()["n"]
        ctx._send_json(
            {
                "total": sum(r["n"] for r in by_plat),
                "favorites": favs,
                "by_platform": [dict(r) for r in by_plat],
                "by_status": [dict(r) for r in by_status],
                "by_region": [dict(r) for r in by_region],
            }
        )

    # ── GET /api/assets ───────────────────────────────────────────────────────
    @router.get("/api/assets")
    def get_assets(ctx) -> None:
        try:
            qs = getattr(ctx, "_qs", {})
            src_root = qs.get("root", [None])[0] or None
            assets_repo = get_repo_fn(src_root or "")
            result = _build_assets(assets_repo, source_root=src_root)
            if not result or "stats" not in result:
                ctx._send_error(500, f"Invalid assets response: {result}")
                return
            ctx._send_json(result)
        except Exception as e:
            import traceback

            ctx._send_error(500, f"Asset query failed: {str(e)} | {traceback.format_exc()}")

    # ── GET /api/assets/orphans ─────────────────────────────────────────────────
    @router.get("/api/assets/orphans")
    def get_assets_orphans(ctx) -> None:
        try:
            qs = getattr(ctx, "_qs", {})
            src_root = qs.get("root", [None])[0] or None
            platform = qs.get("platform", [None])[0] or None
            orphans_repo = get_repo_fn(src_root or "")
            files = orphans_repo.get_orphan_assets(platform=platform, source_root=src_root)
            ctx._send_json({"platform": platform, "files": files})
        except Exception as e:
            import traceback

            ctx._send_error(500, f"Orphan asset query failed: {str(e)} | {traceback.format_exc()}")

    # ── GET /api/asset-image ──────────────────────────────────────────────────
    @router.get("/api/asset-image")
    def get_asset_image(ctx) -> None:
        import mimetypes
        from pathlib import Path

        qs = getattr(ctx, "_qs", {})
        game_id = qs.get("game_id", [None])[0]
        if not game_id:
            ctx._send_error(400, "game_id required")
            return
        try:
            game_id = int(game_id)
        except (ValueError, TypeError):
            ctx._send_error(400, "game_id must be integer")
            return

        # Query metadata for box art path
        with repository.connect() as conn:
            row = conn.execute(
                "SELECT box_art_path FROM game_metadata WHERE game_id = ?", (game_id,)
            ).fetchone()

        if not row or not row["box_art_path"]:
            ctx._send_error(404, "No asset found")
            return

        img_path = Path(row["box_art_path"])
        if not img_path.exists():
            ctx._send_error(404, "Asset file not found")
            return

        # Serve the image file
        try:
            body = img_path.read_bytes()
            mime_type, _ = mimetypes.guess_type(str(img_path))
            mime_type = mime_type or "application/octet-stream"
            ctx._send(200, mime_type, body)
        except Exception as e:
            ctx._send_error(500, f"Could not read asset: {e}")

    # ── GET /api/export-library ───────────────────────────────────────────────
    @router.get("/api/export-library")
    def get_export_library(ctx) -> None:
        import csv as _csv
        import io as _io
        import json as _json

        qs = getattr(ctx, "_qs", {})
        fmt = qs.get("format", ["csv"])[0]
        src_root = qs.get("root", [None])[0] or None
        exp_repo = get_repo_fn(src_root or "")
        rows = exp_repo.get_library_export()
        if fmt == "json":
            body = _json.dumps(rows, ensure_ascii=False, default=str).encode("utf-8")
            ctx._send(
                200,
                "application/json; charset=utf-8",
                body,
                extra_headers={"Content-Disposition": 'attachment; filename="library.json"'},
            )
        else:
            buf = _io.StringIO()
            writer = _csv.writer(buf)
            if rows:
                writer.writerow(rows[0].keys())
                for r in rows:
                    writer.writerow(r.values())
            body = buf.getvalue().encode("utf-8-sig")
            ctx._send(
                200,
                "text/csv; charset=utf-8",
                body,
                extra_headers={"Content-Disposition": 'attachment; filename="library.csv"'},
            )

    # ── GET /api/export-wishlist ──────────────────────────────────────────────
    @router.get("/api/export-wishlist")
    def get_export_wishlist(ctx) -> None:
        import csv as _csv
        import io as _io

        qs = getattr(ctx, "_qs", {})
        src_root = qs.get("root", [None])[0] or None
        wl_repo = get_repo_fn(src_root or "")
        rows = wl_repo.get_wishlist()
        buf = _io.StringIO()
        writer = _csv.writer(buf)
        writer.writerow(["Title", "Platform", "Region", "Notes"])
        for r in rows:
            writer.writerow(
                [r.get("title", ""), r.get("platform", ""), r.get("region", ""), r.get("notes", "")]
            )
        body = buf.getvalue().encode("utf-8-sig")
        ctx._send(
            200,
            "text/csv; charset=utf-8",
            body,
            extra_headers={"Content-Disposition": 'attachment; filename="wishlist.csv"'},
        )

    # ── GET /api/platform-health ─────────────────────────────────────────────
    @router.get("/api/platform-health")
    def get_platform_health(ctx) -> None:
        qs = getattr(ctx, "_qs", {})
        src_root = qs.get("root", [None])[0] or None
        ph_repo = get_repo_fn(src_root or "")
        with ph_repo.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    g.platform,
                    COUNT(*) AS total_roms,
                    SUM(CASE WHEN g.canonical_title IS NOT NULL THEN 1 ELSE 0 END) AS matched_roms,
                    SUM(CASE WHEN gm.box_art_path IS NOT NULL THEN 1 ELSE 0 END) AS roms_with_art
                FROM games g
                LEFT JOIN game_metadata gm ON gm.game_id = g.id
                WHERE g.file_type = 'rom'
                GROUP BY g.platform
                ORDER BY total_roms DESC
                """
            ).fetchall()
            # Last scan time per platform root (best approximation: last scan_run)
            last_scan_row = conn.execute(
                "SELECT MAX(finished_at) AS last_scan FROM scan_runs WHERE finished_at IS NOT NULL"
            ).fetchone()
        last_scan = (
            (last_scan_row["last_scan"] or "")[:16].replace("T", " ") if last_scan_row else ""
        )
        ctx._send_json(
            {
                "platforms": [
                    {
                        "platform": r["platform"] or "?",
                        "total_roms": r["total_roms"],
                        "matched_roms": r["matched_roms"],
                        "roms_with_art": r["roms_with_art"],
                        "match_pct": round(100.0 * r["matched_roms"] / r["total_roms"], 1)
                        if r["total_roms"]
                        else 0.0,
                        "art_pct": round(100.0 * r["roms_with_art"] / r["total_roms"], 1)
                        if r["total_roms"]
                        else 0.0,
                    }
                    for r in rows
                ],
                "last_scan": last_scan,
            }
        )

    # ── GET /api/collection-stats ─────────────────────────────────────────────
    @router.get("/api/collection-stats")
    def get_collection_stats(ctx) -> None:
        data = _build_missing_data(config, repository)
        ctx._send_json(
            {"platforms": [{k: v for k, v in p.items() if k != "entries"} for p in data]}
        )

    # ── GET /api/missing ──────────────────────────────────────────────────────
    @router.get("/api/missing")
    def get_missing(ctx) -> None:
        import urllib.parse

        data = _build_missing_data(config, repository)
        qs = getattr(ctx, "_qs", {})
        pf = urllib.parse.unquote_plus(qs.get("platform", [""])[0])
        if pf:
            data = [p for p in data if p["platform"] == pf]
        ctx._send_json({"platforms": data})

    # ── GET /api/library-diff ─────────────────────────────────────────────────
    @router.get("/api/library-diff")
    def get_library_diff(ctx) -> None:
        qs = getattr(ctx, "_qs", {})
        platform = qs.get("platform", [None])[0] or None
        ctx._send_json(_build_library_diff(repository, repo_android, config, platform=platform))

    # ── GET /api/retroarch-overrides (CFG-PORGAME-6) ──────────────────────────
    @router.get("/api/retroarch-overrides")
    def get_retroarch_overrides(ctx) -> None:
        ctx._send_json(_build_overrides(config, _adb_transport()))

    def _override_side_config(side: str) -> tuple[str, object] | None:
        """(config_dir, adb_transport) for 'pc'/'android', or None if *side* is invalid."""
        if side == "pc":
            return config.sync.ra_config_dir, None
        if side == "android":
            return f"{config.sync.auto_sync_android_path}/config", _adb_transport()
        return None

    # ── GET /api/retroarch-override (CFG-PORGAME-7) ────────────────────────────
    @router.get("/api/retroarch-override")
    def get_retroarch_override(ctx) -> None:
        from rom_manager.services.retroarch_overrides_service import read_override

        qs = getattr(ctx, "_qs", {})
        rom = qs.get("rom", [None])[0] or ""
        core = qs.get("core", [None])[0] or ""
        side = qs.get("side", [None])[0] or ""

        resolved = _override_side_config(side)
        if resolved is None:
            ctx._send_error(400, "side debe ser 'pc' o 'android'")
            return
        config_dir, adb_transport = resolved
        if side == "android" and adb_transport is None:
            ctx._send_error(400, "conecta el dispositivo Android por ADB primero")
            return

        try:
            content = read_override(config_dir, rom, core, adb_transport=adb_transport)
        except ValueError as exc:
            ctx._send_error(400, str(exc))
        except FileNotFoundError:
            ctx._send_error(404, f"No existe override para {rom!r} ({core})")
        except OSError as exc:
            ctx._send_error(500, f"Error leyendo override: {exc}")
        else:
            ctx._send_json({"rom": rom, "core": core, "side": side, "content": content})

    # ── POST /api/retroarch-override (CFG-PORGAME-7) ───────────────────────────
    @router.post("/api/retroarch-override")
    def post_retroarch_override(ctx) -> None:
        from rom_manager.services.retroarch_overrides_service import write_override

        data = ctx._post_data or {}
        rom = data.get("rom") or ""
        core = data.get("core") or ""
        side = data.get("side") or ""
        content = data.get("content")
        if content is None:
            ctx._send_error(400, "content requerido")
            return

        resolved = _override_side_config(side)
        if resolved is None:
            ctx._send_error(400, "side debe ser 'pc' o 'android'")
            return
        config_dir, adb_transport = resolved
        if side == "android" and adb_transport is None:
            ctx._send_error(400, "conecta el dispositivo Android por ADB primero")
            return

        try:
            write_override(config_dir, rom, core, content, adb_transport=adb_transport)
        except ValueError as exc:
            ctx._send_error(400, str(exc))
        except OSError as exc:
            ctx._send_error(500, f"Error guardando override: {exc}")
        else:
            ctx._send_json({"ok": True})

    # ── POST /api/retroarch-override/copy (CFG-PORGAME-8) ──────────────────────
    @router.post("/api/retroarch-override/copy")
    def post_retroarch_override_copy(ctx) -> None:
        from rom_manager.services.retroarch_overrides_service import SHARED_CORES, copy_override

        data = ctx._post_data or {}
        rom = data.get("rom") or ""
        core = data.get("core") or ""
        direction = data.get("direction") or ""

        sides = {
            "pc_to_android": ("pc", "android"),
            "android_to_pc": ("android", "pc"),
        }.get(direction)
        if sides is None:
            ctx._send_error(400, "direction debe ser 'pc_to_android' o 'android_to_pc'")
            return
        source_side, dest_side = sides

        # Comprobar el core antes de resolver ADB: un core no compartido es
        # inválido pase lo que pase con el dispositivo, y así no pedimos
        # conectarlo para una copia que nunca iba a tener sentido.
        if core not in SHARED_CORES:
            ctx._send_error(
                400,
                f"{core!r} no es un core compartido entre PC y Android — "
                "copiar este override no tiene sentido en el otro lado",
            )
            return

        source_resolved = _override_side_config(source_side)
        dest_resolved = _override_side_config(dest_side)
        source_config_dir, source_adb = source_resolved
        dest_config_dir, dest_adb = dest_resolved
        if (source_side == "android" and source_adb is None) or (
            dest_side == "android" and dest_adb is None
        ):
            ctx._send_error(400, "conecta el dispositivo Android por ADB primero")
            return

        try:
            result = copy_override(
                rom,
                core,
                source_config_dir=source_config_dir,
                source_adb_transport=source_adb,
                dest_config_dir=dest_config_dir,
                dest_adb_transport=dest_adb,
            )
        except ValueError as exc:
            ctx._send_error(400, str(exc))
        except FileNotFoundError:
            ctx._send_error(404, f"No existe override de origen para {rom!r} ({core})")
        except OSError as exc:
            ctx._send_error(500, f"Error copiando override: {exc}")
        else:
            ctx._send_json({"ok": True, **result})

    # ── POST /api/storage/delete-bulk (STORAGE-MGR-3) ────────────────────────
    @router.post("/api/storage/delete-bulk")
    def post_storage_delete_bulk(ctx) -> None:
        items = (ctx._post_data or {}).get("items", [])
        if not items:
            ctx._send_json({"trashed": 0, "deleted_device": 0, "errors": []})
            return
        ctx._send_json(
            delete_storage_items(repository, repo_android, items, adb_transport=_adb_transport())
        )

    # ── POST /api/sync-roms (B3-4) ───────────────────────────────────────────
    @router.post("/api/sync-roms")
    def post_sync_roms(ctx) -> None:
        import shutil
        from pathlib import Path

        from rom_manager.sync.device_detector import is_device_connected

        items = (ctx._post_data or {}).get("items", [])
        if not items:
            ctx._send_json({"synced": 0, "errors": []})
            return

        connected, reason = is_device_connected(config.adb, config.anbernic_root)
        if not connected:
            ctx._send_error(400, f"Dispositivo no conectado: {reason}")
            return

        anbernic_root = config.anbernic_root
        library_root = config.library_root
        if not anbernic_root:
            ctx._send_error(400, "anbernic_root no configurado")
            return
        if not library_root:
            ctx._send_error(400, "library_root no configurado")
            return

        synced = 0
        errors = []

        for item in items:
            sha1 = (item.get("sha1") or "").strip().upper()
            direction = item.get("direction", "")
            if not sha1:
                errors.append({"sha1": sha1, "error": "sha1 vacío"})
                continue
            try:
                if direction == "pc_to_android":
                    with repository.connect() as conn:
                        row = conn.execute(
                            "SELECT source_path, platform FROM games "
                            "WHERE sha1 = ? AND file_type = 'rom' LIMIT 1",
                            (sha1,),
                        ).fetchone()
                    if not row:
                        errors.append(
                            {"sha1": sha1, "error": "SHA1 no encontrado en biblioteca PC"}
                        )
                        continue
                    src = Path(row["source_path"])
                    if not src.exists():
                        errors.append({"sha1": sha1, "error": f"Archivo no existe: {src.name}"})
                        continue
                    dest_dir = Path(anbernic_root) / (row["platform"] or "Unknown")
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest_dir / src.name)
                    synced += 1

                elif direction == "android_to_pc":
                    with repo_android.connect() as conn:
                        row = conn.execute(
                            "SELECT source_path, platform FROM games "
                            "WHERE sha1 = ? AND file_type = 'rom' LIMIT 1",
                            (sha1,),
                        ).fetchone()
                    if not row:
                        errors.append(
                            {"sha1": sha1, "error": "SHA1 no encontrado en biblioteca Android"}
                        )
                        continue
                    src = Path(row["source_path"])
                    if not src.exists():
                        errors.append(
                            {"sha1": sha1, "error": f"Archivo SD no accesible: {src.name}"}
                        )
                        continue
                    dest_dir = library_root / (row["platform"] or "Unknown")
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest_dir / src.name)
                    synced += 1

                else:
                    errors.append({"sha1": sha1, "error": f"Dirección desconocida: {direction}"})
            except Exception as e:
                errors.append({"sha1": sha1, "error": str(e)})

        ctx._send_json({"synced": synced, "errors": errors})

    # ── GET /api/disk-usage (P3) ─────────────────────────────────────────────
    @router.get("/api/disk-usage")
    def get_disk_usage(ctx) -> None:
        import shutil
        from pathlib import Path

        qs = getattr(ctx, "_qs", {})
        src_root = qs.get("root", [None])[0] or None
        du_repo = get_repo_fn(src_root or "")

        with du_repo.connect() as conn:
            rows = conn.execute(
                "SELECT platform, source_path FROM games WHERE file_type = 'rom'"
            ).fetchall()

        by_platform: dict[str, dict] = {}
        for row in rows:
            plat = row["platform"] or "?"
            entry = by_platform.setdefault(plat, {"size_bytes": 0, "rom_count": 0, "missing": 0})
            entry["rom_count"] += 1
            try:
                entry["size_bytes"] += Path(row["source_path"]).stat().st_size
            except OSError:
                entry["missing"] += 1

        def _fmt(n: int) -> str:
            for unit in ("B", "KB", "MB", "GB", "TB"):
                if n < 1024:
                    return f"{n:.1f} {unit}"
                n //= 1024
            return f"{n:.1f} PB"

        platforms = sorted(
            [
                {"platform": p, **v, "size_human": _fmt(v["size_bytes"])}
                for p, v in by_platform.items()
            ],
            key=lambda x: x["size_bytes"],
            reverse=True,
        )
        total = sum(p["size_bytes"] for p in platforms)

        result: dict = {"platforms": platforms, "total_bytes": total, "total_human": _fmt(total)}
        root_path = Path(src_root) if src_root else config.library_root
        if root_path:
            try:
                du = shutil.disk_usage(root_path)
                result["disk_total"] = du.total
                result["disk_used"] = du.used
                result["disk_free"] = du.free
            except OSError:
                pass
        ctx._send_json(result)

    # ── GET /api/operations-timeline ─────────────────────────────────────────
    @router.get("/api/operations-timeline")
    def get_operations_timeline(ctx) -> None:
        qs = getattr(ctx, "_qs", {})
        limit = int(qs.get("limit", ["50"])[0])
        with repository.connect() as conn:
            rows = conn.execute(
                "SELECT id, operation_type, source_path, target_path, result, message, created_at "
                "FROM file_operations ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        ctx._send_json({"operations": [dict(r) for r in rows]})

    # ── GET /api/wishlist ─────────────────────────────────────────────────────
    @router.get("/api/wishlist")
    def get_wishlist(ctx) -> None:
        ctx._send_json({"wishlist": repository.get_wishlist()})

    # ── POST /api/wishlist ────────────────────────────────────────────────────
    @router.post("/api/wishlist")
    def post_wishlist(ctx) -> None:
        data = ctx._post_data
        sha1 = (data.get("sha1") or "").strip().upper()
        if not sha1:
            ctx._send_error(400, "sha1 required")
        elif data.get("remove"):
            repository.remove_wishlist_entry(sha1)
            ctx._send_json({"ok": True, "removed": sha1})
        else:
            repository.upsert_wishlist_entry(
                sha1=sha1,
                title=data.get("title", ""),
                platform=data.get("platform", ""),
                status=data.get("status", "searching"),
                region=data.get("region", ""),
                year=data.get("year", ""),
                dat_source=data.get("dat_source", ""),
            )
            ctx._send_json({"ok": True})


# ── Handler logic (moved from server.py) ──────────────────────────────────────


def _build_missing_data(config: AppConfig, repository: LibraryRepository) -> list[dict]:
    """Load all DAT files and compute missing ROMs vs. the library.

    Returns a list of dicts, one per DAT platform:
    {
        "platform": str,
        "total": int,
        "in_library": int,
        "missing": int,
        "coverage_pct": float,
        "entries": [{"sha1": str, "title": str}, ...]  — only the missing ones
    }
    """
    from rom_manager.catalog.catalog_loader import load_dat_files_by_platform

    platforms = load_dat_files_by_platform(
        config.catalogs_nointro_dir,
        config.catalogs_redump_dir,
    )
    if not platforms:
        return []

    library_sha1s = repository.get_all_rom_sha1s()

    results: list[dict] = []
    for platform_label, entries in platforms:
        missing_entries = [
            {"sha1": sha1, "title": entry.title}
            for sha1, entry in entries.items()
            if sha1 not in library_sha1s
        ]
        total = len(entries)
        missing = len(missing_entries)
        in_lib = total - missing
        results.append(
            {
                "platform": platform_label,
                "total": total,
                "in_library": in_lib,
                "missing": missing,
                "coverage_pct": round(100.0 * in_lib / total, 1) if total > 0 else 0.0,
                "entries": missing_entries,
            }
        )

    results.sort(key=lambda r: r["platform"])
    return results
