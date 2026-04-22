from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.router import Router
    import types


# ── Public entry point ────────────────────────────────────────────────────────

def register(
    router: "Router",
    *,
    config: "AppConfig",
    repository: "LibraryRepository",
    repo_android: "LibraryRepository",
    start_ra_check_fn: "Callable[[str], bool]",
    srv_mod: "types.ModuleType",
) -> None:
    """Register sync / cable-sync / rclone / ADB / auto-sync routes on *router*."""

    # ── GET /api/adb-devices ─────────────────────────────────────────────────
    @router.get("/api/adb-devices")
    def get_adb_devices(ctx) -> None:
        try:
            from rom_manager.sync.adb_transport import list_devices
            devs = list_devices(config.adb)
            ctx._send_json({
                "devices": [
                    {"serial": d.serial, "state": d.state,
                     "model": d.model, "product": d.product,
                     "ready": d.ready, "display": d.display}
                    for d in devs
                ],
                "adb_path": config.adb,
            })
        except RuntimeError as exc:
            ctx._send_json({"error": str(exc), "devices": []})

    # ── GET /api/test-adb-path ───────────────────────────────────────────────
    @router.get("/api/test-adb-path")
    def get_test_adb_path(ctx) -> None:
        qs     = getattr(ctx, "_qs", {})
        serial = qs.get("serial", [""])[0]
        ap     = qs.get("path", ["/storage/emulated/0"])[0]
        if not serial:
            ctx._send_json({"accessible": False, "error": "serial requerido"})
        else:
            try:
                from rom_manager.sync.adb_transport import AdbTransport
                t = AdbTransport(config.adb, serial)
                ctx._send_json(t.test_path(ap))
            except Exception as exc:
                ctx._send_json({"accessible": False, "error": str(exc)})

    # ── GET /api/sync-log ────────────────────────────────────────────────────
    @router.get("/api/sync-log")
    def get_sync_log(ctx) -> None:
        from rom_manager.web.response_builders import _build_sync_log
        ctx._send_json(_build_sync_log(repository))

    # ── GET /api/cable-sync-preview ──────────────────────────────────────────
    @router.get("/api/cable-sync-preview")
    def get_cable_sync_preview(ctx) -> None:
        from rom_manager.web.response_builders import _build_cable_sync_preview
        ctx._send_json(_build_cable_sync_preview(getattr(ctx, "_qs", {}), config))

    # ── GET /api/cable-sync-log ──────────────────────────────────────────────
    @router.get("/api/cable-sync-log")
    def get_cable_sync_log(ctx) -> None:
        log_path = config.project_root / ".rommgr" / "cable_sync_ops.log"
        if log_path.exists():
            with open(log_path, "r", encoding="utf-8", errors="replace") as _lf:
                lines = _lf.readlines()
            tail = "".join(lines[-500:])
            ctx._send_json({"log": tail, "lines": len(lines)})
        else:
            ctx._send_json({"log": "", "lines": 0})

    # ── GET /api/rclone-export-config ────────────────────────────────────────
    @router.get("/api/rclone-export-config")
    def get_rclone_export_config(ctx) -> None:
        body, ct = _handle_rclone_export_config(config)
        ctx._send(200, ct, body)

    # ── GET /api/rclone-status ───────────────────────────────────────────────
    @router.get("/api/rclone-status")
    def get_rclone_status(ctx) -> None:
        ctx._send_json(_handle_rclone_status(config))

    # ── POST /api/rclone-open-config ─────────────────────────────────────────
    @router.post("/api/rclone-open-config")
    def post_rclone_open_config(ctx) -> None:
        ctx._send_json(_handle_rclone_open_config(config))

    # ── POST /api/rclone-test-remote ─────────────────────────────────────────
    @router.post("/api/rclone-test-remote")
    def post_rclone_test_remote(ctx) -> None:
        remote = ctx._post_data.get("remote", "").strip()
        ctx._send_json(_handle_rclone_test_remote(config, remote))

    # ── GET /api/auto-sync-status ────────────────────────────────────────────
    @router.get("/api/auto-sync-status")
    def get_auto_sync_status(ctx) -> None:
        ctx._send_json({
            "enabled": srv_mod._auto_sync_enabled,
            "status":  dict(srv_mod._auto_sync_status),
            "config": {
                "direction":      config.auto_sync_direction,
                "conflict_policy": config.conflict_policy,
                "android_path":   config.auto_sync_android_path,
            },
        })

    # ── GET /api/sd-sync-status ──────────────────────────────────────────────
    @router.get("/api/sd-sync-status")
    def get_sd_sync_status(ctx) -> None:
        ctx._send_json(dict(srv_mod._sd_sync_status))

    # ── POST /api/sync ───────────────────────────────────────────────────────
    @router.post("/api/sync")
    def post_sync(ctx) -> None:
        _do_sync(ctx, ctx._post_data, config, repository, srv_mod)

    # ── POST /api/cable-sync ─────────────────────────────────────────────────
    @router.post("/api/cable-sync")
    def post_cable_sync(ctx) -> None:
        _do_cable_sync(ctx, ctx._post_data, config, repository, srv_mod)

    # ── POST /api/auto-sync-toggle ───────────────────────────────────────────
    @router.post("/api/auto-sync-toggle")
    def post_auto_sync_toggle(ctx) -> None:
        import rom_manager.web.server as _srv
        _srv._auto_sync_enabled = not _srv._auto_sync_enabled
        config.auto_sync_enabled = _srv._auto_sync_enabled
        ctx._send_json({"enabled": _srv._auto_sync_enabled})

    # ── POST /api/auto-sync-save ─────────────────────────────────────────────
    @router.post("/api/auto-sync-save")
    def post_auto_sync_save(ctx) -> None:
        _do_auto_sync_save(ctx, ctx._post_data, config, srv_mod)

    # ── POST /api/migrate-split-db ───────────────────────────────────────────
    @router.post("/api/migrate-split-db")
    def post_migrate_split_db(ctx) -> None:
        _do_migrate_split_db(ctx, config, repository, repo_android)

    # ── POST /api/rom-tree-diff ──────────────────────────────────────────────
    @router.post("/api/rom-tree-diff")
    def post_rom_tree_diff(ctx) -> None:
        _do_tree_diff(ctx, ctx._post_data, config, srv_mod)

    # ── POST /api/ra-check ───────────────────────────────────────────────────
    @router.post("/api/ra-check")
    def post_ra_check(ctx) -> None:
        data    = ctx._post_data
        api_key = data.get("api_key", "").strip() or config.ra_api_key
        if not api_key:
            ctx._send_json({"error": "RetroAchievements API key not configured"})
            return
        if start_ra_check_fn(api_key):
            ctx._send_json({"status": "started"})
        else:
            ctx._send_json({"status": "already_running"})


# ── Module-level helpers (moved from server.py) ───────────────────────────────

def _handle_rclone_export_config(config: "AppConfig") -> tuple[bytes, str]:
    """Return the local rclone config file contents as bytes, or an error message."""
    import subprocess as _sp
    import shutil as _sh

    rclone_bin = config.rclone_binary or "rclone"
    if not _sh.which(rclone_bin) and not __import__("pathlib").Path(rclone_bin).exists():
        return b"# rclone not found on this machine\n", "text/plain; charset=utf-8"
    try:
        r = _sp.run([rclone_bin, "config", "file"], capture_output=True, text=True, timeout=8)
        cfg_path = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
        cfg_file = __import__("pathlib").Path(cfg_path)
        if cfg_file.exists():
            return cfg_file.read_bytes(), "text/plain; charset=utf-8"
        return b"# rclone config file not found\n", "text/plain; charset=utf-8"
    except Exception as exc:
        return f"# error reading rclone config: {exc}\n".encode(), "text/plain; charset=utf-8"


def _handle_rclone_status(config: "AppConfig") -> dict:
    """Check if rclone is installed and list configured remotes."""
    import subprocess as _sp
    import shutil as _sh

    rclone_bin = config.rclone_binary or "rclone"
    if not _sh.which(rclone_bin) and not __import__("pathlib").Path(rclone_bin).exists():
        return {"installed": False, "version": None, "remotes": [], "binary": rclone_bin}
    try:
        r = _sp.run([rclone_bin, "version"], capture_output=True, text=True, timeout=8)
        version_line = r.stdout.strip().splitlines()[0] if r.stdout.strip() else "unknown"
        remotes_r = _sp.run([rclone_bin, "listremotes"], capture_output=True, text=True, timeout=8)
        remotes = [l.rstrip(":") for l in remotes_r.stdout.strip().splitlines() if l.strip()]
        return {"installed": True, "version": version_line, "remotes": remotes, "binary": rclone_bin}
    except Exception as exc:
        return {"installed": False, "version": None, "remotes": [], "binary": rclone_bin, "error": str(exc)}


def _handle_rclone_open_config(config: "AppConfig") -> dict:
    """Open a terminal window running 'rclone config' so the user can add remotes."""
    import subprocess as _sp
    import sys as _sys

    rclone_bin = config.rclone_binary or "rclone"
    try:
        if _sys.platform == "win32":
            _sp.Popen(
                ["cmd", "/c", "start", "cmd", "/k", rclone_bin, "config"],
                creationflags=_sp.CREATE_NEW_CONSOLE,
            )
        elif _sys.platform == "darwin":
            _sp.Popen(["open", "-a", "Terminal", "--args", rclone_bin, "config"])
        else:
            for term in ("x-terminal-emulator", "xterm", "gnome-terminal", "konsole"):
                import shutil as _sh
                if _sh.which(term):
                    _sp.Popen([term, "-e", f"{rclone_bin} config"])
                    break
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _handle_rclone_test_remote(config: "AppConfig", remote: str) -> dict:
    """Run 'rclone lsd <remote>:' to verify the connection is working."""
    import subprocess as _sp
    import shutil as _sh

    if not remote:
        return {"ok": False, "error": "remote requerido"}
    rclone_bin = config.rclone_binary or "rclone"
    if not _sh.which(rclone_bin) and not __import__("pathlib").Path(rclone_bin).exists():
        return {"ok": False, "error": "rclone no encontrado"}
    remote_arg = remote if remote.endswith(":") else remote + ":"
    try:
        r = _sp.run(
            [rclone_bin, "lsd", remote_arg, "--max-depth", "1"],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode == 0:
            lines = [l.strip() for l in r.stdout.strip().splitlines() if l.strip()]
            return {"ok": True, "remote": remote, "entries": len(lines), "sample": lines[:5]}
        return {"ok": False, "remote": remote, "error": r.stderr.strip() or "error desconocido"}
    except _sp.TimeoutExpired:
        return {"ok": False, "remote": remote, "error": "timeout — comprueba la conexión a internet"}
    except Exception as exc:
        return {"ok": False, "remote": remote, "error": str(exc)}


# ── Handler logic (moved from server.py) ─────────────────────────────────────

def _do_sync(ctx, data: dict, config: "AppConfig", repository: "LibraryRepository", srv_mod) -> None:
    from rom_manager.web.response_builders import _utc_now_str

    dry_run = data.get("dry_run", True)
    m = srv_mod
    with m._job_lock:
        if m._jobs["sync"]:
            ctx._send_json({"status": "already_running"})
            return
        m._jobs["sync"] = True

    def run() -> None:
        import rom_manager.web.server as _srv13
        if _srv13._tray_instance:
            _srv13._tray_instance.set_status("Sincronizando…")
        try:
            from rom_manager.sync.rclone_transport import RcloneTransport
            from rom_manager.sync.save_syncer import sync_saves
            from pathlib import Path as _Path

            sources = config.sync_sources
            if not sources:
                m._job_results["sync"] = {
                    "error": "No hay fuentes de sync configuradas. "
                             "Añade [[sync.sources]] en config.toml."
                }
                return

            if not dry_run and config.pre_sync_backup and config.library_root:
                try:
                    from rom_manager.backup.save_backup import create_saves_zip
                    _zip_dest = config.data_dir / "saves-backup"
                    create_saves_zip(
                        saves_dirs=[_Path(str(config.library_root))],
                        save_extensions=set(config.save_extensions),
                        output_dir=_zip_dest,
                    )
                except Exception as _bk_exc:
                    import logging
                    logging.getLogger(__name__).warning("Pre-sync backup failed (non-fatal): %s", _bk_exc)

            transport    = RcloneTransport(rclone=config.rclone_binary)
            all_results  = []
            for source in sources:
                saves_dir = _Path(source.local_dir)
                if not saves_dir.exists():
                    all_results.append({
                        "name": source.name,
                        "local_dir": source.local_dir,
                        "remote": source.remote,
                        "error": f"Directorio no encontrado: {source.local_dir}",
                        "uploaded": 0, "downloaded": 0,
                        "up_to_date": 0, "conflicts": 0, "errors": 0,
                        "decisions": [],
                    })
                    continue
                exts = tuple() if source.sync_all else config.save_extensions
                try:
                    _bk_root = config.data_dir if config.backup_saves_enabled else None
                    from rom_manager.sync.delta_cache import DeltaCache as _DeltaCache
                    _delta  = _DeltaCache(config.data_dir) if not dry_run else None
                    result, decisions = sync_saves(
                        saves_dir,
                        saves_remote=source.remote,
                        transport=transport,
                        repository=repository,
                        save_extensions=exts,
                        state_extensions=config.state_extensions if not source.sync_all else tuple(),
                        states_remote=None,
                        dry_run=dry_run,
                        backup_root=_bk_root,
                        backup_keep_n=config.backup_saves_keep_n,
                        delta_cache=_delta,
                        conflict_policy=config.conflict_policy,
                    )
                    all_results.append({
                        "name":          source.name,
                        "local_dir":     source.local_dir,
                        "remote":        source.remote,
                        "uploaded":      result.uploaded,
                        "downloaded":    result.downloaded,
                        "up_to_date":    result.up_to_date,
                        "conflicts":     result.conflicts,
                        "errors":        result.errors,
                        "delta_skipped": result.delta_skipped,
                        "decisions": [
                            {"action": d.action, "relative": d.relative}
                            for d in decisions if d.action != "up_to_date"
                        ],
                    })
                except Exception as exc:
                    all_results.append({
                        "name": source.name, "local_dir": source.local_dir,
                        "remote": source.remote, "error": str(exc),
                        "uploaded": 0, "downloaded": 0,
                        "up_to_date": 0, "conflicts": 0, "errors": 0,
                        "decisions": [],
                    })

            # D2: implicit sync for saves/states remotes
            _bk_root = config.data_dir if config.backup_saves_enabled else None
            _implicit = []
            if config.saves_remote and config.library_root:
                _implicit.append((
                    _Path(config.library_root) / "saves",
                    config.saves_remote,
                    "Saves (permanentes)",
                    config.save_extensions,
                ))
            if config.states_remote and config.library_root:
                _implicit.append((
                    _Path(config.library_root) / "states",
                    config.states_remote,
                    "States",
                    config.state_extensions,
                ))
            for _dir, _remote, _name, _exts in _implicit:
                if not _dir.exists():
                    all_results.append({
                        "name": _name, "local_dir": str(_dir), "remote": _remote,
                        "error": f"Directorio no encontrado: {_dir}",
                        "uploaded": 0, "downloaded": 0,
                        "up_to_date": 0, "conflicts": 0, "errors": 0,
                        "decisions": [],
                    })
                    continue
                try:
                    from rom_manager.sync.delta_cache import DeltaCache as _DeltaCache
                    _delta = _DeltaCache(config.data_dir) if not dry_run else None
                    # D2: For implicit saves/states sync, determine routing based on what type we're syncing
                    _is_states = "States" in _name
                    _saves_remote = _remote if not _is_states else None
                    _states_remote = _remote if _is_states else None
                    result, decisions = sync_saves(
                        _dir,
                        saves_remote=_saves_remote or _remote,
                        transport=transport,
                        repository=repository,
                        save_extensions=_exts,
                        state_extensions=_exts if _is_states else tuple(),
                        states_remote=_states_remote,
                        dry_run=dry_run,
                        backup_root=_bk_root,
                        backup_keep_n=config.backup_saves_keep_n,
                        delta_cache=_delta,
                        conflict_policy=config.conflict_policy,
                    )
                    all_results.append({
                        "name":          _name,
                        "local_dir":     str(_dir),
                        "remote":        _remote,
                        "uploaded":      result.uploaded,
                        "downloaded":    result.downloaded,
                        "up_to_date":    result.up_to_date,
                        "conflicts":     result.conflicts,
                        "errors":        result.errors,
                        "delta_skipped": result.delta_skipped,
                        "decisions": [
                            {"action": d.action, "relative": d.relative}
                            for d in decisions if d.action != "up_to_date"
                        ],
                    })
                except Exception as exc:
                    all_results.append({
                        "name": _name, "local_dir": str(_dir), "remote": _remote,
                        "error": str(exc),
                        "uploaded": 0, "downloaded": 0,
                        "up_to_date": 0, "conflicts": 0, "errors": 0,
                        "decisions": [],
                    })

            _up   = sum(r.get("uploaded",   0) for r in all_results)
            _down = sum(r.get("downloaded", 0) for r in all_results)
            _errs = sum(r.get("errors",     0) for r in all_results)
            m._job_results["sync"] = {
                "dry_run":    dry_run,
                "sources":    all_results,
                "uploaded":   _up,
                "downloaded": _down,
                "up_to_date": sum(r.get("up_to_date", 0) for r in all_results),
                "conflicts":  sum(r.get("conflicts",  0) for r in all_results),
                "errors":     _errs,
            }
            if not dry_run and config.notify_desktop:
                from rom_manager.utils.notifier import notify
                _parts: list[str] = []
                if _up:   _parts.append(f"{_up} subidos")
                if _down: _parts.append(f"{_down} descargados")
                if not _parts: _parts.append("Todo al día")
                _body = ", ".join(_parts)
                if _errs: _body += f" ({_errs} errores)"
                notify("Retro Vault — Sync completado", _body)
            if not dry_run:
                _total_conflicts = sum(r.get("conflicts", 0) for r in all_results)
                if _errs:
                    _srv13._tray_instance and _srv13._tray_instance.set_status(f"✗ Sync: {_errs} errores")
                elif _total_conflicts:
                    _srv13._tray_instance and _srv13._tray_instance.set_status(f"⚠ Conflictos: {_total_conflicts}")
                else:
                    _ts = _utc_now_str()[:16].replace("T", " ")
                    _srv13._tray_instance and _srv13._tray_instance.set_status(f"Sync OK {_ts}")
                _srv13._auto_sync_status["last_sync_at"] = _utc_now_str()
                _srv13._auto_sync_status["last_error"] = (f"{_errs} errores en cloud sync") if _errs else None
        except Exception as exc:
            m._job_results["sync"] = {"error": str(exc)}
            import rom_manager.web.server as _srv13e
            _srv13e._tray_instance and _srv13e._tray_instance.set_status("✗ Error en sync")
        finally:
            with m._job_lock:
                m._jobs["sync"] = False

    threading.Thread(target=run, daemon=True).start()
    ctx._send_json({"status": "started", "dry_run": dry_run})


def _do_cable_sync(ctx, data: dict, config: "AppConfig", repository: "LibraryRepository", srv_mod) -> None:
    import os
    import shutil

    pc_path_str       = data.get("pc_path", "").strip()
    anbernic_path_str = data.get("anbernic_path", "").strip()
    what              = data.get("what", ["saves"])
    direction         = data.get("direction", "pc_to_anbernic")
    dry_run           = bool(data.get("dry_run", True))
    skip_sha1_dups    = bool(data.get("skip_sha1_dups", False))
    skip_existing     = bool(data.get("skip_existing", False))
    safe_mode         = bool(data.get("safe_mode", True))
    delete_extra      = bool(data.get("delete_extra", False))
    use_adb           = bool(data.get("use_adb", False))
    adb_serial        = data.get("adb_serial", "").strip()
    android_path      = data.get("android_path", "/storage/emulated/0").strip()

    if not pc_path_str:
        ctx._send_json({"error": "pc_path is required"})
        return
    if use_adb and not adb_serial:
        ctx._send_json({"error": "adb_serial is required when use_adb is true"})
        return
    if not use_adb and not anbernic_path_str:
        ctx._send_json({"error": "anbernic_path is required"})
        return

    m = srv_mod
    with m._job_lock:
        if m._jobs["cable_sync"]:
            ctx._send_json({"status": "already_running"})
            return
        m._jobs["cable_sync"] = True

    def run() -> None:
        m._cable_cancel.clear()
        _log_file = None
        try:
            import time as _time
            from pathlib import PurePosixPath
            import datetime as _dt
            pc_root   = Path(pc_path_str)
            save_exts = frozenset(config.save_extensions)

            log_path = config.project_root / ".rommgr" / "cable_sync_ops.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            _log_file = open(log_path, "a", encoding="utf-8", buffering=1)
            _ts0 = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            _log_file.write(
                f"\n=== Cable Sync {_ts0} | direction={direction} dry_run={dry_run} safe_mode={safe_mode} ===\n"
            )

            def _log(tag: str, src: str, dst: str = "", note: str = "") -> None:
                ts = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%H:%M:%S")
                _log_file.write(f"[{ts}] [{tag:5s}] {src}{(' -> ' + dst) if dst else ''}{(' | ' + note) if note else ''}\n")

            def _cat_name(name: str) -> str:
                suffix = Path(name).suffix.lower()
                return "save" if suffix in save_exts else "rom"

            _ASSET_EXTS = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif"})

            def _wanted_name(name: str) -> bool:
                if name.startswith("."):
                    return False
                cat = _cat_name(name)
                return (cat == "save" and "saves" in what) or (cat == "rom" and "roms" in what)

            def _category(p: Path) -> str:
                return "save" if p.suffix.lower() in save_exts else "rom"

            def _wanted(p: Path) -> bool:
                if "assets" in what and p.suffix.lower() in _ASSET_EXTS:
                    if "media" in (part.lower() for part in p.parts):
                        return True
                if "gamelists" in what and p.name.lower() == "gamelist.xml":
                    return True
                return _wanted_name(p.name)

            def _iter_files(root: Path):
                for dirpath, dirs, files in os.walk(root):
                    dirs[:] = [d for d in dirs if not d.startswith(".")]
                    for fname in files:
                        yield Path(dirpath) / fname

            copied = skipped = errors = sha1_skipped = safe_mode_skipped = deleted_extra = 0
            copied_bytes = 0
            details: list[dict] = []

            _last_speed_update = _time.monotonic()
            _last_speed_bytes  = 0

            def _update_progress(file_name: str = "") -> None:
                nonlocal _last_speed_update, _last_speed_bytes
                now = _time.monotonic()
                dt  = now - _last_speed_update
                speed = 0.0
                if dt >= 0.5:
                    speed = (copied_bytes - _last_speed_bytes) / dt
                    _last_speed_update = now
                    _last_speed_bytes  = copied_bytes
                elif m._cable_progress.get("speed_bps") is not None:
                    speed = m._cable_progress.get("speed_bps", 0.0)
                m._cable_progress.update({
                    "copied": copied,
                    "bytes_copied": copied_bytes,
                    "speed_bps": speed,
                    "current_file": file_name,
                })

            def _copy(src: Path, dst: Path, arrow: str) -> None:
                nonlocal copied, skipped, errors, copied_bytes, safe_mode_skipped
                if m._cable_cancel.is_set():
                    return
                try:
                    src_stat = src.stat()
                    size = src_stat.st_size
                    if safe_mode and dst.exists():
                        safe_mode_skipped += 1
                        skipped += 1
                        _log("SAFE", str(src), str(dst), "destino existe — omitido por modo seguro")
                        if len(details) < 300:
                            details.append({"file": "SAFE", "path": str(src.name)})
                        return
                    if skip_existing and dst.exists():
                        try:
                            if dst.stat().st_size == size:
                                skipped += 1
                                _log("SKIP", str(src), str(dst), "mismo tamaño")
                                if len(details) < 300:
                                    details.append({"file": "EXISTS", "path": str(src.name)})
                                return
                        except OSError:
                            pass
                    if not dry_run:
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)
                    _log("COPY" if not dry_run else "DRYRUN", str(src), str(dst))
                    copied += 1
                    copied_bytes += size
                    if len(details) < 300:
                        details.append({"file": arrow, "path": str(src.name)})
                    _update_progress(src.name)
                except OSError as exc:
                    errors += 1
                    _log("ERROR", str(src), str(dst), str(exc))
                    if len(details) < 300:
                        details.append({"file": f"ERROR: {exc}", "path": str(src.name)})

            # ── ADB mode ──────────────────────────────────────────────────────
            if use_adb:
                from rom_manager.sync.adb_transport import AdbTransport
                transport = AdbTransport(config.adb, adb_serial)

                def _adb_copy_to_pc(adb_info, rel_posix: str, arrow: str) -> None:
                    nonlocal copied, errors, copied_bytes
                    if m._cable_cancel.is_set():
                        return
                    name      = PurePosixPath(adb_info.android_path).name
                    local_dst = pc_root / Path(rel_posix.replace("/", os.sep))
                    try:
                        size = transport.pull(adb_info.android_path, local_dst, dry_run=dry_run)
                        _log("ADB←" if not dry_run else "DRY←", adb_info.android_path, str(local_dst))
                        copied += 1
                        copied_bytes += size
                        if len(details) < 300:
                            details.append({"file": arrow, "path": name})
                        _update_progress(name)
                    except OSError as exc:
                        _log("ERROR", adb_info.android_path, str(local_dst), str(exc))
                        errors += 1
                        if len(details) < 300:
                            details.append({"file": f"ERROR: {exc}", "path": name})

                def _adb_copy_to_device(local_src: Path, rel_posix: str, arrow: str) -> None:
                    nonlocal copied, errors, copied_bytes
                    if m._cable_cancel.is_set():
                        return
                    android_dst = android_path.rstrip("/") + "/" + rel_posix
                    try:
                        size = transport.push(local_src, android_dst, dry_run=dry_run)
                        _log("ADB→" if not dry_run else "DRY→", str(local_src), android_dst)
                        copied += 1
                        copied_bytes += size
                        if len(details) < 300:
                            details.append({"file": arrow, "path": local_src.name})
                        _update_progress(local_src.name)
                    except OSError as exc:
                        _log("ERROR", str(local_src), android_dst, str(exc))
                        errors += 1
                        if len(details) < 300:
                            details.append({"file": f"ERROR: {exc}", "path": local_src.name})

                m._cable_progress.update({"copied": 0, "current_file": "Listando archivos en el dispositivo…"})
                ab_adb_files = transport.ls_recursive(android_path)
                try:
                    _pre_files = sum(1 for info in ab_adb_files if _wanted_name(PurePosixPath(info.android_path).name))
                    _pre_total = sum(info.size for info in ab_adb_files if _wanted_name(PurePosixPath(info.android_path).name))
                    m._cable_progress.update({"bytes_total": _pre_total, "total_files": _pre_files, "copied": 0, "bytes_copied": 0, "speed_bps": 0.0})
                except Exception:
                    pass
                android_prefix = android_path.rstrip("/") + "/"

                if direction == "pc_to_anbernic":
                    for src in _iter_files(pc_root):
                        if m._cable_cancel.is_set():
                            break
                        if not _wanted(src):
                            continue
                        rel       = src.relative_to(pc_root)
                        rel_posix = rel.as_posix()
                        _adb_copy_to_device(src, rel_posix, "→ ADB")

                    if delete_extra and not m._cable_cancel.is_set():
                        _pc_rels = {f.relative_to(pc_root).as_posix() for f in _iter_files(pc_root) if _wanted(f)}
                        for _info in ab_adb_files:
                            _aname = PurePosixPath(_info.android_path).name
                            if not _wanted_name(_aname):
                                continue
                            _arel = _info.android_path.removeprefix(android_prefix)
                            if _arel not in _pc_rels:
                                if not dry_run:
                                    try:
                                        transport._shell("rm", _info.android_path, timeout=30)
                                        deleted_extra += 1
                                        _log("DEL", _info.android_path, "", "espejo: extra en dispositivo")
                                    except Exception as _exc:
                                        errors += 1
                                        _log("ERROR", _info.android_path, "", f"DEL: {_exc}")
                                else:
                                    deleted_extra += 1
                                    _log("DEL?", _info.android_path, "", "espejo (dry run)")

                elif direction == "anbernic_to_pc":
                    use_sha1 = skip_sha1_dups and "roms" in what
                    for info in ab_adb_files:
                        if m._cable_cancel.is_set():
                            break
                        name = PurePosixPath(info.android_path).name
                        if not _wanted_name(name):
                            continue
                        rel_posix = info.android_path.removeprefix(android_prefix)
                        if use_sha1 and _cat_name(name) == "rom":
                            _update_progress(f"[SHA1] {name}")
                            import tempfile
                            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(name).suffix) as tf:
                                tmp_path = Path(tf.name)
                            try:
                                transport.pull(info.android_path, tmp_path, dry_run=False)
                                from rom_manager.hashing.hash_calculator import calculate_hashes
                                h = calculate_hashes(tmp_path)
                                if repository.sha1_exists(h.sha1):
                                    sha1_skipped += 1
                                    skipped += 1
                                    if len(details) < 300:
                                        details.append({"file": "DUP", "path": name})
                                    tmp_path.unlink(missing_ok=True)
                                    continue
                                dst = pc_root / Path(rel_posix.replace("/", os.sep))
                                if not dry_run:
                                    dst.parent.mkdir(parents=True, exist_ok=True)
                                    shutil.move(str(tmp_path), dst)
                                else:
                                    tmp_path.unlink(missing_ok=True)
                                copied += 1
                                copied_bytes += info.size
                                if len(details) < 300:
                                    details.append({"file": "← ADB", "path": name})
                                _update_progress(name)
                            except OSError as exc:
                                tmp_path.unlink(missing_ok=True)
                                errors += 1
                                if len(details) < 300:
                                    details.append({"file": f"ERROR: {exc}", "path": name})
                        else:
                            _adb_copy_to_pc(info, rel_posix, "← ADB")

                    if delete_extra and not m._cable_cancel.is_set():
                        _ab_rels = {
                            _i.android_path.removeprefix(android_prefix)
                            for _i in ab_adb_files
                            if _wanted_name(PurePosixPath(_i.android_path).name)
                        }
                        for _f in _iter_files(pc_root):
                            if not _wanted(_f):
                                continue
                            _frel = _f.relative_to(pc_root).as_posix()
                            if _frel not in _ab_rels:
                                if not dry_run:
                                    try:
                                        _f.unlink()
                                        deleted_extra += 1
                                        _log("DEL", str(_f), "", "espejo: extra en PC")
                                    except OSError as _exc:
                                        errors += 1
                                        _log("ERROR", str(_f), "", f"DEL: {_exc}")
                                else:
                                    deleted_extra += 1
                                    _log("DEL?", str(_f), "", "espejo: extra en PC (dry run)")

                elif direction == "newest":
                    ab_index = {
                        info.android_path.removeprefix(android_prefix): info
                        for info in ab_adb_files
                        if _wanted_name(PurePosixPath(info.android_path).name)
                    }
                    pc_index: dict[str, Path] = {}
                    for f in _iter_files(pc_root):
                        if _wanted(f):
                            pc_index[f.relative_to(pc_root).as_posix()] = f

                    all_rels = sorted(set(pc_index) | set(ab_index))
                    for rel_posix in all_rels:
                        if m._cable_cancel.is_set():
                            break
                        pc_f   = pc_index.get(rel_posix)
                        ab_inf = ab_index.get(rel_posix)
                        if pc_f and ab_inf:
                            if pc_f.stat().st_mtime > ab_inf.mtime:
                                _adb_copy_to_device(pc_f, rel_posix, "→ ADB (PC más reciente)")
                            elif ab_inf.mtime > pc_f.stat().st_mtime:
                                _adb_copy_to_pc(ab_inf, rel_posix, "← ADB (Anbernic más reciente)")
                            else:
                                skipped += 1
                        elif pc_f:
                            _adb_copy_to_device(pc_f, rel_posix, "→ ADB (solo en PC)")
                        elif ab_inf:
                            _adb_copy_to_pc(ab_inf, rel_posix, "← ADB (solo en Anbernic)")

            # ── Filesystem mode ───────────────────────────────────────────────
            else:
                ab_root = Path(anbernic_path_str)

                try:
                    _pre_total = 0
                    _pre_files = 0
                    if direction == "pc_to_anbernic":
                        for _f in _iter_files(pc_root):
                            if _wanted(_f):
                                try: _pre_total += _f.stat().st_size
                                except OSError: pass
                                _pre_files += 1
                    elif direction == "anbernic_to_pc":
                        for _f in _iter_files(ab_root):
                            if _wanted(_f):
                                try: _pre_total += _f.stat().st_size
                                except OSError: pass
                                _pre_files += 1
                    elif direction == "newest":
                        for _f in _iter_files(pc_root):
                            if _wanted(_f):
                                try: _pre_total += _f.stat().st_size
                                except OSError: pass
                                _pre_files += 1
                        for _f in _iter_files(ab_root):
                            if _wanted(_f):
                                try: _pre_total += _f.stat().st_size
                                except OSError: pass
                                _pre_files += 1
                    m._cable_progress.update({"bytes_total": _pre_total, "total_files": _pre_files, "copied": 0, "bytes_copied": 0, "speed_bps": 0.0})
                except Exception:
                    pass

                if direction == "pc_to_anbernic":
                    for src in _iter_files(pc_root):
                        if m._cable_cancel.is_set():
                            break
                        if not _wanted(src):
                            continue
                        rel = src.relative_to(pc_root)
                        dst = ab_root / rel
                        _copy(src, dst, "→ Anbernic")

                    if delete_extra and not m._cable_cancel.is_set():
                        _pc_rels = {f.relative_to(pc_root) for f in _iter_files(pc_root) if _wanted(f)}
                        for _f in _iter_files(ab_root):
                            if not _wanted(_f):
                                continue
                            try:
                                _frel = _f.relative_to(ab_root)
                            except ValueError:
                                continue
                            if _frel not in _pc_rels:
                                if not dry_run:
                                    try:
                                        _f.unlink()
                                        deleted_extra += 1
                                        _log("DEL", str(_f), "", "espejo: extra en destino")
                                    except OSError as _exc:
                                        errors += 1
                                        _log("ERROR", str(_f), "", f"DEL: {_exc}")
                                else:
                                    deleted_extra += 1
                                    _log("DEL?", str(_f), "", "espejo: extra en destino (dry run)")

                elif direction == "anbernic_to_pc":
                    use_sha1 = skip_sha1_dups and "roms" in what
                    if use_sha1:
                        from rom_manager.hashing.hash_calculator import calculate_hashes
                    for src in _iter_files(ab_root):
                        if m._cable_cancel.is_set():
                            break
                        if not _wanted(src):
                            continue
                        try:
                            rel = src.relative_to(ab_root)
                        except ValueError:
                            continue
                        if use_sha1 and _category(src) == "rom":
                            _update_progress(f"[SHA1] {src.name}")
                            try:
                                h = calculate_hashes(src)
                                if repository.sha1_exists(h.sha1):
                                    sha1_skipped += 1
                                    skipped += 1
                                    if len(details) < 300:
                                        details.append({"file": "DUP", "path": src.name})
                                    continue
                            except OSError:
                                pass
                        dst = pc_root / rel
                        _copy(src, dst, "← PC")

                    if delete_extra and not m._cable_cancel.is_set():
                        _ab_rels: set[Path] = set()
                        for _f in _iter_files(ab_root):
                            if _wanted(_f):
                                try:
                                    _ab_rels.add(_f.relative_to(ab_root))
                                except ValueError:
                                    pass
                        for _f in _iter_files(pc_root):
                            if not _wanted(_f):
                                continue
                            _frel = _f.relative_to(pc_root)
                            if _frel not in _ab_rels:
                                if not dry_run:
                                    try:
                                        _f.unlink()
                                        deleted_extra += 1
                                        _log("DEL", str(_f), "", "espejo: extra en PC")
                                    except OSError as _exc:
                                        errors += 1
                                        _log("ERROR", str(_f), "", f"DEL: {_exc}")
                                else:
                                    deleted_extra += 1
                                    _log("DEL?", str(_f), "", "espejo: extra en PC (dry run)")

                elif direction == "newest":
                    pc_files: dict[Path, Path] = {}
                    for f in _iter_files(pc_root):
                        if _wanted(f):
                            pc_files[f.relative_to(pc_root)] = f

                    ab_files: dict[Path, Path] = {}
                    for f in _iter_files(ab_root):
                        if _wanted(f):
                            try:
                                ab_files[f.relative_to(ab_root)] = f
                            except ValueError:
                                pass

                    all_rels_fs = sorted(set(pc_files) | set(ab_files), key=lambda p: str(p))
                    for rel in all_rels_fs:
                        if m._cable_cancel.is_set():
                            break
                        pc_f = pc_files.get(rel)
                        ab_f = ab_files.get(rel)
                        if pc_f and ab_f:
                            pc_mt = pc_f.stat().st_mtime
                            ab_mt = ab_f.stat().st_mtime
                            if pc_mt > ab_mt:
                                _copy(pc_f, ab_root / rel, "→ Anbernic (PC más reciente)")
                            elif ab_mt > pc_mt:
                                _copy(ab_f, pc_root / rel, "← PC (Anbernic más reciente)")
                            else:
                                skipped += 1
                        elif pc_f:
                            _copy(pc_f, ab_root / rel, "→ Anbernic (solo en PC)")
                        elif ab_f:
                            _copy(ab_f, pc_root / rel, "← PC (solo en Anbernic)")

            _ts1 = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            _log_file.write(
                f"=== Fin {_ts1} | copied={copied} skipped={skipped} safe_skipped={safe_mode_skipped} deleted_extra={deleted_extra} errors={errors} cancelled={m._cable_cancel.is_set()} ===\n"
            )
            _pc_file_count = 0
            _ab_file_count = 0
            if not dry_run and not use_adb:
                try:
                    _ab_r = Path(anbernic_path_str)
                    for _ff in _iter_files(pc_root):
                        if _wanted(_ff):
                            _pc_file_count += 1
                except Exception:
                    pass
                try:
                    for _ff in _iter_files(_ab_r):
                        if _wanted(_ff):
                            _ab_file_count += 1
                except Exception:
                    pass
            m._job_results["cable_sync"] = {
                "dry_run":                     dry_run,
                "direction":                   direction,
                "use_adb":                     use_adb,
                "copied":                      copied,
                "skipped":                     skipped,
                "sha1_skipped":                sha1_skipped,
                "safe_mode_skipped_overwrites": safe_mode_skipped,
                "errors":                      errors,
                "copied_bytes":                copied_bytes,
                "cancelled":                   m._cable_cancel.is_set(),
                "deleted_extra":               deleted_extra,
                "details":                     details,
                "pc_file_count":               _pc_file_count,
                "ab_file_count":               _ab_file_count,
            }
            if not dry_run and not m._cable_cancel.is_set() and config.notify_desktop:
                from rom_manager.utils.notifier import notify
                _via  = "ADB" if use_adb else "SD"
                _body = f"{copied} archivos copiados vía {_via}"
                if errors: _body += f" ({errors} errores)"
                notify("Retro Vault — Cable Sync completado", _body)
        except Exception as exc:
            m._job_results["cable_sync"] = {"error": str(exc)}
        finally:
            if _log_file is not None:
                try:
                    _log_file.close()
                except Exception:
                    pass
            with m._job_lock:
                m._cable_progress.clear()
                m._jobs["cable_sync"] = False

    threading.Thread(target=run, daemon=True).start()
    ctx._send_json({"status": "started", "dry_run": dry_run})


def _do_tree_diff(ctx, data: dict, config: "AppConfig", srv_mod) -> None:
    """Background job: compare the ROM file tree between PC and console."""
    from pathlib import Path as _Path

    source       = data.get("source", "local")        # "local" | "adb"
    serial       = data.get("serial", "").strip()
    pc_path_str  = data.get("pc_path", "").strip()    or (str(config.library_root) if config.library_root else "")
    and_path_str = data.get("android_path", "").strip() or config.anbernic_root or config.auto_sync_android_path

    m = srv_mod
    with m._job_lock:
        if m._jobs.get("tree_diff", False):
            ctx._send_json({"status": "already_running"})
            return
        m._jobs["tree_diff"] = True

    def run() -> None:
        import time as _time
        try:
            from rom_manager.utils.dir_diff import get_local_tree, get_adb_tree, diff_trees

            if not pc_path_str:
                m._job_results["tree_diff"] = {"error": "Ruta PC no configurada (library_root)"}
                return
            pc_root = _Path(pc_path_str)
            if not pc_root.exists():
                m._job_results["tree_diff"] = {"error": f"Ruta PC no existe: {pc_path_str}"}
                return

            skip = frozenset(config.excluded_directories)
            pc_tree = get_local_tree(pc_root, skip)

            if source == "adb":
                if not serial:
                    m._job_results["tree_diff"] = {"error": "serial ADB requerido"}
                    return
                if not and_path_str:
                    m._job_results["tree_diff"] = {"error": "Ruta Android no configurada"}
                    return
                from rom_manager.sync.adb_transport import AdbTransport
                transport = AdbTransport(config.adb, serial, timeout=60)
                android_tree = get_adb_tree(transport, and_path_str, timeout=300)
            else:
                if not and_path_str:
                    m._job_results["tree_diff"] = {"error": "Ruta consola no configurada (anbernic_root)"}
                    return
                and_root = _Path(and_path_str)
                if not and_root.exists():
                    m._job_results["tree_diff"] = {"error": f"Ruta consola no existe: {and_path_str}"}
                    return
                android_tree = get_local_tree(and_root, skip)

            diff = diff_trees(pc_tree, android_tree)
            MAX = 500
            m._job_results["tree_diff"] = {
                "ok":                True,
                "pc_path":           pc_path_str,
                "android_path":      and_path_str,
                "source":            source,
                "only_pc":           diff.only_a[:MAX],
                "only_android":      diff.only_b[:MAX],
                "only_pc_total":     len(diff.only_a),
                "only_android_total": len(diff.only_b),
                "in_both":           diff.in_both,
                "total_pc":          diff.total_a,
                "total_android":     diff.total_b,
                "result_ts":         _time.time(),
            }
        except Exception as exc:
            m._job_results["tree_diff"] = {"error": str(exc)}
        finally:
            with m._job_lock:
                m._jobs["tree_diff"] = False

    threading.Thread(target=run, daemon=True).start()
    ctx._send_json({"status": "started"})


def _do_auto_sync_save(ctx, data: dict, config: "AppConfig", srv_mod) -> None:
    """Save auto-sync settings to config.toml and update in-memory config."""
    from rom_manager.config import write_config_toml
    import rom_manager.web.server as _srv

    updates: dict = {}
    if "sync.auto_sync_direction" in data:
        updates["sync.auto_sync_direction"] = data["sync.auto_sync_direction"]
        config.auto_sync_direction = data["sync.auto_sync_direction"]
    if "sync.auto_sync_android_path" in data:
        updates["sync.auto_sync_android_path"] = data["sync.auto_sync_android_path"]
        config.auto_sync_android_path = data["sync.auto_sync_android_path"]
    if "sync.conflict_policy" in data:
        updates["sync.conflict_policy"] = data["sync.conflict_policy"]
        config.conflict_policy = data["sync.conflict_policy"]
    if "sync.auto_sync_enabled" in data:
        val = bool(data["sync.auto_sync_enabled"])
        updates["sync.auto_sync_enabled"] = val
        config.auto_sync_enabled = val
        _srv._auto_sync_enabled = val

    if updates:
        write_config_toml(config.project_root, updates)

    ctx._send_json({"saved": list(updates.keys()), "enabled": _srv._auto_sync_enabled})


def _do_migrate_split_db(ctx, config: "AppConfig", repository: "LibraryRepository", repo_android: "LibraryRepository") -> None:
    """One-time migration: move Android-path games from PC repo to Android repo."""
    lib_root = str(config.library_root or "").lower().rstrip("/\\")
    if not lib_root:
        ctx._send_json({"error": "library_root not configured — cannot determine which paths are Android"})
        return

    migrated = 0
    errors: list[str] = []
    try:
        with repository.connect() as _conn:
            rows = _conn.execute(
                "SELECT id, original_filename, source_path, platform, file_type, "
                "relative_parent, region, extension, size_bytes, mtime, sha1, md5, "
                "crc32, set_type, created_at, updated_at, canonical_title, "
                "match_confidence, catalog_source "
                "FROM games"
            ).fetchall()

        android_rows = [r for r in rows if not r["source_path"].lower().startswith(lib_root)]

        from rom_manager.scanner.rom_scanner import utc_now as _now
        ts = _now()

        with repo_android.batch() as _android_conn:
            for row in android_rows:
                try:
                    repo_android.upsert_game(
                        original_filename=row["original_filename"],
                        source_path=row["source_path"],
                        platform=row["platform"],
                        file_type=row["file_type"],
                        relative_parent=row["relative_parent"] or "",
                        region=row["region"],
                        extension=row["extension"],
                        size_bytes=int(row["size_bytes"]),
                        mtime=int(row["mtime"] or 0),
                        sha1=row["sha1"] or "",
                        md5=row["md5"] or "",
                        crc32=row["crc32"] or "",
                        set_type=row["set_type"] or "",
                        timestamp=ts,
                        connection=_android_conn,
                    )
                    migrated += 1
                except Exception as exc:
                    errors.append(f"{row['source_path']}: {exc}")

        with repository.batch() as _pc_conn:
            for row in android_rows:
                _pc_conn.execute("DELETE FROM games WHERE source_path = ?", (row["source_path"],))

        with repository.connect() as _conn:
            save_rows = _conn.execute(
                "SELECT original_path, relative_parent, extension, size_bytes, created_at "
                "FROM saves"
            ).fetchall()

        android_saves = [r for r in save_rows if not r["original_path"].lower().startswith(lib_root)]
        if android_saves:
            with repo_android.batch() as _android_conn:
                for row in android_saves:
                    try:
                        repo_android.upsert_save(
                            original_path=row["original_path"],
                            relative_parent=row["relative_parent"] or "",
                            extension=row["extension"],
                            size_bytes=int(row["size_bytes"]),
                            timestamp=ts,
                            connection=_android_conn,
                        )
                    except Exception as exc:
                        errors.append(f"save:{row['original_path']}: {exc}")
            with repository.batch() as _pc_conn:
                for row in android_saves:
                    _pc_conn.execute("DELETE FROM saves WHERE original_path = ?", (row["original_path"],))

    except Exception as exc:
        ctx._send_json({"error": str(exc)})
        return

    ctx._send_json({
        "migrated_games": migrated,
        "errors":         errors[:20],
        "pc_db":          str(config.database_path),
        "android_db":     str(config.database_path_android),
    })
