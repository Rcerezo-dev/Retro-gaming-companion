"""Assets aggregate: media rows plus per-platform asset/orphan statistics.

Mixed into :class:`~rom_manager.database.repository.LibraryRepository`; relies on
``connect``/``batch`` from ``_RepositoryBase``.
"""

from __future__ import annotations

import sqlite3

from rom_manager.database.repositories.base import escape_like_prefix
from rom_manager.utils.media_types import IMAGE_EXTS, VIDEO_EXTS


class AssetsMixin:
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

    def get_asset_platform_stats(self, source_root: str | None = None) -> list[dict]:
        """Return per-platform asset counts (images, videos, XML/gamelists).

        Also includes rom_count from the games table and orphan asset count
        (assets in platforms that have no games).

        *source_root* filters to only entries whose source_path starts with that prefix.
        """
        # REV43-39: asset_type se guarda sin punto — deriva del set canónico en vez de duplicarlo.
        _IMAGE_EXTS = {e.lstrip(".") for e in IMAGE_EXTS}
        _VIDEO_EXTS = {e.lstrip(".") for e in VIDEO_EXTS}

        prefix = escape_like_prefix(source_root.rstrip("/\\")) + "%" if source_root else None

        with self.connect() as connection:
            if prefix:
                game_rows = connection.execute(
                    "SELECT platform, COUNT(*) AS cnt FROM games WHERE source_path LIKE ? ESCAPE '\\' GROUP BY platform",
                    (prefix,),
                ).fetchall()
                asset_rows = connection.execute(
                    "SELECT platform, asset_type, COUNT(*) AS cnt FROM assets WHERE source_path LIKE ? ESCAPE '\\' GROUP BY platform, asset_type",
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
            result.append(
                {
                    "platform": plat,
                    "rom_count": g,
                    "image_count": a["images"],
                    "video_count": a["videos"],
                    "xml_count": a["xml"],
                    "orphan_assets": a["images"] + a["videos"] + a["xml"] + a["other"]
                    if g == 0
                    else 0,
                }
            )
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

    def get_orphan_assets(
        self, *, platform: str | None = None, source_root: str | None = None
    ) -> list[dict]:
        """Return assets in platforms that have no games.

        *source_root* filters to only entries whose source_path starts with that prefix,
        mirroring :meth:`get_asset_platform_stats` so the counts shown in the Assets tab
        match the files returned here for the same device root.
        """
        prefix = escape_like_prefix(source_root.rstrip("/\\")) + "%" if source_root else None
        with self.connect() as connection:
            if platform:
                sql = """
                    SELECT id, source_path, platform, asset_type
                    FROM assets
                    WHERE platform = ?
                      AND (platform NOT IN (SELECT DISTINCT platform FROM games WHERE platform IS NOT NULL)
                           OR platform IS NULL)
                    """
                params: tuple = (platform,)
            else:
                sql = """
                    SELECT id, source_path, platform, asset_type
                    FROM assets
                    WHERE (platform NOT IN (SELECT DISTINCT platform FROM games WHERE platform IS NOT NULL)
                           OR platform IS NULL)
                    """
                params = ()
            if prefix:
                sql += " AND source_path LIKE ? ESCAPE '\\'"
                params += (prefix,)
            sql += " ORDER BY platform, source_path"
            rows = connection.execute(sql, params).fetchall()
        return [
            {
                "id": row["id"],
                "source_path": row["source_path"],
                "platform": row["platform"],
                "asset_type": row["asset_type"],
            }
            for row in rows
        ]
