from __future__ import annotations

import logging
import re
import sqlite3

_logger = logging.getLogger(__name__)

# Whitelist para ALTER TABLE — evita f-strings sin validación sobre nombres de columna/tipo.
_COL_NAME_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
_ALLOWED_COL_TYPES = frozenset({"TEXT", "INTEGER", "REAL", "BLOB", "NUMERIC"})


SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS scan_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_root TEXT NOT NULL,
        started_at TEXT NOT NULL,
        finished_at TEXT,
        files_seen INTEGER NOT NULL DEFAULT 0,
        roms_detected INTEGER NOT NULL DEFAULT 0,
        saves_detected INTEGER NOT NULL DEFAULT 0,
        assets_detected INTEGER NOT NULL DEFAULT 0,
        system_files_detected INTEGER NOT NULL DEFAULT 0,
        unknown_files_detected INTEGER NOT NULL DEFAULT 0,
        errors INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_filename TEXT NOT NULL,
        source_path TEXT NOT NULL UNIQUE,
        platform TEXT,
        file_type TEXT NOT NULL DEFAULT 'rom',
        relative_parent TEXT,
        region TEXT,
        extension TEXT NOT NULL,
        size_bytes INTEGER NOT NULL,
        sha1 TEXT NOT NULL,
        md5 TEXT NOT NULL,
        crc32 TEXT NOT NULL,
        set_type TEXT,
        mtime INTEGER,
        canonical_title TEXT,
        match_confidence TEXT,
        catalog_source TEXT,
        play_status TEXT,
        last_played_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        is_favorite INTEGER NOT NULL DEFAULT 0,
        notes TEXT,
        user_rating INTEGER,
        first_played_at TEXT,
        play_count INTEGER NOT NULL DEFAULT 0,
        metadata_scraped INTEGER DEFAULT 0
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_games_sha1 ON games (sha1)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_games_md5 ON games (md5)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_games_platform ON games (platform)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_games_file_type ON games (file_type)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_games_last_played ON games (last_played_at)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_games_canonical_title ON games (canonical_title)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_games_play_status ON games (play_status)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_games_match_confidence ON games (match_confidence)
    """,
    """
    CREATE TABLE IF NOT EXISTS saves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_path TEXT NOT NULL UNIQUE,
        relative_parent TEXT,
        extension TEXT NOT NULL,
        size_bytes INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        game_id INTEGER REFERENCES games (id) ON DELETE SET NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_path TEXT NOT NULL UNIQUE,
        relative_parent TEXT,
        platform TEXT,
        asset_type TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS file_operations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id INTEGER,
        operation_type TEXT NOT NULL,
        source_path TEXT NOT NULL,
        target_path TEXT,
        result TEXT NOT NULL,
        message TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (game_id) REFERENCES games (id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_file_operations_game ON file_operations (game_id)
    """,
    """
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
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_sync_log_local ON save_sync_log (local_path)
    """,
    """
    CREATE TABLE IF NOT EXISTS game_metadata (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id         INTEGER NOT NULL UNIQUE,
        ss_game_id      TEXT,
        title           TEXT,
        year            TEXT,
        genre           TEXT,
        publisher       TEXT,
        developer       TEXT,
        description     TEXT,
        rating          TEXT,
        box_art_url     TEXT,
        box_art_path    TEXT,
        scraped_at      TEXT NOT NULL,
        FOREIGN KEY (game_id) REFERENCES games (id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_game_metadata_game ON game_metadata (game_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS game_tags (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id INTEGER NOT NULL,
        tag     TEXT NOT NULL,
        FOREIGN KEY (game_id) REFERENCES games (id),
        UNIQUE (game_id, tag)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_game_tags_game ON game_tags (game_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_game_tags_tag ON game_tags (tag)
    """,
    """
    CREATE TABLE IF NOT EXISTS excluded_duplicates (
        sha1        TEXT NOT NULL PRIMARY KEY,
        reason      TEXT NOT NULL DEFAULT 'intentional_copy',
        created_at  TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS wishlist (
        sha1        TEXT NOT NULL PRIMARY KEY,
        title       TEXT NOT NULL,
        platform    TEXT NOT NULL DEFAULT '',
        region      TEXT,
        year        TEXT,
        status      TEXT NOT NULL DEFAULT 'searching',
        dat_source  TEXT,
        created_at  TEXT NOT NULL,
        updated_at  TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_wishlist_platform ON wishlist (platform)
    """,
)

# Columns added after the initial schema that may be missing in existing databases.
# New DBs already have these columns in the CREATE TABLE statement above;
# the migration is a no-op for them but keeps old databases up to date.
_GAMES_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("canonical_title", "TEXT"),
    ("match_confidence", "TEXT"),
    ("catalog_source", "TEXT"),
    ("mtime", "INTEGER"),
    ("play_status", "TEXT"),
    ("last_played_at", "TEXT"),
    ("is_favorite", "INTEGER"),
    ("notes", "TEXT"),
    ("metadata_scraped", "INTEGER"),  # DB-1: boolean flag for metadata cache
    ("user_rating", "INTEGER"),  # NLP-REC: rating 1-5 por el usuario
    ("first_played_at", "TEXT"),  # NLP-REC: primera vez jugado
    ("play_count", "INTEGER"),  # NLP-REC: número de sesiones detectadas vía saves
)

_ASSETS_MIGRATIONS: tuple[tuple[str, str], ...] = ()

_SAVES_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("game_id", "INTEGER"),  # DB-FIX-4: FK → games.id (declarative; enforced at app layer)
)

_SYNC_LOG_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("verified", "INTEGER"),  # AUD-2: post-transfer integrity check passed
)

_METADATA_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("screenshot_path", "TEXT"),  # B6-7: local path to downloaded screenshot
    ("wheel_path", "TEXT"),  # B6-7: local path to downloaded wheel/logo
)

# Columns that existed in old schema but are now removed (DB-FIX-3).
# Dropped on first run if still present — safe for SQLite 3.35+ (Python 3.12 ships 3.39+).
_DEPRECATED_COLUMNS: tuple[tuple[str, str], ...] = (
    ("games", "status"),  # NOT NULL DEFAULT 'scanned', never read/written
    ("games", "library_path"),  # never used
    ("assets", "game_id"),  # never written by upsert_asset()
)


def initialize_database(connection: sqlite3.Connection) -> None:
    cursor = connection.cursor()
    for statement in SCHEMA_STATEMENTS:
        cursor.execute(statement)
    _migrate_games_columns(cursor)
    _migrate_saves_columns(cursor)
    _migrate_assets_columns(cursor)
    _migrate_metadata_columns(cursor)
    _migrate_sync_log_columns(cursor)
    _migrate_is_favorite_default(cursor)
    _drop_deprecated_columns(cursor)
    connection.commit()


def _migrate_is_favorite_default(cursor: sqlite3.Cursor) -> None:
    """Ensure is_favorite has a default value of 0 for existing rows where it is NULL."""
    try:
        cursor.execute("UPDATE games SET is_favorite = 0 WHERE is_favorite IS NULL")
    except Exception:
        _logger.debug("Could not backfill is_favorite default", exc_info=True)


def _alter_table_add_column(
    cursor: sqlite3.Cursor, table: str, col_name: str, col_type: str
) -> None:
    """Execute ALTER TABLE ... ADD COLUMN with validated identifiers (no f-string injection risk)."""
    if not _COL_NAME_RE.match(col_name):
        raise ValueError(f"Invalid column name: {col_name!r}")
    if col_type not in _ALLOWED_COL_TYPES:
        raise ValueError(f"Invalid column type: {col_type!r}")
    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")  # noqa: S608 — identifiers validated above


def _drop_deprecated_columns(cursor: sqlite3.Cursor) -> None:
    """Drop columns that were declared in old schema but never used (DB-FIX-3)."""
    for table, col in _DEPRECATED_COLUMNS:
        existing = {row[1] for row in cursor.execute(f"PRAGMA table_info({table})")}  # noqa: S608 — table is hardcoded
        if col in existing:
            try:
                cursor.execute(f"ALTER TABLE {table} DROP COLUMN {col}")  # noqa: S608 — identifiers hardcoded
            except Exception:
                _logger.debug("Could not drop %s.%s", table, col, exc_info=True)


def _migrate_games_columns(cursor: sqlite3.Cursor) -> None:
    """Add any missing columns to the games table without touching existing data."""
    existing = {row[1] for row in cursor.execute("PRAGMA table_info(games)")}
    for col_name, col_type in _GAMES_MIGRATIONS:
        if col_name not in existing:
            _alter_table_add_column(cursor, "games", col_name, col_type)


def _migrate_saves_columns(cursor: sqlite3.Cursor) -> None:
    """Add any missing columns to the saves table without touching existing data."""
    existing = {row[1] for row in cursor.execute("PRAGMA table_info(saves)")}
    for col_name, col_type in _SAVES_MIGRATIONS:
        if col_name not in existing:
            _alter_table_add_column(cursor, "saves", col_name, col_type)


def _migrate_assets_columns(cursor: sqlite3.Cursor) -> None:
    """Add any missing columns to the assets table without touching existing data."""
    existing = {row[1] for row in cursor.execute("PRAGMA table_info(assets)")}
    for col_name, col_type in _ASSETS_MIGRATIONS:
        if col_name not in existing:
            _alter_table_add_column(cursor, "assets", col_name, col_type)


def _migrate_sync_log_columns(cursor: sqlite3.Cursor) -> None:
    """Add any missing columns to save_sync_log without touching existing data."""
    existing = {row[1] for row in cursor.execute("PRAGMA table_info(save_sync_log)")}
    for col_name, col_type in _SYNC_LOG_MIGRATIONS:
        if col_name not in existing:
            _alter_table_add_column(cursor, "save_sync_log", col_name, col_type)


def _migrate_metadata_columns(cursor: sqlite3.Cursor) -> None:
    """Add any missing columns to game_metadata without touching existing data."""
    existing = {row[1] for row in cursor.execute("PRAGMA table_info(game_metadata)")}
    for col_name, col_type in _METADATA_MIGRATIONS:
        if col_name not in existing:
            _alter_table_add_column(cursor, "game_metadata", col_name, col_type)
