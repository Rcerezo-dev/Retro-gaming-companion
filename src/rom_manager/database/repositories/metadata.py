"""Metadata aggregate: tags, favorites, notes, NLP export and ScreenScraper data.

Mixed into :class:`~rom_manager.database.repository.LibraryRepository`; relies on
``connect``/``batch`` from ``_RepositoryBase``.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from rom_manager.utils.time import utc_now


class MetadataMixin:
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
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S")
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

    def add_tag_bulk(self, game_ids: list[int], tag: str) -> int:
        """Add *tag* to many games in one transaction (idempotent). Returns len(game_ids)."""
        tag = tag.strip().lower()
        if not tag or not game_ids:
            return 0
        with self.batch() as conn:
            conn.executemany(
                "INSERT OR IGNORE INTO game_tags (game_id, tag) VALUES (?, ?)",
                [(gid, tag) for gid in game_ids],
            )
        return len(game_ids)

    def remove_tag_bulk(self, game_ids: list[int], tag: str) -> int:
        """Remove *tag* from many games in one transaction. Returns len(game_ids)."""
        tag = tag.strip().lower()
        if not tag or not game_ids:
            return 0
        with self.batch() as conn:
            conn.executemany(
                "DELETE FROM game_tags WHERE game_id = ? AND tag = ?",
                [(gid, tag) for gid in game_ids],
            )
        return len(game_ids)

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
            rows = conn.execute("SELECT DISTINCT tag FROM game_tags ORDER BY tag").fetchall()
        return [r["tag"] for r in rows]

    def set_notes(self, game_id: int, notes: str | None) -> None:
        with self.connect() as conn:
            conn.execute("UPDATE games SET notes = ? WHERE id = ?", (notes or None, game_id))
            conn.commit()

    def set_canonical_title(self, game_id: int, title: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE games SET canonical_title = ? WHERE id = ?",
                (title.strip() or None, game_id),
            )
            conn.commit()

    def upsert_metadata_manual(self, game_id: int, **fields: str) -> None:
        """Update individual metadata fields manually without overwriting unrelated scraped data."""
        _ALLOWED = {"year", "genre", "publisher", "developer", "description", "rating"}
        updates = {k: v for k, v in fields.items() if k in _ALLOWED}
        if not updates:
            return

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
        genres_list: str = "",
        players: str = "",
        connection: sqlite3.Connection,
    ) -> None:
        connection.execute(
            """
            INSERT INTO game_metadata
                (game_id, ss_game_id, title, year, genre, publisher, developer,
                 description, rating, box_art_url, box_art_path, scraped_at,
                 screenshot_path, wheel_path, genres_list, players)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(game_id) DO UPDATE SET
                ss_game_id=excluded.ss_game_id, title=excluded.title,
                year=excluded.year, genre=excluded.genre,
                publisher=excluded.publisher, developer=excluded.developer,
                description=excluded.description, rating=excluded.rating,
                box_art_url=excluded.box_art_url, box_art_path=excluded.box_art_path,
                scraped_at=excluded.scraped_at,
                screenshot_path=excluded.screenshot_path,
                wheel_path=excluded.wheel_path,
                genres_list=excluded.genres_list,
                players=excluded.players
            """,
            (
                game_id,
                ss_game_id,
                title,
                year,
                genre,
                publisher,
                developer,
                description,
                rating,
                box_art_url,
                box_art_path,
                scraped_at,
                screenshot_path,
                wheel_path,
                genres_list,
                players,
            ),
        )

    def update_image_paths(
        self,
        *,
        game_id: int,
        box_art_path: str = "",
        connection: sqlite3.Connection,
    ) -> None:
        """Update only the local cover path for an existing metadata row.
        Used when downloading images that were previously skipped (no API call needed)."""
        connection.execute(
            "UPDATE game_metadata SET box_art_path = ? WHERE game_id = ?",
            (box_art_path, game_id),
        )

    def mark_metadata_scraped(self, game_id: int, connection: sqlite3.Connection) -> None:
        """DB-1: Mark a game as checked for metadata (success or failure).
        Prevents re-scraping files that were already checked but had no match."""
        connection.execute("UPDATE games SET metadata_scraped = 1 WHERE id = ?", (game_id,))

    def get_games_for_scraping(
        self, platform: str | None = None, missing_descriptions: bool = False
    ) -> list[dict]:
        """Return games that have no metadata yet and haven't been checked, with their hashes.
        DB-1: Excludes games where metadata_scraped=1 (checked but no match found).

        SAGE-1: with *missing_descriptions* also includes games that already have a
        metadata row but an empty description (re-scrape to fill it). ``has_metadata``
        tells the caller which upsert path to use so existing image paths survive.
        """
        pending = "(m.id IS NULL AND (g.metadata_scraped IS NULL OR g.metadata_scraped = 0))"
        if missing_descriptions:
            pending += " OR (m.id IS NOT NULL AND (m.description IS NULL OR m.description = ''))"
        sql = f"""
            SELECT g.id, g.original_filename, g.source_path, g.platform,
                   g.crc32, g.md5, g.sha1, g.size_bytes, g.canonical_title,
                   (m.id IS NOT NULL) AS has_metadata
            FROM games g
            LEFT JOIN game_metadata m ON m.game_id = g.id
            WHERE ({pending})
        """
        params: list = []
        if platform:
            sql += " AND g.platform = ?"
            params.append(platform)
        sql += " ORDER BY g.platform, g.original_filename"
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def update_description(
        self,
        *,
        game_id: int,
        description: str,
        scraped_at: str,
        connection: sqlite3.Connection,
    ) -> None:
        """SAGE-1: fill only the description of an existing metadata row.
        Avoids the full upsert, which would wipe local image paths."""
        connection.execute(
            "UPDATE game_metadata SET description = ?, scraped_at = ? WHERE game_id = ?",
            (description, scraped_at, game_id),
        )

    def get_description_coverage(self) -> dict:
        """SAGE-1: % of ROMs with a non-empty description (done when > 90%)."""
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS total,
                       COALESCE(SUM(m.description IS NOT NULL AND m.description != ''), 0)
                           AS with_description
                FROM games g
                LEFT JOIN game_metadata m ON m.game_id = g.id
                WHERE g.file_type = 'rom'
                """
            ).fetchone()
        total = row["total"]
        with_desc = row["with_description"]
        return {
            "total": total,
            "with_description": with_desc,
            "pct": round(100 * with_desc / total, 1) if total else 0.0,
        }

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
            {
                "platform": r["platform"],
                "total": r["total"],
                "scraped": r["scraped"],
                "missing": r["total"] - r["scraped"],
            }
            for r in rows
        ]
