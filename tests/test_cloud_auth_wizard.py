"""CLOUD-UX-4: el wizard OAuth retiene el provider iniciado, rechaza flujos
concurrentes y el cancel es seguro sin subprocess vivo."""

from __future__ import annotations

import threading
from types import SimpleNamespace

import rom_manager.web.handlers.cloud_auth as cloud_auth


class _FakeRouter:
    def __init__(self) -> None:
        self.gets: dict = {}
        self.posts: dict = {}

    def get(self, path):
        return lambda fn: self.gets.setdefault(path, fn)

    def post(self, path):
        return lambda fn: self.posts.setdefault(path, fn)


class _FakeCtx:
    def __init__(self, post_data: dict | None = None) -> None:
        self._post_data = post_data or {}
        self.out: dict | None = None

    def _send_json(self, obj: dict) -> None:
        self.out = obj


def _router() -> _FakeRouter:
    router = _FakeRouter()
    cloud_auth.register(router, config=SimpleNamespace(rclone_binary="rclone-inexistente"))
    return router


def test_poll_returns_provider_and_remote_name() -> None:
    router = _router()
    cloud_auth._auth_provider = "gdrive"
    cloud_auth._auth_remote_name = "gdrive"
    cloud_auth._auth_done = True
    cloud_auth._auth_token = "{}"
    cloud_auth._auth_error = None

    ctx = _FakeCtx()
    router.gets["/api/cloud-auth/poll"](ctx)

    assert ctx.out["provider"] == "gdrive"
    assert ctx.out["remote_name"] == "gdrive"


def test_start_rejects_concurrent_flow() -> None:
    router = _router()
    ev = threading.Event()
    alive = threading.Thread(target=ev.wait, daemon=True)
    alive.start()
    cloud_auth._auth_thread = alive
    try:
        ctx = _FakeCtx({"provider": "dropbox"})
        router.posts["/api/cloud-auth/start"](ctx)
        assert "error" in ctx.out
        assert "en curso" in ctx.out["error"]
    finally:
        ev.set()
        cloud_auth._auth_thread = None


def test_cancel_without_running_proc_is_safe() -> None:
    router = _router()
    cloud_auth._auth_proc = None
    cloud_auth._auth_done = False
    cloud_auth._auth_error = None

    ctx = _FakeCtx()
    router.posts["/api/cloud-auth/cancel"](ctx)

    assert ctx.out == {"ok": True}
    assert cloud_auth._auth_done is True
    assert cloud_auth._auth_error == "Autorización cancelada"
