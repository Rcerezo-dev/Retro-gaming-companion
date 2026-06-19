"""ES-DE library report and export routes.

Registered onto the shared router by ``register_reports``; the orchestrator in
``esde/__init__.py`` calls it. Covers the library report (JSON for the UI),
the downloadable HTML/JSON/CSV reports and the RetroArch ``.lpl`` playlist export.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.jobs.manager import JobManager
    from rom_manager.web.router import Router

_logger = logging.getLogger(__name__)


def register_reports(
    router: Router,
    *,
    config: AppConfig,
    repository: LibraryRepository,
    get_repo_fn: Callable[[str], LibraryRepository],
    job_manager: JobManager,
) -> None:
    """Register library-report and export (html/json/csv/lpl) routes."""

    from rom_manager.reports import build_report, to_csv
    from rom_manager.reports import to_json as _to_json
    from rom_manager.web.builders.library import _build_library_report

    # ── GET /api/library-report ───────────────────────────────────────────────
    @router.get("/api/library-report")
    def get_library_report(ctx) -> None:
        qs = ctx._qs
        rpt_path = qs.get("path", [None])[0] or str(config.library_root or "")
        if not rpt_path:
            ctx._send_json({"error": "path parameter required (or set library_root in config)"})
            return
        _rpt_repo = get_repo_fn(rpt_path)
        rpt = _build_library_report(rpt_path, _rpt_repo, config)
        _st = job_manager.get_status()
        rpt["retroachievements"] = _st.get("ra_check_result") or {
            "note": "Ejecuta primero la comprobación de RetroAchievements en la pestaña Tools"
        }
        rpt["chd"] = _st.get("convert_chd_result") or {
            "note": "Ejecuta primero la conversión CHD en la pestaña Tools"
        }
        ctx._send_json(rpt)

    # ── GET /api/report/html ──────────────────────────────────────────────────
    @router.get("/api/report/html")
    def get_report_html(ctx) -> None:
        qs = ctx._qs
        rpt_path = qs.get("path", [None])[0] or str(config.library_root or "")
        if not rpt_path:
            ctx._send(
                400,
                "text/plain; charset=utf-8",
                b"path parameter required (or set library_root in config)",
            )
            return
        from rom_manager.utils.library_report_html import generate_html_report

        _rpt_repo = get_repo_fn(rpt_path)
        rpt = _build_library_report(rpt_path, _rpt_repo, config)
        _st = job_manager.get_status()
        rpt["retroachievements"] = _st.get("ra_check_result") or {}
        rpt["chd"] = _st.get("convert_chd_result") or {}
        html = generate_html_report(rpt)
        ctx._send(200, "text/html; charset=utf-8", html.encode("utf-8"))

    # ── GET /api/report.json ──────────────────────────────────────────────────
    @router.get("/api/report.json")
    def get_report_json(ctx) -> None:
        report = build_report(repository)
        body = _to_json(report).encode()
        ctx._send(
            200,
            "application/json; charset=utf-8",
            body,
            extra_headers={"Content-Disposition": 'attachment; filename="report.json"'},
        )

    # ── GET /api/report.csv ───────────────────────────────────────────────────
    @router.get("/api/report.csv")
    def get_report_csv(ctx) -> None:
        report = build_report(repository)
        body = to_csv(report).encode()
        ctx._send(
            200,
            "text/csv; charset=utf-8",
            body,
            extra_headers={"Content-Disposition": 'attachment; filename="report.csv"'},
        )

    # ── POST /api/export-lpl ──────────────────────────────────────────────────
    @router.post("/api/export-lpl")
    def post_export_lpl(ctx) -> None:
        data = ctx._post_data
        if not config.library_root:
            ctx._send_json({"error": "library_root not configured"})
            return
        from rom_manager.utils.lpl_generator import generate_lpl_playlists

        try:
            result = generate_lpl_playlists(
                Path(config.library_root),
                repository,
                output_dir=Path(data["output_dir"]) if data.get("output_dir") else None,
            )
            ctx._send_json(result)
        except Exception as exc:
            ctx._send_json({"error": str(exc)})
