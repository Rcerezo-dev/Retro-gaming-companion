from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

_config_lock = threading.Lock()

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
    from rom_manager.web.response_builders import _build_config

    @router.get("/api/config")
    def get_config(ctx) -> None:
        ctx._send_json(_build_config(config))

    @router.get("/api/device-status")
    def get_device_status(ctx) -> None:
        """UX-1/2: Check if Android device (ADB or SD card) is connected."""
        connected, reason = config.is_device_connected()
        ctx._send_json(
            {
                "connected": connected,
                "reason": reason,
                "device_name": config.device_name or "Android Device",
            }
        )

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
        ctx._send_json(
            _test_binary_status(
                str(config.chdman)
                if config.chdman
                else str(config.project_root / "tools" / "chdman.exe"),
            )
        )

    @router.get("/api/test-maxcso")
    def get_test_maxcso(ctx) -> None:
        ctx._send_json(
            _test_binary_status(
                str(config.project_root / "tools" / "maxcso.exe"),
            )
        )

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

    @router.get("/api/detect-retroarch")
    def get_detect_retroarch(ctx) -> None:
        ctx._send_json(_detect_retroarch_install())

    @router.get("/api/browse-folder")
    def get_browse_folder(ctx) -> None:
        _browse_folder(ctx, getattr(ctx, "_qs", {}))


# ── Handler logic (moved from server.py) ──────────────────────────────────────


def _detect_retroarch_install() -> dict:
    """Scan common Windows paths for a RetroArch installation.

    Checks common install directories, Steam libraries (including non-default ones
    via libraryfolders.vdf), and RetroBat. Returns the first ``retroarch.exe`` found
    plus the ``content_directory`` from its ``retroarch.cfg`` if readable.
    """
    import os
    import re

    candidates: list[Path] = []

    appdata = os.environ.get("APPDATA", "")
    if appdata:
        candidates.append(Path(appdata) / "RetroArch")

    for drive in ("C", "D", "E"):
        candidates += [
            Path(f"{drive}:\\RetroArch-Win64"),
            Path(f"{drive}:\\RetroArch"),
            Path(f"{drive}:\\Program Files\\RetroArch"),
            Path(f"{drive}:\\Program Files (x86)\\RetroArch"),
            Path(f"{drive}:\\Program Files (x86)\\Steam\\steamapps\\common\\RetroArch"),
        ]

    # Steam — additional library folders from libraryfolders.vdf
    localappdata = os.environ.get("LOCALAPPDATA", "")
    vdf_paths = [
        Path(localappdata) / "Steam" / "steamapps" / "libraryfolders.vdf" if localappdata else None,
        Path("C:\\Program Files (x86)\\Steam\\steamapps\\libraryfolders.vdf"),
    ]
    for vdf in vdf_paths:
        if not vdf or not vdf.exists():
            continue
        try:
            text = vdf.read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(r'"path"\s+"([^"]+)"', text):
                lib_path = m.group(1).strip().replace("\\\\", "\\")
                candidates.append(Path(lib_path) / "steamapps" / "common" / "RetroArch")
        except OSError:
            pass

    # RetroBat
    user_profile = os.environ.get("USERPROFILE", "")
    if user_profile:
        candidates.append(Path(user_profile) / "RetroBat" / "emulators" / "retroarch")
    for drive in ("C", "D", "E"):
        candidates.append(Path(f"{drive}:\\RetroBat\\emulators\\retroarch"))

    retroarch_path: str | None = None
    library_root: str | None = None

    for ra_dir in candidates:
        exe = ra_dir / "retroarch.exe"
        if not exe.exists():
            continue
        retroarch_path = str(exe)
        cfg_path = ra_dir / "retroarch.cfg"
        if cfg_path.exists():
            try:
                text = cfg_path.read_text(encoding="utf-8", errors="replace")
                m = re.search(r'^content_directory\s*=\s*"(.+)"', text, re.MULTILINE)
                if m:
                    val = m.group(1).strip()
                    if val not in ("", "default"):
                        library_root = val
            except OSError:
                pass
        break

    return {
        "found": retroarch_path is not None,
        "retroarch_path": retroarch_path,
        "library_root": library_root,
    }


def _detect_wizard(config: AppConfig) -> dict:
    """Auto-detect RetroArch installation and connected ADB devices for the first-run wizard."""
    ra = _detect_retroarch_install()
    library_root_suggestion = ra["library_root"] or ra["retroarch_path"]

    # Check ADB for connected devices
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
        "retroarch_path_suggestion": ra["retroarch_path"],
        "android_suggestion": android_suggestion,
        "device_display": device_display,
        "adb_ok": adb_ok,
    }


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
        config.rclone_remote = new_cfg.rclone_remote
        config.screenscraper_user = new_cfg.screenscraper_user
        config.screenscraper_pass = new_cfg.screenscraper_pass
        config.screenscraper_dev_id = new_cfg.screenscraper_dev_id
        config.screenscraper_dev_pass = new_cfg.screenscraper_dev_pass
        config.chdman = new_cfg.chdman
        config.adb = new_cfg.adb
        config.ra_api_key = new_cfg.ra_api_key
        config.ra_username = new_cfg.ra_username
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


def _read_health_schedule(config: AppConfig) -> dict:
    """Return health-check schedule info for GET /api/health-schedule."""
    import datetime as _dt
    import json as _json

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
            overdue = _dt.datetime.now(tz=_dt.UTC) >= nxt
        except Exception:
            pass

    return {
        "last_run_at": last_run_at,
        "next_run_at": next_run_at,
        "last_ok": data.get("last_ok"),
        "last_corrupted": data.get("last_corrupted"),
        "last_missing": data.get("last_missing"),
        "overdue": overdue,
    }


def _test_binary_status(path_str: str) -> dict:
    """Return {ok, version, path} for an external binary."""
    import shutil as _shutil
    import subprocess as _sp

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


def _browse_folder(ctx, qs: dict) -> None:
    """Open a native OS folder picker and return the selected path.

    Query params:
      - initial_dir: optional starting directory (falls back to user home)
      - title: optional dialog title
    """
    initial_dir = (qs.get("initial_dir", [None])[0] or "").strip() or None
    title = (qs.get("title", [None])[0] or "").strip() or "Seleccionar carpeta"

    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()  # hide blank root window
        root.wm_attributes("-topmost", True)  # bring dialog to front on Windows
        root.lift()
        folder = filedialog.askdirectory(
            parent=root,
            title=title,
            initialdir=initial_dir or Path.home(),
            mustexist=False,
        )
        root.destroy()
    except Exception as exc:
        ctx._send_json({"ok": False, "error": f"No se pudo abrir el selector: {exc}"})
        return

    if not folder:
        # User cancelled
        ctx._send_json({"ok": False, "cancelled": True})
        return

    # Normalize to OS-native separators
    ctx._send_json({"ok": True, "path": str(Path(folder))})
