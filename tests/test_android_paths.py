"""CABLE-ROOT-1d — canonical_rel_posix() traduce el nombre de carpeta de
plataforma del PC a su slug canónico de Android antes de un Cable Sync ADB,
para no espejar carpetas todavía sin renombrar (ver MDFOLDER-FIX-2/MATCH-FIX-5)."""

from __future__ import annotations

from rom_manager.sync.android_paths import (
    canonical_download_rel_posix,
    canonical_rel_posix,
    reconcile_newest_by_name,
)

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


# ---------------------------------------------------------------------------
# reconcile_newest_by_name — CABLE-SYNC-NEWEST-CANON-2
# ---------------------------------------------------------------------------


def test_reconcile_matches_exact_key_first() -> None:
    pairs = list(reconcile_newest_by_name({"gba/mario.sav": "pc"}, {"gba/mario.sav": "ab"}))
    assert pairs == [("gba/mario.sav", "pc", "gba/mario.sav", "ab")]


def test_reconcile_falls_back_to_unique_filename() -> None:
    pairs = list(reconcile_newest_by_name({"gba/mario.sav": "pc"}, {"saves/gba/mario.sav": "ab"}))
    assert pairs == [("gba/mario.sav", "pc", "saves/gba/mario.sav", "ab")]


def test_reconcile_ambiguous_filename_is_left_unmatched() -> None:
    pairs = list(
        reconcile_newest_by_name(
            {"gba/save.sav": "pc"},
            {"saves/gba/save.sav": "ab1", "saves/snes/save.sav": "ab2"},
        )
    )
    assert ("gba/save.sav", "pc", None, None) in pairs
    assert ("gba/save.sav", "pc") not in [(p[0], p[1]) for p in pairs if p[2] is not None]
    ab_only = {p[2] for p in pairs if p[0] is None}
    assert ab_only == {"saves/gba/save.sav", "saves/snes/save.sav"}


def test_reconcile_pc_only_and_ab_only_entries() -> None:
    pairs = list(reconcile_newest_by_name({"gba/new.sav": "pc"}, {"psx/old.sav": "ab"}))
    assert ("gba/new.sav", "pc", None, None) in pairs
    assert (None, None, "psx/old.sav", "ab") in pairs
    assert len(pairs) == 2


# ---------------------------------------------------------------------------
# canonical_download_rel_posix — CABLE-SYNC-DOWNLOAD-DEST-1
# ---------------------------------------------------------------------------


def test_download_strips_saves_prefix_when_platform_recognized() -> None:
    assert canonical_download_rel_posix("saves/gba/mario.sav", _ES_FOLDERS) == "gba/mario.sav"


def test_download_strips_states_prefix_when_platform_recognized() -> None:
    assert canonical_download_rel_posix("states/gba/mario.state", _ES_FOLDERS) == "gba/mario.state"


def test_download_leaves_unrecognized_core_folder_untouched() -> None:
    """saves/mame2003/... -- "mame2003" no es una plataforma reconocida (es un
    core), así que no se puede inferir con seguridad dónde va -- se deja tal
    cual en vez de arriesgar una ubicación incorrecta."""
    assert (
        canonical_download_rel_posix("saves/mame2003/nvram/foo.nv", _ES_FOLDERS)
        == "saves/mame2003/nvram/foo.nv"
    )


def test_download_without_wrapper_prefix_behaves_like_canonical_rel_posix() -> None:
    assert canonical_download_rel_posix("gba/mario.sav", _ES_FOLDERS) == "gba/mario.sav"
    assert (
        canonical_download_rel_posix("PlayStation 2/Dark Cloud (USA).iso", _ES_FOLDERS)
        == "ps2/Dark Cloud (USA).iso"
    )
