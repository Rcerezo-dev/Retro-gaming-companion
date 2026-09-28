"""JOBS-SQLITE-LOCK-1: _commit_with_retry() retries a locked-db commit
instead of aborting the whole scrape job (real crash 2026-09-28, SAGE-1
died mid-run while zip-route-apply held the write lock in parallel)."""

from __future__ import annotations

import sqlite3

import pytest

from rom_manager.web.handlers.scraper import _commit_with_retry


class _FakeConn:
    def __init__(self, fail_times: int, message: str = "database is locked") -> None:
        self.fail_times = fail_times
        self.message = message
        self.calls = 0
        self.committed = False

    def commit(self) -> None:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise sqlite3.OperationalError(self.message)
        self.committed = True


def test_retries_and_succeeds_after_transient_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("rom_manager.web.handlers.scraper.time.sleep", sleeps.append)

    conn = _FakeConn(fail_times=2)
    _commit_with_retry(conn, attempts=5, delay=2.0)

    assert conn.committed
    assert conn.calls == 3
    assert sleeps == [2.0, 2.0]


def test_reraises_after_exhausting_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("rom_manager.web.handlers.scraper.time.sleep", lambda _: None)

    conn = _FakeConn(fail_times=99)
    with pytest.raises(sqlite3.OperationalError, match="locked"):
        _commit_with_retry(conn, attempts=3, delay=0.0)

    assert conn.calls == 3
    assert not conn.committed


def test_non_lock_errors_are_not_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("rom_manager.web.handlers.scraper.time.sleep", sleeps.append)

    conn = _FakeConn(fail_times=99, message="disk I/O error")
    with pytest.raises(sqlite3.OperationalError, match="disk I/O error"):
        _commit_with_retry(conn, attempts=5, delay=1.0)

    assert conn.calls == 1  # no retry at all
    assert sleeps == []
