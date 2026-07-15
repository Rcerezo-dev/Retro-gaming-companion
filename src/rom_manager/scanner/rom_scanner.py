from __future__ import annotations

import logging
import os
import sqlite3
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from rom_manager.config import AppConfig
from rom_manager.database import LibraryRepository
from rom_manager.detection import FileCategory, classify_path, detect_platform
from rom_manager.detection.cue_validator import validate_cue
from rom_manager.detection.region_parser import parse_region_from_name
from rom_manager.detection.set_detector import detect_set_type
from rom_manager.hashing import calculate_hashes_batch
from rom_manager.scanner.asset_scanner import inspect_asset

_PROGRESS_INTERVAL = 10
# ROMs are hashed in parallel batches of this size (hashlib releases the GIL).
# DB writes stay single-threaded; only the hashing fans out across threads.
_HASH_FLUSH_BATCH = 64


@dataclass(slots=True)
class ScanResult:
    files_seen: int = 0
    roms_detected: int = 0
    roms_skipped: int = 0
    saves_detected: int = 0
    assets_detected: int = 0
    system_files_detected: int = 0
    unknown_files_detected: int = 0
    errors: int = 0
    pruned: int = 0


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def scan_library(
    source_path: Path,
    config: AppConfig,
    repository: LibraryRepository,
    logger: logging.Logger,
    *,
    quick: bool = False,
    stop_event: threading.Event | None = None,
    progress_cb: Callable[[int, int, str], None] | None = None,
) -> ScanResult:
    """Scan *source_path* recursively and upsert findings into the repository.

    *stop_event*: if set, the scan exits cleanly at the next file boundary.
    *progress_cb*: called every ``_PROGRESS_INTERVAL`` files with
        (files_seen, roms_detected).
    """
    timestamp = utc_now()
    scan_run_id = repository.create_scan_run(str(source_path), timestamp)
    result = ScanResult()
    known_roms = repository.get_known_roms()
    seen_paths: set[str] = set()

    with repository.batch() as conn:
        # ROMs are not hashed inline; they are accumulated here and hashed in
        # parallel batches so multi-core machines aren't bottlenecked on serial
        # hashing. Saves/assets (no hashing needed) are still written inline.
        pending_hash: list[tuple[Path, os.stat_result]] = []

        def _flush_hash_batch() -> None:
            if not pending_hash:
                return
            hashes = calculate_hashes_batch([p for p, _ in pending_hash], stop_event=stop_event)
            cancelled = bool(stop_event and stop_event.is_set())
            for rom_path, rom_stat in pending_hash:
                file_hashes = hashes.get(rom_path)
                if file_hashes is None:
                    # Absent without cancellation means the read failed (OSError).
                    if not cancelled:
                        result.errors += 1
                        logger.error("Failed to hash %s", rom_path)
                    continue
                _upsert_rom(
                    rom_path,
                    rom_stat,
                    source_path,
                    repository,
                    timestamp,
                    conn,
                    file_hashes.sha1,
                    file_hashes.md5,
                    file_hashes.crc32,
                )
            pending_hash.clear()

        for path in source_path.rglob("*"):
            if stop_event and stop_event.is_set():
                logger.info("Scan cancelled by user after %d files.", result.files_seen)
                break
            if not path.is_file():
                continue

            seen_paths.add(str(path.resolve()))
            result.files_seen += 1
            if result.files_seen % _PROGRESS_INTERVAL == 0:
                logger.info("Progress: %d files seen so far...", result.files_seen)
                if progress_cb:
                    progress_cb(result.files_seen, result.roms_detected, path.name)

            try:
                category = classify_path(path, config, source_path)
                if category is FileCategory.ROM:
                    if path.suffix.lower() == ".cue":
                        for err in validate_cue(path):
                            logger.warning("%s — %s", path.name, err)
                    stat = path.stat()
                    path_str = str(path.resolve())
                    known = known_roms.get(path_str)
                    if known and known == (int(stat.st_mtime), stat.st_size):
                        result.roms_skipped += 1
                        result.roms_detected += 1
                        continue
                    if quick:
                        # Quick scan stores no hashes — nothing to parallelise.
                        _upsert_rom(
                            path, stat, source_path, repository, timestamp, conn, "", "", ""
                        )
                    else:
                        pending_hash.append((path, stat))
                        if len(pending_hash) >= _HASH_FLUSH_BATCH:
                            _flush_hash_batch()
                    result.roms_detected += 1
                elif category is FileCategory.SAVE:
                    _store_save(path, source_path, repository, timestamp, conn)
                    result.saves_detected += 1
                    # Update last_played_at for the associated ROM (same directory + same stem)
                    try:
                        save_mtime_ts = (
                            datetime.fromtimestamp(path.stat().st_mtime, UTC)
                            .replace(microsecond=0)
                            .isoformat()
                        )
                        prefix = str(path.parent.resolve() / path.stem)
                        stem_like = (
                            prefix.replace("\\", "\\\\").replace("%", "%%").replace("_", "\\_")
                            + ".%"
                        )
                        conn.execute(
                            "UPDATE games SET last_played_at = ? WHERE source_path LIKE ? ESCAPE '\\' "
                            "AND (last_played_at IS NULL OR last_played_at < ?)",
                            (save_mtime_ts, stem_like, save_mtime_ts),
                        )
                    except Exception:
                        logging.getLogger(__name__).debug(
                            "Failed to update last_played_at for %s", path, exc_info=True
                        )
                elif category is FileCategory.FRONTEND_ASSET:
                    _store_asset(path, source_path, repository, timestamp, conn)
                    result.assets_detected += 1
                elif category is FileCategory.SYSTEM_SUPPORT:
                    result.system_files_detected += 1
                else:
                    result.unknown_files_detected += 1
            except OSError as error:
                result.errors += 1
                logger.error("Failed to process %s: %s", path, error)

        # Hash and persist any ROMs collected after the last full batch.
        _flush_hash_batch()

    result.pruned = repository.prune_stale_entries(str(source_path.resolve()), seen_paths)
    if result.pruned:
        logger.info("Pruned %d stale entries from database.", result.pruned)

    # Update SQLite query planner statistics so subsequent queries reflect
    # the new data immediately (avoids stale counts after the first scan).
    with repository.connect() as conn:
        conn.execute("PRAGMA optimize")

    finished_at = utc_now()
    repository.complete_scan_run(
        scan_run_id,
        finished_at=finished_at,
        files_seen=result.files_seen,
        roms_detected=result.roms_detected,
        saves_detected=result.saves_detected,
        assets_detected=result.assets_detected,
        system_files_detected=result.system_files_detected,
        unknown_files_detected=result.unknown_files_detected,
        errors=result.errors,
    )
    return result


def _upsert_rom(
    path: Path,
    stat: os.stat_result,
    source_root: Path,
    repository: LibraryRepository,
    timestamp: str,
    connection: sqlite3.Connection,
    sha1: str,
    md5: str,
    crc32: str,
) -> None:
    """Persist a single ROM row. Hashing happens upstream (in parallel batches);
    pass empty strings for *sha1*/*md5*/*crc32* in quick-scan mode."""
    repository.upsert_game(
        original_filename=path.name,
        source_path=str(path.resolve()),
        platform=detect_platform(path),
        file_type="rom",
        relative_parent=_relative_parent(path, source_root),
        region=parse_region_from_name(path.name),
        extension=path.suffix.lower(),
        size_bytes=stat.st_size,
        mtime=int(stat.st_mtime),
        sha1=sha1,
        md5=md5,
        crc32=crc32,
        set_type=detect_set_type(path),
        timestamp=timestamp,
        connection=connection,
    )


def _store_save(
    path: Path,
    source_root: Path,
    repository: LibraryRepository,
    timestamp: str,
    connection: sqlite3.Connection,
) -> None:
    repository.upsert_save(
        original_path=str(path.resolve()),
        relative_parent=_relative_parent(path, source_root),
        extension=path.suffix.lower(),
        size_bytes=path.stat().st_size,
        timestamp=timestamp,
        connection=connection,
    )


def _store_asset(
    path: Path,
    source_root: Path,
    repository: LibraryRepository,
    timestamp: str,
    connection: sqlite3.Connection,
) -> None:
    platform, asset_type = inspect_asset(path)
    repository.upsert_asset(
        source_path=str(path.resolve()),
        relative_parent=_relative_parent(path, source_root),
        platform=platform,
        asset_type=asset_type,
        timestamp=timestamp,
        connection=connection,
    )


def _relative_parent(path: Path, source_root: Path) -> str:
    relative_parent = path.resolve().parent.relative_to(source_root.resolve())
    return "." if str(relative_parent) == "." else relative_parent.as_posix()
