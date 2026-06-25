"""PHASE6-3b: download the latest GitHub release installer and apply it.

Self-contained background-download state (lock + dict), same pattern as the
DAT downloader in ``scan.py`` — no JobManager registration needed for a
one-off, single-instance download.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

from rom_manager.utils.update_checker import get_result
from rom_manager.utils.update_installer import (
    download_update,
    find_update_asset,
    is_frozen,
    launch_installer,
)

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.web.router import Router

_lock = threading.Lock()
_state: dict[str, Any] = {
    "running": False,
    "done": False,
    "error": None,
    "bytes_done": 0,
    "bytes_total": 0,
    "downloaded_path": None,
}


def register(router: Router, *, config: AppConfig) -> None:
    """Register the update download/apply routes."""

    # ── GET /api/update/status ────────────────────────────────────────────────
    @router.get("/api/update/status")
    def get_update_status(ctx) -> None:
        with _lock:
            ctx._send_json(dict(_state))

    # ── POST /api/update/download ─────────────────────────────────────────────
    @router.post("/api/update/download")
    def post_update_download(ctx) -> None:
        if not is_frozen():
            ctx._send_json(
                {
                    "status": "error",
                    "error": "Esta instancia se ejecuta desde el código fuente; "
                    "la actualización automática solo aplica al ejecutable empaquetado.",
                }
            )
            return

        asset = find_update_asset(get_result().get("assets", []))
        if asset is None:
            ctx._send_json(
                {"status": "error", "error": "El último release no tiene un instalador (.exe) adjunto."}
            )
            return

        with _lock:
            if _state["running"]:
                ctx._send_json({"status": "already_running"})
                return
            _state.update(
                {
                    "running": True,
                    "done": False,
                    "error": None,
                    "bytes_done": 0,
                    "bytes_total": 0,
                    "downloaded_path": None,
                }
            )

        threading.Thread(target=_run_download, args=(asset, config), daemon=True).start()
        ctx._send_json({"status": "started"})

    # ── POST /api/update/apply ────────────────────────────────────────────────
    @router.post("/api/update/apply")
    def post_update_apply(ctx) -> None:
        import rom_manager.web.state as _state_mod

        with _lock:
            downloaded = _state.get("downloaded_path")
        if not downloaded:
            ctx._send_json({"status": "error", "error": "No hay una actualización descargada"})
            return

        launch_installer(Path(downloaded))
        ctx._send_json({"status": "launched"})

        threading.Thread(target=_state_mod._httpd_instance.shutdown, daemon=True).start()


# ── Background worker ──────────────────────────────────────────────────────────


def _run_download(asset: dict[str, Any], config: AppConfig) -> None:
    def _on_progress(done: int, total: int) -> None:
        with _lock:
            _state.update({"bytes_done": done, "bytes_total": total})

    try:
        dest_dir = config.data_dir / "updates"
        path = download_update(asset["url"], dest_dir, asset["name"], on_progress=_on_progress)
        with _lock:
            _state.update({"running": False, "done": True, "downloaded_path": str(path)})
    except Exception as exc:  # noqa: BLE001 — network/disk errors all surface the same way to the UI
        with _lock:
            _state.update({"running": False, "done": True, "error": str(exc)})
