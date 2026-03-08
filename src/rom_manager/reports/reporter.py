from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from rom_manager.database.repository import LibraryRepository


@dataclass(slots=True)
class ReportGame:
    id: int
    original_filename: str
    source_path: str
    platform: str | None
    region: str | None
    extension: str
    size_bytes: int
    sha1: str
    canonical_title: str | None
    match_confidence: str | None
    catalog_source: str | None


@dataclass(slots=True)
class LibraryReport:
    generated_at: str
    total_games: int
    total_saves: int
    total_assets: int
    matched_games: int
    unmatched_games: int
    duplicate_groups: int
    duplicate_files: int
    wasted_bytes: int
    games: list[ReportGame]


def build_report(repository: LibraryRepository) -> LibraryReport:
    summary = repository.get_summary()
    duplicate_groups = repository.get_duplicate_groups()
    games = _get_all_games(repository)

    matched = sum(1 for g in games if g.canonical_title is not None)
    dup_files = sum(len(g.entries) for g in duplicate_groups)
    wasted = sum(g.wasted_bytes for g in duplicate_groups)

    return LibraryReport(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        total_games=summary.total_games,
        total_saves=summary.total_saves,
        total_assets=summary.total_assets,
        matched_games=matched,
        unmatched_games=summary.total_games - matched,
        duplicate_groups=len(duplicate_groups),
        duplicate_files=dup_files,
        wasted_bytes=wasted,
        games=games,
    )


def _get_all_games(repository: LibraryRepository) -> list[ReportGame]:
    with repository.connect() as connection:
        rows = connection.execute(
            """
            SELECT id, original_filename, source_path, platform, region,
                   extension, size_bytes, sha1, canonical_title,
                   match_confidence, catalog_source
            FROM games
            ORDER BY platform, canonical_title, original_filename
            """
        ).fetchall()
    return [
        ReportGame(
            id=row["id"],
            original_filename=row["original_filename"],
            source_path=row["source_path"],
            platform=row["platform"],
            region=row["region"],
            extension=row["extension"],
            size_bytes=int(row["size_bytes"]),
            sha1=row["sha1"],
            canonical_title=row["canonical_title"],
            match_confidence=row["match_confidence"],
            catalog_source=row["catalog_source"],
        )
        for row in rows
    ]


def to_json(report: LibraryReport) -> str:
    data = {
        "generated_at": report.generated_at,
        "summary": {
            "total_games": report.total_games,
            "total_saves": report.total_saves,
            "total_assets": report.total_assets,
            "matched_games": report.matched_games,
            "unmatched_games": report.unmatched_games,
            "duplicate_groups": report.duplicate_groups,
            "duplicate_files": report.duplicate_files,
            "wasted_bytes": report.wasted_bytes,
        },
        "games": [asdict(g) for g in report.games],
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def to_csv(report: LibraryReport) -> str:
    buf = io.StringIO()
    fields = [
        "id",
        "platform",
        "canonical_title",
        "original_filename",
        "region",
        "extension",
        "size_bytes",
        "sha1",
        "match_confidence",
        "catalog_source",
        "source_path",
    ]
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for g in report.games:
        writer.writerow(asdict(g))
    return buf.getvalue()
