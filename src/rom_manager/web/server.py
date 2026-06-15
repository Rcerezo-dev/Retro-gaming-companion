from __future__ import annotations

import json
import logging
import secrets
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from rom_manager.config import AppConfig
from rom_manager.database.repository import LibraryRepository
from rom_manager.planner import build_plan
from rom_manager.planner.operation_planner import FormatOptions
from rom_manager.reports import build_report, to_csv, to_json
from rom_manager.web.frontend import HTML
from rom_manager.web.response_builders import (
    _json_response, _test_path, _list_drives, _utc_now_str,
    _repo_for_path,
    _build_junk_scan, _build_library_report, _build_status,
    _build_games, _count_companion_saves,
    _build_folder_analysis,
    _build_assets, _build_sync_log,
    _build_cable_sync_preview,
)
from rom_manager.web.cable_sync_daemon import _auto_sync_loop, _sd_card_sync_loop
from rom_manager.web.inbox_pipeline import (
    _build_inbox_scan, _run_setup_pipeline, _run_inbox_pipeline, _watcher_now,
)
import rom_manager.web.state as _state
from rom_manager.web.state import (
    _job_lock, _jobs, _job_results, _job_manager,
    _chd_progress, _cso_progress, _scrape_progress, _zip_progress,
    _health_progress, _ra_progress, _cable_progress, _scan_progress,
    _apply_progress, _inbox_progress, _setup_progress,
    _verify_chd_progress, _inbox_watcher_status,
    _scan_cancel, _cable_cancel, _chd_cancel, _verify_chd_cancel,
    _cso_cancel, _zip_cancel, _health_cancel, _ra_cancel,
    _scrape_cancel, _match_cancel, _ss_last_quota,
    _auto_sync_enabled, _auto_sync_last_devices,
    _auto_sync_status, _sd_sync_status,
    _tray_instance, _httpd_instance,
)


def _start_job(name: str, fn: "Callable[[], None]") -> dict:
    """Start a background job if not already running.

    Returns ``{"status": "started"}`` or ``{"status": "already_running"}``.
    *fn* is responsible for setting ``_job_results[name]`` and clearing
    ``_jobs[name]`` in its own finally block.
    """
    from typing import Callable  # noqa: F401
    with _job_lock:
        if _jobs[name]:
            return {"status": "already_running"}
        _jobs[name] = True
    threading.Thread(target=fn, daemon=True).start()
    return {"status": "started"}


# Tablas de plataformas y helpers de sistema — implementación en web/handlers/system.py
from rom_manager.web.handlers.system import (
    _ES_PLATFORM_FOLDERS,
    _STANDARD_PLATFORM_FOLDERS,
    _get_local_ip,
    _handle_detect_cloud_folder,
    _handle_rclone_export_config,
    _build_anbernic_setup_sh,
    _handle_rclone_status,
    _handle_system_status,
    _handle_library_doctor,
    _handle_retroarch_check,
)

# ── S25: Session auth — implementación en web/auth.py ─────────────────────────
from rom_manager.web import auth as _auth
_SESSION_COOKIE        = _auth.SESSION_COOKIE
_sessions              = _auth._sessions
_sessions_lock         = _auth._sessions_lock
_hash_pin              = _auth.hash_pin
_check_auth_rate_limit = _auth.check_rate_limit
_record_auth_failure   = _auth.record_failure
_clear_auth_failures   = _auth.clear_failures
_create_session        = _auth.create_session
_destroy_session       = _auth.destroy_session
_validate_session      = _auth.validate_session
_LOGIN_HTML            = _auth.LOGIN_HTML

_logger = logging.getLogger(__name__)



def make_handler(repository: LibraryRepository, config: AppConfig, repository_android: LibraryRepository | None = None):
    logger = logging.getLogger(__name__)
    # If no android repo is provided (e.g. called from CLI), use a no-op fallback = same as PC repo
    _repo_android: LibraryRepository = repository_android if repository_android is not None else repository

    # ── Phase 1: Router (replaces if/elif ladder incrementally) ───────────────
    from rom_manager.web.router import Router
    import rom_manager.web.server as _srv_mod  # used by set_auto_sync_fn

    _router = Router()

    def _set_auto_sync_fn(val: bool) -> None:
        _state._auto_sync_enabled = val

    import rom_manager.web.handlers.config as _h_config
    _h_config.register(_router, config=config, set_auto_sync_fn=_set_auto_sync_fn)

    # ── End Phase 1 router setup ───────────────────────────────────────────────

    def _get_repo(path_str: str) -> LibraryRepository:
        return _repo_for_path(path_str, repository, _repo_android, config)

    def _start_ra_check_bg(api_key: str) -> bool:
        """Start RA check via JobManager. Returns True if started, False if already running."""
        from rom_manager.web.handlers.sync import _do_ra_check
        return _do_ra_check(api_key, config, repository, _job_manager).get("status") == "started"

    import rom_manager.web.handlers.collection as _h_collection
    import sys as _sys_dbg
    try:
        _h_collection.register(_router, config=config, repository=repository, repo_android=_repo_android, get_repo_fn=_get_repo)
        asset_routes = [r for r in _router.routes() if 'asset' in r[1].lower()]
        print(f"[DEBUG] Registered asset routes: {asset_routes}", file=_sys_dbg.stderr)
        print(f"[DEBUG] Total routes after collection: {len(_router.routes())}", file=_sys_dbg.stderr)
        if not asset_routes:
            print(f"[DEBUG] WARNING: No asset routes registered!", file=_sys_dbg.stderr)
            print(f"[DEBUG] All routes: {_router.routes()[:10]}", file=_sys_dbg.stderr)
    except Exception as _reg_err:
        print(f"[ERROR] Failed to register collection handlers: {_reg_err}", file=_sys_dbg.stderr)
        import traceback
        traceback.print_exc(file=_sys_dbg.stderr)
        raise

    import rom_manager.web.handlers.scan as _h_scan
    _h_scan.register(
        _router,
        config=config,
        repository=repository,
        repo_android=_repo_android,
        get_repo_fn=_get_repo,
        start_ra_check_fn=_start_ra_check_bg,
        srv_mod=_srv_mod,
        job_manager=_job_manager,
    )

    import rom_manager.web.handlers.duplicates as _h_duplicates
    _h_duplicates.register(
        _router,
        config=config,
        repository=repository,
        repo_android=_repo_android,
        srv_mod=_srv_mod,
        job_manager=_job_manager,
    )

    import rom_manager.web.handlers.organize as _h_organize
    _h_organize.register(
        _router,
        config=config,
        repository=repository,
        get_repo_fn=_get_repo,
        srv_mod=_srv_mod,
        job_manager=_job_manager,
    )

    import rom_manager.web.handlers.sync as _h_sync
    _h_sync.register(
        _router,
        config=config,
        repository=repository,
        repo_android=_repo_android,
        start_ra_check_fn=_start_ra_check_bg,
        srv_mod=_srv_mod,
        job_manager=_job_manager,
    )

    import rom_manager.web.handlers.inbox as _h_inbox
    _h_inbox.register(
        _router,
        config=config,
        repository=repository,
        srv_mod=_srv_mod,
        job_manager=_job_manager,
    )

    import rom_manager.web.handlers.scraper as _h_scraper
    _h_scraper.register(
        _router,
        config=config,
        repository=repository,
        srv_mod=_srv_mod,
        job_manager=_job_manager,
    )

    import rom_manager.web.handlers.games as _h_games
    _h_games.register(
        _router,
        config=config,
        repository=repository,
        get_repo_fn=_get_repo,
        srv_mod=_srv_mod,
        job_manager=_job_manager,
    )

    import rom_manager.web.handlers.play_history as _h_play_history
    _h_play_history.register(
        _router,
        repository=repository,
    )

    import rom_manager.web.handlers.esde as _h_esde
    _h_esde.register(
        _router,
        config=config,
        repository=repository,
        repo_android=_repo_android,
        get_repo_fn=_get_repo,
        srv_mod=_srv_mod,
        job_manager=_job_manager,
    )

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            pass  # suppress default request logging

        # ── S25: Auth helpers ─────────────────────────────────────────────────

        def _auth_required(self) -> bool:
            """True when PIN protection is active (pin_hash is set in config)."""
            return bool(config.web_pin_hash)

        def _session_token(self) -> str | None:
            raw = self.headers.get("Cookie", "")
            if not raw:
                return None
            c = SimpleCookie()
            c.load(raw)
            morsel = c.get(_SESSION_COOKIE)
            return morsel.value if morsel else None

        def _is_authenticated(self) -> bool:
            if not self._auth_required():
                return True
            token = self._session_token()
            return bool(token and _validate_session(token))

        def _redirect_to_login(self) -> None:
            self._send(302, "text/plain", b"", extra_headers={"Location": "/login"})

        def _set_session_header(self, token: str) -> dict[str, str]:
            cookie = f"{_SESSION_COOKIE}={token}; HttpOnly; SameSite=Strict; Path=/"
            return {"Set-Cookie": cookie}

        # ── GET ──────────────────────────────────────────────────────────────

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            qs = parse_qs(parsed.query)

            try:
                # S25: serve login page and static assets without auth
                if path == "/login":
                    self._send(200, "text/html; charset=utf-8", _LOGIN_HTML.encode())
                    return
                if path.startswith("/static/") or path == "/favicon.ico":
                    pass  # fall through to normal handling (no auth on static)
                elif not self._is_authenticated():
                    self._redirect_to_login()
                    return

                # Phase 1: try router before the legacy ladder
                self._qs = qs
                if _router.dispatch("GET", path, self):
                    return

                if path == "/":
                    self._send(200, "text/html; charset=utf-8", HTML.encode())
                elif path.startswith("/static/"):
                    filename = path[len("/static/"):]
                    import sys as _sys
                    if getattr(_sys, "frozen", False) and hasattr(_sys, "_MEIPASS"):
                        static_dir = Path(_sys._MEIPASS) / "rom_manager" / "web" / "static"
                    else:
                        static_dir = Path(__file__).parent / "static"
                    if not filename:
                        self._send(404, "text/plain", b"Not found")
                    else:
                        file_path = (static_dir / filename).resolve()
                        # Security: prevent path traversal while allowing subdirectories
                        try:
                            file_path.relative_to(static_dir.resolve())
                        except (ValueError, OSError):
                            self._send(404, "text/plain", b"Not found")
                            return
                        if not file_path.is_file():
                            self._send(404, "text/plain", b"Not found")
                        else:
                            ext = file_path.suffix.lower()
                            content_type = {
                                ".css": "text/css; charset=utf-8",
                                ".js":  "application/javascript; charset=utf-8",
                            }.get(ext, "application/octet-stream")
                            self._send(200, content_type, file_path.read_bytes())
                else:
                    self._send(404, "text/plain", b"Not found")
            except Exception as exc:
                body = json.dumps({"error": str(exc)}).encode()
                self._send(500, "application/json", body)

        # ── POST ─────────────────────────────────────────────────────────────

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path

            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"

            # Handle multipart file uploads before JSON parse
            _ct = self.headers.get("Content-Type", "")
            if _ct.startswith("multipart/form-data") and path == "/api/inbox-upload":
                from rom_manager.web.handlers.inbox import handle_inbox_upload
                handle_inbox_upload(config, _ct, raw, self)
                return

            try:
                data: dict = json.loads(raw) if raw else {}
            except Exception:
                data = {}

            try:
                # S25: auth endpoints bypass session check
                if path == "/api/auth":
                    client_ip = self.client_address[0]
                    pin = str(data.get("pin", "")).strip()
                    if not config.web_pin_hash:
                        self._send_json({"ok": True})   # no PIN set → open access
                        return
                    if _check_auth_rate_limit(client_ip):
                        self._send(429, "application/json; charset=utf-8",
                                   _json_response({"ok": False, "error": "Demasiados intentos fallidos. Espera unos minutos."}))
                        return
                    if not pin:
                        self._send_json({"ok": False, "error": "PIN requerido"})
                        return
                    expected = _hash_pin(pin, config.web_pin_salt)
                    if secrets.compare_digest(expected, config.web_pin_hash):
                        _clear_auth_failures(client_ip)
                        token = _create_session(config.web_session_ttl)
                        self._send(200, "application/json; charset=utf-8",
                                   _json_response({"ok": True}),
                                   extra_headers=self._set_session_header(token))
                    else:
                        _record_auth_failure(client_ip)
                        self._send_json({"ok": False, "error": "PIN incorrecto"})
                    return
                elif path == "/api/auth/logout":
                    token = self._session_token()
                    if token:
                        _destroy_session(token)
                    self._send(200, "application/json; charset=utf-8",
                               _json_response({"ok": True}),
                               extra_headers={"Set-Cookie": f"{_SESSION_COOKIE}=; Max-Age=0; Path=/"})
                    return
                elif path == "/api/set-pin":
                    # Authenticated OR no PIN configured yet (first-time setup)
                    if not self._is_authenticated():
                        self._send_json({"error": "No autorizado"})
                        return
                    pin = str(data.get("pin", "")).strip()
                    if len(pin) < 4 or len(pin) > 10:
                        self._send_json({"error": "El PIN debe tener entre 4 y 10 dígitos"})
                        return
                    salt = secrets.token_hex(16)
                    pin_hash = _hash_pin(pin, salt)
                    from rom_manager.config import write_config_toml
                    write_config_toml(config.project_root, {
                        "web.pin_hash": pin_hash,
                        "web.pin_salt": salt,
                    })
                    config.web_pin_hash = pin_hash
                    config.web_pin_salt = salt
                    # Invalidate all existing sessions so new PIN takes effect
                    with _sessions_lock:
                        _sessions.clear()
                    self._send_json({"ok": True})
                    return
                elif path == "/api/clear-pin":
                    if not self._is_authenticated():
                        self._send_json({"error": "No autorizado"})
                        return
                    from rom_manager.config import write_config_toml
                    write_config_toml(config.project_root, {
                        "web.pin_hash": "",
                        "web.pin_salt": "",
                    })
                    config.web_pin_hash = ""
                    config.web_pin_salt = ""
                    with _sessions_lock:
                        _sessions.clear()
                    self._send_json({"ok": True})
                    return

                # All other POST endpoints require auth
                if not self._is_authenticated():
                    self._send_json({"error": "No autorizado", "auth_required": True})
                    return

                # Phase 1: try router before the legacy ladder
                self._post_data = data
                if _router.dispatch("POST", path, self):
                    return

                else:
                    self._send(404, "text/plain", b"Not found")
            except Exception as exc:
                body = json.dumps({"error": str(exc)}).encode()
                self._send(500, "application/json", body)

        # ── Helpers ──────────────────────────────────────────────────────────

        def _send(
            self,
            code: int,
            content_type: str,
            body: bytes,
            extra_headers: dict[str, str] | None = None,
        ) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            for k, v in (extra_headers or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, data: object) -> None:
            body = _json_response(data)
            self._send(200, "application/json; charset=utf-8", body)

        def _send_error(self, code: int, message: str) -> None:
            body = _json_response({"error": message})
            self._send(code, "application/json; charset=utf-8", body)

    return Handler


# ── Health-check scheduler (S37-1) ────────────────────────────────────────────

_HEALTH_CHECK_INTERVAL_DAYS = 7


def _health_schedule_path(config: "AppConfig") -> "Path":
    return config.data_dir / "health_schedule.json"


def _read_health_schedule(config: "AppConfig") -> dict:
    """Return the stored schedule dict, or empty dict if not found."""
    import json as _json
    p = _health_schedule_path(config)
    try:
        return _json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_health_schedule(config: "AppConfig", *, ok: int, corrupted: int, missing: int) -> None:
    """Persist health check completion time and summary."""
    import json as _json
    import datetime as _dt
    data = {
        "last_run_at": _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_ok": ok,
        "last_corrupted": corrupted,
        "last_missing": missing,
    }
    p = _health_schedule_path(config)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(_json.dumps(data, indent=2), encoding="utf-8")
    except Exception as exc:
        _logger.debug("Could not write health schedule: %s", exc)


def _health_scheduler_loop(config: "AppConfig", get_repo_fn) -> None:  # type: ignore[type-arg]
    """Daemon: trigger an automatic health check once per week."""
    import datetime as _dt
    import time as _time

    _time.sleep(60)  # let the server finish startup before first check

    while True:
        try:
            schedule = _read_health_schedule(config)
            last_run_raw = schedule.get("last_run_at")
            overdue = True
            if last_run_raw:
                try:
                    last_run = _dt.datetime.fromisoformat(last_run_raw.replace("Z", "+00:00"))
                    elapsed = (_dt.datetime.now(tz=_dt.timezone.utc) - last_run).days
                    overdue = elapsed >= _HEALTH_CHECK_INTERVAL_DAYS
                except Exception:
                    pass

            if overdue:
                if not _job_manager.get_status()["health_check_running"]:
                    repository = get_repo_fn()
                    _logger.info("Scheduled health check starting (overdue by %s days)", "?" if not last_run_raw else elapsed)
                    _cancel = _job_manager.cancel_event("health_check")

                    def _scheduled_run(_repo=repository, _c=_cancel) -> None:
                        job_result = None
                        try:
                            from rom_manager.utils.health_checker import check_library_health

                            def _prog(current: int, total: int, filename: str) -> None:
                                _job_manager.update_progress("health_check", {"current": current, "total": total, "current_file": filename})

                            summary = check_library_health(_repo, progress_cb=_prog, cancel_event=_c)
                            job_result = {
                                "ok": summary.ok,
                                "corrupted": summary.corrupted,
                                "missing": summary.missing,
                                "cancelled": _c.is_set(),
                                "auto": True,
                                "issues": [
                                    {"source_path": r.source_path, "status": r.status,
                                     "stored_sha1": r.stored_sha1[:12],
                                     "computed_sha1": r.computed_sha1[:12] if r.computed_sha1 else "",
                                     "platform": r.platform, "canonical_title": r.canonical_title}
                                    for r in summary.results
                                ],
                            }
                            _write_health_schedule(config, ok=summary.ok,
                                                   corrupted=summary.corrupted, missing=summary.missing)
                            if not _c.is_set() and config.notify_desktop:
                                from rom_manager.utils.notifier import notify
                                if summary.corrupted or summary.missing:
                                    notify("Retro Vault — Health Check",
                                           f"⚠ {summary.corrupted} corruptos, {summary.missing} desaparecidos")
                                else:
                                    notify("Retro Vault — Health Check",
                                           f"✓ {summary.ok} ROMs verificados, sin problemas")
                        except Exception as exc:
                            _logger.error("Scheduled health check error: %s", exc)
                        finally:
                            _job_manager.finish("health_check", job_result)

                    _job_manager.start("health_check", _scheduled_run)

        except Exception as exc:
            _logger.debug("Health scheduler error: %s", exc)

        _time.sleep(3600)  # check every hour


def serve(
    *,
    host: str,
    port: int,
    repository: LibraryRepository,
    config: AppConfig,
    repository_android: LibraryRepository | None = None,
    tray: bool = False,
) -> None:
    global _tray_instance
    _state._auto_sync_enabled = config.auto_sync_enabled

    if host != "127.0.0.1" and not config.web_pin_hash:
        _logger.warning(
            "AVISO DE SEGURIDAD: el servidor está expuesto en la red (%s:%d) sin PIN configurado. "
            "Cualquier usuario de tu red local puede acceder y modificar todos los datos. "
            "Activa un PIN en Settings → Seguridad.",
            host, port,
        )

    # S34-1: reload platform tables with user override if present
    from rom_manager.detection.platform_detector import reload_platforms
    user_platforms = config.data_dir / "platforms.toml"
    reload_platforms(user_platforms if user_platforms.exists() else None)

    if config.auto_sync_enabled:
        t = threading.Thread(
            target=_auto_sync_loop,
            args=(config, lambda: repository),
            daemon=True,
        )
        t.name = "auto-sync-daemon"
        t.start()
        _logger.info("Auto-sync daemon started (polling every 10 s)")

    sd_t = threading.Thread(
        target=_sd_card_sync_loop,
        args=(config, lambda: repository),
        daemon=True,
    )
    sd_t.name = "sd-sync-daemon"
    sd_t.start()
    _logger.info("SD card sync daemon started (polling every 8 s)")

    # Inbox watcher daemon (runs only when inbox_auto_process is True)
    def _inbox_watcher_with_repo() -> None:
        import time as _time
        while True:
            try:
                _time.sleep(30)
                if not config.inbox_path or not config.inbox_auto_process:
                    _inbox_watcher_status.update({"watching": False, "last_check": None, "pending_files": 0})
                    continue
                inbox = Path(config.inbox_path).resolve()
                if not inbox.exists():
                    _inbox_watcher_status.update({"watching": True, "last_check": _watcher_now(), "pending_files": 0})
                    continue
                pending: list[Path] = [
                    e for e in inbox.iterdir()
                    if e.is_file() and not e.name.startswith(".") and not e.name.startswith("_")
                ]
                _inbox_watcher_status.update({
                    "watching": True,
                    "last_check": _watcher_now(),
                    "pending_files": len(pending),
                })
                if pending:
                    if not _job_manager.get_status()["inbox_running"]:
                        _logger.info("Inbox watcher: %d files detected, launching pipeline", len(pending))
                        _inbox_watcher_status["trigger_ts"] = _time.time()
                        target_root_str = config.inbox_target_root or (str(config.library_root) if config.library_root else "")

                        def _watcher_run(_tr=target_root_str) -> None:
                            _run_inbox_pipeline(config.inbox_path, _tr, config.inbox_delete_source, repository, config, _job_manager)

                        _job_manager.start("inbox", _watcher_run)
            except Exception as exc:
                _logger.debug("Inbox watcher error: %s", exc)

    tw = threading.Thread(target=_inbox_watcher_with_repo, daemon=True)
    tw.name = "inbox-watcher-daemon"
    tw.start()
    _logger.info("Inbox watcher daemon started")

    # Health check scheduler (S37-1)
    ht = threading.Thread(
        target=_health_scheduler_loop,
        args=(config, lambda: repository),
        daemon=True,
    )
    ht.name = "health-check-scheduler"
    ht.start()
    _logger.info("Health check scheduler started (interval: %d days)", _HEALTH_CHECK_INTERVAL_DAYS)

    # S39-3: system tray icon (Windows only)
    if tray:
        import sys as _sys
        if _sys.platform == "win32":
            try:
                from rom_manager.utils.tray_icon import TrayIcon

                def _on_sync_from_tray() -> None:
                    import rom_manager.web.server as _srv
                    sources = config.sync_sources
                    if not sources:
                        return
                    from rom_manager.sync.rclone_transport import RcloneTransport
                    from rom_manager.sync.save_syncer import sync_saves
                    from pathlib import Path as _Path
                    transport = RcloneTransport(rclone=config.rclone_binary)
                    for src in sources:
                        saves_dir = _Path(src.local_dir)
                        if not saves_dir.exists():
                            continue
                        try:
                            sync_saves(
                                saves_dir,
                                saves_remote=src.remote,
                                transport=transport,
                                repository=repository,
                                save_extensions=config.save_extensions,
                                state_extensions=config.state_extensions,
                                states_remote=None,
                                dry_run=False,
                            )
                        except Exception:
                            pass
                    # D2: implicit saves/states remotes
                    _implicit_tray = []
                    if config.saves_remote and config.library_root:
                        _implicit_tray.append((_Path(config.library_root) / "saves", config.saves_remote, config.save_extensions))
                    if config.states_remote and config.library_root:
                        _implicit_tray.append((_Path(config.library_root) / "states", config.states_remote, config.state_extensions))
                    for _dir, _remote, _exts in _implicit_tray:
                        if not _dir.exists():
                            continue
                        try:
                            # D2: implicit tray sync with dual remotes
                            _is_states_tray = _exts == config.state_extensions
                            sync_saves(
                                _dir,
                                saves_remote=_remote if not _is_states_tray else None,
                                transport=transport,
                                repository=repository,
                                save_extensions=_exts,
                                state_extensions=_exts if _is_states_tray else tuple(),
                                states_remote=_remote if _is_states_tray else None,
                                dry_run=False,
                            )
                        except Exception:
                            pass
                    if _tray_instance:
                        _tray_instance.set_status(f"Sync OK {_utc_now_str()[:16]}")
                        _tray_instance.show_balloon("Retro Vault", "Sync completado.")

                def _on_quit_from_tray() -> None:
                    import threading as _threading
                    _threading.Thread(target=httpd.shutdown, daemon=True).start()

                _tray_instance = TrayIcon(
                    port=port,
                    on_sync=_on_sync_from_tray,
                    on_quit=_on_quit_from_tray,
                )
                _tray_instance.start()
                _logger.info("Tray icon started")
            except Exception as _te:
                _logger.warning("Could not start tray icon: %s", _te)

    global _httpd_instance
    handler = make_handler(repository, config, repository_android=repository_android)
    with ThreadingHTTPServer((host, port), handler) as httpd:
        _httpd_instance = httpd
        httpd.serve_forever()

    # Clean up tray when server exits
    if _tray_instance is not None:
        try:
            _tray_instance.stop()
        except Exception:
            pass
