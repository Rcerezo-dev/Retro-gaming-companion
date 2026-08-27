"""CABLE-UX-9b/9f — tests del motor compartido de sync por filesystem.

Cubre las tres direcciones de plan_direction y todas las ramas de policy en
copy_item (safe_mode, skip_existing, dry_run, error, on_event) en un solo
sitio -- el "hecho cuando" de CABLE-UX-9. La politica ADB ("verify MD5 solo
en saves") vive en adb_transport.should_verify y su cobertura esta en
test_adb_transport_policy.py (CABLE-UX-9e); el guard de reloj ("skew") tiene
la suya en test_cable_sync_clock_guard.py / test_sync_doctor.py -- ninguno
de los dos es responsabilidad de este motor (ver docstring de
cable_engine.py).
"""

from __future__ import annotations

from pathlib import Path

from rom_manager.sync.cable_engine import (
    CopyPlanItem,
    CopyPolicy,
    copy_item,
    iter_files,
    plan_direction,
)

_WANTED = lambda p: p.suffix == ".sav"  # noqa: E731


def _write(root: Path, *parts: str, content: bytes = b"x") -> Path:
    p = root.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return p


def test_iter_files_skips_descartados(tmp_path: Path) -> None:
    """TRASH-FIX-1: la papelera nunca debe volver a entrar en un plan de sync
    (si no, cada sync repetida anida _descartados/_descartados/... sin fin)."""
    _write(tmp_path, "psx", "game.chd")
    _write(tmp_path, "psx", "_descartados", "old_game.bin")
    _write(tmp_path, ".hidden", "junk.txt")

    found = {p.name for p in iter_files(tmp_path)}

    assert found == {"game.chd"}


def test_plan_pc_to_anbernic(tmp_path: Path) -> None:
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    _write(pc, "gba", "mario.sav")
    _write(pc, "notes.txt")

    items = list(plan_direction(pc, ab, "pc_to_anbernic", _WANTED))

    assert len(items) == 1
    assert items[0].dst == ab / "gba" / "mario.sav"


def test_plan_newest_picks_newer_side(tmp_path: Path) -> None:
    import os

    pc, ab = tmp_path / "pc", tmp_path / "ab"
    pc_f = _write(pc, "gba", "mario.sav", content=b"OLD")
    ab_f = _write(ab, "gba", "mario.sav", content=b"NEW")
    os.utime(pc_f, (0, 0))
    os.utime(ab_f, (100, 100))

    items = list(plan_direction(pc, ab, "newest", _WANTED))

    assert len(items) == 1
    assert items[0].src == ab_f
    assert items[0].dst == pc_f


def test_copy_item_safe_mode_skips_existing_dst(tmp_path: Path) -> None:
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    src = _write(pc, "mario.sav", content=b"NEW")
    dst = _write(ab, "mario.sav", content=b"OLD")

    tag, size = copy_item(CopyPlanItem(src, dst, "-> Anbernic"), CopyPolicy(safe_mode=True))

    assert tag == "SAFE"
    assert size == 0
    assert dst.read_bytes() == b"OLD"


def test_copy_item_copies_when_no_conflict(tmp_path: Path) -> None:
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    src = _write(pc, "mario.sav", content=b"DATA")
    dst = ab / "mario.sav"

    tag, size = copy_item(CopyPlanItem(src, dst, "-> Anbernic"), CopyPolicy())

    assert tag == "COPY"
    assert size == 4
    assert dst.read_bytes() == b"DATA"


def test_copy_item_dry_run_does_not_touch_disk(tmp_path: Path) -> None:
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    src = _write(pc, "mario.sav", content=b"DATA")
    dst = ab / "mario.sav"

    tag, _ = copy_item(CopyPlanItem(src, dst, "-> Anbernic"), CopyPolicy(dry_run=True))

    assert tag == "DRYRUN"
    assert not dst.exists()


def test_plan_anbernic_to_pc(tmp_path: Path) -> None:
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    _write(ab, "gba", "mario.sav")

    items = list(plan_direction(pc, ab, "anbernic_to_pc", _WANTED))

    assert len(items) == 1
    assert items[0].dst == pc / "gba" / "mario.sav"
    assert items[0].arrow == "<- PC"


def test_plan_newest_skips_equal_mtimes(tmp_path: Path) -> None:
    import os

    pc, ab = tmp_path / "pc", tmp_path / "ab"
    pc_f = _write(pc, "mario.sav", content=b"A")
    ab_f = _write(ab, "mario.sav", content=b"B")
    os.utime(pc_f, (50, 50))
    os.utime(ab_f, (50, 50))

    items = list(plan_direction(pc, ab, "newest", _WANTED))

    assert items == []


def test_plan_newest_skips_mtimes_within_tolerance(tmp_path: Path) -> None:
    """REV43-4: diferencia de 1s (redondeo típico de FAT32/exFAT en la SD del
    Anbernic) no debe elegir un "ganador" — ambos lados se tratan como
    equivalentes, igual que con mtimes idénticos."""
    import os

    pc, ab = tmp_path / "pc", tmp_path / "ab"
    pc_f = _write(pc, "mario.sav", content=b"A")
    ab_f = _write(ab, "mario.sav", content=b"B")
    os.utime(pc_f, (50, 50))
    os.utime(ab_f, (51, 51))

    items = list(plan_direction(pc, ab, "newest", _WANTED))

    assert items == []


def test_plan_newest_picks_side_beyond_tolerance(tmp_path: Path) -> None:
    import os

    pc, ab = tmp_path / "pc", tmp_path / "ab"
    pc_f = _write(pc, "mario.sav", content=b"A")
    ab_f = _write(ab, "mario.sav", content=b"B")
    os.utime(pc_f, (50, 50))
    os.utime(ab_f, (53, 53))  # 3s > tolerancia por defecto (2s)

    items = list(plan_direction(pc, ab, "newest", _WANTED))

    assert len(items) == 1
    assert items[0].src == ab_f


def test_copy_item_skip_existing_same_size(tmp_path: Path) -> None:
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    src = _write(pc, "mario.sav", content=b"DATA")
    dst = _write(ab, "mario.sav", content=b"OLDD")  # same size, different bytes

    tag, size = copy_item(CopyPlanItem(src, dst, "-> Anbernic"), CopyPolicy(skip_existing=True))

    assert tag == "SKIP"
    assert size == 0
    assert dst.read_bytes() == b"OLDD"


def test_copy_item_error_on_missing_source(tmp_path: Path) -> None:
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    src = pc / "ghost.sav"  # never written
    dst = ab / "ghost.sav"

    tag, size = copy_item(CopyPlanItem(src, dst, "-> Anbernic"), CopyPolicy())

    assert tag == "ERROR"
    assert size == 0


def test_copy_item_emits_on_event(tmp_path: Path) -> None:
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    src = _write(pc, "mario.sav", content=b"DATA")
    dst = ab / "mario.sav"
    events: list[tuple[str, Path, Path]] = []

    def _on_event(tag: str, item: CopyPlanItem, note: str) -> None:
        events.append((tag, item.src, item.dst))

    tag, _ = copy_item(CopyPlanItem(src, dst, "-> Anbernic"), CopyPolicy(), on_event=_on_event)

    assert tag == "COPY"
    assert events == [("COPY", src, dst)]
