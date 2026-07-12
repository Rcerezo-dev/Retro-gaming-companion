"""Tests del Sync Doctor (AUD-1) — analyze_saves es pura, sin dispositivo."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from rom_manager.sync.adb_transport import AdbFileInfo
from rom_manager.sync.save_syncer import LocalSave
from rom_manager.web.builders.sync_doctor import analyze_saves

NOW = 1_750_000_000.0
ROOT = "/storage/emulated/0/RetroArch"


def _local(rel: str, mtime: float) -> LocalSave:
    return LocalSave(
        relative=rel,
        absolute=Path("C:/saves") / rel,
        mtime=datetime.fromtimestamp(mtime, tz=UTC),
        size=100,
    )


def _remote(rel: str, mtime: float) -> AdbFileInfo:
    return AdbFileInfo(android_path=f"{ROOT}/{rel}", size=100, mtime=mtime)


def _analyze(**kw):
    defaults = dict(
        pc_epoch=NOW,
        device_epoch=int(NOW),
        threshold_s=120,
        local_saves=[],
        remote_files=[],
        android_root=ROOT,
    )
    defaults.update(kw)
    return analyze_saves(**defaults)


def test_clock_ok_within_threshold():
    r = _analyze(device_epoch=int(NOW) + 60)
    assert r["clock"]["exceeded"] is False
    assert r["clock"]["skew_seconds"] == 60.0


def test_clock_exceeded_device_behind():
    r = _analyze(device_epoch=int(NOW) - 600)
    assert r["clock"]["exceeded"] is True
    assert r["clock"]["skew_seconds"] == -600.0


def test_future_mtime_detected_both_sides():
    r = _analyze(
        local_saves=[_local("gba/a.srm", NOW + 999), _local("gba/b.srm", NOW - 10)],
        remote_files=[_remote("saves/c.srm", NOW + 500), _remote("saves/d.srm", NOW)],
    )
    assert [f["path"] for f in r["future_local"]] == ["gba/a.srm"]
    assert [f["path"] for f in r["future_remote"]] == ["saves/c.srm"]
    assert r["future_local_total"] == 1
    assert r["future_remote_total"] == 1


def test_only_one_side_join_strips_android_root():
    r = _analyze(
        local_saves=[_local("saves/both.srm", NOW), _local("saves/pc_only.srm", NOW)],
        remote_files=[_remote("saves/both.srm", NOW), _remote("saves/dev_only.srm", NOW)],
    )
    assert r["only_local"] == ["saves/pc_only.srm"]
    assert r["only_remote"] == ["saves/dev_only.srm"]
    assert r["local_total"] == 2
    assert r["remote_total"] == 2


def test_identical_sides_report_clean():
    saves = [("saves/x.srm", NOW - 100), ("saves/y.sav", NOW - 200)]
    r = _analyze(
        local_saves=[_local(rel, mt) for rel, mt in saves],
        remote_files=[_remote(rel, mt) for rel, mt in saves],
    )
    assert r["only_local"] == []
    assert r["only_remote"] == []
    assert r["future_local"] == []
    assert r["future_remote"] == []
