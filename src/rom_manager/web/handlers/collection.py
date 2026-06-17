from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.router import Router


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
    import sys

    from rom_manager.web.builders.diff import _build_library_diff
    from rom_manager.web.builders.misc import _build_assets

    print(f"[collection.register] Starting registration, router={router}", file=sys.stderr)

    # ── GET /api/platform-stats ───────────────────────────────────────────────
    @router.get("/api/platform-stats")
    def get_platform_stats(ctx) -> None:
        qs = getattr(ctx, "_qs", {})
        src_root = qs.get("root", [None])[0] or None
        ps_repo = get_repo_fn(src_root or "")
        with ps_repo.connect() as conn:
            if src_root:
                rows = conn.execute(
                    "SELECT platform, COUNT(*) AS cnt FROM games "
                    "WHERE source_path LIKE ? AND file_type = 'rom' "
                    "GROUP BY platform ORDER BY cnt DESC",
                    [src_root.rstrip("/\\") + "%"],
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT platform, COUNT(*) AS cnt FROM games "
                    "WHERE file_type = 'rom' "
                    "GROUP BY platform ORDER BY cnt DESC"
                ).fetchall()
        ctx._send_json(
            {
                "platforms": [
                    {"platform": r["platform"] or "?", "total_games": r["cnt"]} for r in rows
                ]
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

    # ── POST /api/sync-roms (B3-4) ───────────────────────────────────────────
    @router.post("/api/sync-roms")
    def post_sync_roms(ctx) -> None:
        import shutil
        from pathlib import Path

        items = (ctx._post_data or {}).get("items", [])
        if not items:
            ctx._send_json({"synced": 0, "errors": []})
            return

        connected, reason = config.is_device_connected()
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
