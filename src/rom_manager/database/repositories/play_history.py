"""Play-history aggregate: record play sessions from synced saves.

Mixed into :class:`~rom_manager.database.repository.LibraryRepository`; relies on
``connect`` from ``_RepositoryBase``.

SAGE-2 — contrato de ``game_metadata.genres_list``/``players`` (consumidos por
``GET /api/export-history`` en ``web/handlers/play_history.py``):
    genres_list  TEXT  todos los géneros de ScreenScraper separados por coma
                        (``genre`` solo guarda el primero). Poblado por
                        ``upsert_metadata()`` en cada (re-)scrape; para filas
                        scrapeadas antes de esta migración, backfill único
                        desde ``genre`` (``_migrate_genres_list_backfill`` en
                        ``database/schema.py``) — no es la lista completa
                        real hasta que el juego se re-scrapee.
    players      TEXT  nº de jugadores tal cual lo reporta ScreenScraper
                        (p.ej. ``"1-2"``). Sin fuente local para backfill —
                        queda NULL en filas scrapeadas antes de esta
                        migración hasta que se re-scrapeen.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


class PlayHistoryMixin:
    def record_play_session(
        self,
        save_path: str | Path,
        timestamp: str,
        connection: sqlite3.Connection | None = None,
    ) -> bool:
        """Increment play_count for the game matching *save_path* stem.

        Matches by canonical_title first, then by original_filename stem (case-insensitive).
        Sets first_played_at on the first session. Updates last_played_at always.

        Returns True if a matching game was found and updated, False otherwise.
        """
        stem = Path(save_path).stem

        def _run(conn: sqlite3.Connection) -> bool:
            row = conn.execute(
                """
                SELECT id FROM games
                WHERE LOWER(canonical_title) = LOWER(?)
                   OR LOWER(SUBSTR(original_filename, 1, LENGTH(original_filename) - LENGTH(extension))) = LOWER(?)
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
            return True

        if connection is not None:
            return _run(connection)
        with self.connect() as conn:
            found = _run(conn)
            if found:
                conn.commit()
            return found

    def set_playtime_minutes(
        self,
        rom_stem: str,
        minutes: int,
        origin: str,
        last_played: str | None = None,
        connection: sqlite3.Connection | None = None,
    ) -> bool:
        """Upsert per-origin playtime for the game matching *rom_stem* (JUEGOS-UX-5/6).

        *origin* is ``"pc"`` or ``"android"`` — each origin owns its own counter
        so PC and Android minutes can be summed without double-counting.
        RetroArch ``.lrtl`` runtimes are cumulative totals, so the stored value
        is ``MAX(existing, new)`` — it never decreases (regla del proyecto:
        ante duda, no sobreescribir). ``last_played_at`` only moves forward.

        Returns True if a matching game was found and updated.
        """
        if origin not in ("pc", "android"):
            raise ValueError(f"origin must be 'pc' or 'android', got {origin!r}")
        col = f"playtime_minutes_{origin}"

        def _run(conn: sqlite3.Connection) -> bool:
            row = conn.execute(
                """
                SELECT id FROM games
                WHERE LOWER(canonical_title) = LOWER(?)
                   OR LOWER(SUBSTR(original_filename, 1, LENGTH(original_filename) - LENGTH(extension))) = LOWER(?)
                LIMIT 1
                """,
                (rom_stem, rom_stem),
            ).fetchone()
            if row is None:
                return False
            conn.execute(
                f"""
                UPDATE games
                SET {col} = MAX(COALESCE({col}, 0), ?),
                    last_played_at = NULLIF(MAX(COALESCE(last_played_at, ''), COALESCE(?, '')), ''),
                    first_played_at = COALESCE(first_played_at, ?)
                WHERE id = ?
                """,  # noqa: S608 — col validado arriba contra {'pc','android'}
                (int(minutes), last_played, last_played, row[0]),
            )
            return True

        if connection is not None:
            return _run(connection)
        with self.connect() as conn:
            found = _run(conn)
            if found:
                conn.commit()
            return found
