"""Saves aggregate: save rows and the save-sync log.

Mixed into :class:`~rom_manager.database.repository.LibraryRepository`; relies on
``connect``/``batch`` from ``_RepositoryBase``.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC
from pathlib import Path


class SyncMixin:
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
        from datetime import datetime

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
                    local_mtime = datetime.fromtimestamp(Path(sp).stat().st_mtime, tz=UTC).strftime(
                        "%Y-%m-%dT%H:%M:%S"
                    )
                except (OSError, ValueError):
                    pass
                results.append(
                    {
                        "title": g["canonical_title"] or g["original_filename"],
                        "filename": g["original_filename"],
                        "platform": g["platform"],
                        "local_path": sp,
                        "local_mtime": local_mtime,
                        "db_updated": g["updated_at"],
                        "last_sync_at": sync["created_at"] if sync else None,
                        "last_direction": sync["direction"] if sync else None,
                        "last_result": sync["result"] if sync else None,
                    }
                )
        return results
