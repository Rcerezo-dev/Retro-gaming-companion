from __future__ import annotations

import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rom_manager.config import load_config
from rom_manager.scanner.rom_scanner import ScanResult, scan_library


# ── helpers ───────────────────────────────────────────────────────────────────

def _write(root: Path, *parts: str, content: bytes = b"\x00" * 64) -> Path:
    p = root.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return p


def _mock_repo():
    repo = MagicMock()
    repo.get_known_roms.return_value = {}
    repo.create_scan_run.return_value = 1
    repo.prune_stale_entries.return_value = 0
    repo.batch.return_value.__enter__ = lambda s: MagicMock()
    repo.batch.return_value.__exit__ = MagicMock(return_value=False)
    return repo


# ── scan is recursive ─────────────────────────────────────────────────────────

def test_scan_recursive(tmp_path):
    """scan_library must walk subdirectories recursively."""
    _write(tmp_path, "gba", "Castlevania.gba")
    _write(tmp_path, "psx", "disc1", "FFVII.cue",
           content=b'FILE "FFVII.bin" BINARY\n  TRACK 01 MODE1/2352\n    INDEX 01 00:00:00\n')
    _write(tmp_path, "psx", "disc1", "FFVII.bin")
    _write(tmp_path, "snes", "sub", "deep", "Zelda.sfc")

    repo = _mock_repo()
    cfg = load_config()
    logger = MagicMock()

    result = scan_library(tmp_path, cfg, repo, logger)

    assert result.files_seen >= 4
    assert result.roms_detected >= 3  # .gba, .cue, .sfc (.bin classified as ROM too)
    assert result.errors == 0


def test_scan_sd_card_path(tmp_path):
    """scan_library works with any filesystem path (simulates SD card drive letter)."""
    # Simulate typical Anbernic SD card structure
    _write(tmp_path, "RetroArch", "roms", "gba", "Mario.gba")
    _write(tmp_path, "RetroArch", "roms", "gba", "Zelda.gba")
    _write(tmp_path, "RetroArch", "saves", "gba", "Mario.srm")
    _write(tmp_path, "RetroArch", "roms", "psx", "FFVII.chd")

    repo = _mock_repo()
    cfg = load_config()
    logger = MagicMock()

    result = scan_library(tmp_path, cfg, repo, logger)

    assert result.roms_detected >= 3  # .gba x2, .chd
    assert result.saves_detected >= 1  # .srm
    assert result.errors == 0


def test_scan_excludes_android_folder(tmp_path):
    """Files inside excluded directories (Android, DCIM, etc.) are not stored as ROMs."""
    _write(tmp_path, "roms", "game.gba")
    _write(tmp_path, "Android", "data", "some.gba")   # excluded
    _write(tmp_path, "DCIM", "Camera", "photo.jpg")   # excluded

    repo = _mock_repo()
    cfg = load_config()
    logger = MagicMock()

    result = scan_library(tmp_path, cfg, repo, logger)

    # Only the ROM outside excluded dirs should be counted
    assert result.roms_detected == 1
    # The excluded files count as system_support or unknown, not ROM
    assert result.system_files_detected >= 1


def test_scan_stop_event(tmp_path):
    """scan_library exits early when the stop_event is set."""
    # Create many files so the scan takes a while
    for i in range(300):
        _write(tmp_path, f"game_{i}.gba")

    stop_event = threading.Event()
    stop_event.set()  # Pre-set: scan should abort immediately

    repo = _mock_repo()
    cfg = load_config()
    logger = MagicMock()

    result = scan_library(tmp_path, cfg, repo, logger, stop_event=stop_event)

    # With stop_event already set, the scan should exit before processing all files
    assert result.files_seen < 300


def test_scan_stop_event_mid_run(tmp_path):
    """stop_event set during scan stops it cleanly without error."""
    for i in range(200):
        _write(tmp_path, f"game_{i}.gba")

    stop_event = threading.Event()
    files_at_cancel = []

    original_progress_interval = 10  # matches _PROGRESS_INTERVAL

    def progress_cb(files_seen: int, roms: int, current_file: str = "") -> None:
        if files_seen >= original_progress_interval:
            stop_event.set()
        files_at_cancel.append(files_seen)

    repo = _mock_repo()
    cfg = load_config()
    logger = MagicMock()

    result = scan_library(tmp_path, cfg, repo, logger,
                          stop_event=stop_event, progress_cb=progress_cb)

    # Scan should have stopped before all 200 files
    assert result.files_seen < 200
    assert result.errors == 0


def test_scan_progress_callback(tmp_path):
    """progress_cb is called every _PROGRESS_INTERVAL files."""
    for i in range(250):
        _write(tmp_path, f"game_{i}.gba")

    calls: list[tuple[int, int]] = []

    def progress_cb(files_seen: int, roms: int, current_file: str = "") -> None:
        calls.append((files_seen, roms))

    repo = _mock_repo()
    cfg = load_config()
    logger = MagicMock()

    result = scan_library(tmp_path, cfg, repo, logger, progress_cb=progress_cb)

    assert result.files_seen == 250
    # Should be called at 10, 20, ..., 250 (25 calls with interval=10)
    assert len(calls) == 25
    assert calls[0][0] == 10
    assert calls[1][0] == 20


def test_scan_result_aggregation(tmp_path):
    """ScanResult fields are populated correctly."""
    _write(tmp_path, "gba", "game.gba")
    _write(tmp_path, "gba", "game.sav")   # save file
    _write(tmp_path, "text.txt")           # unknown

    repo = _mock_repo()
    cfg = load_config()
    logger = MagicMock()

    result = scan_library(tmp_path, cfg, repo, logger)

    assert result.roms_detected == 1
    assert result.saves_detected == 1
    assert result.unknown_files_detected >= 1
    assert result.errors == 0
