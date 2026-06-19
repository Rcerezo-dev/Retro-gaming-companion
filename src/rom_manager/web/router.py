from __future__ import annotations

import logging
from collections.abc import Callable

_log = logging.getLogger(__name__)


class Router:
    """Simple URL router for the HTTP server.

    Supports exact-match routes and prefix-match routes.
    Used in Phase 1 migration to replace the if/elif ladder in server.py.

    Usage (future)::

        router = Router()

        @router.get('/api/config')
        def handle_config(ctx):
            ...

        # In do_GET / do_POST:
        if not router.dispatch('GET', self.path, self):
            self._send_404()
    """

    def __init__(self) -> None:
        self._exact: dict[tuple[str, str], Callable] = {}
        self._prefix: list[tuple[str, str, Callable]] = []

    # ── Decorators ────────────────────────────────────────────────────────────

    def get(self, path: str, *, prefix: bool = False) -> Callable:
        """Register a GET handler.

        Args:
            path: Exact path (e.g. ``'/api/config'``) or prefix
                  (e.g. ``'/api/games'``) when *prefix=True*.
            prefix: If True, matches any path that starts with *path*.
        """

        def decorator(fn: Callable) -> Callable:
            self._register("GET", path, fn, prefix)
            return fn

        return decorator

    def post(self, path: str, *, prefix: bool = False) -> Callable:
        """Register a POST handler."""

        def decorator(fn: Callable) -> Callable:
            self._register("POST", path, fn, prefix)
            return fn

        return decorator

    # ── Internal ──────────────────────────────────────────────────────────────

    def _register(self, method: str, path: str, fn: Callable, prefix: bool) -> None:
        if prefix:
            self._prefix.append((method, path, fn))
        else:
            self._exact[(method, path)] = fn

    def dispatch(self, method: str, path: str, ctx: object) -> bool:
        """Try to dispatch *method* + *path* to a registered handler.

        Args:
            method: HTTP method (``'GET'`` or ``'POST'``).
            path: Request path (without query string).
            ctx: Handler context — the ``BaseHTTPRequestHandler`` instance.

        Returns:
            ``True`` if a handler was found and called, ``False`` otherwise.

        Exceptions raised by a handler propagate to the caller (``do_GET`` /
        ``do_POST`` in ``server.py``), which logs the traceback and returns a
        readable error response — a single, central error point.
        """
        # 1. Exact match
        handler = self._exact.get((method, path))
        if handler is not None:
            handler(ctx)
            return True

        # 2. Prefix match (first registered wins)
        for m, prefix, handler in self._prefix:
            if m == method and path.startswith(prefix):
                handler(ctx)
                return True

        if path.startswith("/api/"):
            _log.debug("Ruta no registrada: %s %s", method, path)

        return False

    # ── Introspection ─────────────────────────────────────────────────────────

    def routes(self) -> list[tuple[str, str]]:
        """Return all registered (method, path) pairs (for debugging)."""
        result = [(m, p) for (m, p) in self._exact]
        result += [(m, p + "*") for (m, p, _) in self._prefix]
        return sorted(result)
