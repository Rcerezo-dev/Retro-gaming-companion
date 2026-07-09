"""ES-DE library maintenance routes: health check, ZIP/cue+bin cleanup, junk delete.

Registered onto the shared router by ``register_maintenance``; the orchestrator
in ``esde/__init__.py`` calls it. The health check runs as a background job via
the JobManager; the cleanup/junk routes are synchronous filesystem operations.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.jobs.manager import JobManager
    from rom_manager.web.router import Router

_logger = logging.getLogger(__name__)


def register_maintenance(
    router: Router,
    *,
    config: AppConfig,
    repository: LibraryRepository,
    job_manager: JobManager,
) -> None:
    """Register health-check, cleanup-zips, cleanup-cue-bin and junk-delete routes."""

    # ── POST /api/health-check ────────────────────────────────────────────────
    @router.post("/api/health-check")
    def post_health_check(ctx) -> None:
        _cancel = job_manager.cancel_event("health_check")

        def run() -> None:
            job_result = None
            try:
                from rom_manager.scanner.rom_scanner import utc_now
                from rom_manager.utils.health_checker import check_library_health

                def progress_cb(current: int, total: int, filename: str) -> None:
                    job_manager.update_progress(
                        "health_check",
                        {"current": current, "total": total, "current_file": filename},
                    )

                summary = check_library_health(
                    repository, progress_cb=progress_cb, cancel_event=_cancel
                )
                job_result = {
                    "ok": summary.ok,
                    "corrupted": summary.corrupted,
                    "missing": summary.missing,
                    "cancelled": _cancel.is_set(),
                    "issues": [
                        {
                            "source_path": r.source_path,
                            "status": r.status,
                            "stored_sha1": r.stored_sha1[:12],
                            "computed_sha1": r.computed_sha1[:12] if r.computed_sha1 else "",
                            "platform": r.platform,
                            "canonical_title": r.canonical_title,
                        }
                        for r in summary.results
                    ],
                    "result_ts": utc_now(),
                }
                from rom_manager.web.server import _write_health_schedule

                _write_health_schedule(
                    config, ok=summary.ok, corrupted=summary.corrupted, missing=summary.missing
                )
                if not _cancel.is_set() and config.notify_desktop:
                    from rom_manager.utils.notifier import notify

                    if summary.corrupted or summary.missing:
                        notify(
                            "Retro Vault — Health Check",
                            f"⚠ {summary.corrupted} corruptos, {summary.missing} desaparecidos — revisa la pestaña Tools",
                        )
                    else:
                        notify(
                            "Retro Vault — Health Check",
                            f"✓ {summary.ok} ROMs verificados, sin problemas",
                        )
            except Exception as exc:
                job_result = {"error": str(exc)}
            finally:
                job_manager.finish("health_check", job_result)

        ctx._send_json(job_manager.start("health_check", run))

    # ── POST /api/cleanup-zips ────────────────────────────────────────────────
    @router.post("/api/cleanup-zips")
    def post_cleanup_zips(ctx) -> None:
        data = ctx._post_data
        source_path_str = data.get("source_path", "").strip()
        if not source_path_str:
            ctx._send_json({"error": "source_path is required"})
            return
        source = Path(source_path_str).resolve()
        deleted = failed = 0
        freed_bytes = 0
        for zp in source.rglob("*.zip"):
            try:
                freed_bytes += zp.stat().st_size
                os.remove(zp)
                deleted += 1
            except OSError:
                failed += 1
        ctx._send_json({"deleted": deleted, "failed": failed, "freed_bytes": freed_bytes})

    # ── POST /api/cleanup-cue-bin ─────────────────────────────────────────────
    @router.post("/api/cleanup-cue-bin")
    def post_cleanup_cue_bin(ctx) -> None:
        data = ctx._post_data
        source_path_str = data.get("source_path", "").strip()
        if not source_path_str:
            ctx._send_json({"error": "source_path is required"})
            return
        source = Path(source_path_str).resolve()
        deleted = failed = skipped = 0
        freed_bytes = 0
        for cue in source.rglob("*.cue"):
            chd = cue.with_suffix(".chd")
            if not chd.exists():
                skipped += 1
                continue
            from rom_manager.converters.chd_converter import parse_bins_from_cue

            bins = parse_bins_from_cue(cue)
            for f in [cue, *bins]:
                try:
                    freed_bytes += f.stat().st_size
                    os.remove(f)
                    deleted += 1
                except OSError:
                    failed += 1
        ctx._send_json(
            {"deleted": deleted, "failed": failed, "skipped": skipped, "freed_bytes": freed_bytes}
        )

    # ── POST /api/junk-scan ───────────────────────────────────────────────────
    @router.post("/api/junk-scan")
    def post_junk_scan(ctx) -> None:
        # ponytail: síncrono como el original pre-refactor; es un walk local rápido
        folder = ctx._post_data.get("path", "").strip() or (
            str(config.library_root) if config.library_root else ""
        )
        if not folder:
            ctx._send_json({"error": "path required"})
            return
        from rom_manager.web.builders.folders import _build_junk_scan

        # JUNK-SMART-1: rutas con match de catálogo — evidencia de "no es basura"
        with repository.connect() as conn:
            rows = conn.execute(
                "SELECT source_path FROM games WHERE canonical_title IS NOT NULL"
            ).fetchall()
        matched = {os.path.normpath(r[0]).lower() for r in rows}
        ctx._send_json(_build_junk_scan(folder, matched_paths=matched))

    # ── POST /api/junk-delete ─────────────────────────────────────────────────
    @router.post("/api/junk-delete")
    def post_junk_delete(ctx) -> None:
        data = ctx._post_data
        paths_to_delete = data.get("paths", [])
        dry_run = bool(data.get("dry_run", True))
        deleted = failed = 0
        freed_bytes = 0
        errors: list[str] = []
        for fp in paths_to_delete:
            try:
                p = Path(fp)
                if p.is_file():
                    sz = p.stat().st_size
                    if not dry_run:
                        p.unlink()
                    deleted += 1
                    freed_bytes += sz
            except OSError as exc:
                failed += 1
                errors.append(str(exc))
        ctx._send_json(
            {
                "deleted": deleted,
                "failed": failed,
                "freed_bytes": freed_bytes,
                "dry_run": dry_run,
                "errors": errors[:10],
            }
        )
