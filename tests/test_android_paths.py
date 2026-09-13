"""CABLE-ROOT-1d — canonical_rel_posix() traduce el nombre de carpeta de
plataforma del PC a su slug canónico de Android antes de un Cable Sync ADB,
para no espejar carpetas todavía sin renombrar (ver MDFOLDER-FIX-2/MATCH-FIX-5)."""

from __future__ import annotations

from rom_manager.sync.android_paths import canonical_rel_posix

_ES_FOLDERS = {"PlayStation 2": "ps2", "Game Boy Advance": "gba"}


def test_translates_known_non_canonical_folder() -> None:
    assert (
        canonical_rel_posix("PlayStation 2/Dark Cloud (USA).iso", _ES_FOLDERS)
        == "ps2/Dark Cloud (USA).iso"
    )


def test_leaves_already_canonical_folder_untouched() -> None:
    assert canonical_rel_posix("gba/Kirby.gba", _ES_FOLDERS) == "gba/Kirby.gba"


def test_leaves_unknown_folder_untouched() -> None:
    assert canonical_rel_posix("BIOS/scph5501.bin", _ES_FOLDERS) == "BIOS/scph5501.bin"


def test_leaves_single_segment_path_untouched() -> None:
    assert canonical_rel_posix("gamelist.xml", _ES_FOLDERS) == "gamelist.xml"
