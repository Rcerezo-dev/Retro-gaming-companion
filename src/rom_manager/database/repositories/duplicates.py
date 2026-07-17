"""Duplicates aggregate: SHA1/title duplicate detection plus the wishlist.

Mixed into :class:`~rom_manager.database.repository.LibraryRepository`; relies on
``connect``/``batch`` from ``_RepositoryBase``.
"""

from __future__ import annotations

from datetime import UTC, datetime

from rom_manager.database.repositories.models import DuplicateEntry, DuplicateGroup


class DuplicatesMixin:
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
            groups[key].append(
                {
                    "id": row["id"],
                    "original_filename": row["original_filename"],
                    "source_path": row["source_path"],
                    "platform": row["platform"],
                    "canonical_title": row["canonical_title"],
                    "size_bytes": int(row["size_bytes"]),
                    "sha1": row["sha1"],
                }
            )
        return [
            {"platform": k[0], "canonical_title": k[1], "entries": v} for k, v in groups.items()
        ]

    def exclude_duplicate_sha1(self, sha1: str, reason: str = "intentional_copy") -> None:
        """Mark a SHA1 group as an intentional copy — it will no longer appear as a duplicate."""
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S")
        with self.connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO excluded_duplicates (sha1, reason, created_at) VALUES (?, ?, ?)",
                (sha1, reason, now),
            )
            conn.commit()

    def get_excluded_duplicates(self) -> list[dict]:
        """Return excluded SHA1 groups with a representative title/platform (DUPLICADOS-UX-5)."""
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT e.sha1, e.reason, e.created_at,
                       MAX(g.canonical_title) AS canonical_title,
                       MAX(g.original_filename) AS original_filename,
                       MAX(g.platform) AS platform
                FROM excluded_duplicates e
                LEFT JOIN games g ON g.sha1 = e.sha1
                GROUP BY e.sha1
                ORDER BY e.created_at DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def remove_excluded_duplicate(self, sha1: str) -> None:
        """Remove a SHA1 from the exclusion list — the group reappears as a duplicate."""
        with self.connect() as conn:
            conn.execute("DELETE FROM excluded_duplicates WHERE sha1=?", (sha1,))
            conn.commit()

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
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S")
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
