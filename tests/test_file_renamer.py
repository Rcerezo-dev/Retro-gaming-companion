"""ZIP-ROUTE-FIX-1: rename_rom_with_saves must create the target directory."""

from __future__ import annotations

from pathlib import Path

from rom_manager.renamer.file_renamer import rename_rom_with_saves


def test_rename_creates_missing_target_dir(tmp_path: Path) -> None:
    source = tmp_path / "Game (USA).nes"
    source.write_bytes(b"rom data")
    target = tmp_path / "Virtual Console" / "Game (USA).nes"

    outcome = rename_rom_with_saves(source, target, frozenset({".srm"}))

    assert outcome.success is True
    assert target.exists()
    assert not source.exists()


def test_rename_same_dir_still_works(tmp_path: Path) -> None:
    source = tmp_path / "Old Name.nes"
    source.write_bytes(b"rom data")
    target = tmp_path / "New Name.nes"

    outcome = rename_rom_with_saves(source, target, frozenset({".srm"}))

    assert outcome.success is True
    assert target.exists()
