"""
Integration test: end-to-end pipeline on synthetic data.
Does NOT touch the real library at E:\\Carpetas anbernic.
Run with:
  C:\\Users\\rammu\\anaconda3\\envs\\rom_manager\\python.exe tests/integration_test_pipeline.py
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

# Make sure the src tree is importable when running directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

PYTHON = r"C:\Users\rammu\anaconda3\envs\rom_manager\python.exe"

# ── helpers ──────────────────────────────────────────────────────────────────

def _ok(detail: str = "") -> str:
    return f"PASS  {detail}"

def _fail(detail: str = "") -> str:
    return f"FAIL  {detail}"

def section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

# ── stage 0: create test library ─────────────────────────────────────────────

section("Step 1 — Create synthetic test library")

tmpdir = Path(tempfile.mkdtemp(prefix="rommgr_test_"))
print(f"Temp dir: {tmpdir}")

files_to_create = [
    tmpdir / "Game Boy Advance" / "Metroid Fusion (USA).gba",
    tmpdir / "Game Boy Advance" / "Pokemon - Fire Red Version (USA).gba",
    tmpdir / "Game Boy Advance" / "Castlevania - Aria of Sorrow (USA).gba",
]

step1_ok = True
try:
    for f in files_to_create:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(os.urandom(512))
    created = sum(1 for f in files_to_create if f.exists())
    step1_result = _ok(f"{created} files created in {tmpdir}")
    print(step1_result)
except Exception:
    step1_ok = False
    step1_result = _fail(traceback.format_exc())
    print(step1_result)

# ── stage 1: scan ─────────────────────────────────────────────────────────────

section("Step 2 — Scan the test library")

# We import directly to avoid config conflicts with the real library.
scan2_ok = False
scan2_result = ""
scan_result_obj = None
repo = None
cfg = None

try:
    import logging

    from rom_manager.config import load_config
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.scanner.rom_scanner import scan_library

    # Point load_config at a *temporary* project root so it creates its own DB.
    test_project_root = tmpdir / "_project"
    test_project_root.mkdir(exist_ok=True)

    # Write a minimal config.toml in the test project root.
    (test_project_root / "config.toml").write_text(
        f'[library]\nlibrary_root = "{str(tmpdir).replace(chr(92), "/")}"\n',
        encoding="utf-8",
    )

    cfg = load_config(test_project_root)
    db_path = cfg.database_path           # .rommgr/library_pc.db inside tmpdir/_project
    repo = LibraryRepository(db_path)

    logger = logging.getLogger("integration_test")
    logging.basicConfig(level=logging.WARNING)

    scan_result_obj = scan_library(tmpdir, cfg, repo, logger, quick=True)

    roms = scan_result_obj.roms_detected
    errors = scan_result_obj.errors
    files_seen = scan_result_obj.files_seen

    if roms >= 3 and errors == 0:
        scan2_ok = True
        scan2_result = _ok(f"{roms} ROMs detected, {files_seen} files seen, {errors} errors")
    else:
        scan2_result = _fail(f"roms_detected={roms} (expected >=3), errors={errors}")

    print(f"files_seen={files_seen}, roms_detected={roms}, errors={errors}, pruned={scan_result_obj.pruned}")
    print(scan2_result)
except Exception:
    scan2_result = _fail(traceback.format_exc())
    print(scan2_result)

# ── stage 2: DB integrity ──────────────────────────────────────────────────────

section("Step 3 — Verify database contents")

step3_ok = False
step3_result = ""

try:
    if repo is None:
        raise RuntimeError("repo not initialised — step 2 failed")

    with repo.connect() as conn:
        rows = conn.execute(
            "SELECT id, original_filename, source_path, platform, file_type FROM games ORDER BY id"
        ).fetchall()

    print(f"Rows in games table: {len(rows)}")
    for r in rows:
        print(f"  id={r['id']}  file={r['original_filename']}  platform={r['platform']}  type={r['file_type']}")

    # Verify: all 3 GBA files present
    filenames = {r["original_filename"] for r in rows}
    expected = {f.name for f in files_to_create}
    missing = expected - filenames
    extra = filenames - expected

    # Verify platform detection
    platforms = {r["platform"] for r in rows}
    gba_platform_ok = all(
        r["platform"] == "Game Boy Advance"
        for r in rows if r["original_filename"].endswith(".gba")
    )

    # Verify no duplicate source_path
    source_paths = [r["source_path"] for r in rows]
    no_dupes = len(source_paths) == len(set(source_paths))

    # Verify file_type = rom for all
    all_rom_type = all(r["file_type"] == "rom" for r in rows)

    if len(rows) == 3 and not missing and gba_platform_ok and no_dupes and all_rom_type:
        step3_ok = True
        step3_result = _ok(f"{len(rows)} rows, platform=Game Boy Advance for all, no dupes, file_type=rom")
    else:
        issues = []
        if len(rows) != 3:
            issues.append(f"row count={len(rows)} (expected 3)")
        if missing:
            issues.append(f"missing filenames: {missing}")
        if not gba_platform_ok:
            bad = [(r['original_filename'], r['platform']) for r in rows if r['platform'] != 'Game Boy Advance']
            issues.append(f"bad platforms: {bad}")
        if not no_dupes:
            issues.append("duplicate source_path entries found")
        if not all_rom_type:
            issues.append("some rows have file_type != rom")
        step3_result = _fail("; ".join(issues))

    print(step3_result)
except Exception:
    step3_result = _fail(traceback.format_exc())
    print(step3_result)

# ── stage 3: plan ─────────────────────────────────────────────────────────────

section("Step 4 — Run build_plan()")

step4_ok = False
step4_result = ""

try:
    if repo is None:
        raise RuntimeError("repo not initialised — step 2 failed")

    from rom_manager.planner import build_plan

    plan = build_plan(repo)
    total = plan.total
    print(f"plan.total={total}, pending={len(plan.pending)}, conflicts={len(plan.conflicts)}, already_correct={len(plan.already_correct)}")

    # plan.total >= 0 is guaranteed; no exception = success
    step4_ok = True
    step4_result = _ok(f"plan.total={total} (no exception raised)")
    print(step4_result)
except Exception:
    step4_result = _fail(traceback.format_exc())
    print(step4_result)

# ── stage 4: prune stale ──────────────────────────────────────────────────────

section("Step 5 — Prune stale entries after deleting one file")

step5_ok = False
step5_result = ""

try:
    if repo is None or cfg is None:
        raise RuntimeError("repo/cfg not initialised — step 2 failed")

    # Delete the first GBA file
    deleted_file = files_to_create[0]
    deleted_file.unlink()
    print(f"Deleted: {deleted_file.name}")

    # Re-scan
    scan2 = scan_library(tmpdir, cfg, repo, logger, quick=True)
    print(f"Second scan: files_seen={scan2.files_seen}, roms_detected={scan2.roms_detected}, pruned={scan2.pruned}")

    # Check DB
    with repo.connect() as conn:
        rows2 = conn.execute(
            "SELECT original_filename FROM games ORDER BY id"
        ).fetchall()

    remaining = {r["original_filename"] for r in rows2}
    print(f"Remaining in DB: {sorted(remaining)}")

    deleted_gone = deleted_file.name not in remaining
    others_present = all(
        f.name in remaining for f in files_to_create[1:]
    )

    if deleted_gone and others_present and scan2.pruned == 1:
        step5_ok = True
        step5_result = _ok(f"pruned=1, deleted file gone, {len(remaining)} rows remain")
    else:
        issues = []
        if not deleted_gone:
            issues.append(f"deleted file still in DB: {deleted_file.name}")
        if not others_present:
            issues.append("some surviving files missing from DB")
        if scan2.pruned != 1:
            issues.append(f"pruned={scan2.pruned} (expected 1)")
        step5_result = _fail("; ".join(issues))

    print(step5_result)
except Exception:
    step5_result = _fail(traceback.format_exc())
    print(step5_result)

# ── stage 5: cleanup ──────────────────────────────────────────────────────────

section("Step 6 — Cleanup temporary directory")

step6_ok = False
step6_result = ""

try:
    shutil.rmtree(tmpdir, ignore_errors=True)
    if not tmpdir.exists():
        step6_ok = True
        step6_result = _ok(f"Removed {tmpdir}")
    else:
        step6_result = _fail("tmpdir still exists after shutil.rmtree")
    print(step6_result)
except Exception:
    step6_result = _fail(traceback.format_exc())
    print(step6_result)

# ── final report ──────────────────────────────────────────────────────────────

section("RESULTS TABLE")

results = [
    (1, "Crear biblioteca de prueba",      step1_ok, step1_result),
    (2, "Scan",                            scan2_ok, scan2_result),
    (3, "Verificar BD",                    step3_ok, step3_result),
    (4, "Plan",                            step4_ok, step4_result),
    (5, "Prune stale",                     step5_ok, step5_result),
    (6, "Limpieza",                        step6_ok, step6_result),
]

passed = sum(1 for _, _, ok, _ in results if ok)
total  = len(results)

print()
print("| Paso | Descripcion                 | Resultado |")
print("|------|-----------------------------|-----------|")
for step_num, desc, ok, detail in results:
    icon = "OK" if ok else "FAIL"
    # Trim detail for table display
    short = detail.replace("\n", " ")[:90]
    print(f"| {step_num}    | {desc:<27} | [{icon}] {short} |")

print()
print(f"Overall: {'PASS' if passed == total else 'FAIL'} ({passed}/{total} stages passed)")

sys.exit(0 if passed == total else 1)
