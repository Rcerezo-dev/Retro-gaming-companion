from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from rom_manager.database.schema import initialize_database


@dataclass(slots=True)
class ScanSummary:
    total_games: int
    total_saves: int
    total_assets: int
    last_scan_at: str | None


@dataclass(slots=True)
class MatchedGame:
    id: int
    original_filename: str
    source_path: str
    platform: str | None
    extension: str
    canonical_title: str
    match_confidence: str


@dataclass(slots=True)
class UnresolvedGame:
    original_filename: str
    source_path: str
    platform: str | None
    region: str | None
    sha1: str


class LibraryRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            initialize_database(connection)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def batch(self) -> Iterator[sqlite3.Connection]:
        """Single open connection for bulk writes. Commits once on exit, rolls back on error."""
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def create_scan_run(self, source_root: str, started_at: str) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO scan_runs (source_root, started_at)
                VALUES (?, ?)
                """,
                (source_root, started_at),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def complete_scan_run(
        self,
        scan_run_id: int,
        *,
        finished_at: str,
        files_seen: int,
        roms_detected: int,
        saves_detected: int,
        assets_detected: int,
        system_files_detected: int,
        unknown_files_detected: int,
        errors: int,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE scan_runs
                SET finished_at = ?,
                    files_seen = ?,
                    roms_detected = ?,
                    saves_detected = ?,
                    assets_detected = ?,
                    system_files_detected = ?,
                    unknown_files_detected = ?,
                    errors = ?
                WHERE id = ?
                """,
                (
                    finished_at,
                    files_seen,
                    roms_detected,
                    saves_detected,
                    assets_detected,
                    system_files_detected,
                    unknown_files_detected,
                    errors,
                    scan_run_id,
                ),
            )
            connection.commit()

    def get_known_roms(self) -> dict[str, tuple[int, int]]:
        """Return {source_path: (mtime, size_bytes)} for all games with a stored mtime.

        Used by the scanner to skip files that have not changed since the last scan.
        """
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT source_path, mtime, size_bytes FROM games WHERE mtime IS NOT NULL"
            ).fetchall()
        return {row["source_path"]: (int(row["mtime"]), int(row["size_bytes"])) for row in rows}

    def upsert_game(
        self,
        *,
        original_filename: str,
        source_path: str,
        platform: str | None,
        file_type: str,
        relative_parent: str,
        region: str | None,
        extension: str,
        size_bytes: int,
        mtime: int,
        sha1: str,
        md5: str,
        crc32: str,
        set_type: str,
        timestamp: str,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        sql = """
            INSERT INTO games (
                original_filename,
                source_path,
                platform,
                file_type,
                relative_parent,
                region,
                extension,
                size_bytes,
                mtime,
                sha1,
                md5,
                crc32,
                set_type,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_path) DO UPDATE SET
                original_filename = excluded.original_filename,
                platform = excluded.platform,
                file_type = excluded.file_type,
                relative_parent = excluded.relative_parent,
                region = excluded.region,
                extension = excluded.extension,
                size_bytes = excluded.size_bytes,
                mtime = excluded.mtime,
                sha1 = excluded.sha1,
                md5 = excluded.md5,
                crc32 = excluded.crc32,
                set_type = excluded.set_type,
                updated_at = excluded.updated_at
            """
        params = (
            original_filename,
            source_path,
            platform,
            file_type,
            relative_parent,
            region,
            extension,
            size_bytes,
            mtime,
            sha1,
            md5,
            crc32,
            set_type,
            timestamp,
            timestamp,
        )
        if connection is not None:
            connection.execute(sql, params)
            return
        with self.connect() as conn:
            conn.execute(sql, params)
            conn.commit()

    def upsert_save(
        self,
        *,
        original_path: str,
        relative_parent: str,
        extension: str,
        size_bytes: int,
        timestamp: str,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        sql = """
            INSERT INTO saves (
                original_path,
                relative_parent,
                extension,
                size_bytes,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(original_path) DO UPDATE SET
                relative_parent = excluded.relative_parent,
                extension = excluded.extension,
                size_bytes = excluded.size_bytes,
                updated_at = excluded.updated_at
            """
        params = (
            original_path,
            relative_parent,
            extension,
            size_bytes,
            timestamp,
            timestamp,
        )
        if connection is not None:
            connection.execute(sql, params)
            return
        with self.connect() as conn:
            conn.execute(sql, params)
            conn.commit()

    def upsert_asset(
        self,
        *,
        source_path: str,
        relative_parent: str,
        platform: str | None,
        asset_type: str,
        timestamp: str,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        sql = """
            INSERT INTO assets (
                source_path,
                relative_parent,
                platform,
                asset_type,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_path) DO UPDATE SET
                relative_parent = excluded.relative_parent,
                platform = excluded.platform,
                asset_type = excluded.asset_type,
                updated_at = excluded.updated_at
            """
        params = (
            source_path,
            relative_parent,
            platform,
            asset_type,
            timestamp,
            timestamp,
        )
        if connection is not None:
            connection.execute(sql, params)
            return
        with self.connect() as conn:
            conn.execute(sql, params)
            conn.commit()

    def get_unresolved_games(self) -> list[UnresolvedGame]:
        """Return all games that have not yet been matched against a catalog."""
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT original_filename, source_path, platform, region, sha1
                FROM games
                WHERE match_confidence IS NULL
                ORDER BY platform, original_filename
                """
            ).fetchall()
        return [
            UnresolvedGame(
                original_filename=row["original_filename"],
                source_path=row["source_path"],
                platform=row["platform"],
                region=row["region"],
                sha1=row["sha1"],
            )
            for row in rows
        ]

    def get_matched_games(self) -> list[MatchedGame]:
        """Return all games that have been matched against a catalog."""
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, original_filename, source_path, platform, extension,
                       canonical_title, match_confidence
                FROM games
                WHERE canonical_title IS NOT NULL
                ORDER BY platform, canonical_title
                """
            ).fetchall()
        return [
            MatchedGame(
                id=row["id"],
                original_filename=row["original_filename"],
                source_path=row["source_path"],
                platform=row["platform"],
                extension=row["extension"],
                canonical_title=row["canonical_title"],
                match_confidence=row["match_confidence"],
            )
            for row in rows
        ]

    def apply_rename(
        self,
        *,
        game_id: int,
        old_source_path: str,
        new_source_path: str,
        new_filename: str,
        timestamp: str,
    ) -> None:
        """Update source_path and original_filename for a renamed game and log the operation."""
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE games
                SET source_path = ?, original_filename = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_source_path, new_filename, timestamp, game_id),
            )
            connection.execute(
                """
                INSERT INTO file_operations
                    (game_id, operation_type, source_path, target_path, result, created_at)
                VALUES (?, 'rename', ?, ?, 'done', ?)
                """,
                (game_id, old_source_path, new_source_path, timestamp),
            )
            connection.commit()

    def update_match(
        self,
        source_path: str,
        *,
        canonical_title: str,
        match_confidence: str,
        catalog_source: str,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        """Update catalog-match columns for a game row identified by source_path."""
        sql = """
            UPDATE games
            SET canonical_title = ?,
                match_confidence = ?,
                catalog_source    = ?
            WHERE source_path = ?
            """
        params = (canonical_title, match_confidence, catalog_source, source_path)
        if connection is not None:
            connection.execute(sql, params)
            return
        with self.connect() as conn:
            conn.execute(sql, params)
            conn.commit()

    def get_summary(self) -> ScanSummary:
        with self.connect() as connection:
            games_count = connection.execute(
                "SELECT COUNT(*) AS count FROM games"
            ).fetchone()["count"]
            saves_count = connection.execute(
                "SELECT COUNT(*) AS count FROM saves"
            ).fetchone()["count"]
            assets_count = connection.execute(
                "SELECT COUNT(*) AS count FROM assets"
            ).fetchone()["count"]
            last_scan = connection.execute(
                """
                SELECT finished_at
                FROM scan_runs
                WHERE finished_at IS NOT NULL
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
        return ScanSummary(
            total_games=int(games_count),
            total_saves=int(saves_count),
            total_assets=int(assets_count),
            last_scan_at=last_scan["finished_at"] if last_scan else None,
        )
