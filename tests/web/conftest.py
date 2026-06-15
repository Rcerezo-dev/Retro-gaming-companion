from __future__ import annotations

import io
import json
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


class WebClient:
    """Drives a handler created by ``make_handler`` without a real socket."""

    def __init__(self, repository: LibraryRepository, config) -> None:
        self._handler_class = make_handler(repository, config)

    def _request(self, method: str, path: str, json_body: dict | None = None):
        body = json.dumps(json_body if json_body is not None else {}).encode()
        captured: dict = {}
        handler_class = self._handler_class

        class H(handler_class):  # type: ignore[misc]
            def __init__(self):
                self.command = method
                self.path = path
                self.headers = {"Content-Length": str(len(body)), "Content-Type": "application/json"}
                self.rfile = io.BytesIO(body)
                self._buf = io.BytesIO()
                self.wfile = self._buf
                self.server = MagicMock()
                self.request = FakeSocket()
                self.client_address = ("127.0.0.1", 0)

            def send_response(self, code, message=""):
                captured["code"] = code

            def send_header(self, key, value):
                if key == "Content-Type":
                    captured["content_type"] = value

            def end_headers(self):
                pass

            def log_message(self, fmt, *args):
                pass

        h = H()
        (h.do_GET if method == "GET" else h.do_POST)()
        return captured.get("code", 0), captured.get("content_type", ""), h._buf.getvalue()

    def get(self, path: str):
        return self._request("GET", path)

    def post(self, path: str, json_body: dict | None = None):
        return self._request("POST", path, json_body)

    def get_json(self, path: str):
        _, _, body = self.get(path)
        return json.loads(body)

    def post_json(self, path: str, json_body: dict | None = None):
        _, _, body = self.post(path, json_body)
        return json.loads(body)


@pytest.fixture
def repo(tmp_path: Path) -> LibraryRepository:
    return LibraryRepository(tmp_path / "lib.sqlite")


@pytest.fixture
def config(tmp_path: Path):
    cfg = load_config(tmp_path)
    cfg.library_root = tmp_path / "library"
    return cfg


@pytest.fixture
def client(repo: LibraryRepository, config) -> WebClient:
    return WebClient(repo, config)


@pytest.fixture(autouse=True)
def _reset_job_manager():
    """``state._job_manager`` is a process-wide singleton — reset between tests."""
    jm = _state._job_manager
    with jm._lock:
        for name in jm._running:
            jm._running[name] = False
        jm._results.clear()
        jm._progress.clear()
        for event in jm._cancel.values():
            event.clear()
    yield
