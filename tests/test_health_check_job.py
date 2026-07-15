"""Regression test for REV43-14: the /api/health-check job used to always
fail with an ImportError (_write_health_schedule imported from the wrong
module), silently swallowed by the job's broad except Exception.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.handlers.esde.maintenance import register_maintenance
from rom_manager.web.jobs.manager import JobManager
from rom_manager.web.router import Router


class _FakeCtx:
    def __init__(self) -> None:
        self.sent: dict | None = None

    def _send_json(self, data: dict) -> None:
        self.sent = data


@pytest.fixture
def repo(tmp_path: Path) -> LibraryRepository:
    return LibraryRepository(tmp_path / "library.db")


def test_health_check_job_writes_schedule_instead_of_import_error(tmp_path, repo):
    config = load_config(project_root=tmp_path)
    job_manager = JobManager()
    router = Router()
    register_maintenance(router, config=config, repository=repo, job_manager=job_manager)

    router.dispatch("POST", "/api/health-check", _FakeCtx())

    for _ in range(50):
        if not job_manager.get_status()["health_check_running"]:
            break
        time.sleep(0.1)
    else:
        pytest.fail("health_check job never finished")

    result = job_manager.get_status()["health_check_result"]
    assert result is not None
    assert "error" not in result, f"health check failed: {result.get('error')}"
    assert result["ok"] == 0  # empty repo, but the job actually ran to completion

    schedule_path = config.data_dir / "health_schedule.json"
    assert schedule_path.exists(), "_write_health_schedule was never called"
