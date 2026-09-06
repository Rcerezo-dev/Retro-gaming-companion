"""Tests for health_checker.py — library integrity verification."""

from __future__ import annotations

import hashlib
import os
import threading
from pathlib import Path

import pytest

from rom_manager.database.repository import LibraryRepository
from rom_manager.utils.health_checker import (
    check_disc_set_health,
    check_library_health,
    check_misplaced_extensions_health,
)


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


class TestCheckDiscSetHealth:
    """DISC-HEALTH-1: repeats the manual method from
    Tareas/psx-cue-rotos-2026-08-30.md as a reusable function."""

    def test_no_cues_reports_nothing(self, tmp_path: Path) -> None:
        summary = check_disc_set_health(tmp_path)

        assert summary.broken == 0
        assert summary.results == []

    def test_intact_cue_is_not_reported(self, tmp_path: Path) -> None:
        bin_path = tmp_path / "Game (USA).bin"
        bin_path.touch()
        (tmp_path / "Game (USA).cue").write_text('FILE "Game (USA).bin" BINARY\n', encoding="utf-8")

        summary = check_disc_set_health(tmp_path)

        assert summary.broken == 0

    def test_broken_cue_with_rescue_candidate_elsewhere(self, tmp_path: Path) -> None:
        """Same real-world shape as psx-cue-rotos-2026-08-30.md: a broken
        .cue for one region, an already-playable .chd of another region for
        the same game living elsewhere in the tree."""
        broken_cue = tmp_path / "Game (Europe).cue"
        broken_cue.write_text('FILE "Game (Europe).bin" BINARY\n', encoding="utf-8")
        # .bin deliberately not created -> broken

        rescue = tmp_path / "converted" / "Game (USA).chd"
        rescue.parent.mkdir()
        rescue.write_bytes(b"fake chd")

        summary = check_disc_set_health(tmp_path)

        assert summary.broken == 1
        result = summary.results[0]
        assert result.cue_path == str(broken_cue)
        assert result.rescue_candidates == [str(rescue)]

    def test_broken_cue_lists_multiple_rescue_candidates(self, tmp_path: Path) -> None:
        broken_cue = tmp_path / "Game (Japan).cue"
        broken_cue.write_text('FILE "Game (Japan).bin" BINARY\n', encoding="utf-8")

        usa = tmp_path / "Game (USA).chd"
        usa.write_bytes(b"fake chd")
        pbp = tmp_path / "Game (Europe).pbp"
        pbp.write_bytes(b"fake pbp")

        summary = check_disc_set_health(tmp_path)

        assert summary.results[0].rescue_candidates == sorted([str(usa), str(pbp)])

    def test_broken_cue_without_rescue_candidate(self, tmp_path: Path) -> None:
        broken_cue = tmp_path / "Game (Europe).cue"
        broken_cue.write_text('FILE "Game (Europe).bin" BINARY\n', encoding="utf-8")

        summary = check_disc_set_health(tmp_path)

        assert summary.broken == 1
        assert summary.results[0].rescue_candidates == []

    def test_unrelated_chd_is_not_offered_as_rescue(self, tmp_path: Path) -> None:
        """A .chd of a *different* game must never show up as a rescue
        candidate for an unrelated broken cue."""
        broken_cue = tmp_path / "Game A (Europe).cue"
        broken_cue.write_text('FILE "Game A (Europe).bin" BINARY\n', encoding="utf-8")

        (tmp_path / "Game B (USA).chd").write_bytes(b"fake chd")

        summary = check_disc_set_health(tmp_path)

        assert summary.results[0].rescue_candidates == []


class TestCheckMisplacedExtensionsHealth:
    """LIB-MISPLACED-1: finds files whose extension belongs to a different
    platform than the already-organized folder they're sitting in."""

    def test_empty_library_reports_nothing(self, tmp_path: Path) -> None:
        summary = check_misplaced_extensions_health(tmp_path)

        assert summary.misplaced == 0
        assert summary.results == []

    def test_matching_extension_is_not_reported(self, tmp_path: Path) -> None:
        gba_dir = tmp_path / "gba"
        gba_dir.mkdir()
        (gba_dir / "Kirby (USA).gba").touch()

        summary = check_misplaced_extensions_health(tmp_path)

        assert summary.misplaced == 0

    def test_wrong_platform_extension_is_reported(self, tmp_path: Path) -> None:
        """Real-world case: a .nes ROM mixed into gba/."""
        gba_dir = tmp_path / "gba"
        gba_dir.mkdir()
        misplaced = gba_dir / "Contra (USA).nes"
        misplaced.touch()

        summary = check_misplaced_extensions_health(tmp_path)

        assert summary.misplaced == 1
        result = summary.results[0]
        assert result.path == str(misplaced)
        assert result.folder_platform == "Game Boy Advance"
        assert result.detected_platform == "NES"

    def test_unrecognized_extension_is_not_reported(self, tmp_path: Path) -> None:
        """BIOS/assets/unknown chip dumps never get treated as ROMs."""
        gba_dir = tmp_path / "gba"
        gba_dir.mkdir()
        (gba_dir / "boxart.png").touch()

        summary = check_misplaced_extensions_health(tmp_path)

        assert summary.misplaced == 0

    def test_unrecognized_folder_is_skipped(self, tmp_path: Path) -> None:
        """saves/, bios/, inbox/ etc. aren't platform folders -- never scanned."""
        (tmp_path / "saves").mkdir()
        (tmp_path / "saves" / "Contra (USA).nes").touch()

        summary = check_misplaced_extensions_health(tmp_path)

        assert summary.misplaced == 0

    def test_nested_misplaced_file_is_found(self, tmp_path: Path) -> None:
        psx_dir = tmp_path / "psx"
        nested = psx_dir / "_descartados" / "_descartados"
        nested.mkdir(parents=True)
        misplaced = nested / "Sonic (USA).sfc"
        misplaced.touch()

        summary = check_misplaced_extensions_health(tmp_path)

        assert summary.misplaced == 1
        assert summary.results[0].path == str(misplaced)
        assert summary.results[0].detected_platform == "SNES"

    def test_multiple_misplaced_files_across_folders(self, tmp_path: Path) -> None:
        gba_dir = tmp_path / "gba"
        gba_dir.mkdir()
        (gba_dir / "Sonic (USA).md").touch()
        (gba_dir / "Contra (USA).nes").touch()
        (gba_dir / "Pokemon (USA).gba").touch()  # correctly placed, not reported

        summary = check_misplaced_extensions_health(tmp_path)

        assert summary.misplaced == 1
        assert summary.results[0].detected_platform == "NES"
