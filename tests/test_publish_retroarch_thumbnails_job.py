"""Integration test for the publish-retroarch-thumbnails background job wiring.

The thumbnail-publishing logic itself is covered by
``test_retroarch_thumbnails.py`` (pure function). This only exercises the web
layer: POST starts a job, GET status reports progress while running and the
result once finished — same job pattern as convert_chd/download_dats.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock

from rom_manager.web.handlers.esde import reports as _reports
from rom_manager.web.jobs.manager import JobManager
from rom_manager.web.router import Router


class _Ctx:
    def __init__(self, post_data: dict | None = None) -> None:
        self._post_data = post_data or {}
        self.status: int | None = None
        self.body: bytes | None = None

    def _send(self, status: int, content_type: str, body: bytes) -> None:
        self.status = status
        self.body = body

    def _send_json(self, data: object) -> None:
        self._send(200, "application/json; charset=utf-8", json.dumps(data).encode())

    @property
    def json(self) -> dict:
        return json.loads(self.body)


def _make_config(tmp_path: Path):
    cfg = MagicMock()
    cfg.library_root = tmp_path / "library"
    cfg.retroarch_path = str(tmp_path / "RetroArch" / "retroarch.exe")
    return cfg


def test_post_starts_job_and_status_reports_result(tmp_path, monkeypatch):
    calls = []

    def _fake_publish(library_root, repository, retroarch_root, *, on_progress=None):
        calls.append((library_root, retroarch_root))
        if on_progress:
            on_progress(1, 2)
            on_progress(2, 2)
        return {
            "published": 2,
            "converted": 1,
            "skipped_no_title": 0,
            "missing_source": 0,
            "errors": [],
        }

    monkeypatch.setattr(
        "rom_manager.utils.retroarch_thumbnails.publish_retroarch_thumbnails", _fake_publish
    )

    router = Router()
    job_manager = JobManager()
    _reports.register_reports(
        router,
        config=_make_config(tmp_path),
        repository=MagicMock(),
        get_repo_fn=lambda path: MagicMock(),
        job_manager=job_manager,
    )

    start_ctx = _Ctx()
    router.dispatch("POST", "/api/publish-retroarch-thumbnails", start_ctx)
    assert start_ctx.json["status"] == "started"

    # Job runs in a background thread — wait briefly for it to finish.
    for _ in range(50):
        status_ctx = _Ctx()
        router.dispatch("GET", "/api/publish-retroarch-thumbnails-status", status_ctx)
        if not status_ctx.json["running"]:
            break
        time.sleep(0.02)

    assert status_ctx.json["running"] is False
    assert status_ctx.json["result"]["published"] == 2
    assert status_ctx.json["result"]["converted"] == 1
    assert len(calls) == 1


def test_post_without_retroarch_path_configured_errors(tmp_path):
    cfg = MagicMock()
    cfg.library_root = tmp_path / "library"
    cfg.retroarch_path = ""

    router = Router()
    job_manager = JobManager()
    _reports.register_reports(
        router,
        config=cfg,
        repository=MagicMock(),
        get_repo_fn=lambda path: MagicMock(),
        job_manager=job_manager,
    )

    ctx = _Ctx()
    router.dispatch("POST", "/api/publish-retroarch-thumbnails", ctx)
    assert "error" in ctx.json
