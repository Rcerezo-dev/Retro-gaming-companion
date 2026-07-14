"""CABLE-UX-9b — smoke test del motor compartido de sync por filesystem.

Cobertura minima de plan_direction/copy_item para no dejar la logica sin un
check que reviente si se rompe. CABLE-UX-9f amplia esto (safe_mode/skew) una
vez el motor este enchufado a manual y SD-auto.
"""

from __future__ import annotations

from pathlib import Path

from rom_manager.sync.cable_engine import CopyPolicy, copy_item, plan_direction

_WANTED = lambda p: p.suffix == ".sav"  # noqa: E731


def _write(root: Path, *parts: str, content: bytes = b"x") -> Path:
    p = root.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return p


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

    from rom_manager.sync.cable_engine import CopyPlanItem

    tag, size = copy_item(CopyPlanItem(src, dst, "-> Anbernic"), CopyPolicy(safe_mode=True))

    assert tag == "SAFE"
    assert size == 0
    assert dst.read_bytes() == b"OLD"


def test_copy_item_copies_when_no_conflict(tmp_path: Path) -> None:
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    src = _write(pc, "mario.sav", content=b"DATA")
    dst = ab / "mario.sav"

    from rom_manager.sync.cable_engine import CopyPlanItem

    tag, size = copy_item(CopyPlanItem(src, dst, "-> Anbernic"), CopyPolicy())

    assert tag == "COPY"
    assert size == 4
    assert dst.read_bytes() == b"DATA"


def test_copy_item_dry_run_does_not_touch_disk(tmp_path: Path) -> None:
    pc, ab = tmp_path / "pc", tmp_path / "ab"
    src = _write(pc, "mario.sav", content=b"DATA")
    dst = ab / "mario.sav"

    from rom_manager.sync.cable_engine import CopyPlanItem

    tag, _ = copy_item(CopyPlanItem(src, dst, "-> Anbernic"), CopyPolicy(dry_run=True))

    assert tag == "DRYRUN"
    assert not dst.exists()
