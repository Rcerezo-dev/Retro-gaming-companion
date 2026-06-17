from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from rom_manager.database.repository import LibraryRepository
from rom_manager.reports.reporter import build_report, to_csv, to_json

_TS = "2024-01-01T00:00:00"
_SHA1_A = "A" * 40
_SHA1_B = "B" * 40
_SHA1_C = "C" * 40


def _insert_game(
    repo: LibraryRepository,
    *,
    source_path: str,
    sha1: str,
    platform: str | None = "Game Boy",
    canonical_title: str | None = None,
    size_bytes: int = 1024,
) -> None:
    filename = source_path.rsplit("/", 1)[-1]
    repo.upsert_game(
        original_filename=filename,
        source_path=source_path,
        platform=platform,
        file_type="rom",
        relative_parent="",
        region="USA",
        extension=".gb",
        size_bytes=size_bytes,
        mtime=0,
        sha1=sha1,
        md5="M" * 32,
        crc32="CCCCCCCC",
        set_type="single",
        timestamp=_TS,
    )
    if canonical_title:
        repo.update_match(
            source_path,
            canonical_title=canonical_title,
            match_confidence="high",
            catalog_source="test.dat",
        )


def test_report_empty_library(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    report = build_report(repo)
    assert report.total_games == 0
    assert report.matched_games == 0
    assert report.games == []


def test_report_counts(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path="/roms/a.gb", sha1=_SHA1_A, canonical_title="Game A")
    _insert_game(repo, source_path="/roms/b.gb", sha1=_SHA1_B)  # unmatched
    # duplicate of A
    _insert_game(repo, source_path="/roms/a2.gb", sha1=_SHA1_A, canonical_title="Game A")

    report = build_report(repo)
    assert report.total_games == 3
    assert report.matched_games == 2
    assert report.unmatched_games == 1
    assert report.duplicate_groups == 1
    assert report.duplicate_files == 2
    assert report.wasted_bytes == 1024  # one copy wasted


def test_to_json_structure(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path="/roms/a.gb", sha1=_SHA1_A, canonical_title="Game A")
    report = build_report(repo)
    data = json.loads(to_json(report))

    assert "summary" in data
    assert "games" in data
    assert data["summary"]["total_games"] == 1
    assert data["games"][0]["sha1"] == _SHA1_A


def test_to_csv_has_header(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path="/roms/a.gb", sha1=_SHA1_A, canonical_title="Game A")
    report = build_report(repo)
    csv_text = to_csv(report)

    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["sha1"] == _SHA1_A
    assert rows[0]["canonical_title"] == "Game A"


def test_to_csv_all_games_present(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    for i in range(5):
        _insert_game(repo, source_path=f"/roms/game{i}.gb", sha1=f"{'0' * 39}{i}")
    report = build_report(repo)
    csv_text = to_csv(report)
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    assert len(rows) == 5


def test_report_generated_at_is_set(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    report = build_report(repo)
    assert "T" in report.generated_at  # ISO-8601 format
