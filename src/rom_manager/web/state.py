from __future__ import annotations

import threading

from rom_manager.web.jobs.manager import JobManager

# ── Background job state ──────────────────────────────────────────────────
_job_lock = threading.Lock()
_jobs: dict[str, bool] = {
    "scan": False,
    "match": False,
    "sync": False,
    "convert_chd": False,
    "convert_cso": False,
    "scrape": False,
    "extract_zip": False,
    "health_check": False,
    "ra_check": False,
    "cable_sync": False,
    "apply": False,
    "inbox": False,
    "setup": False,
    "backup_now": False,
    "tree_diff": False,
    "verify_chd": False,
}
_job_results: dict[str, dict] = {}
_job_manager = JobManager()

# ── Progress dicts ────────────────────────────────────────────────────────
_chd_progress: dict = {}  # {"current": int, "total": int, "current_file": str}
_cso_progress: dict = {}  # {"current": int, "total": int, "current_file": str}
_scrape_progress: dict = {}  # {"current": int, "total": int, "found": int, "current_game": str}
_zip_progress: dict = {}  # {"current": int, "total": int, "current_file": str}
_health_progress: dict = {}  # {"current": int, "total": int, "current_file": str}
_ra_progress: dict = {}  # {"current": int, "total": int, "current_file": str}
_cable_progress: dict = {}  # {"copied": int, "total_files": int, "bytes_copied": int, ...}
_scan_progress: dict = {}  # {"files_seen": int, "roms_detected": int, "current_path": str}
_apply_progress: dict = {}  # {"current": int, "total": int, "current_file": str}
_inbox_progress: dict = {}  # {"step": str, "step_num": int, "total_steps": int, ...}
_setup_progress: dict = {}  # {"step": str, "step_num": int, "total_steps": int, "pct": int}
_verify_chd_progress: dict = {}  # {"current": int, "total": int, "current_file": str}
_inbox_watcher_status: dict = {
    "watching": False,
    "last_check": None,
    "pending_files": 0,
    "trigger_ts": 0,
}

# ── Cancel events ─────────────────────────────────────────────────────────
_scan_cancel: threading.Event = threading.Event()
_cable_cancel: threading.Event = threading.Event()
_chd_cancel: threading.Event = threading.Event()
_verify_chd_cancel: threading.Event = threading.Event()
_cso_cancel: threading.Event = threading.Event()
_zip_cancel: threading.Event = threading.Event()
_health_cancel: threading.Event = threading.Event()
_ra_cancel: threading.Event = threading.Event()
_scrape_cancel: threading.Event = threading.Event()
_match_cancel: threading.Event = threading.Event()
_ss_last_quota: dict = {}  # último snapshot de cuota de ScreenScraper

# ── Auto-sync / SD daemon state ───────────────────────────────────────────
_auto_sync_enabled: bool = True
_auto_sync_last_devices: set = set()
_auto_sync_status: dict = {
    "state": "waiting",
    "last_sync_at": None,
    "last_device": None,
    "last_error": None,
}
_sd_sync_status: dict = {
    "state": "waiting",
    "last_sync_at": None,
    "drive": None,
}

# ── HTTP / tray instances (set por serve()) ───────────────────────────────
_tray_instance = None  # type: ignore[assignment]
_httpd_instance = None  # type: ignore[assignment]
