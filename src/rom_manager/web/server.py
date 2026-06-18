from __future__ import annotations

import json
import logging
import secrets
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import rom_manager.web.handlers.collection as _h_collection
import rom_manager.web.handlers.config as _h_config
import rom_manager.web.handlers.duplicates as _h_duplicates
import rom_manager.web.handlers.esde as _h_esde
import rom_manager.web.handlers.games as _h_games
import rom_manager.web.handlers.inbox as _h_inbox
import rom_manager.web.handlers.organize as _h_organize
import rom_manager.web.handlers.play_history as _h_play_history
import rom_manager.web.handlers.scan as _h_scan
import rom_manager.web.handlers.scraper as _h_scraper
import rom_manager.web.handlers.sync as _h_sync
import rom_manager.web.state as _state
from rom_manager.config import AppConfig
from rom_manager.database.repository import LibraryRepository
from rom_manager.web import auth as _auth
from rom_manager.web.builders.common import _json_response, _repo_for_path, _utc_now_str
from rom_manager.web.daemons import start_all as _start_all_daemons
from rom_manager.web.frontend import HTML

# Re-exported for backward compatibility: these constants moved to handlers/system.py
# during the monolith split, but the original public API lived on `server`.
from rom_manager.web.handlers.system import (  # noqa: F401
    _ES_PLATFORM_FOLDERS,
    _STANDARD_PLATFORM_FOLDERS,
)
from rom_manager.web.router import Router
from rom_manager.web.state import _job_manager

# Tablas de plataformas y helpers de sistema — implementación en web/handlers/system.py

# ── S25: Session auth — implementación en web/auth.py ─────────────────────────
_SESSION_COOKIE = _auth.SESSION_COOKIE
_sessions = _auth._sessions
_sessions_lock = _auth._sessions_lock
_hash_pin = _auth.hash_pin
_check_auth_rate_limit = _auth.check_rate_limit
_record_auth_failure = _auth.record_failure
_clear_auth_failures = _auth.clear_failures
_create_session = _auth.create_session
_destroy_session = _auth.destroy_session
_validate_session = _auth.validate_session
_LOGIN_HTML = _auth.LOGIN_HTML

_logger = logging.getLogger(__name__)


def make_handler(
    repository: LibraryRepository,
    config: AppConfig,
    repository_android: LibraryRepository | None = None,
):
    # If no android repo is provided (e.g. called from CLI), use a no-op fallback = same as PC repo
    _repo_android: LibraryRepository = (
        repository_android if repository_android is not None else repository
    )

    # ── Phase 1: Router (replaces if/elif ladder incrementally) ───────────────
    _router = Router()

    def _set_auto_sync_fn(val: bool) -> None:
        _state._auto_sync_enabled = val

    _h_config.register(_router, config=config, set_auto_sync_fn=_set_auto_sync_fn)

    # ── End Phase 1 router setup ───────────────────────────────────────────────

    def _get_repo(path_str: str) -> LibraryRepository:
        return _repo_for_path(path_str, repository, _repo_android, config)

    def _start_ra_check_bg(api_key: str) -> bool:
        """Start RA check via JobManager. Returns True if started, False if already running."""
        from rom_manager.web.handlers.sync import _do_ra_check

        return _do_ra_check(api_key, config, repository, _job_manager).get("status") == "started"

    _h_collection.register(
        _router,
        config=config,
        repository=repository,
        repo_android=_repo_android,
        get_repo_fn=_get_repo,
    )

    _h_scan.register(
        _router,
        config=config,
        repository=repository,
        repo_android=_repo_android,
        get_repo_fn=_get_repo,
        start_ra_check_fn=_start_ra_check_bg,
        job_manager=_job_manager,
    )

    _h_duplicates.register(
        _router,
        config=config,
        repository=repository,
        repo_android=_repo_android,
        job_manager=_job_manager,
    )

    _h_organize.register(
        _router,
        config=config,
        repository=repository,
        get_repo_fn=_get_repo,
        job_manager=_job_manager,
    )

    _h_sync.register(
        _router,
        config=config,
        repository=repository,
        repo_android=_repo_android,
        start_ra_check_fn=_start_ra_check_bg,
        job_manager=_job_manager,
    )

    _h_inbox.register(
        _router,
        config=config,
        repository=repository,
        job_manager=_job_manager,
    )

    _h_scraper.register(
        _router,
        config=config,
        repository=repository,
        job_manager=_job_manager,
    )

    _h_games.register(
        _router,
        config=config,
        repository=repository,
        get_repo_fn=_get_repo,
        job_manager=_job_manager,
    )

    _h_play_history.register(
        _router,
        repository=repository,
    )

    _h_esde.register(
        _router,
        config=config,
        repository=repository,
        repo_android=_repo_android,
        get_repo_fn=_get_repo,
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
                    filename = path[len("/static/") :]
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
                                ".js": "application/javascript; charset=utf-8",
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
                _h_inbox.handle_inbox_upload(config, _ct, raw, self)
                return

            try:
                data: dict = json.loads(raw) if raw else {}
            except Exception:
                _logger.debug("Cuerpo de petición no era JSON válido; usando {}", exc_info=True)
                data = {}

            try:
                # S25: auth endpoints bypass session check
                if path == "/api/auth":
                    client_ip = self.client_address[0]
                    pin = str(data.get("pin", "")).strip()
                    if not config.web_pin_hash:
                        self._send_json({"ok": True})  # no PIN set → open access
                        return
                    if _check_auth_rate_limit(client_ip):
                        self._send(
                            429,
                            "application/json; charset=utf-8",
                            _json_response(
                                {
                                    "ok": False,
                                    "error": "Demasiados intentos fallidos. Espera unos minutos.",
                                }
                            ),
                        )
                        return
                    if not pin:
                        self._send_json({"ok": False, "error": "PIN requerido"})
                        return
                    expected = _hash_pin(pin, config.web_pin_salt)
                    if secrets.compare_digest(expected, config.web_pin_hash):
                        _clear_auth_failures(client_ip)
                        token = _create_session(config.web_session_ttl)
                        self._send(
                            200,
                            "application/json; charset=utf-8",
                            _json_response({"ok": True}),
                            extra_headers=self._set_session_header(token),
                        )
                    else:
                        _record_auth_failure(client_ip)
                        self._send_json({"ok": False, "error": "PIN incorrecto"})
                    return
                elif path == "/api/auth/logout":
                    token = self._session_token()
                    if token:
                        _destroy_session(token)
                    self._send(
                        200,
                        "application/json; charset=utf-8",
                        _json_response({"ok": True}),
                        extra_headers={"Set-Cookie": f"{_SESSION_COOKIE}=; Max-Age=0; Path=/"},
                    )
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

                    write_config_toml(
                        config.project_root,
                        {
                            "web.pin_hash": pin_hash,
                            "web.pin_salt": salt,
                        },
                    )
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

                    write_config_toml(
                        config.project_root,
                        {
                            "web.pin_hash": "",
                            "web.pin_salt": "",
                        },
                    )
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


def serve(
    *,
    host: str,
    port: int,
    repository: LibraryRepository,
    config: AppConfig,
    repository_android: LibraryRepository | None = None,
    tray: bool = False,
) -> None:
    _state._auto_sync_enabled = config.sync.auto_sync_enabled

    if host != "127.0.0.1" and not config.web_pin_hash:
        _logger.warning(
            "AVISO DE SEGURIDAD: el servidor está expuesto en la red (%s:%d) sin PIN configurado. "
            "Cualquier usuario de tu red local puede acceder y modificar todos los datos. "
            "Activa un PIN en Settings → Seguridad.",
            host,
            port,
        )

    # S34-1: reload platform tables with user override if present
    from rom_manager.detection.platform_detector import reload_platforms

    user_platforms = config.data_dir / "platforms.toml"
    reload_platforms(user_platforms if user_platforms.exists() else None)

    _start_all_daemons(config, repository)

    # S39-3: system tray icon (Windows only)
    if tray:
        import sys as _sys

        if _sys.platform == "win32":
            try:
                from rom_manager.utils.tray_icon import TrayIcon

                def _on_sync_from_tray() -> None:
                    sources = config.sync.sync_sources
                    if not sources:
                        return
                    from pathlib import Path as _Path

                    from rom_manager.sync.rclone_transport import RcloneTransport
                    from rom_manager.sync.save_syncer import sync_saves

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
                            _logger.warning(
                                "Sync automático tras setup (saves) falló", exc_info=True
                            )
                    # D2: implicit saves/states remotes
                    _implicit_tray = []
                    if config.sync.saves_remote and config.library_root:
                        _implicit_tray.append(
                            (
                                _Path(config.library_root) / "saves",
                                config.sync.saves_remote,
                                config.save_extensions,
                            )
                        )
                    if config.sync.states_remote and config.library_root:
                        _implicit_tray.append(
                            (
                                _Path(config.library_root) / "states",
                                config.sync.states_remote,
                                config.state_extensions,
                            )
                        )
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
                            _logger.warning(
                                "Sync automático tras setup (remote configurado) falló",
                                exc_info=True,
                            )
                    if _state._tray_instance:
                        _state._tray_instance.set_status(f"Sync OK {_utc_now_str()[:16]}")
                        _state._tray_instance.show_balloon("Retro Vault", "Sync completado.")

                def _on_quit_from_tray() -> None:
                    import threading as _threading

                    _threading.Thread(target=httpd.shutdown, daemon=True).start()

                _state._tray_instance = TrayIcon(
                    port=port,
                    on_sync=_on_sync_from_tray,
                    on_quit=_on_quit_from_tray,
                )
                _state._tray_instance.start()
                _logger.info("Tray icon started")
            except Exception as _te:
                _logger.warning("Could not start tray icon: %s", _te)

    global _httpd_instance
    handler = make_handler(repository, config, repository_android=repository_android)
    with ThreadingHTTPServer((host, port), handler) as httpd:
        _httpd_instance = httpd
        httpd.serve_forever()

    # Clean up tray when server exits
    if _state._tray_instance is not None:
        try:
            _state._tray_instance.stop()
        except Exception:
            _logger.debug("No se pudo detener el icono de la bandeja al salir", exc_info=True)
