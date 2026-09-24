from __future__ import annotations

import threading
from pathlib import Path
from unittest.mock import MagicMock

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.scanner.rom_scanner import scan_library

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
    _write(
        tmp_path,
        "psx",
        "disc1",
        "FFVII.cue",
        content=b'FILE "FFVII.bin" BINARY\n  TRACK 01 MODE1/2352\n    INDEX 01 00:00:00\n',
    )
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
    # Saves inside the dedicated saves/ folder are intentionally excluded from
    # the ROM scan (the sync subsystem owns them); they count as system files.
    assert result.saves_detected == 0
    assert result.system_files_detected >= 1  # the .srm under saves/
    assert result.errors == 0


def test_scan_excludes_android_folder(tmp_path):
    """Files inside excluded directories (Android, DCIM, etc.) are not stored as ROMs."""
    _write(tmp_path, "roms", "game.gba")
    _write(tmp_path, "Android", "data", "some.gba")  # excluded
    _write(tmp_path, "DCIM", "Camera", "photo.jpg")  # excluded

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

    result = scan_library(
        tmp_path, cfg, repo, logger, stop_event=stop_event, progress_cb=progress_cb
    )

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
    _write(tmp_path, "gba", "game.sav")  # save file
    _write(tmp_path, "text.txt")  # unknown

    repo = _mock_repo()
    cfg = load_config()
    logger = MagicMock()

    result = scan_library(tmp_path, cfg, repo, logger)

    assert result.roms_detected == 1
    assert result.saves_detected == 1
    assert result.unknown_files_detected >= 1
    assert result.errors == 0


# ── prune stale entries (integration) ─────────────────────────────────────────


def test_prune_stale_entries(tmp_path):
    """Scan 3 files → delete 1 → re-scan → stale entry pruned from DB."""
    rom_dir = tmp_path / "roms"
    rom_dir.mkdir()
    db_path = tmp_path / ".rommgr" / "library.db"

    _write(rom_dir, "gba", "GameA.gba")
    game_b = _write(rom_dir, "gba", "GameB.gba")
    _write(rom_dir, "gba", "GameC.gba")

    repo = LibraryRepository(db_path)
    cfg = load_config()
    logger = MagicMock()

    # First scan: all 3 files should be in the DB
    scan_library(rom_dir, cfg, repo, logger)
    _, total_after_first = repo.get_games_paginated()
    assert total_after_first == 3

    # Delete one file from disk
    game_b.unlink()

    # Second scan: stale entry for GameB must be pruned
    result = scan_library(rom_dir, cfg, repo, logger)
    _, total_after_second = repo.get_games_paginated()
    assert total_after_second == 2
    assert result.pruned == 1


# ── last_played_at update on save detection (REV43-22) ────────────────────────


def test_save_last_played_at_does_not_match_wrong_sibling_with_underscore(tmp_path):
    """A save's filename with a literal '_' must not update a sibling ROM whose
    name only differs at that position — SQL LIKE treats '_' as a wildcard
    unless escaped, so 'Zelda_of_Time.srm' could previously match
    'ZeldaXofXTime.gba' too."""
    rom_dir = tmp_path / "roms"
    db_path = tmp_path / ".rommgr" / "library.db"

    correct_rom = _write(rom_dir, "Zelda_of_Time.gba")
    decoy_rom = _write(rom_dir, "ZeldaXofXTime.gba")  # differs only where '_' is

    repo = LibraryRepository(db_path)
    cfg = load_config()
    logger = MagicMock()

    # First pass: discover both ROMs (last_played_at starts NULL).
    scan_library(rom_dir, cfg, repo, logger)

    # Second pass: a save file appears for the correct ROM only.
    _write(rom_dir, "Zelda_of_Time.srm")
    scan_library(rom_dir, cfg, repo, logger)

    with repo.connect() as conn:
        rows = {
            r["source_path"]: r["last_played_at"]
            for r in conn.execute("SELECT source_path, last_played_at FROM games").fetchall()
        }
    assert rows[str(correct_rom.resolve())] is not None
    assert rows[str(decoy_rom.resolve())] is None


def test_scan_excludes_trash_dir(tmp_path):
    """VAL-FIX-1: a ROM inside _descartados/ (AUD-3 papelera) must not be
    re-indexed — otherwise a "deleted" duplicate reappears on the next scan."""
    rom_dir = tmp_path / "roms"
    _write(rom_dir, "gba", "Kept.gba")
    _write(rom_dir, "gba", "_descartados", "Discarded.gba")

    repo = LibraryRepository(tmp_path / ".rommgr" / "library.db")
    cfg = load_config()
    logger = MagicMock()

    result = scan_library(rom_dir, cfg, repo, logger)

    with repo.connect() as conn:
        paths = {r["source_path"] for r in conn.execute("SELECT source_path FROM games").fetchall()}
    assert any(p.endswith("Kept.gba") for p in paths)
    assert not any("_descartados" in p for p in paths)
    assert result.roms_detected == 1


def test_scan_excludes_os_junk_dirs(tmp_path):
    """VAL-FIX-1: Windows system folders ($RECYCLE.BIN, System Volume
    Information) must never be indexed as ROM folders."""
    rom_dir = tmp_path / "roms"
    _write(rom_dir, "gba", "Kept.gba")
    _write(rom_dir, "$RECYCLE.BIN", "S-1-5-21", "Junk.gba")
    _write(rom_dir, "System Volume Information", "Junk2.gba")

    repo = LibraryRepository(tmp_path / ".rommgr" / "library.db")
    cfg = load_config()
    logger = MagicMock()

    scan_library(rom_dir, cfg, repo, logger)

    with repo.connect() as conn:
        paths = {r["source_path"] for r in conn.execute("SELECT source_path FROM games").fetchall()}
    assert any(p.endswith("Kept.gba") for p in paths)
    assert not any("Junk" in p for p in paths)


def test_scan_backfills_hash_after_quick_scan(tmp_path):
    """LIBRARY-AUDIT-5: a full scan must re-hash a row a --quick scan (or the
    ADB device scan) left with sha1='', even if the file's mtime/size haven't
    changed since — otherwise it stays unhashed forever ("sticky skip" bug)."""
    rom_dir = tmp_path / "roms"
    _write(rom_dir, "gba", "Game.gba")

    repo = LibraryRepository(tmp_path / ".rommgr" / "library.db")
    cfg = load_config()
    logger = MagicMock()

    scan_library(rom_dir, cfg, repo, logger, quick=True)
    with repo.connect() as conn:
        row = conn.execute("SELECT sha1 FROM games WHERE original_filename='Game.gba'").fetchone()
    assert row["sha1"] == ""

    scan_library(rom_dir, cfg, repo, logger, quick=False)
    with repo.connect() as conn:
        row = conn.execute("SELECT sha1 FROM games WHERE original_filename='Game.gba'").fetchone()
    assert row["sha1"] != ""
