"""ARCADE-RECON — reconstrucción de sets MAME sueltos por cobertura CRC.

Un chip suelto no dice a qué máquina pertenece por sí solo (su CRC puede
vivir en varios sets, parent/clones comparten roms) — pero un set completo
sí es inequívoco: solo se reclama una máquina cuando el 100% de sus roms
esperados están presentes entre los sueltos.
"""

from __future__ import annotations

import logging
import zipfile
import zlib
from pathlib import Path

import pytest

from rom_manager.catalog import mame_loader
from rom_manager.config import load_config
from rom_manager.web.inbox_pipeline import _reconstruct_loose_arcade_sets

_logger = logging.getLogger("test")

CHIP_A = b"PROGRAM ROM CHIP A"
CHIP_B = b"GRAPHICS ROM CHIP B"
CRC_A = f"{zlib.crc32(CHIP_A) & 0xFFFFFFFF:08X}"
CRC_B = f"{zlib.crc32(CHIP_B) & 0xFFFFFFFF:08X}"

MANIFEST = {
    "pacgame": [("prog.u1", CRC_A, len(CHIP_A)), ("gfx.u2", CRC_B, len(CHIP_B))],
}
CRC_INDEX = {CRC_A: {"pacgame"}, CRC_B: {"pacgame"}}


@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(mame_loader, "load_arcade_crc_index", lambda d: CRC_INDEX)
    monkeypatch.setattr(mame_loader, "load_arcade_manifest", lambda d: MANIFEST)
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    target = tmp_path / "library"
    target.mkdir()
    return inbox, target


def _run(inbox: Path, target: Path) -> dict:
    return _reconstruct_loose_arcade_sets(inbox, target, load_config(), _logger)


def test_full_coverage_reconstructs_and_discards_originals(env) -> None:
    inbox, target = env
    (inbox / "01.epr").write_bytes(CHIP_A)
    (inbox / "02.epr").write_bytes(CHIP_B)

    result = _run(inbox, target)

    assert result == {"reconstructed": 1, "chips_used": 2}
    dest = target / "arcade" / "pacgame.zip"
    assert dest.exists()
    with zipfile.ZipFile(dest) as zf:
        assert set(zf.namelist()) == {"prog.u1", "gfx.u2"}
        assert zf.read("prog.u1") == CHIP_A
        assert zf.read("gfx.u2") == CHIP_B
    assert not (inbox / "01.epr").exists()
    assert not (inbox / "02.epr").exists()


def test_partial_coverage_leaves_pool_untouched(env) -> None:
    inbox, target = env
    (inbox / "01.epr").write_bytes(CHIP_A)  # falta gfx.u2

    result = _run(inbox, target)

    assert result == {"reconstructed": 0, "chips_used": 0}
    assert (inbox / "01.epr").exists()
    assert not (target / "arcade" / "pacgame.zip").exists()


def test_existing_destination_is_never_overwritten(env) -> None:
    inbox, target = env
    (inbox / "01.epr").write_bytes(CHIP_A)
    (inbox / "02.epr").write_bytes(CHIP_B)
    dest_dir = target / "arcade"
    dest_dir.mkdir(parents=True)
    (dest_dir / "pacgame.zip").write_bytes(b"YA EXISTIA")

    result = _run(inbox, target)

    assert result == {"reconstructed": 0, "chips_used": 0}
    assert (dest_dir / "pacgame.zip").read_bytes() == b"YA EXISTIA"
    assert (inbox / "01.epr").exists()
    assert (inbox / "02.epr").exists()
