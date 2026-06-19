from __future__ import annotations

import io
import json
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.server import _readable_error, make_handler

# ---------------------------------------------------------------------------
# Minimal fake HTTP infrastructure — no real socket needed.
# ---------------------------------------------------------------------------


class FakeSocket:
    def makefile(self, mode: str) -> io.BytesIO:
        return io.BytesIO(b"")


def _make_request(method: str, path: str, repository: LibraryRepository):
    """Send a simulated GET request and return (status_code, content_type, body_bytes)."""
    handler_class = make_handler(repository, load_config(Path(__file__).parent.parent))

    captured: dict = {}

    class TestHandler(handler_class):  # type: ignore[misc]
        def __init__(self):
            self.command = method
            self.path = path
            self.headers = {}
            self.rfile = io.BytesIO(b"")
            self._buf = io.BytesIO()
            self.wfile = self._buf
            self.server = MagicMock()
            self.request = FakeSocket()

        def send_response(self, code: int, message: str = "") -> None:
            captured["code"] = code

        def send_header(self, key: str, value: str) -> None:
            if key == "Content-Type":
                captured["content_type"] = value

        def end_headers(self) -> None:
            pass

        def log_message(self, fmt, *args):
            pass

    h = TestHandler()
    h.do_GET()
    body = h._buf.getvalue()
    return captured.get("code", 0), captured.get("content_type", ""), body


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.fixture
def repo(tmp_path: Path) -> LibraryRepository:
    return LibraryRepository(tmp_path / "lib.sqlite")


def test_root_returns_html(repo: LibraryRepository) -> None:
    code, ct, body = _make_request("GET", "/", repo)
    assert code == 200
    assert "text/html" in ct
    assert b"Retro Vault" in body


def test_api_status_empty_library(repo: LibraryRepository) -> None:
    code, ct, body = _make_request("GET", "/api/status", repo)
    assert code == 200
    data = json.loads(body)
    assert data["total_games"] == 0
    assert data["matched_games"] == 0
    assert data["duplicate_groups"] == 0


def test_api_games_empty(repo: LibraryRepository) -> None:
    code, _, body = _make_request("GET", "/api/games", repo)
    assert code == 200
    data = json.loads(body)
    assert data["games"] == []


def test_api_plan_empty(repo: LibraryRepository) -> None:
    code, _, body = _make_request("GET", "/api/plan", repo)
    assert code == 200
    data = json.loads(body)
    assert data["total"] == 0
    assert data["pending"] == []


def test_api_duplicates_empty(repo: LibraryRepository) -> None:
    code, _, body = _make_request("GET", "/api/duplicates", repo)
    assert code == 200
    data = json.loads(body)
    assert data["groups"] == []
    assert data["wasted_bytes"] == 0


def test_api_report_json(repo: LibraryRepository) -> None:
    code, ct, body = _make_request("GET", "/api/report.json", repo)
    assert code == 200
    assert "application/json" in ct
    data = json.loads(body)
    assert "summary" in data
    assert "games" in data


def test_api_report_csv(repo: LibraryRepository) -> None:
    code, ct, body = _make_request("GET", "/api/report.csv", repo)
    assert code == 200
    assert "text/csv" in ct
    # Should at minimum have a header row
    lines = body.decode().strip().splitlines()
    assert lines[0].startswith("id,")


def test_unknown_route_returns_404(repo: LibraryRepository) -> None:
    code, _, _ = _make_request("GET", "/does-not-exist", repo)
    assert code == 404


def test_api_sync_log_empty(repo: LibraryRepository) -> None:
    code, ct, body = _make_request("GET", "/api/sync-log", repo)
    assert code == 200
    data = json.loads(body)
    assert data["entries"] == []


def test_api_config_returns_expected_keys(repo: LibraryRepository) -> None:
    code, ct, body = _make_request("GET", "/api/config", repo)
    assert code == 200
    data = json.loads(body)
    assert "library_root" in data
    assert "rclone_remote" in data
    assert "web_host" in data
    assert "web_port" in data


# ---------------------------------------------------------------------------
# PHASE4-1 — readable errors for unhandled handler exceptions
# ---------------------------------------------------------------------------


def test_readable_error_maps_known_exceptions() -> None:
    assert _readable_error(FileNotFoundError())[0] == 404
    assert _readable_error(PermissionError())[0] == 403
    assert _readable_error(IsADirectoryError())[0] == 400
    assert _readable_error(TimeoutError())[0] == 504
    assert _readable_error(sqlite3.OperationalError("locked"))[0] == 503
    assert _readable_error(sqlite3.IntegrityError("dup"))[0] == 409
    assert _readable_error(sqlite3.Error("x"))[0] == 500
    assert _readable_error(ValueError("x"))[0] == 400
    assert _readable_error(KeyError("x"))[0] == 400


def test_readable_error_generic_never_leaks_detail() -> None:
    code, message = _readable_error(RuntimeError("boom secret /home/user/x"))
    assert code == 500
    # The raw exception text (paths, secrets, internals) must not reach the user.
    assert "boom" not in message
    assert "secret" not in message


def test_unhandled_handler_exception_returns_readable_json(
    repo: LibraryRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom(*_a: object, **_k: object) -> object:
        raise sqlite3.OperationalError("database is locked: C:/secret/lib.sqlite")

    monkeypatch.setattr(repo, "get_summary", _boom)
    code, ct, body = _make_request("GET", "/api/status", repo)

    assert code == 503
    assert "application/json" in ct
    data = json.loads(body)
    assert "base de datos" in data["error"].lower()
    # Neither the raw detail nor a traceback is exposed to the client.
    decoded = body.decode()
    assert "secret" not in decoded
    assert "Traceback" not in decoded
