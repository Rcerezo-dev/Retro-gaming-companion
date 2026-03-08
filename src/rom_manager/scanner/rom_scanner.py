from __future__ import annotations

import logging
import os
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from rom_manager.config import AppConfig
from rom_manager.database import LibraryRepository
from rom_manager.detection import FileCategory, classify_path, detect_platform
from rom_manager.detection.region_parser import parse_region_from_name
from rom_manager.detection.set_detector import detect_set_type
from rom_manager.hashing import calculate_hashes
from rom_manager.detection.cue_validator import validate_cue
from rom_manager.scanner.asset_scanner import inspect_asset

_PROGRESS_INTERVAL = 100


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


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def scan_library(
    source_path: Path,
    config: AppConfig,
    repository: LibraryRepository,
    logger: logging.Logger,
) -> ScanResult:
    timestamp = utc_now()
    scan_run_id = repository.create_scan_run(str(source_path), timestamp)
    result = ScanResult()
    known_roms = repository.get_known_roms()

    with repository.batch() as conn:
        for path in source_path.rglob("*"):
            if not path.is_file():
                continue

            result.files_seen += 1
            if result.files_seen % _PROGRESS_INTERVAL == 0:
                logger.info("Progress: %d files seen so far...", result.files_seen)

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
                    _store_rom(path, stat, source_path, repository, timestamp, conn)
                    result.roms_detected += 1
                elif category is FileCategory.SAVE:
                    _store_save(path, source_path, repository, timestamp, conn)
                    result.saves_detected += 1
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


def _store_rom(
    path: Path,
    stat: os.stat_result,
    source_root: Path,
    repository: LibraryRepository,
    timestamp: str,
    connection: sqlite3.Connection,
) -> None:
    hashes = calculate_hashes(path)
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
        sha1=hashes.sha1,
        md5=hashes.md5,
        crc32=hashes.crc32,
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
