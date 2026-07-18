from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

# ── Job names (canonical) ─────────────────────────────────────────────────────
JOB_NAMES: tuple[str, ...] = (
    "scan",
    "match",
    "sync",
    "convert_chd",
    "convert_cso",
    "scrape",
    "extract_zip",
    "health_check",
    "ra_check",
    "cable_sync",
    "apply",
    "inbox",
    "setup",
    "backup_now",
    "tree_diff",
    "verify_chd",
    "playtime_scan",
)


class JobManager:
    """Centralised state for background jobs.

    Replaces the 11 module-level variables in server.py
    (``_job_lock``, ``_jobs``, ``_job_results``, ``_*_progress``, …).

    Usage (future — Phase 1)::

        jobs = JobManager()

        def _do_scan():
            try:
                jobs.update_progress("scan", {"files_seen": 0, ...})
                # ... work ...
                jobs.finish("scan", {"ok": True, "roms": 42})
            finally:
                jobs.finish("scan", {"ok": False, "error": "..."})

        def handle_start_scan(ctx):
            result = jobs.start("scan", _do_scan)
            ctx._send_json(result)
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._running: dict[str, bool] = {name: False for name in JOB_NAMES}
        self._results: dict[str, dict[str, Any]] = {}
        self._progress: dict[str, dict[str, Any]] = {}

        # Per-job cancel events
        self._cancel: dict[str, threading.Event] = {name: threading.Event() for name in JOB_NAMES}

    # ── Job lifecycle ─────────────────────────────────────────────────────────

    def start(self, job_id: str, fn: Callable[[], None]) -> dict[str, str]:
        """Start *job_id* in a daemon thread if not already running.

        Returns ``{"status": "started"}`` or ``{"status": "already_running"}``.
        *fn* is responsible for calling :meth:`finish` in its ``finally`` block.
        """
        with self._lock:
            if self._running.get(job_id, False):
                return {"status": "already_running"}
            self._running[job_id] = True
            self._cancel[job_id].clear()
        threading.Thread(target=fn, daemon=True).start()
        return {"status": "started"}

    def update_progress(self, job_id: str, data: dict[str, Any]) -> None:
        """Merge *data* into the progress dict for *job_id*."""
        with self._lock:
            if job_id in self._progress:
                self._progress[job_id].update(data)
            else:
                self._progress[job_id] = dict(data)

    def finish(self, job_id: str, result: dict[str, Any] | None = None) -> None:
        """Mark *job_id* as done and optionally store its result."""
        with self._lock:
            self._running[job_id] = False
            self._progress.pop(job_id, None)
            if result is not None:
                self._results[job_id] = result

    def cancel(self, job_id: str) -> None:
        """Set the cancel event for *job_id* (job must check it periodically)."""
        self._cancel[job_id].set()

    def is_cancel_requested(self, job_id: str) -> bool:
        return self._cancel[job_id].is_set()

    def cancel_event(self, job_id: str) -> threading.Event:
        """Return the cancel Event so workers can pass it directly to I/O helpers."""
        return self._cancel[job_id]

    def clear_result(self, job_id: str) -> None:
        with self._lock:
            self._results.pop(job_id, None)

    # ── Status snapshot ───────────────────────────────────────────────────────

    def get_status(self) -> dict[str, Any]:
        """Return a status dict compatible with ``/api/job-status``.

        This mirrors the existing hand-built dict in server.py so that
        the frontend sees no change during the Phase 1 migration.
        """
        with self._lock:
            r = self._results
            p = self._progress
            running = dict(self._running)

        def _prog(key: str) -> dict | None:
            d = p.get(key)
            return dict(d) if d else None

        return {
            # running flags
            "scan_running": running.get("scan", False),
            "match_running": running.get("match", False),
            "sync_running": running.get("sync", False),
            "convert_chd_running": running.get("convert_chd", False),
            "convert_cso_running": running.get("convert_cso", False),
            "scrape_running": running.get("scrape", False),
            "extract_zip_running": running.get("extract_zip", False),
            "health_check_running": running.get("health_check", False),
            "ra_check_running": running.get("ra_check", False),
            "cable_sync_running": running.get("cable_sync", False),
            "apply_running": running.get("apply", False),
            "inbox_running": running.get("inbox", False),
            "setup_running": running.get("setup", False),
            "backup_now_running": running.get("backup_now", False),
            "tree_diff_running": running.get("tree_diff", False),
            "verify_chd_running": running.get("verify_chd", False),
            "playtime_scan_running": running.get("playtime_scan", False),
            # results
            "scan_result": r.get("scan"),
            "match_result": r.get("match"),
            "sync_result": r.get("sync"),
            "convert_chd_result": r.get("convert_chd"),
            "convert_cso_result": r.get("convert_cso"),
            "scrape_result": r.get("scrape"),
            "extract_zip_result": r.get("extract_zip"),
            "health_check_result": r.get("health_check"),
            "ra_check_result": r.get("ra_check"),
            "cable_sync_result": r.get("cable_sync"),
            "apply_result": r.get("apply"),
            "inbox_result": r.get("inbox"),
            "setup_result": r.get("setup"),
            "backup_now_result": r.get("backup_now"),
            "tree_diff_result": r.get("tree_diff"),
            "verify_chd_result": r.get("verify_chd"),
            "playtime_scan_result": r.get("playtime_scan"),
            # progress
            "chd_progress": _prog("convert_chd"),
            "cso_progress": _prog("convert_cso"),
            "scrape_progress": _prog("scrape"),
            "zip_progress": _prog("extract_zip"),
            "health_progress": _prog("health_check"),
            "ra_progress": _prog("ra_check"),
            "cable_progress": _prog("cable_sync"),
            "scan_progress": _prog("scan"),
            "apply_progress": _prog("apply"),
            "inbox_progress": _prog("inbox"),
            "setup_progress": _prog("setup"),
            "verify_chd_progress": _prog("verify_chd"),
        }
