"""TEST-1b — SD-card cable-sync daemon: the file-moving logic.

`_run_sd_auto_sync` is the riskiest code in the sync layer (it copies/overwrites
save files between the PC library and the Anbernic SD card). These tests drive it
with synthetic directory trees and assert the directional copy logic and the
"newest wins" resolution, so a regression that loses or overwrites the wrong save
is caught.

Note: the SD daemon has no mid-run stop_event today (cancellation is tracked under
ARC-JM-3). When that lands, add a cancellation test here.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

import rom_manager.web.state as _state
from rom_manager.config import load_config
from rom_manager.web.cable_sync_daemon import _run_sd_auto_sync

_BASE = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


def _set_mtime(path: Path, seconds_offset: float) -> None:
    ts = (_BASE.timestamp()) + seconds_offset
    os.utime(path, (ts, ts))


def _make_config(tmp_path: Path, pc_root: Path, ab_root: Path, direction: str):
    cfg = load_config()
    cfg.project_root = tmp_path
    cfg.library_root = pc_root
    cfg.anbernic_root = str(ab_root)
    cfg.auto_sync_direction = direction
    cfg.save_extensions = (".sav",)
    return cfg


def _run(cfg) -> dict:
    _state._job_manager.clear_result("cable_sync")
    _run_sd_auto_sync(cfg, lambda: None)
    return _state._job_manager.get_status()["cable_sync_result"]


def _write(root: Path, *parts: str, content: bytes) -> Path:
    p = root.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return p


def test_pc_to_anbernic_copies_saves(tmp_path: Path) -> None:
    pc = tmp_path / "pc"
    ab = tmp_path / "ab"
    ab.mkdir()
    _write(pc, "gba", "mario.sav", content=b"PCDATA")

    res = _run(_make_config(tmp_path, pc, ab, "pc_to_anbernic"))

    assert res["copied"] == 1
    assert res["errors"] == 0
    assert (ab / "gba" / "mario.sav").read_bytes() == b"PCDATA"


def test_anbernic_to_pc_copies_saves(tmp_path: Path) -> None:
    pc = tmp_path / "pc"
    ab = tmp_path / "ab"
    pc.mkdir()
    _write(ab, "gba", "zelda.sav", content=b"ABDATA")

    res = _run(_make_config(tmp_path, pc, ab, "anbernic_to_pc"))

    assert res["copied"] == 1
    assert (pc / "gba" / "zelda.sav").read_bytes() == b"ABDATA"


def test_only_save_extensions_are_copied(tmp_path: Path) -> None:
    pc = tmp_path / "pc"
    ab = tmp_path / "ab"
    ab.mkdir()
    _write(pc, "gba", "mario.sav", content=b"SAVE")
    _write(pc, "notes.txt", content=b"not a save")

    res = _run(_make_config(tmp_path, pc, ab, "pc_to_anbernic"))

    assert res["copied"] == 1
    assert (ab / "gba" / "mario.sav").exists()
    assert not (ab / "notes.txt").exists()


def test_newest_propagates_newer_side(tmp_path: Path) -> None:
    pc = tmp_path / "pc"
    ab = tmp_path / "ab"
    pc_file = _write(pc, "gba", "mario.sav", content=b"OLD")
    ab_file = _write(ab, "gba", "mario.sav", content=b"NEW")
    _set_mtime(pc_file, 0)  # PC older
    _set_mtime(ab_file, 100)  # Anbernic newer

    res = _run(_make_config(tmp_path, pc, ab, "newest"))

    # Newer side (Anbernic) wins; PC older copy is skipped, not overwritten onto AB.
    assert res["copied"] >= 1
    assert pc_file.read_bytes() == b"NEW"
    assert ab_file.read_bytes() == b"NEW"


def test_newest_skips_when_pc_is_newer(tmp_path: Path) -> None:
    pc = tmp_path / "pc"
    ab = tmp_path / "ab"
    pc_file = _write(pc, "gba", "mario.sav", content=b"NEWER_PC")
    ab_file = _write(ab, "gba", "mario.sav", content=b"OLDER_AB")
    _set_mtime(pc_file, 100)  # PC newer
    _set_mtime(ab_file, 0)  # Anbernic older

    res = _run(_make_config(tmp_path, pc, ab, "newest"))

    # PC wins → its content propagates to Anbernic; AB never overwrites PC.
    assert pc_file.read_bytes() == b"NEWER_PC"
    assert ab_file.read_bytes() == b"NEWER_PC"
    assert res["errors"] == 0
