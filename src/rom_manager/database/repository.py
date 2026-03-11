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
    sha1: str = ""


@dataclass(slots=True)
class DuplicateEntry:
    id: int
    original_filename: str
    source_path: str
    platform: str | None
    canonical_title: str | None
    size_bytes: int


@dataclass(slots=True)
class DuplicateGroup:
    sha1: str
    entries: list[DuplicateEntry]

    @property
    def wasted_bytes(self) -> int:
        """Bytes that could be freed by keeping only one copy."""
        if not self.entries:
            return 0
        return self.entries[0].size_bytes * (len(self.entries) - 1)


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
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def batch(self) -> Iterator[sqlite3.Connection]:
        """Single open connection for bulk writes. Commits once on exit, rolls back on error."""
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
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
                       canonical_title, match_confidence, sha1
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
                sha1=row["sha1"],
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

    def get_duplicate_groups(self) -> list[DuplicateGroup]:
        """Return groups of games that share the same SHA1 (exact duplicates)."""
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, original_filename, source_path, platform,
                       canonical_title, size_bytes, sha1
                FROM games
                WHERE sha1 IN (
                    SELECT sha1 FROM games GROUP BY sha1 HAVING COUNT(*) > 1
                )
                ORDER BY sha1, source_path
                """
            ).fetchall()
        groups: dict[str, list[DuplicateEntry]] = {}
        for row in rows:
            sha1 = row["sha1"]
            if sha1 not in groups:
                groups[sha1] = []
            groups[sha1].append(
                DuplicateEntry(
                    id=row["id"],
                    original_filename=row["original_filename"],
                    source_path=row["source_path"],
                    platform=row["platform"],
                    canonical_title=row["canonical_title"],
                    size_bytes=int(row["size_bytes"]),
                )
            )
        return [DuplicateGroup(sha1=sha1, entries=entries) for sha1, entries in groups.items()]

    def backfill_platforms(self, detect_fn) -> int:
        """Update platform for all games where it is currently NULL.

        *detect_fn* must accept a Path and return str | None.
        Returns the number of rows updated.
        """
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT source_path FROM games WHERE platform IS NULL"
            ).fetchall()

        updated = 0
        with self.batch() as conn:
            for (source_path,) in rows:
                platform = detect_fn(Path(source_path))
                if platform:
                    conn.execute(
                        "UPDATE games SET platform = ? WHERE source_path = ?",
                        (platform, source_path),
                    )
                    updated += 1
        return updated

    def prune_stale_entries(self, source_root: str, seen_paths: set[str]) -> int:
        """Delete records for files that were under *source_root* but are no longer on disk.

        *seen_paths* is the set of resolved absolute path strings found during the scan.
        Only paths that start with *source_root* are considered — other roots are untouched.
        Returns the total number of records deleted across all tables.
        """
        import os
        root_prefix = source_root + os.sep

        def _under_root(p: str) -> bool:
            p_lower = p.lower()
            return p_lower == source_root.lower() or p_lower.startswith(root_prefix.lower())

        with self.connect() as conn:
            game_paths  = [r[0] for r in conn.execute("SELECT source_path  FROM games").fetchall()]
            save_paths  = [r[0] for r in conn.execute("SELECT original_path FROM saves").fetchall()]
            asset_paths = [r[0] for r in conn.execute("SELECT source_path  FROM assets").fetchall()]

        stale_games  = [p for p in game_paths  if _under_root(p) and p not in seen_paths]
        stale_saves  = [p for p in save_paths  if _under_root(p) and p not in seen_paths]
        stale_assets = [p for p in asset_paths if _under_root(p) and p not in seen_paths]

        total = len(stale_games) + len(stale_saves) + len(stale_assets)
        if total == 0:
            return 0

        with self.batch() as conn:
            for p in stale_games:
                conn.execute("DELETE FROM games  WHERE source_path   = ?", (p,))
            for p in stale_saves:
                conn.execute("DELETE FROM saves  WHERE original_path = ?", (p,))
            for p in stale_assets:
                conn.execute("DELETE FROM assets WHERE source_path   = ?", (p,))
        return total

    def delete_game(self, game_id: int) -> None:
        """Remove a game record from the database (file must be deleted from disk first)."""
        with self.connect() as connection:
            connection.execute("DELETE FROM games WHERE id = ?", (game_id,))
            connection.commit()

    def get_sync_log(self, limit: int = 100) -> list[dict]:
        """Return the last *limit* entries from save_sync_log, newest first."""
        with self.connect() as connection:
            # The table may not exist in older databases; return empty list if so.
            try:
                rows = connection.execute(
                    """
                    SELECT local_path, remote_path, direction, result, message, created_at
                    FROM save_sync_log
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            except Exception:
                return []
        return [
            {
                "local_path": row["local_path"],
                "remote_path": row["remote_path"],
                "direction": row["direction"],
                "result": row["result"],
                "message": row["message"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def get_asset_platform_stats(self, source_root: str | None = None) -> list[dict]:
        """Return per-platform asset counts (images, videos, XML/gamelists).

        Also includes rom_count from the games table and orphan asset count
        (assets in platforms that have no games).

        *source_root* filters to only entries whose source_path starts with that prefix.
        """
        _IMAGE_EXTS = {"jpg", "jpeg", "png", "webp", "tga", "bmp"}
        _VIDEO_EXTS = {"mp4", "mkv", "avi", "webm", "mov"}

        prefix = source_root.rstrip("/\\") + "%" if source_root else None

        with self.connect() as connection:
            if prefix:
                game_rows = connection.execute(
                    "SELECT platform, COUNT(*) AS cnt FROM games WHERE source_path LIKE ? GROUP BY platform",
                    (prefix,),
                ).fetchall()
                asset_rows = connection.execute(
                    "SELECT platform, asset_type, COUNT(*) AS cnt FROM assets WHERE source_path LIKE ? GROUP BY platform, asset_type",
                    (prefix,),
                ).fetchall()
            else:
                game_rows = connection.execute(
                    "SELECT platform, COUNT(*) AS cnt FROM games GROUP BY platform"
                ).fetchall()
                asset_rows = connection.execute(
                    "SELECT platform, asset_type, COUNT(*) AS cnt FROM assets GROUP BY platform, asset_type"
                ).fetchall()

        game_counts: dict[str, int] = {
            (row["platform"] or "Unknown"): int(row["cnt"]) for row in game_rows
        }

        # Build asset stats per platform
        asset_stats: dict[str, dict] = {}
        for row in asset_rows:
            plat = row["platform"] or "Unknown"
            if plat not in asset_stats:
                asset_stats[plat] = {"images": 0, "videos": 0, "xml": 0, "other": 0}
            ext = (row["asset_type"] or "").lower()
            cnt = int(row["cnt"])
            if ext in _IMAGE_EXTS:
                asset_stats[plat]["images"] += cnt
            elif ext in _VIDEO_EXTS:
                asset_stats[plat]["videos"] += cnt
            elif ext == "gamelist":
                asset_stats[plat]["xml"] += cnt
            else:
                asset_stats[plat]["other"] += cnt

        # Merge: all platforms from either table
        all_platforms = sorted(set(game_counts) | set(asset_stats))
        result: list[dict] = []
        for plat in all_platforms:
            g = game_counts.get(plat, 0)
            a = asset_stats.get(plat, {"images": 0, "videos": 0, "xml": 0, "other": 0})
            result.append({
                "platform": plat,
                "rom_count": g,
                "image_count": a["images"],
                "video_count": a["videos"],
                "xml_count": a["xml"],
                "orphan_assets": a["images"] + a["videos"] + a["xml"] + a["other"] if g == 0 else 0,
            })
        return result

    def get_roms_without_assets(self, *, platform: str | None = None) -> list[dict]:
        """Return games in platforms that have no assets at all."""
        with self.connect() as connection:
            if platform:
                rows = connection.execute(
                    """
                    SELECT id, original_filename, source_path, platform
                    FROM games
                    WHERE platform = ?
                      AND platform NOT IN (SELECT DISTINCT platform FROM assets WHERE platform IS NOT NULL)
                    ORDER BY platform, original_filename
                    """,
                    (platform,),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT id, original_filename, source_path, platform
                    FROM games
                    WHERE platform NOT IN (SELECT DISTINCT platform FROM assets WHERE platform IS NOT NULL)
                    ORDER BY platform, original_filename
                    """
                ).fetchall()
        return [
            {
                "id": row["id"],
                "original_filename": row["original_filename"],
                "source_path": row["source_path"],
                "platform": row["platform"],
            }
            for row in rows
        ]

    def get_orphan_assets(self, *, platform: str | None = None) -> list[dict]:
        """Return assets in platforms that have no games."""
        with self.connect() as connection:
            if platform:
                rows = connection.execute(
                    """
                    SELECT id, source_path, platform, asset_type
                    FROM assets
                    WHERE platform = ?
                      AND (platform NOT IN (SELECT DISTINCT platform FROM games WHERE platform IS NOT NULL)
                           OR platform IS NULL)
                    ORDER BY platform, source_path
                    """,
                    (platform,),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT id, source_path, platform, asset_type
                    FROM assets
                    WHERE platform NOT IN (SELECT DISTINCT platform FROM games WHERE platform IS NOT NULL)
                       OR platform IS NULL
                    ORDER BY platform, source_path
                    """
                ).fetchall()
        return [
            {
                "id": row["id"],
                "source_path": row["source_path"],
                "platform": row["platform"],
                "asset_type": row["asset_type"],
            }
            for row in rows
        ]

    def get_games_paginated(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        platform: str | None = None,
        status: str | None = None,
        source_root: str | None = None,
        file_type: str | None = "rom",
    ) -> tuple[list[dict], int]:
        """Return a paginated list of games and the total count matching the filters.

        *status* can be ``'unresolved'`` (no canonical_title) or ``'matched'``.
        *source_root* filters to only games whose source_path starts with the given prefix.
        *file_type*: ``'rom'`` = ROMs only (default); ``''`` = ROMs + saves; ``None`` = all.
        """
        conditions: list[str] = []
        params: list[object] = []

        # Default: show only ROMs; filetype='' means ROMs+saves; filetype=None means all
        if file_type == "rom":
            conditions.append("file_type = 'rom'")
        elif file_type == "":
            conditions.append("file_type IN ('rom', 'save')")

        if platform:
            conditions.append("platform = ?")
            params.append(platform)
        if status == "unresolved":
            conditions.append("canonical_title IS NULL")
        elif status == "matched":
            conditions.append("canonical_title IS NOT NULL")
        if source_root:
            conditions.append("source_path LIKE ?")
            params.append(source_root.rstrip("/\\").replace("%", "%%") + "%")

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        with self.connect() as connection:
            total = int(
                connection.execute(
                    f"SELECT COUNT(*) AS cnt FROM games {where}", params
                ).fetchone()["cnt"]
            )
            rows = connection.execute(
                f"""
                SELECT id, original_filename, source_path, platform, region,
                       extension, size_bytes, sha1, canonical_title,
                       match_confidence, catalog_source
                FROM games {where}
                ORDER BY platform, canonical_title, original_filename
                LIMIT ? OFFSET ?
                """,
                [*params, limit, offset],
            ).fetchall()

        games = [
            {
                "id": row["id"],
                "original_filename": row["original_filename"],
                "source_path": row["source_path"],
                "platform": row["platform"],
                "region": row["region"],
                "extension": row["extension"],
                "size_bytes": int(row["size_bytes"]),
                "sha1": row["sha1"],
                "canonical_title": row["canonical_title"],
                "match_confidence": row["match_confidence"],
                "catalog_source": row["catalog_source"],
            }
            for row in rows
        ]
        return games, total

    # ------------------------------------------------------------------
    # Metadata (ScreenScraper)
    # ------------------------------------------------------------------

    def upsert_metadata(
        self,
        *,
        game_id: int,
        ss_game_id: str,
        title: str,
        year: str,
        genre: str,
        publisher: str,
        developer: str,
        description: str,
        rating: str,
        box_art_url: str,
        box_art_path: str,
        scraped_at: str,
        connection: sqlite3.Connection,
    ) -> None:
        connection.execute(
            """
            INSERT INTO game_metadata
                (game_id, ss_game_id, title, year, genre, publisher, developer,
                 description, rating, box_art_url, box_art_path, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(game_id) DO UPDATE SET
                ss_game_id=excluded.ss_game_id, title=excluded.title,
                year=excluded.year, genre=excluded.genre,
                publisher=excluded.publisher, developer=excluded.developer,
                description=excluded.description, rating=excluded.rating,
                box_art_url=excluded.box_art_url, box_art_path=excluded.box_art_path,
                scraped_at=excluded.scraped_at
            """,
            (game_id, ss_game_id, title, year, genre, publisher, developer,
             description, rating, box_art_url, box_art_path, scraped_at),
        )

    def get_games_for_scraping(self, platform: str | None = None) -> list[dict]:
        """Return games that have no metadata yet, with their hashes."""
        sql = """
            SELECT g.id, g.original_filename, g.source_path, g.platform,
                   g.crc32, g.md5, g.sha1, g.size_bytes, g.canonical_title
            FROM games g
            LEFT JOIN game_metadata m ON m.game_id = g.id
            WHERE m.id IS NULL
        """
        params: list = []
        if platform:
            sql += " AND g.platform = ?"
            params.append(platform)
        sql += " ORDER BY g.platform, g.original_filename"
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def get_metadata_for_platform(self, platform: str) -> list[dict]:
        """Return games + metadata for a platform (for gamelist.xml generation)."""
        sql = """
            SELECT g.original_filename, g.source_path,
                   m.title, m.year, m.genre, m.publisher, m.developer,
                   m.description, m.rating, m.box_art_path
            FROM games g
            JOIN game_metadata m ON m.game_id = g.id
            WHERE g.platform = ?
            ORDER BY m.title, g.original_filename
        """
        with self.connect() as conn:
            rows = conn.execute(sql, (platform,)).fetchall()
        return [dict(r) for r in rows]

    def get_scraped_platform_summary(self) -> list[dict]:
        """Return per-platform counts: total games, scraped, missing."""
        sql = """
            SELECT g.platform,
                   COUNT(*) AS total,
                   COUNT(m.id) AS scraped
            FROM games g
            LEFT JOIN game_metadata m ON m.game_id = g.id
            WHERE g.platform IS NOT NULL
            GROUP BY g.platform
            ORDER BY g.platform
        """
        with self.connect() as conn:
            rows = conn.execute(sql).fetchall()
        return [
            {"platform": r["platform"], "total": r["total"], "scraped": r["scraped"],
             "missing": r["total"] - r["scraped"]}
            for r in rows
        ]

    def sha1_exists(self, sha1: str) -> bool:
        """Return True if *sha1* is already present in the games table."""
        with self.connect() as conn:
            return bool(
                conn.execute(
                    "SELECT EXISTS(SELECT 1 FROM games WHERE sha1 = ?)", (sha1.upper(),)
                ).fetchone()[0]
            )

    def get_summary(self, source_root: str | None = None) -> ScanSummary:
        """Return library-wide counts.

        When *source_root* is provided only rows whose ``source_path`` starts
        with that prefix are counted (used to get per-device stats).
        """
        prefix = source_root.rstrip("/\\") if source_root else None
        with self.connect() as connection:
            if prefix:
                like = prefix.replace("%", "%%") + "%"
                games_count = connection.execute(
                    "SELECT COUNT(*) AS count FROM games WHERE source_path LIKE ?", (like,)
                ).fetchone()["count"]
                saves_count = connection.execute(
                    "SELECT COUNT(*) AS count FROM saves WHERE original_path LIKE ?", (like,)
                ).fetchone()["count"]
                assets_count = connection.execute(
                    "SELECT COUNT(*) AS count FROM assets WHERE source_path LIKE ?", (like,)
                ).fetchone()["count"]
            else:
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
