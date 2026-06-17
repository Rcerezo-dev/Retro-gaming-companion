from __future__ import annotations

import pytest

from rom_manager.web.router import Router


def test_exact_match_dispatch():
    router = Router()
    called = []

    @router.get("/api/config")
    def handler(ctx):
        called.append(ctx)

    assert router.dispatch("GET", "/api/config", "ctx") is True
    assert called == ["ctx"]


def test_no_match_returns_false():
    router = Router()
    assert router.dispatch("GET", "/api/does-not-exist", "ctx") is False


def test_prefix_match():
    router = Router()
    called = []

    @router.get("/api/games", prefix=True)
    def handler(ctx):
        called.append(ctx)

    assert router.dispatch("GET", "/api/games/123", "ctx") is True
    assert called == ["ctx"]


def test_wrong_method_no_match():
    router = Router()

    @router.get("/api/config")
    def handler(ctx): ...

    assert router.dispatch("POST", "/api/config", "ctx") is False


def test_routes_introspection():
    router = Router()

    @router.get("/api/a")
    def h1(ctx): ...

    @router.post("/api/b", prefix=True)
    def h2(ctx): ...

    assert router.routes() == [("GET", "/api/a"), ("POST", "/api/b*")]


def test_handler_exception_propagates():
    router = Router()

    @router.get("/api/boom")
    def handler(ctx):
        raise ValueError("boom")

    with pytest.raises(ValueError):
        router.dispatch("GET", "/api/boom", "ctx")
