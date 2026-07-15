"""Regression test for REV43-15: with a PIN configured, /s and
/api/rclone-export-config used to get redirected to /login (302) before
reaching their own loopback/token check, breaking curl-based Termux setup.
"""

from __future__ import annotations

import io
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import rom_manager.web.state as _state
from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.server import make_handler


class FakeSocket:
    def makefile(self, mode: str) -> io.BytesIO:
        return io.BytesIO(b"")


def _get(handler_class, path: str, *, client_ip: str):
    """Drive a single GET request from *client_ip* without a real socket."""
    captured: dict = {"headers": {}}

    class H(handler_class):  # type: ignore[misc]
        def __init__(self):
            self.command = "GET"
            self.path = path
            self.headers = {"Content-Length": "0"}
            self.rfile = io.BytesIO(b"")
            self._buf = io.BytesIO()
            self.wfile = self._buf
            self.server = MagicMock()
            self.request = FakeSocket()
            self.client_address = (client_ip, 0)

        def send_response(self, code, message=""):
            captured["code"] = code

        def send_header(self, key, value):
            captured["headers"][key] = value

        def end_headers(self):
            pass

        def log_message(self, fmt, *args):
            pass

    h = H()
    h.do_GET()
    return captured["code"], captured["headers"], h._buf.getvalue()


@pytest.fixture
def repo(tmp_path: Path) -> LibraryRepository:
    return LibraryRepository(tmp_path / "lib.sqlite")


@pytest.fixture
def config_with_pin(tmp_path: Path):
    cfg = load_config(tmp_path)
    cfg.library_root = tmp_path / "library"
    cfg.credentials.web_pin_hash = "deadbeef"
    cfg.credentials.web_pin_salt = "salt"
    return cfg


@pytest.fixture(autouse=True)
def _reset_setup_token():
    _state._anbernic_setup_token = {"value": None, "expires": 0.0}
    yield
    _state._anbernic_setup_token = {"value": None, "expires": 0.0}


def test_bootstrap_script_not_redirected_to_login_with_pin(repo, config_with_pin):
    """A Termux curl (no session cookie, LAN IP) must reach /s's own token
    check (403 without a valid ?t=) instead of a login redirect it can't use."""
    handler_class = make_handler(repo, config_with_pin)
    code, headers, _body = _get(handler_class, "/s", client_ip="192.168.1.50")
    assert code == 403
    assert "Location" not in headers


def test_rclone_export_config_not_redirected_to_login_with_pin(repo, config_with_pin):
    handler_class = make_handler(repo, config_with_pin)
    code, headers, _body = _get(
        handler_class, "/api/rclone-export-config", client_ip="192.168.1.50"
    )
    assert code == 403
    assert "Location" not in headers


def test_bootstrap_script_served_with_valid_setup_token_and_pin(repo, config_with_pin):
    token = "test-token-123"
    _state._anbernic_setup_token = {"value": token, "expires": time.time() + 600}
    handler_class = make_handler(repo, config_with_pin)
    code, headers, body = _get(handler_class, f"/s?t={token}", client_ip="192.168.1.50")
    assert code == 200
    assert "Location" not in headers
    assert b"curl" in body or b"rclone" in body or len(body) > 0


def test_other_routes_still_require_pin_session(repo, config_with_pin):
    """Sanity check: the exemption is scoped to /s and the export-config route,
    not a blanket bypass of the PIN gate for LAN clients."""
    handler_class = make_handler(repo, config_with_pin)
    code, headers, _body = _get(handler_class, "/api/config", client_ip="192.168.1.50")
    assert code == 302
    assert headers.get("Location") == "/login"
