from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.web.router import Router


# ── Public entry point ────────────────────────────────────────────────────────

def register(
    router: "Router",
    *,
    config: "AppConfig",
    set_auto_sync_fn: "Callable[[bool], None]",
) -> None:
    """Register config and wizard routes on *router*.

    Called once from ``make_handler()`` after the router is created.
    All handler closures capture *config* and *set_auto_sync_fn* by reference.
    """
    from rom_manager.web.response_builders import _build_config

    @router.get("/api/config")
    def get_config(ctx) -> None:
        ctx._send_json(_build_config(config))

    @router.get("/api/device-status")
    def get_device_status(ctx) -> None:
        """UX-1/2: Check if Android device (ADB or SD card) is connected."""
        connected, reason = config.is_device_connected()
        ctx._send_json({
            "connected": connected,
            "reason": reason,
            "device_name": config.device_name or "Android Device",
        })

    @router.get("/api/wizard-detect")
    def get_wizard_detect(ctx) -> None:
        ctx._send_json(_detect_wizard(config))

    @router.post("/api/config")
    def post_config(ctx) -> None:
        _save_config(ctx, ctx._post_data, config, set_auto_sync_fn)

    @router.get("/api/auth/status")
    def get_auth_status(ctx) -> None:
        ctx._send_json({"pin_configured": bool(config.web_pin_hash)})

    @router.get("/api/health-schedule")
    def get_health_schedule(ctx) -> None:
        ctx._send_json(_read_health_schedule(config))

    @router.get("/api/test-chdman")
    def get_test_chdman(ctx) -> None:
        ctx._send_json(_test_binary_status(
            str(config.chdman) if config.chdman else str(config.project_root / "tools" / "chdman.exe"),
        ))

    @router.get("/api/test-maxcso")
    def get_test_maxcso(ctx) -> None:
        ctx._send_json(_test_binary_status(
            str(config.project_root / "tools" / "maxcso.exe"),
        ))

    @router.get("/api/autostart-status")
    def get_autostart_status(ctx) -> None:
        from rom_manager.utils.tray_icon import get_autostart_status as _get_autostart
        ctx._send_json({"enabled": _get_autostart()})

    @router.post("/api/autostart-toggle")
    def post_autostart_toggle(ctx) -> None:
        from rom_manager.utils.tray_icon import (
            get_autostart_status as _get_autostart,
            set_autostart as _set_autostart,
            _default_launch_cmd,
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

def _detect_wizard(config: "AppConfig") -> dict:
    """Auto-detect RetroArch installation and connected ADB devices for the first-run wizard."""
    import os
    import re

    # --- 1. Scan common RetroArch installation paths ---
    candidates: list[Path] = []
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        candidates.append(Path(appdata) / "RetroArch")
    for drive_letter in ("C", "D", "E"):
        candidates += [
            Path(f"{drive_letter}:\\RetroArch-Win64"),
            Path(f"{drive_letter}:\\RetroArch"),
            Path(f"{drive_letter}:\\Program Files\\RetroArch"),
            Path(f"{drive_letter}:\\Program Files (x86)\\RetroArch"),
        ]

    library_root_suggestion = None
    for ra_dir in candidates:
        cfg_path = ra_dir / "retroarch.cfg"
        if not cfg_path.exists():
            continue
        try:
            text = cfg_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        m = re.search(r'^content_directory\s*=\s*"(.+)"', text, re.MULTILINE)
        if m:
            candidate = m.group(1).strip()
            if candidate not in ("", "default"):
                library_root_suggestion = candidate
                break
        # Fallback: use the RetroArch dir itself as a hint
        if library_root_suggestion is None:
            library_root_suggestion = str(ra_dir)

    # --- 2. Check ADB for connected devices ---
    android_suggestion = None
    device_display = None
    adb_ok = False
    try:
        from rom_manager.sync.adb_transport import list_devices
        devs = list_devices(config.adb)
        adb_ok = True
        ready_devs = [d for d in devs if d.ready]
        if ready_devs:
            dev = ready_devs[0]
            device_display = dev.display or dev.serial
            android_suggestion = config.anbernic_root or "/storage/emulated/0/RetroArch/roms"
    except Exception:
        pass

    return {
        "library_root_suggestion": library_root_suggestion,
        "android_suggestion": android_suggestion,
        "device_display": device_display,
        "adb_ok": adb_ok,
    }


def _save_config(
    ctx,
    data: dict,
    config: "AppConfig",
    set_auto_sync_fn: "Callable[[bool], None]",
) -> None:
    """Handle POST /api/config — persist allowed fields and reload in-memory config."""
    from rom_manager.config import write_config_toml, load_config

    allowed = {
        "library.library_root", "library.anbernic_root", "sync.remote",
        "sync.saves_remote", "sync.states_remote",
        "screenscraper.user", "screenscraper.pass",
        "screenscraper.dev_id", "screenscraper.dev_pass",
        "tools.chdman", "tools.adb",
        "retroachievements.api_key",
        "sync.auto_sync_enabled", "sync.auto_sync_direction",
        "sync.auto_sync_android_path", "sync.conflict_policy",
        "inbox.path", "inbox.target_root",
        "inbox.auto_process", "inbox.delete_source",
        "android.device_name",
        "web.host",
        "launchers.retroarch",
        "backup.saves_enabled", "backup.saves_keep_n",
        "notifications.desktop",
    }
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        ctx._send_json({"error": "No recognised fields to update"})
        return

    write_config_toml(config.project_root, updates)

    # Reload in-memory config so changes take effect without restart
    new_cfg = load_config(config.project_root)
    config.library_root = new_cfg.library_root
    config.anbernic_root = new_cfg.anbernic_root
    config.device_name = new_cfg.device_name
    config.rclone_remote = new_cfg.rclone_remote
    config.screenscraper_user = new_cfg.screenscraper_user
    config.screenscraper_pass = new_cfg.screenscraper_pass
    config.screenscraper_dev_id = new_cfg.screenscraper_dev_id
    config.screenscraper_dev_pass = new_cfg.screenscraper_dev_pass
    config.chdman = new_cfg.chdman
    config.adb = new_cfg.adb
    config.ra_api_key = new_cfg.ra_api_key
    config.auto_sync_enabled = new_cfg.auto_sync_enabled
    config.auto_sync_direction = new_cfg.auto_sync_direction
    config.auto_sync_android_path = new_cfg.auto_sync_android_path
    config.conflict_policy = new_cfg.conflict_policy
    config.inbox_path = new_cfg.inbox_path
    config.inbox_target_root = new_cfg.inbox_target_root
    config.inbox_auto_process = new_cfg.inbox_auto_process
    config.inbox_delete_source = new_cfg.inbox_delete_source
    config.sync_sources = new_cfg.sync_sources
    config.web_host = new_cfg.web_host
    config.retroarch_path = new_cfg.retroarch_path
    config.launcher_cores = new_cfg.launcher_cores
    config.backup_saves_enabled = new_cfg.backup_saves_enabled
    config.backup_saves_keep_n = new_cfg.backup_saves_keep_n
    config.pre_sync_backup = new_cfg.pre_sync_backup
    config.notify_desktop = new_cfg.notify_desktop
    config.saves_remote = new_cfg.saves_remote
    config.states_remote = new_cfg.states_remote
    set_auto_sync_fn(new_cfg.auto_sync_enabled)

    ctx._send_json({"saved": list(updates.keys())})


def _read_health_schedule(config: "AppConfig") -> dict:
    """Return health-check schedule info for GET /api/health-schedule."""
    import json as _json
    import datetime as _dt

    _INTERVAL_DAYS = 7
    p = config.data_dir / "health_schedule.json"
    try:
        data = _json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        data = {}

    last_run_at = data.get("last_run_at")
    next_run_at: str | None = None
    overdue = False
    if last_run_at:
        try:
            last = _dt.datetime.fromisoformat(last_run_at.replace("Z", "+00:00"))
            nxt = last + _dt.timedelta(days=_INTERVAL_DAYS)
            next_run_at = nxt.strftime("%Y-%m-%dT%H:%M:%SZ")
            overdue = _dt.datetime.now(tz=_dt.timezone.utc) >= nxt
        except Exception:
            pass

    return {
        "last_run_at":    last_run_at,
        "next_run_at":    next_run_at,
        "last_ok":        data.get("last_ok"),
        "last_corrupted": data.get("last_corrupted"),
        "last_missing":   data.get("last_missing"),
        "overdue":        overdue,
    }


def _test_binary_status(path_str: str) -> dict:
    """Return {ok, version, path} for an external binary."""
    import subprocess as _sp
    import shutil as _shutil

    p = Path(path_str) if path_str else None
    if not p or not p.exists():
        found = _shutil.which(path_str or "")
        if not found:
            return {"ok": False, "version": "", "path": path_str}
        p = Path(found)
    try:
        r = _sp.run([str(p), "--version"], capture_output=True, text=True, timeout=5)
        ver = (r.stdout or r.stderr or "").strip().splitlines()[0][:60]
        return {"ok": True, "version": ver, "path": str(p)}
    except Exception:
        return {"ok": True, "version": "", "path": str(p)}
