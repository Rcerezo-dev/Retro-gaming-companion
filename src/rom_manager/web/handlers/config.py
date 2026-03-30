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

    @router.get("/api/wizard-detect")
    def get_wizard_detect(ctx) -> None:
        ctx._send_json(_detect_wizard(config))

    @router.post("/api/config")
    def post_config(ctx) -> None:
        _save_config(ctx, ctx._post_data, config, set_auto_sync_fn)


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
