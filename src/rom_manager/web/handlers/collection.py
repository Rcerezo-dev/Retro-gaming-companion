from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.router import Router


# ── Public entry point ────────────────────────────────────────────────────────

def register(
    router: "Router",
    *,
    config: "AppConfig",
    repository: "LibraryRepository",
    repo_android: "LibraryRepository",
) -> None:
    """Register collection / library-data routes on *router*."""
    from rom_manager.web.response_builders import _build_library_diff

    # ── GET /api/collection-stats ─────────────────────────────────────────────
    @router.get("/api/collection-stats")
    def get_collection_stats(ctx) -> None:
        data = _build_missing_data(config, repository)
        ctx._send_json({
            "platforms": [
                {k: v for k, v in p.items() if k != "entries"}
                for p in data
            ]
        })

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
        ctx._send_json(_build_library_diff(repository, repo_android, config))

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

def _build_missing_data(config: "AppConfig", repository: "LibraryRepository") -> list[dict]:
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
        results.append({
            "platform": platform_label,
            "total": total,
            "in_library": in_lib,
            "missing": missing,
            "coverage_pct": round(100.0 * in_lib / total, 1) if total > 0 else 0.0,
            "entries": missing_entries,
        })

    results.sort(key=lambda r: r["platform"])
    return results
