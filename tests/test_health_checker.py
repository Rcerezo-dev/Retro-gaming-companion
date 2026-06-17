"""Tests for health_checker.py — library integrity verification."""

from __future__ import annotations

import hashlib
import os
import threading
from pathlib import Path

import pytest

from rom_manager.database.repository import LibraryRepository
from rom_manager.utils.health_checker import check_library_health


def _insert_game(repo: LibraryRepository, path: Path, sha1: str) -> None:
    now = "2026-01-01T00:00:00"
    with repo.connect() as conn:
        conn.execute(
            """INSERT INTO games
               (source_path, original_filename, sha1, md5, crc32, extension,
                size_bytes, file_type, platform, created_at, updated_at)
               VALUES (?, ?, ?, '', '', ?, 0, 'rom', 'Game Boy Advance', ?, ?)""",
            (str(path.resolve()), path.name, sha1, path.suffix.lower(), now, now),
        )
        conn.commit()


@pytest.fixture
def repo(tmp_path: Path) -> LibraryRepository:
    return LibraryRepository(tmp_path / "lib.sqlite")


class TestCheckLibraryHealth:
    def test_ok_file(self, tmp_path: Path, repo: LibraryRepository) -> None:
        data = b"healthy rom content"
        p = tmp_path / "game.gba"
        p.write_bytes(data)
        sha1 = hashlib.sha1(data).hexdigest().upper()
        _insert_game(repo, p, sha1)

        summary = check_library_health(repo)
        assert summary.ok == 1
        assert summary.corrupted == 0
        assert summary.missing == 0
        assert summary.results == []

    def test_missing_file(self, tmp_path: Path, repo: LibraryRepository) -> None:
        p = tmp_path / "gone.nes"
        _insert_game(repo, p, "A" * 40)  # file never written

        summary = check_library_health(repo)
        assert summary.missing == 1
        assert summary.ok == 0
        assert len(summary.results) == 1
        assert summary.results[0].status == "missing"
        assert summary.results[0].computed_sha1 == ""

    def test_corrupted_file(self, tmp_path: Path, repo: LibraryRepository) -> None:
        p = tmp_path / "corrupt.sfc"
        p.write_bytes(b"bad data")
        _insert_game(repo, p, "A" * 40)  # wrong SHA1 stored

        summary = check_library_health(repo)
        assert summary.corrupted == 1
        assert len(summary.results) == 1
        assert summary.results[0].status == "corrupted"
        assert len(summary.results[0].computed_sha1) == 40

    def test_mixed_results(self, tmp_path: Path, repo: LibraryRepository) -> None:
        data = b"good"
        good = tmp_path / "good.gba"
        good.write_bytes(data)
        sha1_good = hashlib.sha1(data).hexdigest().upper()
        _insert_game(repo, good, sha1_good)

        corrupt = tmp_path / "corrupt.gba"
        corrupt.write_bytes(b"wrong")
        _insert_game(repo, corrupt, "B" * 40)

        missing = tmp_path / "missing.gba"  # never written
        _insert_game(repo, missing, "C" * 40)

        summary = check_library_health(repo)
        assert summary.ok == 1
        assert summary.corrupted >= 1
        assert summary.missing == 1

    def test_empty_sha1_skipped(self, tmp_path: Path, repo: LibraryRepository) -> None:
        """Games with empty SHA1 in DB should not be checked."""
        p = tmp_path / "unscanned.gba"
        p.write_bytes(b"data")
        with repo.connect() as conn:
            conn.execute(
                "INSERT INTO games (source_path, original_filename, sha1, md5, crc32, extension, size_bytes, file_type, platform, created_at, updated_at) VALUES (?, ?, '', '', '', ?, 0, 'rom', 'GBA', '2026-01-01T00:00:00', '2026-01-01T00:00:00')",
                (str(p.resolve()), p.name, p.suffix.lower()),
            )
            conn.commit()

        summary = check_library_health(repo)
        assert summary.ok == 0
        assert summary.missing == 0
        assert summary.corrupted == 0

    def test_progress_callback_called(self, tmp_path: Path, repo: LibraryRepository) -> None:
        data = b"rom"
        p = tmp_path / "game.gb"
        p.write_bytes(data)
        sha1 = hashlib.sha1(data).hexdigest().upper()
        _insert_game(repo, p, sha1)

        calls: list[tuple] = []
        check_library_health(repo, progress_cb=lambda c, t, f: calls.append((c, t, f)))

        assert len(calls) == 1
        current, total, filename = calls[0]
        assert current == 1
        assert total == 1
        assert "game.gb" in filename

    def test_cancel_event_stops_processing(self, tmp_path: Path, repo: LibraryRepository) -> None:
        for i in range(5):
            data = os.urandom(32)
            p = tmp_path / f"game{i}.gba"
            p.write_bytes(data)
            _insert_game(repo, p, hashlib.sha1(data).hexdigest().upper())

        cancel = threading.Event()
        processed: list[int] = []

        def cb(current: int, total: int, filename: str) -> None:
            processed.append(current)
            if current == 1:
                cancel.set()

        check_library_health(repo, progress_cb=cb, cancel_event=cancel)
        assert len(processed) < 5  # stopped before processing all

    def test_no_games_empty_summary(self, repo: LibraryRepository) -> None:
        summary = check_library_health(repo)
        assert summary.ok == 0
        assert summary.corrupted == 0
        assert summary.missing == 0
        assert summary.results == []

    def test_stored_and_computed_sha1_in_result(
        self, tmp_path: Path, repo: LibraryRepository
    ) -> None:
        p = tmp_path / "game.nes"
        p.write_bytes(b"data")
        stored = "A" * 40
        _insert_game(repo, p, stored)

        summary = check_library_health(repo)
        assert len(summary.results) == 1
        result = summary.results[0]
        assert result.stored_sha1 == stored
        assert len(result.computed_sha1) == 40
        assert result.stored_sha1 != result.computed_sha1
