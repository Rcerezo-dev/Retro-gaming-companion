"""REV43-33: cable sync (filesystem mode, manual endpoint) must leave a trail
in save_sync_log — before this fix it only wrote to the .log text file,
violating "toda operación sobre archivos se registra en SQLite" (CLAUDE.md).
"""

from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace

import rom_manager.web.state as _state
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.handlers.sync_cable import _do_cable_sync


class _FakeCtx:
    def __init__(self, post_data: dict) -> None:
        self._post_data = post_data
        self.out = None

    def _send_json(self, obj) -> None:
        self.out = obj


def _config(tmp_path: Path):
    return SimpleNamespace(
        adb="adb",
        project_root=tmp_path,
        library_root=str(tmp_path / "pc"),
        anbernic_root=str(tmp_path / "ab"),
        save_extensions=(".sav",),
        backup=SimpleNamespace(saves_enabled=False),
        data_dir=tmp_path / "data",
        notify_desktop=False,
        sync=SimpleNamespace(auto_sync_direction="pc_to_anbernic"),
    )


def _wait_done() -> dict:
    for _ in range(50):
        status = _state._job_manager.get_status()
        if not status["cable_sync_running"]:
            return status["cable_sync_result"]
        time.sleep(0.05)
    raise AssertionError("cable_sync job never finished")


def test_manual_cable_sync_writes_save_sync_log(tmp_path: Path) -> None:
    pc = tmp_path / "pc"
    ab = tmp_path / "ab"
    (pc / "gba").mkdir(parents=True)
    ab.mkdir()
    mario = pc / "gba" / "mario.sav"
    mario.write_bytes(b"PCDATA")

    _state._job_manager.finish("cable_sync", None)
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    config = _config(tmp_path)

    ctx = _FakeCtx(
        {
            "pc_path": str(pc),
            "anbernic_path": str(ab),
            "what": ["saves"],
            "direction": "pc_to_anbernic",
            "dry_run": False,
            "safe_mode": False,
        }
    )
    _do_cable_sync(ctx, ctx._post_data, config, repo, _state._job_manager)
    result = _wait_done()

    assert result["copied"] == 1
    assert result["errors"] == 0
    assert (ab / "gba" / "mario.sav").read_bytes() == b"PCDATA"

    with repo.connect() as conn:
        rows = conn.execute(
            "SELECT local_path, remote_path, direction, result FROM save_sync_log"
        ).fetchall()
    assert len(rows) == 1
    row = rows[0]
    assert row["local_path"] == str(mario)
    assert row["remote_path"] == str(ab / "gba" / "mario.sav")
    assert row["direction"] == "upload"
    assert row["result"] == "ok"
