"""REV43-8: el job "sync" (cloud) debe llevar result_ts en su resultado final
— sin él, _pollSync (flow_wizard.js) nunca detecta que terminó y el paso
"Sync" del wizard hace polling para siempre."""

from __future__ import annotations

import time
from types import SimpleNamespace

import rom_manager.web.state as _state
from rom_manager.web.handlers.sync_cloud import _do_sync


class _FakeCtx:
    def __init__(self, post_data: dict) -> None:
        self._post_data = post_data
        self.out: dict | None = None

    def _send_json(self, obj: dict) -> None:
        self.out = obj


def _config() -> SimpleNamespace:
    return SimpleNamespace(
        sync=SimpleNamespace(sync_sources=[], ra_config_dir="", ra_config_remote=""),
    )


def test_no_sources_configured_result_has_result_ts() -> None:
    _state._job_manager.finish("sync", None)
    ctx = _FakeCtx({"dry_run": True})

    _do_sync(ctx, ctx._post_data, _config(), repository=None, job_manager=_state._job_manager)

    for _ in range(100):
        if not _state._job_manager.get_status()["sync_running"]:
            break
        time.sleep(0.02)

    res = _state._job_manager.get_status()["sync_result"]
    assert "error" in res
    assert res.get("result_ts")
