from __future__ import annotations

from rom_manager.web.jobs.manager import JobManager

# ── Background job state ──────────────────────────────────────────────────
# Single source of truth for all background jobs (running flags, results,
# progress, cancel events). The legacy _job_lock / _jobs / _job_results /
# _*_progress / _*_cancel globals were removed in ARC-JM-6.
_job_manager = JobManager()

# ── Inbox watcher status (poblado por el daemon de inbox) ──────────────────
# Nota: todo el progreso/cancelación de jobs vive ahora en JobManager (_job_manager).
_inbox_watcher_status: dict = {
    "watching": False,
    "last_check": None,
    "pending_files": 0,
    "trigger_ts": 0,
}

# ── ScreenScraper: último snapshot de cuota ────────────────────────────────
_ss_last_quota: dict = {}

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

# ── Tokens efímeros de setup Anbernic (ANBERNIC-UX-3) ──────────────────────
# Protegen /s y /api/rclone-export-config fuera de loopback. 10 min de vida.
# ANBERNIC-UX-10: lista (no un slot único) — abrir la pestaña Anbernic en dos
# sitios a la vez no debe invalidar el token ya copiado en el primero.
_anbernic_setup_tokens: list = []

# ── HTTP / tray instances (set por serve()) ───────────────────────────────
_tray_instance = None  # type: ignore[assignment]
_httpd_instance = None  # type: ignore[assignment]
