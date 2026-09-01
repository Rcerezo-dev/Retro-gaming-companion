"""Games aggregate: ROM rows, matching, renames, pagination and pruning.

Mixed into :class:`~rom_manager.database.repository.LibraryRepository`; relies on
``connect``/``batch`` from ``_RepositoryBase``.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from rom_manager.database.repositories.base import escape_like_prefix
from rom_manager.database.repositories.models import MatchedGame, UnresolvedGame


def _delete_game_children(conn: sqlite3.Connection, game_id: int) -> None:
    """Delete a game's metadata/tags/operation history. Call before deleting the games row."""
    conn.execute("DELETE FROM game_metadata WHERE game_id = ?", (game_id,))
    conn.execute("DELETE FROM game_tags WHERE game_id = ?", (game_id,))
    conn.execute("DELETE FROM file_operations WHERE game_id = ?", (game_id,))


def cascade_delete_games_by_source_path(
    conn: sqlite3.Connection, source_path: str, *, exclude_id: int | None = None
) -> None:
    """Delete game row(s) matching source_path, and their metadata/tags/file_operations.

    For callers that key a delete off source_path within their own transaction
    (inbox pipeline, RA duplicate resolution, cloud migration) instead of
    delete_game() (keyed by id) -- same cascade, different key, so a row with
    children doesn't violate the FK constraint on games.
    """
    where = "source_path = ?"
    params: tuple = (source_path,)
    if exclude_id is not None:
        where += " AND id != ?"
        params = (source_path, exclude_id)
    game_ids = [
        r[0] for r in conn.execute(f"SELECT id FROM games WHERE {where}", params).fetchall()
    ]
    for game_id in game_ids:
        _delete_game_children(conn, game_id)
    conn.execute(f"DELETE FROM games WHERE {where}", params)


class GamesMixin:
    def get_known_roms(self) -> dict[str, tuple[int, int, bool]]:
        """Return {source_path: (mtime, size_bytes, has_sha1)} for all games with a stored mtime.

        Used by the scanner to skip files that have not changed since the last scan.
        LIBRARY-AUDIT-5: ``has_sha1`` lets a full (non ``--quick``) scan re-hash a
        row that was previously written without one (``--quick`` scan or the ADB
        device scan, both of which always store ``sha1=""``) even when its
        mtime/size haven't changed — otherwise it stays unhashed forever.
        """
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT source_path, mtime, size_bytes, sha1 FROM games WHERE mtime IS NOT NULL"
            ).fetchall()
        return {
            row["source_path"]: (int(row["mtime"]), int(row["size_bytes"]), bool(row["sha1"]))
            for row in rows
        }

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

    def get_unresolved_games(self, include_low_confidence: bool = False) -> list[UnresolvedGame]:
        """Return games that have not yet been matched against a catalog.

        MATCH-FIX-2: ``include_low_confidence=True`` also re-queues rows already
        matched with ``match_confidence = 'low'`` (ambiguous title, possibly
        wrong platform) so a matcher fix can correct them on re-run — otherwise
        they're invisible here forever once ``match_confidence`` is non-NULL.
        """
        where = "match_confidence IS NULL"
        if include_low_confidence:
            where += " OR match_confidence = 'low'"
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT original_filename, source_path, platform, region, sha1
                FROM games
                WHERE {where}
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

    def get_last_apply_batch(self) -> list[dict]:
        """Return the rows from the most recent apply, newest first (MEJ-2 undo).

        All renames from one apply share the same ``created_at`` (set once per
        job, see ``_do_apply``/``cli.py apply``) — that timestamp is the
        natural grouping key for "last batch". Undoing writes new rows via
        ``apply_rename`` (reversed source/target), so a second undo call
        reverses the undo itself instead of silently no-op'ing.
        """
        with self.connect() as connection:
            last = connection.execute(
                "SELECT created_at FROM file_operations "
                "WHERE operation_type = 'rename' ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if not last:
                return []
            rows = connection.execute(
                """
                SELECT id, game_id, source_path, target_path
                FROM file_operations
                WHERE operation_type = 'rename' AND created_at = ?
                ORDER BY id DESC
                """,
                (last["created_at"],),
            ).fetchall()
        return [dict(r) for r in rows]

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

    def get_all_rom_sha1s(self) -> set[str]:
        """Return the set of all non-empty SHA1 hashes for ROM files in the library."""
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT sha1 FROM games WHERE file_type='rom' AND sha1 != '' AND sha1 IS NOT NULL"
            ).fetchall()
        return {row["sha1"].upper() for row in rows}

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
            rows = conn.execute("SELECT source_path FROM games WHERE platform IS NULL").fetchall()

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
        root_prefix = source_root + os.sep

        def _under_root(p: str) -> bool:
            p_lower = p.lower()
            return p_lower == source_root.lower() or p_lower.startswith(root_prefix.lower())

        with self.connect() as conn:
            game_paths = [r[0] for r in conn.execute("SELECT source_path  FROM games").fetchall()]
            save_paths = [r[0] for r in conn.execute("SELECT original_path FROM saves").fetchall()]
            asset_paths = [r[0] for r in conn.execute("SELECT source_path  FROM assets").fetchall()]

        stale_games = [p for p in game_paths if _under_root(p) and p not in seen_paths]
        stale_saves = [p for p in save_paths if _under_root(p) and p not in seen_paths]
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
        """Remove a game record and its metadata/tags/operation history (file must be deleted from disk first)."""
        with self.connect() as connection:
            _delete_game_children(connection, game_id)
            connection.execute("DELETE FROM games WHERE id = ?", (game_id,))
            connection.commit()

    def set_play_status(self, game_id: int, status: str | None) -> None:
        """Set play_status for a game. status: 'playing'|'completed'|'100pct'|'abandoned'|None"""
        with self.connect() as conn:
            conn.execute("UPDATE games SET play_status = ? WHERE id = ?", (status, game_id))
            conn.commit()

    def get_recommendation_candidates(self) -> list[dict]:
        """Rows for the "¿A qué juego hoy?" recommender (MEJ-5).

        Every ROM not already finished — ``completed``/``100pct`` have
        nothing left to recommend. Weighting (status/rating/recency) is the
        caller's job (``services/recommend_service.py``); this just returns
        the columns it needs.
        """
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, original_filename, canonical_title, platform,
                       play_status, user_rating, last_played_at
                FROM games
                WHERE file_type = 'rom'
                  AND (play_status IS NULL OR play_status NOT IN ('completed', '100pct'))
                """
            ).fetchall()
        return [dict(r) for r in rows]

    def get_filter_options(self) -> dict:
        """Return distinct values for advanced filter dropdowns: genres, years, regions, platforms."""
        with self.connect() as conn:
            genres = [
                r[0]
                for r in conn.execute(
                    "SELECT DISTINCT genre FROM game_metadata WHERE genre IS NOT NULL AND genre != '' ORDER BY genre"
                ).fetchall()
            ]
            years = [
                r[0]
                for r in conn.execute(
                    "SELECT DISTINCT year FROM game_metadata WHERE year IS NOT NULL AND year != '' ORDER BY year DESC"
                ).fetchall()
            ]
            regions = [
                r[0]
                for r in conn.execute(
                    "SELECT DISTINCT region FROM games WHERE region IS NOT NULL AND region != '' ORDER BY region"
                ).fetchall()
            ]
            platforms = [
                r[0]
                for r in conn.execute(
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
        initial: str | None = None,
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
            conditions.append("source_path LIKE ? ESCAPE '\\'")
            params.append(escape_like_prefix(source_root.rstrip("/\\")) + "%")
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
            conditions.append("id IN (SELECT game_id FROM game_tags WHERE tag = ?)")
            params.append(tag)
        if region:
            conditions.append("region = ?")
            params.append(region)
        if initial:
            _first_char = "UPPER(SUBSTR(COALESCE(canonical_title, original_filename), 1, 1))"
            if initial == "#":
                conditions.append(f"({_first_char} < 'A' OR {_first_char} > 'Z')")
            else:
                conditions.append(f"{_first_char} = ?")
                params.append(initial[0].upper())

        # genre / year require JOIN with game_metadata
        need_meta = bool(genre or year)
        if genre:
            conditions.append("gm.genre = ?")
            params.append(genre)
        if year:
            conditions.append("gm.year = ?")
            params.append(year)

        table_expr = (
            "games g LEFT JOIN game_metadata gm ON gm.game_id = g.id" if need_meta else "games"
        )
        # Rewrite conditions that reference bare column names when we alias
        if need_meta:
            conditions = [
                c
                if c.startswith("gm.")
                else c.replace("file_type", "g.file_type")
                .replace("platform", "g.platform")
                .replace("canonical_title", "g.canonical_title")
                .replace("original_filename", "g.original_filename")
                .replace("source_path", "g.source_path")
                .replace("play_status", "g.play_status")
                .replace("is_favorite", "g.is_favorite")
                .replace("region", "g.region")
                .replace("id IN", "g.id IN")
                for c in conditions
            ]

        where_sql = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        _order = (
            {
                "year": "gm.year DESC, g.platform, g.canonical_title, g.original_filename",
                "last_played": "g.last_played_at DESC, g.platform, g.canonical_title",
                "added": "g.created_at DESC, g.platform, g.canonical_title",
                "title": "g.canonical_title, g.original_filename",
                "platform": "g.platform, g.canonical_title, g.original_filename",
            }.get(sort_by or "", "g.platform, g.canonical_title, g.original_filename")
            if need_meta
            else {
                "year": "(SELECT year FROM game_metadata WHERE game_id=id) DESC, platform, canonical_title",
                "last_played": "last_played_at DESC, platform, canonical_title",
                "added": "created_at DESC, platform, canonical_title",
                "title": "canonical_title, original_filename",
                "platform": "platform, canonical_title, original_filename",
            }.get(sort_by or "", "platform, canonical_title, original_filename")
        )

        id_col = "g.id" if need_meta else "id"
        count_sql = f"SELECT COUNT(*) AS cnt FROM {table_expr} " + where_sql
        select_sql = (
            (
                f"SELECT {id_col} AS id, g.original_filename, g.source_path, g.platform, g.region,"
                " g.extension, g.size_bytes, g.sha1, g.md5, g.canonical_title,"
                " g.match_confidence, g.catalog_source, g.play_status, g.last_played_at,"
                f" g.is_favorite, g.notes, g.user_rating, g.play_count, g.first_played_at,"
                " g.playtime_minutes_pc, g.playtime_minutes_android, g.created_at,"
                " EXISTS(SELECT 1 FROM game_tags WHERE game_id = g.id AND tag = 'anbernic') AS is_anbernic,"
                " gm.genre, gm.year AS meta_year, gm.publisher"
                f" FROM {table_expr} " + where_sql + f" ORDER BY {_order} LIMIT ? OFFSET ?"
            )
            if need_meta
            else (
                "SELECT id, original_filename, source_path, platform, region,"
                " extension, size_bytes, sha1, md5, canonical_title,"
                " match_confidence, catalog_source, play_status, last_played_at,"
                " is_favorite, notes, user_rating, play_count, first_played_at,"
                " playtime_minutes_pc, playtime_minutes_android, created_at,"
                " EXISTS(SELECT 1 FROM game_tags WHERE game_id = games.id AND tag = 'anbernic') AS is_anbernic"
                " FROM games " + where_sql + f" ORDER BY {_order} LIMIT ? OFFSET ?"
            )
        )

        with self.connect() as connection:
            total = int(connection.execute(count_sql, params).fetchone()["cnt"])
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
                "md5": row["md5"],
                "canonical_title": row["canonical_title"],
                "match_confidence": row["match_confidence"],
                "catalog_source": row["catalog_source"],
                "play_status": row["play_status"],
                "last_played_at": row["last_played_at"],
                "is_favorite": bool(row["is_favorite"]),
                "notes": row["notes"],
                "user_rating": row["user_rating"],
                "play_count": row["play_count"] or 0,
                "first_played_at": row["first_played_at"],
                "created_at": row["created_at"],
                "is_anbernic": bool(row["is_anbernic"]),
                **(
                    {"genre": row["genre"], "year": row["meta_year"], "publisher": row["publisher"]}
                    if "genre" in _keys
                    else {}
                ),
            }
            for row in rows
        ]
        return games, total

    def sha1_exists(self, sha1: str) -> bool:
        """Return True if *sha1* is already present in the games table."""
        with self.connect() as conn:
            return bool(
                conn.execute(
                    "SELECT EXISTS(SELECT 1 FROM games WHERE sha1 = ?)", (sha1.upper(),)
                ).fetchone()[0]
            )
