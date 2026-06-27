"""Play-history aggregate: record play sessions from synced saves.

Mixed into :class:`~rom_manager.database.repository.LibraryRepository`; relies on
``connect`` from ``_RepositoryBase``.
"""

from __future__ import annotations

from pathlib import Path


class PlayHistoryMixin:
    def record_play_session(self, save_path: str | Path, timestamp: str) -> bool:
        """Increment play_count for the game matching *save_path* stem.

        Matches by canonical_title first, then by original_filename stem (case-insensitive).
        Sets first_played_at on the first session. Updates last_played_at always.

        Returns True if a matching game was found and updated, False otherwise.
        """
        stem = Path(save_path).stem
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT id FROM games
                WHERE LOWER(canonical_title) = LOWER(?)
                   OR LOWER(SUBSTR(original_filename, 1, LENGTH(original_filename) - LENGTH(extension) - 1)) = LOWER(?)
                LIMIT 1
                """,
                (stem, stem),
            ).fetchone()

            if row is None:
                return False

            conn.execute(
                """
                UPDATE games
                SET play_count      = play_count + 1,
                    last_played_at  = ?,
                    first_played_at = COALESCE(first_played_at, ?)
                WHERE id = ?
                """,
                (timestamp, timestamp, row[0]),
            )
            conn.commit()
        return True
