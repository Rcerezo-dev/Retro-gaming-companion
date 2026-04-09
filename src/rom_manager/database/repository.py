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
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=30000")
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def batch(self) -> Iterator[sqlite3.Connection]:
        """Single open connection for bulk writes. Commits once on exit, rolls back on error."""
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=30000")
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
        platform: str | None = None,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        """Update catalog-match columns for a game row identified by source_path."""
        if platform is not None:
            sql = """
                UPDATE games
                SET canonical_title = ?,
                    match_confidence = ?,
                    catalog_source    = ?,
                    platform          = ?
                WHERE source_path = ?
                """
            params = (canonical_title, match_confidence, catalog_source, platform, source_path)
        else:
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
        """Return groups of games that share the same SHA1, excluding intentional copies."""
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, original_filename, source_path, platform,
                       canonical_title, size_bytes, sha1
                FROM games
                WHERE sha1 IN (
                    SELECT sha1 FROM games GROUP BY sha1 HAVING COUNT(*) > 1
                )
                AND sha1 NOT IN (SELECT sha1 FROM excluded_duplicates)
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

    def get_title_duplicate_groups(self) -> list[dict]:
        """Return groups of games that share the same canonical_title+platform but have different SHA1s.

        These are 'semantic duplicates' — same game, possibly different revision or region.
        Only returns groups where canonical_title is not NULL.
        """
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, original_filename, source_path, platform,
                       canonical_title, size_bytes, sha1
                FROM games
                WHERE canonical_title IS NOT NULL
                  AND (platform, canonical_title) IN (
                      SELECT platform, canonical_title
                      FROM games
                      WHERE canonical_title IS NOT NULL
                      GROUP BY platform, canonical_title
                      HAVING COUNT(DISTINCT sha1) > 1
                  )
                ORDER BY platform, canonical_title, source_path
                """
            ).fetchall()
        groups: dict[tuple, list[dict]] = {}
        for row in rows:
            key = (row["platform"], row["canonical_title"])
            if key not in groups:
                groups[key] = []
            groups[key].append({
                "id": row["id"],
                "original_filename": row["original_filename"],
                "source_path": row["source_path"],
                "platform": row["platform"],
                "canonical_title": row["canonical_title"],
                "size_bytes": int(row["size_bytes"]),
                "sha1": row["sha1"],
            })
        return [
            {"platform": k[0], "canonical_title": k[1], "entries": v}
            for k, v in groups.items()
        ]

    def exclude_duplicate_sha1(self, sha1: str, reason: str = "intentional_copy") -> None:
        """Mark a SHA1 group as an intentional copy — it will no longer appear as a duplicate."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        with self.connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO excluded_duplicates (sha1, reason, created_at) VALUES (?, ?, ?)",
                (sha1, reason, now),
            )
            conn.commit()

    def get_all_rom_sha1s(self) -> set[str]:
        """Return the set of all non-empty SHA1 hashes for ROM files in the library."""
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT sha1 FROM games WHERE file_type='rom' AND sha1 != '' AND sha1 IS NOT NULL"
            ).fetchall()
        return {row["sha1"].upper() for row in rows}

    # ── Wishlist ────────────────────────────────────────────────────────────────

    def get_wishlist(self) -> list[dict]:
        """Return all wishlist entries ordered by platform then title."""
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT sha1, title, platform, region, year, status, dat_source, created_at "
                "FROM wishlist ORDER BY platform, title"
            ).fetchall()
        return [dict(row) for row in rows]

    def upsert_wishlist_entry(
        self,
        sha1: str,
        title: str,
        platform: str,
        status: str,
        *,
        region: str = "",
        year: str = "",
        dat_source: str = "",
    ) -> None:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO wishlist (sha1, title, platform, region, year, status, dat_source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(sha1) DO UPDATE SET
                    status=excluded.status,
                    updated_at=excluded.updated_at
                """,
                (sha1, title, platform, region, year, status, dat_source, now, now),
            )
            conn.commit()

    def remove_wishlist_entry(self, sha1: str) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM wishlist WHERE sha1=?", (sha1,))
            conn.commit()

    def get_last_scan_by_root(self) -> dict[str, str]:
        """Return a mapping of source_root → last finished_at for each scanned root."""
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT source_root, MAX(finished_at) as last_at
                FROM scan_runs
                WHERE finished_at IS NOT NULL
                GROUP BY source_root
                """
            ).fetchall()
        return {row["source_root"]: row["last_at"] for row in rows}

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
        DB-2: Also cleans up orphaned metadata, tags, and operation logs when games are deleted.
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
            # Get game IDs for stale games to clean up related records
            stale_game_ids = []
            for p in stale_games:
                rows = conn.execute("SELECT id FROM games WHERE source_path = ?", (p,)).fetchall()
                stale_game_ids.extend([r[0] for r in rows])

            # Delete stale games and their related metadata, tags, and operation logs (cascading cleanup)
            for game_id in stale_game_ids:
                conn.execute("DELETE FROM game_metadata WHERE game_id = ?", (game_id,))
                conn.execute("DELETE FROM game_tags WHERE game_id = ?", (game_id,))
                conn.execute("DELETE FROM file_operations WHERE game_id = ?", (game_id,))
            for p in stale_games:
                conn.execute("DELETE FROM games WHERE source_path = ?", (p,))

            for p in stale_saves:
                conn.execute("DELETE FROM saves WHERE original_path = ?", (p,))
            for p in stale_assets:
                conn.execute("DELETE FROM assets WHERE source_path = ?", (p,))
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

    def set_play_status(self, game_id: int, status: str | None) -> None:
        """Set play_status for a game. status: 'playing'|'completed'|'100pct'|'abandoned'|None"""
        with self.connect() as conn:
            conn.execute("UPDATE games SET play_status = ? WHERE id = ?", (status, game_id))
            conn.commit()

    def get_filter_options(self) -> dict:
        """Return distinct values for advanced filter dropdowns: genres, years, regions, platforms."""
        with self.connect() as conn:
            genres = [
                r[0] for r in conn.execute(
                    "SELECT DISTINCT genre FROM game_metadata WHERE genre IS NOT NULL AND genre != '' ORDER BY genre"
                ).fetchall()
            ]
            years = [
                r[0] for r in conn.execute(
                    "SELECT DISTINCT year FROM game_metadata WHERE year IS NOT NULL AND year != '' ORDER BY year DESC"
                ).fetchall()
            ]
            regions = [
                r[0] for r in conn.execute(
                    "SELECT DISTINCT region FROM games WHERE region IS NOT NULL AND region != '' ORDER BY region"
                ).fetchall()
            ]
            platforms = [
                r[0] for r in conn.execute(
                    "SELECT DISTINCT platform FROM games WHERE platform IS NOT NULL AND platform != '' AND file_type='rom' ORDER BY platform"
                ).fetchall()
            ]
        return {"genres": genres, "years": years, "regions": regions, "platforms": platforms}

    def get_games_paginated(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        platform: str | None = None,
        status: str | None = None,
        source_root: str | None = None,
        file_type: str | None = "rom",
        search: str | None = None,
        play_status: str | None = None,
        favorite: bool = False,
        tag: str | None = None,
        genre: str | None = None,
        year: str | None = None,
        region: str | None = None,
        sort_by: str | None = None,
    ) -> tuple[list[dict], int]:
        """Return a paginated list of games and the total count matching the filters.

        *status* can be ``'unresolved'`` (no canonical_title) or ``'matched'``.
        *source_root* filters to only games whose source_path starts with the given prefix.
        *file_type*: ``'rom'`` = ROMs only (default); ``''`` = ROMs + saves; ``None`` = all.
        *search*: filters by canonical_title, original_filename or platform (case-insensitive LIKE).
        *favorite*: if True, only return favorites.
        *tag*: if given, only return games with that tag.
        """
        conditions: list[str] = []
        params: list[object] = []

        # Default: show only ROMs; filetype='' means ROMs+saves; filetype='save' means saves only; filetype=None means all
        if file_type == "rom":
            conditions.append("file_type = 'rom'")
        elif file_type == "save":
            conditions.append("file_type = 'save'")
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
        if search:
            like = "%" + search.replace("%", "%%").replace("_", "\\_") + "%"
            conditions.append(
                "(canonical_title LIKE ? ESCAPE '\\' OR original_filename LIKE ? ESCAPE '\\'"
                " OR platform LIKE ? ESCAPE '\\')"
            )
            params.extend([like, like, like])
        if play_status:
            conditions.append("play_status = ?")
            params.append(play_status)
        if favorite:
            conditions.append("is_favorite = 1")
        if tag:
            conditions.append(
                "id IN (SELECT game_id FROM game_tags WHERE tag = ?)"
            )
            params.append(tag)
        if region:
            conditions.append("region = ?")
            params.append(region)

        # genre / year require JOIN with game_metadata
        need_meta = bool(genre or year)
        if genre:
            conditions.append("gm.genre = ?")
            params.append(genre)
        if year:
            conditions.append("gm.year = ?")
            params.append(year)

        table_expr = (
            "games g LEFT JOIN game_metadata gm ON gm.game_id = g.id"
            if need_meta else "games"
        )
        col_prefix = "g." if need_meta else ""
        # Rewrite conditions that reference bare column names when we alias
        if need_meta:
            conditions = [
                c if c.startswith("gm.") or c.startswith("id IN") else
                c.replace("file_type", "g.file_type")
                 .replace("platform", "g.platform")
                 .replace("canonical_title", "g.canonical_title")
                 .replace("source_path", "g.source_path")
                 .replace("play_status", "g.play_status")
                 .replace("is_favorite", "g.is_favorite")
                 .replace("region", "g.region")
                 .replace("id IN", "g.id IN")
                for c in conditions
            ]

        where_sql = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        _order = {
            "year": "gm.year DESC, g.platform, g.canonical_title, g.original_filename",
            "last_played": "g.last_played_at DESC, g.platform, g.canonical_title",
            "title": "g.canonical_title, g.original_filename",
            "platform": "g.platform, g.canonical_title, g.original_filename",
        }.get(sort_by or "", "g.platform, g.canonical_title, g.original_filename") if need_meta else {
            "year": "(SELECT year FROM game_metadata WHERE game_id=id) DESC, platform, canonical_title",
            "last_played": "last_played_at DESC, platform, canonical_title",
            "title": "canonical_title, original_filename",
            "platform": "platform, canonical_title, original_filename",
        }.get(sort_by or "", "platform, canonical_title, original_filename")

        id_col = "g.id" if need_meta else "id"
        count_sql = f"SELECT COUNT(*) AS cnt FROM {table_expr} " + where_sql
        select_sql = (
            f"SELECT {id_col} AS id, g.original_filename, g.source_path, g.platform, g.region,"
            " g.extension, g.size_bytes, g.sha1, g.canonical_title,"
            " g.match_confidence, g.catalog_source, g.play_status, g.last_played_at,"
            f" g.is_favorite, g.notes, gm.genre, gm.year AS meta_year, gm.publisher"
            f" FROM {table_expr} " + where_sql +
            f" ORDER BY {_order} LIMIT ? OFFSET ?"
        ) if need_meta else (
            "SELECT id, original_filename, source_path, platform, region,"
            " extension, size_bytes, sha1, canonical_title,"
            " match_confidence, catalog_source, play_status, last_played_at,"
            " is_favorite, notes"
            " FROM games " + where_sql +
            f" ORDER BY {_order} LIMIT ? OFFSET ?"
        )

        with self.connect() as connection:
            total = int(
                connection.execute(count_sql, params).fetchone()["cnt"]
            )
            rows = connection.execute(
                select_sql,
                [*params, limit, offset],
            ).fetchall()

        _keys = {k for k in rows[0].keys()} if rows else set()
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
                "play_status": row["play_status"],
                "last_played_at": row["last_played_at"],
                "is_favorite": bool(row["is_favorite"]),
                "notes": row["notes"],
                **({"genre": row["genre"], "year": row["meta_year"], "publisher": row["publisher"]}
                   if "genre" in _keys else {}),
            }
            for row in rows
        ]
        return games, total

    def get_save_sync_history(self, source_path: str, limit: int = 10) -> list[dict]:
        """Return the last N sync log entries whose local_path starts with the game directory."""
        game_dir = str(Path(source_path).parent)
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT local_path, remote_path, direction, result, message, created_at "
                "FROM save_sync_log WHERE local_path LIKE ? ORDER BY id DESC LIMIT ?",
                (game_dir.replace("%", "%%").replace("_", "\\_") + "%", limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_save_comparison(self) -> list[dict]:
        """Return save files with their last sync event, for the comparator UI."""
        from datetime import datetime, timezone
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id, canonical_title, original_filename, platform, source_path, updated_at "
                "FROM games WHERE file_type='save' "
                "ORDER BY platform, canonical_title LIMIT 500"
            ).fetchall()
            results = []
            for g in rows:
                sp = g["source_path"]
                sync = conn.execute(
                    "SELECT direction, result, created_at FROM save_sync_log "
                    "WHERE local_path = ? ORDER BY id DESC LIMIT 1",
                    (sp,),
                ).fetchone()
                local_mtime = None
                try:
                    local_mtime = datetime.fromtimestamp(
                        Path(sp).stat().st_mtime, tz=timezone.utc
                    ).strftime("%Y-%m-%dT%H:%M:%S")
                except (OSError, ValueError):
                    pass
                results.append({
                    "title": g["canonical_title"] or g["original_filename"],
                    "filename": g["original_filename"],
                    "platform": g["platform"],
                    "local_path": sp,
                    "local_mtime": local_mtime,
                    "db_updated": g["updated_at"],
                    "last_sync_at": sync["created_at"] if sync else None,
                    "last_direction": sync["direction"] if sync else None,
                    "last_result": sync["result"] if sync else None,
                })
        return results

    def get_metadata_for_nlp(self) -> list[dict]:
        """Return scraped ROMs with NLP-relevant fields only (no paths/hashes).

        Only includes games that have been scraped AND have a non-empty description.
        Tags are aggregated into a comma-separated string.
        """
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    COALESCE(gm.title, g.canonical_title, g.original_filename) AS title,
                    g.platform,
                    g.region,
                    gm.year,
                    gm.genre,
                    gm.developer,
                    gm.publisher,
                    gm.description,
                    gm.rating,
                    g.play_status,
                    g.is_favorite,
                    g.notes,
                    (SELECT GROUP_CONCAT(tag, ', ')
                     FROM game_tags
                     WHERE game_id = g.id) AS tags
                FROM games g
                JOIN game_metadata gm ON gm.game_id = g.id
                WHERE g.file_type = 'rom'
                  AND gm.description IS NOT NULL AND gm.description != ''
                  AND (g.set_type IS NULL OR g.set_type NOT IN ('disc_image', 'disc_auxiliary'))
                  AND g.id = (
                      SELECT MIN(g2.id) FROM games g2
                      JOIN game_metadata gm2 ON gm2.game_id = g2.id
                      WHERE gm2.ss_game_id IS NOT NULL AND gm2.ss_game_id = gm.ss_game_id
                      UNION ALL
                      SELECT g3.id FROM games g3
                      WHERE gm.ss_game_id IS NULL AND g3.id = g.id
                  )
                ORDER BY g.platform, title
                """
            ).fetchall()
        return [dict(r) for r in rows]

    def get_library_export(self) -> list[dict]:
        """Return all ROMs with their metadata (genre, year, publisher, etc.) for export."""
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT g.id, g.original_filename, g.source_path, g.platform, g.region,
                       g.extension, g.size_bytes, g.sha1, g.canonical_title,
                       g.match_confidence, g.play_status, g.last_played_at, g.is_favorite,
                       gm.title AS meta_title, gm.year, gm.genre, gm.publisher,
                       gm.developer, gm.rating, gm.description
                FROM games g
                LEFT JOIN game_metadata gm ON gm.game_id = g.id
                WHERE g.file_type = 'rom'
                  AND (g.set_type IS NULL OR g.set_type NOT IN ('disc_image', 'disc_auxiliary'))
                ORDER BY g.platform, g.canonical_title, g.original_filename
                """
            ).fetchall()
        return [dict(r) for r in rows]

    def toggle_favorite(self, game_id: int) -> bool:
        """Toggle is_favorite for a game. Returns the new value."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        with self.connect() as conn:
            current = conn.execute(
                "SELECT is_favorite FROM games WHERE id = ?", (game_id,)
            ).fetchone()
            if current is None:
                return False
            new_val = 0 if current["is_favorite"] else 1
            conn.execute(
                "UPDATE games SET is_favorite = ?, updated_at = ? WHERE id = ?",
                (new_val, now, game_id),
            )
            conn.commit()
        return bool(new_val)

    def add_tag(self, game_id: int, tag: str) -> None:
        """Add a tag to a game (idempotent)."""
        tag = tag.strip().lower()
        if not tag:
            return
        with self.connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO game_tags (game_id, tag) VALUES (?, ?)",
                (game_id, tag),
            )
            conn.commit()

    def remove_tag(self, game_id: int, tag: str) -> None:
        """Remove a tag from a game."""
        tag = tag.strip().lower()
        with self.connect() as conn:
            conn.execute(
                "DELETE FROM game_tags WHERE game_id = ? AND tag = ?",
                (game_id, tag),
            )
            conn.commit()

    def get_tags(self, game_id: int) -> list[str]:
        """Return all tags for a game."""
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT tag FROM game_tags WHERE game_id = ? ORDER BY tag",
                (game_id,),
            ).fetchall()
        return [r["tag"] for r in rows]

    def get_all_tags(self) -> list[str]:
        """Return all unique tags in the library."""
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT tag FROM game_tags ORDER BY tag"
            ).fetchall()
        return [r["tag"] for r in rows]

    def set_notes(self, game_id: int, notes: str | None) -> None:
        with self.connect() as conn:
            conn.execute("UPDATE games SET notes = ? WHERE id = ?", (notes or None, game_id))
            conn.commit()

    def set_canonical_title(self, game_id: int, title: str) -> None:
        with self.connect() as conn:
            conn.execute("UPDATE games SET canonical_title = ? WHERE id = ?", (title.strip() or None, game_id))
            conn.commit()

    def upsert_metadata_manual(self, game_id: int, **fields: str) -> None:
        """Update individual metadata fields manually without overwriting unrelated scraped data."""
        _ALLOWED = {"year", "genre", "publisher", "developer", "description", "rating"}
        updates = {k: v for k, v in fields.items() if k in _ALLOWED}
        if not updates:
            return
        from rom_manager.scanner.rom_scanner import utc_now
        with self.connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO game_metadata (game_id, scraped_at) VALUES (?, ?)",
                (game_id, utc_now()),
            )
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            conn.execute(
                f"UPDATE game_metadata SET {set_clause} WHERE game_id = ?",
                [*updates.values(), game_id],
            )
            conn.commit()

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
        screenshot_path: str = "",
        wheel_path: str = "",
        connection: sqlite3.Connection,
    ) -> None:
        connection.execute(
            """
            INSERT INTO game_metadata
                (game_id, ss_game_id, title, year, genre, publisher, developer,
                 description, rating, box_art_url, box_art_path, scraped_at,
                 screenshot_path, wheel_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(game_id) DO UPDATE SET
                ss_game_id=excluded.ss_game_id, title=excluded.title,
                year=excluded.year, genre=excluded.genre,
                publisher=excluded.publisher, developer=excluded.developer,
                description=excluded.description, rating=excluded.rating,
                box_art_url=excluded.box_art_url, box_art_path=excluded.box_art_path,
                scraped_at=excluded.scraped_at,
                screenshot_path=excluded.screenshot_path,
                wheel_path=excluded.wheel_path
            """,
            (game_id, ss_game_id, title, year, genre, publisher, developer,
             description, rating, box_art_url, box_art_path, scraped_at,
             screenshot_path, wheel_path),
        )

    def update_image_paths(
        self,
        *,
        game_id: int,
        box_art_path: str = "",
        connection: "sqlite3.Connection",
    ) -> None:
        """Update only the local cover path for an existing metadata row.
        Used when downloading images that were previously skipped (no API call needed)."""
        connection.execute(
            "UPDATE game_metadata SET box_art_path = ? WHERE game_id = ?",
            (box_art_path, game_id),
        )

    def mark_metadata_scraped(self, game_id: int, connection: "sqlite3.Connection") -> None:
        """DB-1: Mark a game as checked for metadata (success or failure).
        Prevents re-scraping files that were already checked but had no match."""
        connection.execute("UPDATE games SET metadata_scraped = 1 WHERE id = ?", (game_id,))

    def get_games_for_scraping(self, platform: str | None = None) -> list[dict]:
        """Return games that have no metadata yet and haven't been checked, with their hashes.
        DB-1: Excludes games where metadata_scraped=1 (checked but no match found)."""
        sql = """
            SELECT g.id, g.original_filename, g.source_path, g.platform,
                   g.crc32, g.md5, g.sha1, g.size_bytes, g.canonical_title
            FROM games g
            LEFT JOIN game_metadata m ON m.game_id = g.id
            WHERE m.id IS NULL AND (g.metadata_scraped IS NULL OR g.metadata_scraped = 0)
        """
        params: list = []
        if platform:
            sql += " AND g.platform = ?"
            params.append(platform)
        sql += " ORDER BY g.platform, g.original_filename"
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def get_games_missing_images(self, platform: str | None = None) -> list[dict]:
        """Return games that have metadata with a stored box_art_url but no local
        box_art_path. These can have their cover downloaded without a new API call."""
        sql = """
            SELECT g.id, g.original_filename, g.source_path, g.platform,
                   m.box_art_url
            FROM games g
            JOIN game_metadata m ON m.game_id = g.id
            WHERE m.box_art_url IS NOT NULL AND m.box_art_url != ''
              AND (m.box_art_path IS NULL OR m.box_art_path = '')
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
        """Return games + metadata for a platform (for gamelist.xml generation).

        Excludes disc tracks (.bin/.img) that belong to a .cue set — only the
        cue sheet itself (or standalone .chd/.pbp) should appear as a game entry.
        """
        sql = """
            SELECT g.original_filename AS filename, g.source_path,
                   m.title, m.year, m.genre, m.publisher, m.developer,
                   m.description, m.rating, m.box_art_path,
                   m.screenshot_path, m.wheel_path
            FROM games g
            JOIN game_metadata m ON m.game_id = g.id
            WHERE g.platform = ?
              AND (g.set_type IS NULL OR g.set_type NOT IN ('disc_image', 'disc_auxiliary'))
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
