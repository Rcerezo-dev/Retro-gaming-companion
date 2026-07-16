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


def _config(**overrides) -> SimpleNamespace:
    cfg = SimpleNamespace(
        sync=SimpleNamespace(
            sync_sources=[],
            ra_config_dir="",
            ra_config_remote="",
            saves_remote="",
            states_remote="",
            conflict_policy="newest",
        ),
        library_root=None,
        rclone_binary=None,
        data_dir=None,
        save_extensions=(".srm",),
        state_extensions=(".state",),
        notify_desktop=False,
        backup=SimpleNamespace(pre_sync=False, saves_enabled=False, saves_keep_n=5),
    )
    for key, value in overrides.items():
        setattr(cfg, key, value)
    return cfg


def _run_sync(cfg) -> dict:
    _state._job_manager.finish("sync", None)
    ctx = _FakeCtx({"dry_run": True})
    _do_sync(ctx, ctx._post_data, cfg, repository=None, job_manager=_state._job_manager)
    for _ in range(100):
        if not _state._job_manager.get_status()["sync_running"]:
            break
        time.sleep(0.02)
    return _state._job_manager.get_status()["sync_result"]


def test_no_sources_configured_result_has_result_ts() -> None:
    res = _run_sync(_config())
    assert "error" in res
    assert res.get("result_ts")


def test_implicit_saves_remote_counts_as_source(tmp_path) -> None:
    """CLOUD-UX-3: con saves_remote y sin [[sync.sources]] el sync no debe
    cortar con 'sin destino' — llega al bloque D2 de remotes implícitos."""
    cfg = _config(library_root=str(tmp_path), data_dir=tmp_path)
    cfg.sync.saves_remote = "dropbox:RetroSync/saves"

    res = _run_sync(cfg)

    assert "error" not in res
    assert res["sources"], "el remote implícito debe aparecer como fuente"
    assert res["sources"][0]["remote"] == "dropbox:RetroSync/saves"
    assert res.get("result_ts")
