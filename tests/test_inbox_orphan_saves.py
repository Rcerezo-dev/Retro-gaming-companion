"""Un save suelto en la raíz del Inbox (sin ROM acompañante en el mismo lote,
p. ej. copiado suelto desde la Anbernic) se reúne con su ROM ya organizado en
la biblioteca por coincidencia EXACTA de stem — nunca se sobreescribe, y si no
hay match único se deja intacto (nunca se descarta un save sin estar seguro
de que ya tiene copia en otro sitio)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from rom_manager.database.repository import LibraryRepository
from rom_manager.web.inbox_pipeline import _route_orphan_saves

_logger = logging.getLogger("test")
_TS = "2024-01-01T00:00:00"


@dataclass
class _FakeConfig:
    save_extensions: tuple[str, ...] = field(default_factory=lambda: (".sav",))


def _insert_game(repo: LibraryRepository, *, source_path: Path, platform: str) -> None:
    repo.upsert_game(
        original_filename=source_path.name,
        source_path=str(source_path),
        platform=platform,
        file_type="rom",
        relative_parent="",
        region="World",
        extension=source_path.suffix,
        size_bytes=1024,
        mtime=0,
        sha1="S" * 40,
        md5="M" * 32,
        crc32="CCCCCCCC",
        set_type="single",
        timestamp=_TS,
    )


@pytest.fixture()
def env(tmp_path):
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    nes_dir = tmp_path / "library" / "nes"
    nes_dir.mkdir(parents=True)
    return repo, inbox, nes_dir


def test_orphan_save_reunited_with_its_rom(env) -> None:
    repo, inbox, nes_dir = env
    rom = nes_dir / "Kid Dracula.nes"
    rom.write_bytes(b"rom data")
    _insert_game(repo, source_path=rom, platform="NES")

    save = inbox / "Kid Dracula.sav"
    save.write_bytes(b"save data")

    moved = _route_orphan_saves(inbox, repo, _FakeConfig(), _logger)

    assert moved == 1
    assert not save.exists()
    assert (nes_dir / "Kid Dracula.sav").read_bytes() == b"save data"


def test_no_match_leaves_save_untouched(env) -> None:
    repo, inbox, _nes_dir = env
    save = inbox / "Unknown Game.sav"
    save.write_bytes(b"save data")

    moved = _route_orphan_saves(inbox, repo, _FakeConfig(), _logger)

    assert moved == 0
    assert save.exists()


def test_ambiguous_match_leaves_save_untouched(env) -> None:
    repo, inbox, nes_dir = env
    gb_dir = nes_dir.parent / "gb"
    gb_dir.mkdir()
    rom_nes = nes_dir / "Kid Dracula.nes"
    rom_gb = gb_dir / "Kid Dracula.gb"
    rom_nes.write_bytes(b"a")
    rom_gb.write_bytes(b"b")
    _insert_game(repo, source_path=rom_nes, platform="NES")
    _insert_game(repo, source_path=rom_gb, platform="Game Boy")

    save = inbox / "Kid Dracula.sav"
    save.write_bytes(b"save data")

    moved = _route_orphan_saves(inbox, repo, _FakeConfig(), _logger)

    assert moved == 0
    assert save.exists()


def test_existing_destination_is_never_overwritten(env) -> None:
    repo, inbox, nes_dir = env
    rom = nes_dir / "Kid Dracula.nes"
    rom.write_bytes(b"rom data")
    _insert_game(repo, source_path=rom, platform="NES")
    existing = nes_dir / "Kid Dracula.sav"
    existing.write_bytes(b"already there")

    save = inbox / "Kid Dracula.sav"
    save.write_bytes(b"incoming save")

    moved = _route_orphan_saves(inbox, repo, _FakeConfig(), _logger)

    assert moved == 0
    assert save.exists()
    assert existing.read_bytes() == b"already there"
