from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import TYPE_CHECKING

from rom_manager.web.handlers.config_dialogs import register_dialogs
from rom_manager.web.handlers.config_tools import register_tools

_config_lock = threading.Lock()
_logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.web.router import Router

# ── Public entry point ────────────────────────────────────────────────────────


def register(
    router: Router,
    *,
    config: AppConfig,
    set_auto_sync_fn: Callable[[bool], None],
) -> None:
    """Register config and wizard routes on *router*.

    Called once from ``make_handler()`` after the router is created.
    All handler closures capture *config* and *set_auto_sync_fn* by reference.
    """
    from rom_manager.web.builders.misc import _build_config

    register_tools(router, config=config)
    register_dialogs(router)

    @router.get("/api/config")
    def get_config(ctx) -> None:
        ctx._send_json(_build_config(config))

    @router.get("/api/device-status")
    def get_device_status(ctx) -> None:
        """UX-1/2: Check if Android device (ADB or SD card) is connected."""
        from rom_manager.sync.device_detector import is_device_connected

        connected, reason = is_device_connected(config.adb, config.anbernic_root)
        ctx._send_json(
            {
                "connected": connected,
                "reason": reason,
                "device_name": config.device_name or "Android Device",
            }
        )

    @router.post("/api/config")
    def post_config(ctx) -> None:
        _save_config(ctx, ctx._post_data, config, set_auto_sync_fn)

    @router.get("/api/auth/status")
    def get_auth_status(ctx) -> None:
        ctx._send_json({"pin_configured": bool(config.credentials.web_pin_hash)})

    @router.get("/api/health-schedule")
    def get_health_schedule(ctx) -> None:
        ctx._send_json(_read_health_schedule(config))

    @router.get("/api/autostart-status")
    def get_autostart_status(ctx) -> None:
        from rom_manager.utils.tray_icon import get_autostart_status as _get_autostart

        ctx._send_json({"enabled": _get_autostart()})

    @router.post("/api/autostart-toggle")
    def post_autostart_toggle(ctx) -> None:
        from rom_manager.utils.tray_icon import (
            _default_launch_cmd,
        )
        from rom_manager.utils.tray_icon import (
            get_autostart_status as _get_autostart,
        )
        from rom_manager.utils.tray_icon import (
            set_autostart as _set_autostart,
        )

        try:
            new_state = not _get_autostart()
            if new_state:
                _set_autostart(True, _default_launch_cmd())
            else:
                _set_autostart(False)
            ctx._send_json({"ok": True, "enabled": new_state})
        except Exception as exc:
            ctx._send_json({"ok": False, "error": str(exc)})


# ── Handler logic (moved from server.py) ──────────────────────────────────────


def _save_config(
    ctx,
    data: dict,
    config: AppConfig,
    set_auto_sync_fn: Callable[[bool], None],
) -> None:
    """Handle POST /api/config — persist allowed fields and reload in-memory config."""
    from rom_manager.config import load_config, write_config_toml

    allowed = {
        "library.library_root",
        "library.anbernic_root",
        "sync.remote",
        "sync.saves_remote",
        "sync.states_remote",
        "sync.ra_config_dir",
        "sync.ra_config_remote",
        "sync.cheats_dir",
        "sync.cheats_remote",
        "sync.playtime_remote",
        "sync.sources",  # DEVPROFILE-4a: [[sync.sources]] confirmed from "Perfil del dispositivo"
        "screenscraper.user",
        "screenscraper.pass",
        "screenscraper.dev_id",
        "screenscraper.dev_pass",
        "tools.chdman",
        "tools.adb",
        "retroachievements.api_key",
        "retroachievements.username",
        "sync.auto_sync_enabled",
        "sync.auto_sync_direction",
        "sync.auto_sync_android_path",
        "sync.conflict_policy",
        "inbox.path",
        "inbox.target_root",
        "inbox.auto_process",
        "inbox.delete_source",
        "android.device_name",
        "web.host",
        "launchers.retroarch",
        "launchers.esde",
        "backup.saves_enabled",
        "backup.saves_keep_n",
        "notifications.desktop",
    }
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        ctx._send_json({"error": "No recognised fields to update"})
        return

    write_config_toml(config.project_root, updates)

    # Reload in-memory config so changes take effect without restart.
    # Lock prevents concurrent saves from interleaving partial field writes.
    new_cfg = load_config(config.project_root)
    with _config_lock:
        config.library_root = new_cfg.library_root
        config.anbernic_root = new_cfg.anbernic_root
        config.device_name = new_cfg.device_name
        config.sync = new_cfg.sync
        config.credentials = new_cfg.credentials
        config.chdman = new_cfg.chdman
        config.adb = new_cfg.adb
        config.inbox = new_cfg.inbox
        config.web_host = new_cfg.web_host
        config.retroarch_path = new_cfg.retroarch_path
        config.esde_path = new_cfg.esde_path
        config.launcher_cores = new_cfg.launcher_cores
        config.backup = new_cfg.backup
        config.notify_desktop = new_cfg.notify_desktop
    set_auto_sync_fn(new_cfg.sync.auto_sync_enabled)

    ctx._send_json({"saved": list(updates.keys())})


def _read_health_schedule(config: AppConfig) -> dict:
    """Return health-check schedule info for GET /api/health-schedule."""
    import datetime as _dt

    from rom_manager.web.daemons import _HEALTH_CHECK_INTERVAL_DAYS as _INTERVAL_DAYS
    from rom_manager.web.daemons import _read_health_schedule as _read_raw

    data = _read_raw(config)

    last_run_at = data.get("last_run_at")
    next_run_at: str | None = None
    overdue = False
    if last_run_at:
        try:
            last = _dt.datetime.fromisoformat(last_run_at.replace("Z", "+00:00"))
            nxt = last + _dt.timedelta(days=_INTERVAL_DAYS)
            next_run_at = nxt.strftime("%Y-%m-%dT%H:%M:%SZ")
            overdue = _dt.datetime.now(tz=_dt.UTC) >= nxt
        except Exception:
            _logger.debug("No se pudo calcular next_run del health schedule", exc_info=True)

    return {
        "last_run_at": last_run_at,
        "next_run_at": next_run_at,
        "last_ok": data.get("last_ok"),
        "last_corrupted": data.get("last_corrupted"),
        "last_missing": data.get("last_missing"),
        "overdue": overdue,
    }
