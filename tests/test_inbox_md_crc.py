"""AUD-4 — identificación de .md ambiguos del Inbox por CRC32.

Un .md suelto en la raíz del Inbox se identifica por contenido contra el
índice CRC de los DATs: hit de Mega Drive → inbox/megadrive/ (contexto de
carpeta para el resto del pipeline); miss o hit de otra plataforma → no se
toca (posible markdown real / caso raro a revisar a mano).
"""

from __future__ import annotations

import logging
import zlib
from pathlib import Path

import pytest

from rom_manager.catalog.matcher import CatalogMatcher
from rom_manager.config import load_config
from rom_manager.web.inbox_pipeline import _resolve_ambiguous_md

_logger = logging.getLogger("test")

ROM_BYTES = b"SEGA MEGA DRIVE ROM CONTENT"
ROM_CRC = f"{zlib.crc32(ROM_BYTES) & 0xFFFFFFFF:08X}"
GB_BYTES = b"GAME BOY ROM CONTENT"
GB_CRC = f"{zlib.crc32(GB_BYTES) & 0xFFFFFFFF:08X}"


@pytest.fixture()
def inbox(tmp_path, monkeypatch):
    index = {
        ROM_CRC: (
            "Sonic The Hedgehog (World)",
            "Sega - Mega Drive - Genesis.dat",
            "Sega Mega Drive",
        ),
        GB_CRC: ("Tetris (World)", "Nintendo - Game Boy.dat", "Game Boy"),
    }
    monkeypatch.setattr(CatalogMatcher, "crc_index", lambda self: index)
    # OJO: el nombre del test forma parte de tmp_path y sus tokens cuentan como
    # contexto de carpeta ("megadrive"/"md" en el nombre harían is_rom_file=True)
    box = tmp_path / "bandeja"
    box.mkdir()
    return box


def _run(inbox: Path) -> int:
    return _resolve_ambiguous_md(inbox, load_config(), _logger)


def test_rom_content_moves_to_platform_folder(inbox) -> None:
    (inbox / "sonic.md").write_bytes(ROM_BYTES)
    assert _run(inbox) == 1
    assert not (inbox / "sonic.md").exists()
    assert (inbox / "megadrive" / "sonic.md").read_bytes() == ROM_BYTES


def test_real_markdown_is_left_alone(inbox) -> None:
    readme = inbox / "README.md"
    readme.write_bytes(b"# Esto es markdown de verdad\n")
    assert _run(inbox) == 0
    assert readme.exists()
    assert not (inbox / "megadrive").exists()


def test_foreign_platform_crc_is_left_alone(inbox) -> None:
    weird = inbox / "tetris.md"
    weird.write_bytes(GB_BYTES)  # CRC de Game Boy con extensión .md — caso raro
    assert _run(inbox) == 0
    assert weird.exists()


def test_file_with_folder_context_is_not_a_candidate(inbox) -> None:
    # ya desambiguado por carpeta — lo procesa el pipeline normal, no este paso
    ctx = inbox / "megadrive" / "streets.md"
    ctx.parent.mkdir()
    ctx.write_bytes(ROM_BYTES)
    assert _run(inbox) == 0
    assert ctx.exists()


def test_collision_in_dest_is_not_overwritten(inbox) -> None:
    dest = inbox / "megadrive" / "sonic.md"
    dest.parent.mkdir()
    dest.write_bytes(b"YA EXISTIA")
    (inbox / "sonic.md").write_bytes(ROM_BYTES)
    assert _run(inbox) == 0
    assert dest.read_bytes() == b"YA EXISTIA"
    assert (inbox / "sonic.md").exists()
