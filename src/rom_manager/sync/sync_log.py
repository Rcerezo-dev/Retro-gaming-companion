from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SYNC_LOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS save_sync_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    local_path      TEXT NOT NULL,
    remote_path     TEXT NOT NULL,
    direction       TEXT NOT NULL,
    local_mtime     TEXT,
    remote_mtime    TEXT,
    result          TEXT NOT NULL,
    message         TEXT,
    created_at      TEXT NOT NULL,
    verified        INTEGER
)
"""

SYNC_LOG_INDEX = """
CREATE INDEX IF NOT EXISTS idx_sync_log_local ON save_sync_log (local_path)
"""


def ensure_sync_log_schema(connection: sqlite3.Connection) -> None:
    """Create the save_sync_log table if it doesn't exist."""
    connection.execute(SYNC_LOG_SCHEMA)
    connection.execute(SYNC_LOG_INDEX)
    try:
        connection.execute("ALTER TABLE save_sync_log ADD COLUMN verified INTEGER")
    except sqlite3.OperationalError:
        pass  # la columna ya existe (AUD-2)
    connection.commit()


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class SyncLogEntry:
    id: int
    local_path: str
    remote_path: str
    direction: str  # 'upload' | 'download' | 'conflict'
    local_mtime: str | None
    remote_mtime: str | None
    result: str  # 'ok' | 'error' | 'skipped'
    message: str | None
    created_at: str
    verified: int | None = None  # AUD-2: 1 = MD5 comprobado tras la transferencia


# ---------------------------------------------------------------------------
# Repository helpers
# ---------------------------------------------------------------------------


def log_sync_event(
    connection: sqlite3.Connection,
    *,
    local_path: str,
    remote_path: str,
    direction: str,
    local_mtime: datetime | None,
    remote_mtime: datetime | None,
    result: str,
    message: str | None = None,
    created_at: str,
    verified: bool | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO save_sync_log
            (local_path, remote_path, direction,
             local_mtime, remote_mtime, result, message, created_at, verified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            local_path,
            remote_path,
            direction,
            local_mtime.strftime("%Y-%m-%dT%H:%M:%S") if local_mtime else None,
            remote_mtime.strftime("%Y-%m-%dT%H:%M:%S") if remote_mtime else None,
            result,
            message,
            created_at,
            1 if verified else (0 if verified is False else None),
        ),
    )


def adb_sync_log_entry(
    local_path: str,
    remote_path: str,
    direction: str,
    result: str,
    message: str | None,
    verified: bool | None,
) -> dict:
    """Entrada (kwargs de log_sync_event) para una transferencia ADB de un save (AUD-2)."""
    return {
        "local_path": local_path,
        "remote_path": remote_path,
        "direction": direction,
        "local_mtime": None,
        "remote_mtime": None,
        "result": result,
        "message": message,
        "created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S"),
        "verified": verified,
    }


def write_sync_log_entries(repository, entries: list[dict]) -> None:
    """Vuelca entradas acumuladas a save_sync_log en una sola transacción.

    *repository* solo necesita ``.connect()``; los fallos se tragan con warning —
    el log nunca debe romper un sync ya completado.
    """
    if not entries:
        return
    import logging

    try:
        with repository.connect() as conn:
            for e in entries:
                log_sync_event(conn, **e)
            conn.commit()
    except Exception:
        logging.getLogger(__name__).warning("No se pudo escribir en save_sync_log", exc_info=True)


def get_last_sync(
    connection: sqlite3.Connection,
    local_path: str,
) -> datetime | None:
    """Return the UTC datetime of the last successful sync for *local_path*, or None."""
    row = connection.execute(
        """
        SELECT created_at FROM save_sync_log
        WHERE local_path = ? AND result = 'ok'
        ORDER BY id DESC
        LIMIT 1
        """,
        (local_path,),
    ).fetchone()
    if row is None:
        return None
    raw = row[0]
    return datetime.fromisoformat(raw).replace(tzinfo=UTC)
