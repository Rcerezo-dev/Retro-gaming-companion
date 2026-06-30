from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.jobs.manager import JobManager
    from rom_manager.web.router import Router

from rom_manager.web.handlers.cloud_auth import register as register_cloud_auth
from rom_manager.web.handlers.sync_cable import register_cable
from rom_manager.web.handlers.sync_cloud import register_cloud

# ── Public entry point ────────────────────────────────────────────────────────


def register(
    router: Router,
    *,
    config: AppConfig,
    repository: LibraryRepository,
    repo_android: LibraryRepository,
    start_ra_check_fn: Callable[[str], bool],
    job_manager: JobManager,
) -> None:
    """Register sync / cable-sync / rclone / ADB / auto-sync routes on *router*."""

    register_cloud_auth(router, config=config)

    register_cable(
        router,
        config=config,
        repository=repository,
        job_manager=job_manager,
    )

    register_cloud(
        router,
        config=config,
        repository=repository,
        repo_android=repo_android,
        job_manager=job_manager,
    )

    # ── POST /api/ra-check ───────────────────────────────────────────────────
    @router.post("/api/ra-check")
    def post_ra_check(ctx) -> None:
        data = ctx._post_data
        api_key = data.get("api_key", "").strip() or config.credentials.ra_api_key
        if not api_key:
            ctx._send_json({"error": "RetroAchievements API key not configured"})
            return
        ctx._send_json(_do_ra_check(api_key, config, repository, job_manager))


# ── RetroAchievements check ───────────────────────────────────────────────────


def _do_ra_check(api_key: str, config, repository, job_manager) -> dict:
    """Start RA check in background using JobManager. Returns start status dict."""
    _cancel = job_manager.cancel_event("ra_check")

    def run() -> None:
        job_result = None
        try:
            from rom_manager.retroachievements.ra_checker import check_library, to_csv
            from rom_manager.scanner.rom_scanner import utc_now

            cache_dir = config.data_dir / "ra_cache"

            def _prog(current: int, total: int, filename: str) -> None:
                job_manager.update_progress(
                    "ra_check", {"current": current, "total": total, "current_file": filename}
                )
                if _cancel.is_set():
                    raise InterruptedError("RA check cancelled")

            try:
                summary = check_library(repository, api_key, cache_dir=cache_dir, progress_cb=_prog)
            except InterruptedError:
                job_result = {
                    "cancelled": True,
                    "total": 0,
                    "supported": 0,
                    "no_support_alternative": 0,
                    "no_support": 0,
                    "no_md5": 0,
                    "platform_unknown": 0,
                    "alternatives_csv": "",
                    "results": [],
                    "alternatives": [],
                    "result_ts": "",
                }
                return

            alternatives_csv = to_csv(summary) if summary.no_support_alternative > 0 else ""
            job_result = {
                "total": summary.total,
                "supported": summary.supported,
                "no_support_alternative": summary.no_support_alternative,
                "no_support": summary.no_support,
                "no_md5": summary.no_md5,
                "platform_unknown": summary.platform_unknown,
                "cancelled": _cancel.is_set(),
                "alternatives_csv": alternatives_csv,
                "results": [
                    {
                        "status": r.status,
                        "original_filename": r.original_filename,
                        "platform": r.platform,
                        "source_path": r.source_path,
                        **(
                            {
                                "alternative": {
                                    "id": r.alternative.id,
                                    "title": r.alternative.title,
                                    "achievements": r.alternative.achievements,
                                    "points": r.alternative.points,
                                }
                            }
                            if r.alternative
                            else {}
                        ),
                    }
                    for r in summary.results
                ],
                "alternatives": [
                    {
                        "platform": r.platform,
                        "filename": r.original_filename,
                        "our_md5": r.our_md5[:12],
                        "ra_id": r.alternative.id,
                        "ra_title": r.alternative.title,
                        "ra_achievements": r.alternative.achievements,
                        "ra_points": r.alternative.points,
                    }
                    for r in summary.results
                    if r.status == "no_support_alternative" and r.alternative
                ],
                "no_support_entries": [
                    {
                        "source_path": r.source_path,
                        "filename": r.original_filename,
                        "platform": r.platform,
                    }
                    for r in summary.results
                    if r.status == "no_support"
                ],
                "result_ts": utc_now(),
            }
        except Exception as exc:
            job_result = {"error": str(exc)}
        finally:
            job_manager.finish("ra_check", job_result)

    return job_manager.start("ra_check", run)
