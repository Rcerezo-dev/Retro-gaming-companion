"""Connection management and scan-run bookkeeping shared by all repository mixins.

``_RepositoryBase`` owns ``database_path`` and the ``connect``/``batch`` context
managers; every aggregate mixin relies on those. It also holds the scan-run
lifecycle (`create_scan_run`/`complete_scan_run`) and the library-wide
`get_summary`, which span every table and so belong to no single aggregate.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from rom_manager.database.repositories.models import ScanSummary
from rom_manager.database.schema import initialize_database


def escape_like_prefix(prefix: str) -> str:
    """Escape *prefix* for a ``LIKE ? ESCAPE '\\'`` "starts with" pattern.

    Backslashes must be escaped first: on Windows *prefix* already uses
    ``\\`` as the path separator, which would otherwise collide with the
    escape character itself. Caller appends the trailing ``%`` wildcard.
    """
    return prefix.replace("\\", "\\\\").replace("%", "%%").replace("_", "\\_")


class _RepositoryBase:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            initialize_database(connection)

    def _open_conn(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=30000")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = self._open_conn()
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def batch(self) -> Iterator[sqlite3.Connection]:
        """Single open connection for bulk writes. Commits once on exit, rolls back on error."""
        connection = self._open_conn()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def backup_database(self, keep_n: int = 5) -> Path:
        """Snapshot the live database before a risky write (e.g. apply).

        Uses ``sqlite3.Connection.backup()`` rather than a raw file copy so a
        concurrent WAL writer can't produce a torn snapshot. Prunes older
        backups, keeping at most *keep_n*.
        """
        backup_dir = self.database_path.parent / "db-backup"
        backup_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        dest = backup_dir / f"{self.database_path.stem}.{ts}.db"
        with self.connect() as source, sqlite3.connect(dest) as target:
            source.backup(target)
        backups = sorted(backup_dir.glob(f"{self.database_path.stem}.*.db"), reverse=True)
        for old in backups[keep_n:]:
            old.unlink(missing_ok=True)
        return dest

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

    def get_summary(self, source_root: str | None = None) -> ScanSummary:
        """Return library-wide counts.

        When *source_root* is provided only rows whose ``source_path`` starts
        with that prefix are counted (used to get per-device stats).
        """
        prefix = source_root.rstrip("/\\") if source_root else None
        with self.connect() as connection:
            if prefix:
                like = escape_like_prefix(prefix) + "%"
                games_count = connection.execute(
                    "SELECT COUNT(*) AS count FROM games WHERE source_path LIKE ? ESCAPE '\\'",
                    (like,),
                ).fetchone()["count"]
                saves_count = connection.execute(
                    "SELECT COUNT(*) AS count FROM saves WHERE original_path LIKE ? ESCAPE '\\'",
                    (like,),
                ).fetchone()["count"]
                assets_count = connection.execute(
                    "SELECT COUNT(*) AS count FROM assets WHERE source_path LIKE ? ESCAPE '\\'",
                    (like,),
                ).fetchone()["count"]
            else:
                games_count = connection.execute("SELECT COUNT(*) AS count FROM games").fetchone()[
                    "count"
                ]
                saves_count = connection.execute("SELECT COUNT(*) AS count FROM saves").fetchone()[
                    "count"
                ]
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
