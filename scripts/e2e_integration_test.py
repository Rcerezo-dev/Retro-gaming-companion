"""
End-to-end integration test for Retro Vault ROM manager pipeline.

Tests: Setup -> Scan -> DB integrity -> Plan -> Prune -> Schema -> Config roundtrip
"""
from __future__ import annotations

import logging
import os
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

# Ensure src is on sys.path (this script lives in scripts/, project root is its parent)
SRC = Path(__file__).parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------
results: list[dict] = []


def record(stage: str, test: str, passed: bool, details: str, tb: str = "") -> None:
    results.append({"stage": stage, "test": test, "passed": passed, "details": details, "tb": tb})
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] Stage {stage} — {test}: {details}")
    if tb:
        print(tb)


# ---------------------------------------------------------------------------
# SETUP: Create temporary test library
# ---------------------------------------------------------------------------
def setup_test_library() -> tuple[Path, Path]:
    """Return (tmpdir, config_toml_path)."""
    tmpdir = Path(tempfile.mkdtemp(prefix="retrovault_e2e_"))

    structure = {
        "Game Boy Advance/Metroid Fusion (USA).gba": 512,
        "Game Boy Advance/Castlevania - Aria of Sorrow (USA).gba": 512,
        "Game Boy Advance/Pokemon - FireRed Version (USA).gba": 512,
        "Super Nintendo/Super Mario World (USA).sfc": 512,
        "Super Nintendo/Donkey Kong Country (USA).sfc": 512,
        "PlayStation/Final Fantasy VII (USA) (Disc 1).bin": 2048,
        "PlayStation/Final Fantasy VII (USA) (Disc 2).bin": 2048,
    }

    files_created = 0
    for rel_path, size in structure.items():
        full = tmpdir / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_bytes(os.urandom(size))
        files_created += 1

    # Valid CUE files referencing the BIN files
    cue1 = tmpdir / "PlayStation/Final Fantasy VII (USA) (Disc 1).cue"
    cue1.write_text(
        'FILE "Final Fantasy VII (USA) (Disc 1).bin" BINARY\n'
        '  TRACK 01 MODE2/2352\n'
        '    INDEX 01 00:00:00\n',
        encoding="utf-8",
    )
    cue2 = tmpdir / "PlayStation/Final Fantasy VII (USA) (Disc 2).cue"
    cue2.write_text(
        'FILE "Final Fantasy VII (USA) (Disc 2).bin" BINARY\n'
        '  TRACK 01 MODE2/2352\n'
        '    INDEX 01 00:00:00\n',
        encoding="utf-8",
    )
    files_created += 2

    # Write minimal config.toml inside tmpdir (used as project_root)
    lib_root_escaped = str(tmpdir).replace("\\", "\\\\")
    config_toml = tmpdir / "config.toml"
    config_toml.write_text(
        f'[library]\nlibrary_root = "{lib_root_escaped}"\n\n'
        '[web]\nhost = "127.0.0.1"\nport = 7778\n',
        encoding="utf-8",
    )

    return tmpdir, config_toml, files_created


# ---------------------------------------------------------------------------
# Stage 1 — Scan
# ---------------------------------------------------------------------------
def run_stage1(tmpdir: Path) -> dict:
    from rom_manager.config import load_config
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.scanner.rom_scanner import scan_library

    config = load_config(tmpdir)
    db_path = tmpdir / ".rommgr" / "library_pc.db"
    repo = LibraryRepository(db_path)
    logger = logging.getLogger("e2e")

    result = scan_library(tmpdir, config, repo, logger, quick=True)
    return result, repo, config


# ---------------------------------------------------------------------------
# Stage 2 — DB integrity
# ---------------------------------------------------------------------------
def check_db_integrity(repo, tmpdir: Path) -> tuple[bool, str, list]:
    issues = []
    with repo.connect() as conn:
        rows = conn.execute("SELECT source_path, platform, file_type FROM games ORDER BY source_path").fetchall()

    total = len(rows)
    if total < 8:
        issues.append(f"Expected >= 8 rows, got {total}")

    platform_map = {
        ".gba": "Game Boy Advance",
        ".sfc": "SNES",  # canonical value returned by detect_platform()
        ".bin": "PlayStation",
        ".cue": "PlayStation",
    }
    wrong_platform = []
    wrong_type = []
    for row in rows:
        sp = row["source_path"]
        ext = Path(sp).suffix.lower()
        expected_platform = platform_map.get(ext)
        if expected_platform and row["platform"] != expected_platform:
            wrong_platform.append(f"{Path(sp).name}: got '{row['platform']}' expected '{expected_platform}'")
        if row["file_type"] != "rom":
            wrong_type.append(f"{Path(sp).name}: file_type={row['file_type']}")

    # Check no duplicate source_paths
    with repo.connect() as conn:
        dup_rows = conn.execute(
            "SELECT source_path, COUNT(*) as cnt FROM games GROUP BY source_path HAVING cnt > 1"
        ).fetchall()

    if wrong_platform:
        issues.append("Platform mismatches: " + "; ".join(wrong_platform))
    if wrong_type:
        issues.append("Wrong file_type: " + "; ".join(wrong_type))
    if dup_rows:
        issues.append(f"Duplicate source_paths: {[r['source_path'] for r in dup_rows]}")

    ok = len(issues) == 0
    detail = f"{total} rows, platforms OK" if ok else "; ".join(issues)
    return ok, detail, rows


# ---------------------------------------------------------------------------
# Stage 3 — Plan generation
# ---------------------------------------------------------------------------
def check_plan(repo) -> tuple[bool, str]:
    from rom_manager.planner.operation_planner import build_plan

    plan = build_plan(repo)
    # Verify it's a valid RenamePlan with total attribute
    total = plan.total
    return True, f"{total} operations in plan"


# ---------------------------------------------------------------------------
# Stage 4 — Prune stale entries
# ---------------------------------------------------------------------------
def check_prune(tmpdir: Path, repo) -> tuple[bool, str]:
    from rom_manager.config import load_config
    from rom_manager.scanner.rom_scanner import scan_library

    config = load_config(tmpdir)
    logger = logging.getLogger("e2e")

    # Delete one GBA file
    to_delete = tmpdir / "Game Boy Advance" / "Metroid Fusion (USA).gba"
    deleted_path = str(to_delete.resolve())
    to_delete.unlink()

    result2 = scan_library(tmpdir, config, repo, logger, quick=True)

    # Check deleted file is gone from DB
    with repo.connect() as conn:
        remaining = conn.execute(
            "SELECT source_path FROM games WHERE source_path LIKE '%Game Boy Advance%'"
        ).fetchall()

    remaining_paths = [r["source_path"] for r in remaining]
    deleted_still_present = any(deleted_path.replace("\\", "/").lower() in p.replace("\\", "/").lower()
                                 or p.replace("\\", "/").lower() in deleted_path.replace("\\", "/").lower()
                                 for p in remaining_paths)

    issues = []
    if deleted_still_present:
        issues.append(f"Deleted file still in DB: {deleted_path}")
    if len(remaining_paths) != 2:
        issues.append(f"Expected 2 remaining GBA records, got {len(remaining_paths)}: {remaining_paths}")
    if result2.pruned != 1:
        issues.append(f"Expected pruned=1, got {result2.pruned}")

    ok = len(issues) == 0
    detail = f"pruned={result2.pruned}, {len(remaining_paths)} GBA records remaining" if ok else "; ".join(issues)
    return ok, detail


# ---------------------------------------------------------------------------
# Stage 5 — Schema migrations (column presence)
# ---------------------------------------------------------------------------
def check_schema(repo) -> tuple[bool, str]:
    required_games = {"play_status", "last_played_at", "canonical_title", "match_confidence", "mtime"}
    required_assets = {"game_id"}

    with repo.connect() as conn:
        games_cols = {row[1] for row in conn.execute("PRAGMA table_info(games)")}
        assets_cols = {row[1] for row in conn.execute("PRAGMA table_info(assets)")}

    missing_games = required_games - games_cols
    missing_assets = required_assets - assets_cols

    issues = []
    if missing_games:
        issues.append(f"Missing games columns: {missing_games}")
    if missing_assets:
        issues.append(f"Missing assets columns: {missing_assets}")

    ok = len(issues) == 0
    detail = "All columns present" if ok else "; ".join(issues)
    return ok, detail


# ---------------------------------------------------------------------------
# Stage 6 — Config roundtrip
# ---------------------------------------------------------------------------
def check_config_roundtrip(tmpdir: Path) -> tuple[bool, str]:
    from rom_manager.config import load_config

    config = load_config(tmpdir)

    issues = []
    if config.library_root is None:
        issues.append("library_root is None")
    elif str(config.library_root.resolve()) != str(tmpdir.resolve()):
        issues.append(f"library_root mismatch: {config.library_root} != {tmpdir}")
    if config.web_host != "127.0.0.1":
        issues.append(f"web_host wrong: {config.web_host}")
    if config.web_port != 7778:
        issues.append(f"web_port wrong: {config.web_port}")
    if config.project_root != tmpdir.resolve():
        issues.append(f"project_root wrong: {config.project_root}")
    if config.database_path != tmpdir.resolve() / ".rommgr" / "library_pc.db":
        issues.append(f"database_path wrong: {config.database_path}")

    ok = len(issues) == 0
    detail = "All fields OK" if ok else "; ".join(issues)
    return ok, detail


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    tmpdir = None

    # SETUP
    try:
        tmpdir, config_toml, files_created = setup_test_library()
        record("Setup", "Create test library", True, f"{files_created} files created in {tmpdir}")
    except Exception:
        tb = traceback.format_exc()
        record("Setup", "Create test library", False, "Exception during setup", tb)
        print_report()
        return

    # Stage 1 — Scan
    try:
        scan_result, repo, config = run_stage1(tmpdir)
        ok = scan_result.files_seen > 0 and scan_result.roms_detected >= 7 and scan_result.errors == 0
        detail = f"{scan_result.roms_detected} ROMs, {scan_result.files_seen} files seen, {scan_result.errors} errors"
        record("1", "Scan", ok, detail)
    except Exception:
        tb = traceback.format_exc()
        record("1", "Scan", False, "Exception during scan", tb)
        print_report()
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)
        return

    # Stage 2 — DB integrity
    try:
        ok, detail, rows = check_db_integrity(repo, tmpdir)
        record("2", "DB integrity", ok, detail)
    except Exception:
        tb = traceback.format_exc()
        record("2", "DB integrity", False, "Exception during DB check", tb)

    # Stage 3 — Plan generation
    try:
        ok, detail = check_plan(repo)
        record("3", "Plan", ok, detail)
    except Exception:
        tb = traceback.format_exc()
        record("3", "Plan", False, "Exception during plan generation", tb)

    # Stage 4 — Prune stale entries
    try:
        ok, detail = check_prune(tmpdir, repo)
        record("4", "Prune stale", ok, detail)
    except Exception:
        tb = traceback.format_exc()
        record("4", "Prune stale", False, "Exception during prune check", tb)

    # Stage 5 — Schema migrations
    try:
        ok, detail = check_schema(repo)
        record("5", "Schema migrations", ok, detail)
    except Exception:
        tb = traceback.format_exc()
        record("5", "Schema migrations", False, "Exception during schema check", tb)

    # Stage 6 — Config roundtrip
    try:
        ok, detail = check_config_roundtrip(tmpdir)
        record("6", "Config roundtrip", ok, detail)
    except Exception:
        tb = traceback.format_exc()
        record("6", "Config roundtrip", False, "Exception during config roundtrip", tb)

    # Cleanup
    if tmpdir:
        shutil.rmtree(tmpdir, ignore_errors=True)
        print(f"\nCleaned up temp dir: {tmpdir}")

    print_report()


def print_report() -> None:
    print("\n" + "=" * 70)
    print("INTEGRATION TEST REPORT")
    print("=" * 70)
    print(f"{'Stage':<8} {'Test':<25} {'Status':<8} {'Details'}")
    print("-" * 70)
    passed = 0
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"{r['stage']:<8} {r['test']:<25} {status:<8} {r['details']}")
        if r["passed"]:
            passed += 1
    total = len(results)
    print("=" * 70)
    overall = "PASS" if passed == total else "FAIL"
    print(f"Overall: {overall} ({passed}/{total} stages passed)")
    print("=" * 70)
    # Print tracebacks for failures
    for r in results:
        if r["tb"]:
            print(f"\n--- Traceback for Stage {r['stage']} ({r['test']}) ---")
            print(r["tb"])


if __name__ == "__main__":
    main()
