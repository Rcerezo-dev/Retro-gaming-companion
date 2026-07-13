"""AUD-3 — Papelera unificada: soft-discard, stats y purga por antigüedad."""

from __future__ import annotations

import os
import time
from pathlib import Path

from rom_manager.utils.trash import discard_to_trash, purge_trash, trash_stats


def _mk(root: Path, rel: str, content: bytes = b"DATA") -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return p


def test_discard_moves_to_sibling_trash(tmp_path) -> None:
    f = _mk(tmp_path, "snes/mario.sfc")
    dest = discard_to_trash(f)
    assert not f.exists()
    assert dest == tmp_path / "snes" / "_descartados" / "mario.sfc"
    assert dest.read_bytes() == b"DATA"


def test_discard_collision_gets_suffix_never_overwrites(tmp_path) -> None:
    first = discard_to_trash(_mk(tmp_path, "snes/mario.sfc", b"PRIMERO"))
    second = discard_to_trash(_mk(tmp_path, "snes/mario.sfc", b"SEGUNDO"))
    assert first.read_bytes() == b"PRIMERO"  # el anterior no se pisa ni se borra
    assert second.name == "mario (1).sfc"
    assert second.read_bytes() == b"SEGUNDO"


def test_discard_sets_mtime_to_now(tmp_path) -> None:
    f = _mk(tmp_path, "gba/old.gba")
    old = time.time() - 400 * 86400
    os.utime(f, (old, old))
    dest = discard_to_trash(f)
    # mtime = momento del descarte, no el original — base de la purga por edad
    assert time.time() - dest.stat().st_mtime < 60


def test_stats_and_purge_by_age(tmp_path) -> None:
    fresh = discard_to_trash(_mk(tmp_path, "snes/fresco.sfc"))
    stale = discard_to_trash(_mk(tmp_path, "gba/viejo.gba", b"VIEJO!"))
    old_ts = time.time() - 40 * 86400
    os.utime(stale, (old_ts, old_ts))

    stats = trash_stats([tmp_path])
    assert stats["files"] == 2 and stats["bytes"] == len(b"DATA") + len(b"VIEJO!")

    purged = purge_trash([tmp_path], older_than_days=30)
    assert purged == {"deleted": 1, "bytes": len(b"VIEJO!")}
    assert fresh.exists()
    assert not stale.exists()
    assert not stale.parent.exists()  # _descartados/ vacío se elimina

    # older_than_days=0 → vaciar todo (botón "Vaciar ahora")
    purged_all = purge_trash([tmp_path], older_than_days=0)
    assert purged_all["deleted"] == 1
    assert trash_stats([tmp_path]) == {"files": 0, "bytes": 0}


def test_purge_ignores_files_outside_trash(tmp_path) -> None:
    rom = _mk(tmp_path, "snes/juego.sfc")
    old_ts = time.time() - 100 * 86400
    os.utime(rom, (old_ts, old_ts))
    purged = purge_trash([tmp_path], older_than_days=0)
    assert purged["deleted"] == 0
    assert rom.exists()  # la biblioteca nunca se toca
