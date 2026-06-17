from __future__ import annotations

from datetime import UTC, datetime, timedelta

from rom_manager.sync.conflict_resolver import decide


def _dt(offset_seconds: float = 0) -> datetime:
    base = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    return base + timedelta(seconds=offset_seconds)


# ---------------------------------------------------------------------------
# Basic direction decisions
# ---------------------------------------------------------------------------

def test_upload_when_local_newer() -> None:
    d = decide("game.sav", local_mtime=_dt(100), remote_mtime=_dt(0), last_sync_at=None)
    assert d.action == "upload"


def test_download_when_remote_newer() -> None:
    d = decide("game.sav", local_mtime=_dt(0), remote_mtime=_dt(100), last_sync_at=None)
    assert d.action == "download"


def test_up_to_date_within_tolerance() -> None:
    d = decide("game.sav", local_mtime=_dt(0), remote_mtime=_dt(1), last_sync_at=None)
    assert d.action == "up_to_date"


def test_up_to_date_exactly_equal() -> None:
    t = _dt(0)
    d = decide("game.sav", local_mtime=t, remote_mtime=t, last_sync_at=None)
    assert d.action == "up_to_date"


# ---------------------------------------------------------------------------
# Missing sides
# ---------------------------------------------------------------------------

def test_upload_when_remote_missing() -> None:
    d = decide("game.sav", local_mtime=_dt(0), remote_mtime=None, last_sync_at=None)
    assert d.action == "upload"


def test_download_when_local_missing() -> None:
    d = decide("game.sav", local_mtime=None, remote_mtime=_dt(0), last_sync_at=None)
    assert d.action == "download"


def test_up_to_date_when_both_missing() -> None:
    d = decide("game.sav", local_mtime=None, remote_mtime=None, last_sync_at=None)
    assert d.action == "up_to_date"


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_conflict_when_both_changed_after_last_sync() -> None:
    last_sync = _dt(0)
    d = decide(
        "game.sav",
        local_mtime=_dt(50),
        remote_mtime=_dt(40),
        last_sync_at=last_sync,
    )
    assert d.action == "conflict"


def test_no_conflict_when_only_local_changed() -> None:
    last_sync = _dt(0)
    # Remote mtime equals last_sync (remote not changed)
    d = decide(
        "game.sav",
        local_mtime=_dt(50),
        remote_mtime=_dt(0),
        last_sync_at=last_sync,
    )
    assert d.action == "upload"


def test_no_conflict_when_only_remote_changed() -> None:
    last_sync = _dt(0)
    d = decide(
        "game.sav",
        local_mtime=_dt(0),
        remote_mtime=_dt(50),
        last_sync_at=last_sync,
    )
    assert d.action == "download"


def test_decision_carries_relative_path() -> None:
    d = decide("subdir/game.sav", local_mtime=_dt(10), remote_mtime=_dt(0), last_sync_at=None)
    assert d.relative == "subdir/game.sav"


def test_tolerance_boundary_just_outside() -> None:
    # diff = 3s > default tolerance (2s) → upload
    d = decide("game.sav", local_mtime=_dt(3), remote_mtime=_dt(0), last_sync_at=None)
    assert d.action == "upload"
