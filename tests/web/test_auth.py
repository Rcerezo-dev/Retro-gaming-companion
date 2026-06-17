from __future__ import annotations

import time

import pytest

from rom_manager.web import auth


@pytest.fixture(autouse=True)
def _reset_auth_state():
    auth.invalidate_all()
    with auth._auth_failures_lock:
        auth._auth_failures.clear()
    yield
    auth.invalidate_all()
    with auth._auth_failures_lock:
        auth._auth_failures.clear()


def test_hash_pin_deterministic():
    assert auth.hash_pin("1234", "salt") == auth.hash_pin("1234", "salt")
    assert auth.hash_pin("1234", "salt") != auth.hash_pin("1234", "other")


def test_session_create_and_validate():
    token = auth.create_session(ttl=60)
    assert auth.validate_session(token) is True
    auth.destroy_session(token)
    assert auth.validate_session(token) is False


def test_session_expires(monkeypatch):
    token = auth.create_session(ttl=0)
    original_monotonic = time.monotonic
    monkeypatch.setattr(time, "monotonic", lambda: original_monotonic() + 1)
    assert auth.validate_session(token) is False


def test_rate_limit_blocks_after_max_attempts():
    ip = "10.0.0.1"
    for _ in range(auth._AUTH_MAX_ATTEMPTS):
        auth.record_failure(ip)
    assert auth.check_rate_limit(ip) is True
    auth.clear_failures(ip)
    assert auth.check_rate_limit(ip) is False
