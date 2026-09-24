"""Blocklist aggregate: permanent per-SHA1 exclusion (GAME-BLOCKLIST-1).

Keyed by sha1, not game_id -- a game_id doesn't survive the file being
deleted and reappearing later (fresh row, new id after a sync/adb pull),
but its content hash does. Each ``LibraryRepository`` (PC and Android are
separate SQLite DBs) carries its own ``blocklist`` table; the mark is
applied to both explicitly by the caller (``services/storage_service.py``),
same as ``game_tags``/``excluded_duplicates`` are per-repository already.
"""

from __future__ import annotations

from datetime import UTC, datetime


class BlocklistMixin:
    def block_sha1(self, sha1: str, canonical_title: str = "", reason: str = "") -> None:
        """Mark *sha1* as permanently excluded (idempotent)."""
        sha1 = (sha1 or "").strip().upper()
        if not sha1:
            return
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S")
        with self.connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO blocklist (sha1, canonical_title, reason, created_at) "
                "VALUES (?, ?, ?, ?)",
                (sha1, canonical_title or None, reason or None, now),
            )
            conn.commit()

    def is_blocked(self, sha1: str) -> bool:
        sha1 = (sha1 or "").strip().upper()
        if not sha1:
            return False
        with self.connect() as conn:
            row = conn.execute("SELECT 1 FROM blocklist WHERE sha1 = ?", (sha1,)).fetchone()
        return row is not None

    def get_blocklist(self) -> list[dict]:
        """Return all blocked SHA1s, most recently blocked first."""
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT sha1, canonical_title, reason, created_at FROM blocklist "
                "ORDER BY created_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]
