from __future__ import annotations

import sqlite3


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
        status TEXT NOT NULL DEFAULT 'scanned',
        canonical_title TEXT,
        match_confidence TEXT,
        catalog_source TEXT,
        library_path TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_games_sha1 ON games (sha1)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_games_platform ON games (platform)
    """,
    """
    CREATE TABLE IF NOT EXISTS saves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_path TEXT NOT NULL UNIQUE,
        relative_parent TEXT,
        extension TEXT NOT NULL,
        size_bytes INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
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
)

# Columns added after the initial schema that may be missing in existing databases.
_GAMES_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("canonical_title", "TEXT"),
    ("match_confidence", "TEXT"),
    ("catalog_source", "TEXT"),
    ("library_path", "TEXT"),
)


def initialize_database(connection: sqlite3.Connection) -> None:
    cursor = connection.cursor()
    for statement in SCHEMA_STATEMENTS:
        cursor.execute(statement)
    _migrate_games_columns(cursor)
    connection.commit()


def _migrate_games_columns(cursor: sqlite3.Cursor) -> None:
    """Add any missing columns to the games table without touching existing data."""
    existing = {row[1] for row in cursor.execute("PRAGMA table_info(games)")}
    for col_name, col_type in _GAMES_MIGRATIONS:
        if col_name not in existing:
            cursor.execute(f"ALTER TABLE games ADD COLUMN {col_name} {col_type}")
