"""PHASE6-3a: background GitHub release check and version comparison."""

from __future__ import annotations

import logging
import threading
from typing import Any

_logger = logging.getLogger(__name__)

_GITHUB_API = "https://api.github.com/repos/Rcerezo-dev/Retro-gaming-companion/releases/latest"
_TIMEOUT = 10  # seconds

_lock = threading.Lock()
_result: dict[str, Any] = {}  # populated by _do_check(); read by get_result()
_check_started = False


# ── Public API ────────────────────────────────────────────────────────────────


def get_result() -> dict[str, Any]:
    """Return the cached check result (empty dict if check hasn't finished yet)."""
    with _lock:
        return dict(_result)


def start_background_check(current_version: str) -> None:
    """Fire a one-shot daemon thread to check GitHub for a newer release.

    Safe to call multiple times — only the first call launches the thread.
    """
    global _check_started
    with _lock:
        if _check_started:
            return
        _check_started = True
    threading.Thread(
        target=_do_check, args=(current_version,), daemon=True, name="update-checker"
    ).start()


# ── Internals ─────────────────────────────────────────────────────────────────


def _parse_version(tag: str) -> tuple[int, ...]:
    """Return a comparable tuple from a semver string like 'v1.2.3' or '1.2.3'."""
    clean = tag.lstrip("vV").strip()
    try:
        return tuple(int(x) for x in clean.split("."))
    except ValueError:
        return (0,)


def _do_check(current_version: str) -> None:
    import json
    import urllib.error
    import urllib.request

    try:
        req = urllib.request.Request(
            _GITHUB_API,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "RetroVault"},
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())

        tag = data.get("tag_name", "")
        url = data.get("html_url", "")
        name = data.get("name", tag)

        if not tag:
            raise ValueError("Respuesta de GitHub sin tag_name")

        latest_tuple = _parse_version(tag)
        current_tuple = _parse_version(current_version)
        update_available = latest_tuple > current_tuple

        with _lock:
            _result.update(
                {
                    "latest": tag.lstrip("vV"),
                    "latest_tag": tag,
                    "release_name": name,
                    "release_url": url,
                    "update_available": update_available,
                    "checked": True,
                    "error": None,
                }
            )
        if update_available:
            _logger.info("Nueva versión disponible: %s (actual: %s)", tag, current_version)

    except urllib.error.URLError as exc:
        _logger.debug("Update check falló (red): %s", exc)
        with _lock:
            _result.update({"checked": True, "update_available": False, "error": str(exc.reason)})
    except Exception as exc:
        _logger.debug("Update check falló: %s", exc)
        with _lock:
            _result.update({"checked": True, "update_available": False, "error": str(exc)})
