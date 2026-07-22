"""Cloud provider OAuth wizard — rclone authorize flow without a terminal.

Routes:
  GET  /api/cloud-auth/status        — list configured remotes
  POST /api/cloud-auth/start         — begin OAuth flow (opens browser)
  GET  /api/cloud-auth/poll          — check if flow finished
  POST /api/cloud-auth/cancel        — abort a running flow (kills rclone)
  POST /api/cloud-auth/finalize      — write remote to rclone config
  POST /api/cloud-auth/disconnect    — delete remote from rclone config
"""

from __future__ import annotations

import re
import subprocess
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.web.router import Router

# rclone provider display names → (rclone_type, suggested_remote_name)
_PROVIDERS: dict[str, tuple[str, str]] = {
    "dropbox": ("dropbox", "dropbox"),
    "gdrive": ("drive", "gdrive"),
}

# Module-level auth state (one flow at a time)
_auth_lock = threading.Lock()
_auth_thread: threading.Thread | None = None
_auth_proc: subprocess.Popen | None = None
_auth_done = False
_auth_token: str | None = None
_auth_error: str | None = None
# CLOUD-UX-4: el poll devuelve el provider que inició el flujo — sin esto el
# frontend finalizaba contra "el primer provider no configurado" y el token de
# Google Drive podía acabar escrito bajo el remote dropbox.
_auth_provider: str | None = None
_auth_remote_name: str | None = None


def _rclone(config: AppConfig, *args: str) -> subprocess.CompletedProcess:
    rclone_bin = getattr(config, "rclone_binary", None) or "rclone"
    return subprocess.run(  # noqa: S603
        [rclone_bin, *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


def _run_authorize(rclone_bin: str, provider: str, remote_name: str) -> None:
    global _auth_done, _auth_token, _auth_error, _auth_proc
    try:
        # Popen (no run) para que /api/cloud-auth/cancel pueda matar el proceso
        # — antes 'rclone authorize' seguía vivo hasta 5 min tras cancelar.
        proc = subprocess.Popen(  # noqa: S603
            [rclone_bin, "authorize", provider],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        with _auth_lock:
            _auth_proc = proc
        try:
            stdout, stderr = proc.communicate(timeout=300)  # 5 min browser flow
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            raise
        out = stdout + stderr
        # rclone outputs token between "--->" and "<---End paste"
        m = re.search(r"--->\s*(\{.*?\})\s*<---", out, re.DOTALL)
        if m:
            token = m.group(1).strip()
            with _auth_lock:
                _auth_token = token
                _auth_done = True
        else:
            with _auth_lock:
                # No pisar el "cancelado" que pudo dejar /api/cloud-auth/cancel
                if _auth_error is None:
                    _auth_error = (
                        stderr.strip() or "No se recibió token — ¿autorizaste en el navegador?"
                    )
                _auth_done = True
    except subprocess.TimeoutExpired:
        with _auth_lock:
            _auth_error = "Tiempo de espera agotado (5 min)"
            _auth_done = True
    except Exception as exc:
        with _auth_lock:
            _auth_error = str(exc)
            _auth_done = True


def register(router: Router, *, config: AppConfig) -> None:

    @router.get("/api/cloud-auth/status")
    def get_status(ctx) -> None:
        rclone_bin = getattr(config, "rclone_binary", None) or "rclone"
        try:
            proc = subprocess.run(  # noqa: S603
                [rclone_bin, "listremotes"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            existing = {r.rstrip(":") for r in proc.stdout.splitlines() if r.strip()}
            providers = [
                {
                    "id": pid,
                    "label": "Dropbox" if pid == "dropbox" else "Google Drive",
                    "remote_name": suggested,
                    "configured": suggested in existing,
                }
                for pid, (_, suggested) in _PROVIDERS.items()
            ]
            ctx._send_json({"providers": providers, "all_remotes": sorted(existing)})
        except FileNotFoundError:
            ctx._send_json(
                {"error": "rclone no encontrado — instálalo o configura su ruta en Settings"}
            )
        except Exception as exc:
            ctx._send_json({"error": str(exc)})

    @router.post("/api/cloud-auth/start")
    def post_start(ctx) -> None:
        global _auth_thread, _auth_done, _auth_token, _auth_error
        global _auth_provider, _auth_remote_name
        data = ctx._post_data
        provider_id = (data.get("provider") or "").strip()
        if provider_id not in _PROVIDERS:
            ctx._send_json({"error": f"Provider desconocido: {provider_id!r}"})
            return
        rclone_type, remote_name = _PROVIDERS[provider_id]
        rclone_bin = getattr(config, "rclone_binary", None) or "rclone"
        with _auth_lock:
            # CLOUD-UX-4: un solo flujo a la vez — todo el estado es global
            if _auth_thread is not None and _auth_thread.is_alive():
                busy = True
            else:
                busy = False
                _auth_done = False
                _auth_token = None
                _auth_error = None
                _auth_provider = provider_id
                _auth_remote_name = remote_name
                _auth_thread = threading.Thread(
                    target=_run_authorize,
                    args=(rclone_bin, rclone_type, remote_name),
                    daemon=True,
                )
                _auth_thread.start()
        if busy:
            ctx._send_json({"error": "Ya hay una autorización en curso — cancélala primero"})
            return
        ctx._send_json({"started": True, "provider": provider_id, "remote_name": remote_name})

    @router.get("/api/cloud-auth/poll")
    def get_poll(ctx) -> None:
        with _auth_lock:
            done = _auth_done
            token = _auth_token
            error = _auth_error
            provider = _auth_provider
            remote_name = _auth_remote_name
        ctx._send_json(
            {
                "done": done,
                "token": token,
                "error": error,
                "provider": provider,
                "remote_name": remote_name,
            }
        )

    @router.post("/api/cloud-auth/cancel")
    def post_cancel(ctx) -> None:
        global _auth_done, _auth_error
        with _auth_lock:
            proc = _auth_proc
            if _auth_error is None and not _auth_done:
                _auth_error = "Autorización cancelada"
            _auth_done = True
        if proc is not None and proc.poll() is None:
            proc.kill()
        ctx._send_json({"ok": True})

    @router.post("/api/cloud-auth/finalize")
    def post_finalize(ctx) -> None:
        data = ctx._post_data
        provider_id = (data.get("provider") or "").strip()
        remote_name = (data.get("remote_name") or "").strip()
        token = (data.get("token") or "").strip()
        if not all([provider_id, remote_name, token]):
            ctx._send_json({"error": "Faltan parámetros: provider, remote_name, token"})
            return
        if provider_id not in _PROVIDERS:
            ctx._send_json({"error": f"Provider desconocido: {provider_id!r}"})
            return
        rclone_type, _ = _PROVIDERS[provider_id]
        rclone_bin = getattr(config, "rclone_binary", None) or "rclone"
        try:
            proc = subprocess.run(  # noqa: S603
                [rclone_bin, "config", "create", remote_name, rclone_type, "token", token],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if proc.returncode != 0:
                ctx._send_json({"error": proc.stderr.strip() or "Error al crear el remote"})
            else:
                ctx._send_json({"ok": True, "remote_name": remote_name})
        except Exception as exc:
            ctx._send_json({"error": str(exc)})

    @router.post("/api/cloud-auth/disconnect")
    def post_disconnect(ctx) -> None:
        data = ctx._post_data
        remote_name = (data.get("remote_name") or "").strip()
        if not remote_name:
            ctx._send_json({"error": "Falta remote_name"})
            return
        rclone_bin = getattr(config, "rclone_binary", None) or "rclone"
        try:
            proc = subprocess.run(  # noqa: S603
                [rclone_bin, "config", "delete", remote_name],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if proc.returncode != 0:
                ctx._send_json({"error": proc.stderr.strip() or "Error al eliminar el remote"})
            else:
                ctx._send_json({"ok": True})
        except Exception as exc:
            ctx._send_json({"error": str(exc)})
