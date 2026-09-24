"""Tests de zip_router._route_identified (ZIP-ROUTE-4) — fases previas al pipeline."""

from __future__ import annotations

import zipfile
import zlib
from pathlib import Path

from rom_manager.web.builders.folders import _build_junk_scan
from rom_manager.web.zip_router import _route_identified


def _make_zip(path: Path, entries: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w") as z:
        for name, data in entries.items():
            z.writestr(name, data)


def _scan(root: Path, **kw) -> dict:
    defaults = dict(
        matched_paths=set(),
        arcade_names=set(),
        mame_infra_names=set(),
        known_bios_files=set(),
        crc_index={},
        arcade_crc_index={},
    )
    defaults.update(kw)
    return _build_junk_scan(str(root), **defaults)


def test_route_arcade_renames_and_moves(tmp_path: Path) -> None:
    """Arcade identificada → renombrada al set; con nombre correcto → tal cual."""
    unknown = tmp_path / "Unknown"
    unknown.mkdir()
    chip = b"chip"
    _make_zip(unknown / "Lemmings (United Kingdom).zip", {"lem.bin": chip})
    _make_zip(unknown / "flicky.zip", {"f1.117": b"x", "f2.110": b"y"})
    arcade_crcs = {f"{zlib.crc32(chip):08X}": {"lemmings"}}

    scan = _scan(tmp_path, arcade_names={"flicky"}, arcade_crc_index=arcade_crcs)
    arcade = tmp_path / "arcade"
    counts = _route_identified(scan, {"flicky"}, set(), set(), tmp_path / "Inbox", arcade)

    assert counts["arcade_moved"] == 2
    assert (arcade / "lemmings.zip").exists()  # renombrada al set
    assert (arcade / "flicky.zip").exists()
    assert not (unknown / "Lemmings (United Kingdom).zip").exists()
    assert counts["route_skipped"] == []


def test_route_never_overwrites(tmp_path: Path) -> None:
    """Conflicto en destino → no se toca nada y se reporta."""
    unknown = tmp_path / "Unknown"
    unknown.mkdir()
    chip = b"chip"
    _make_zip(unknown / "Lemmings (United Kingdom).zip", {"lem.bin": chip})
    arcade = tmp_path / "arcade"
    arcade.mkdir()
    (arcade / "lemmings.zip").write_bytes(b"ya existia")

    scan = _scan(tmp_path, arcade_crc_index={f"{zlib.crc32(chip):08X}": {"lemmings"}})
    counts = _route_identified(scan, set(), set(), set(), tmp_path / "Inbox", arcade)

    assert counts["arcade_moved"] == 0
    assert (unknown / "Lemmings (United Kingdom).zip").exists()  # fuente intacta
    assert (arcade / "lemmings.zip").read_bytes() == b"ya existia"
    assert len(counts["route_skipped"]) == 1


def test_route_collections_by_member_majority(tmp_path: Path) -> None:
    """Colección de consola → Inbox; de sets arcade → arcade\\; BIOS/infra → no tocar."""
    unknown = tmp_path / "Unknown"
    unknown.mkdir()
    _make_zip(unknown / "Nintendo - SNES.zip", {"a.zip": b"1", "b.zip": b"2"})
    _make_zip(unknown / "mamecol.zip", {"sf2.zip": b"3", "pang.zip": b"4"})
    _make_zip(unknown / "MAME BIOS 0.277.zip", {"neogeo.zip": b"5", "qsound.zip": b"6"})

    scan = _scan(tmp_path)
    inbox = tmp_path / "Inbox"
    arcade = tmp_path / "arcade"
    counts = _route_identified(
        scan,
        arcade_names={"sf2", "pang"},
        mame_infra_names={"neogeo", "qsound"},
        known_bios_files=set(),
        inbox_dir=inbox,
        arcade_folder=arcade,
    )

    assert counts["collections_extracted"] == 2
    assert counts["collection_members"] == 4
    # consola → subcarpeta del Inbox, contenedor borrado
    assert (inbox / "Nintendo - SNES" / "a.zip").exists()
    assert not (unknown / "Nintendo - SNES.zip").exists()
    # arcade → directo a arcade\, contenedor borrado
    assert (arcade / "sf2.zip").exists()
    assert not (unknown / "mamecol.zip").exists()
    # BIOS/infra → intacto y reportado
    assert (unknown / "MAME BIOS 0.277.zip").exists()
    assert any("BIOS/infra" in s for s in counts["route_skipped"])


def test_route_arcade_collection_with_subsystem_subfolders_flattens(tmp_path: Path) -> None:
    """ZIP-ROUTE-6: bestset con subcarpetas por sub-sistema (cps1/neogeo/...)
    — todo va a arcade\\ plano, sin anidar por la carpeta interna del ZIP."""
    unknown = tmp_path / "Unknown"
    unknown.mkdir()
    _make_zip(
        unknown / "fbneo_1003_bestset.zip",
        {
            "games/cps1/sf2.zip": b"1",
            "games/cps2/mvsc.zip": b"2",
            "games/neogeo/mslug.zip": b"3",
            "games/toaplan_cave_stg/ddonpach.zip": b"4",
        },
    )

    scan = _scan(tmp_path)
    arcade = tmp_path / "arcade"
    counts = _route_identified(
        scan,
        arcade_names={"sf2", "mvsc", "mslug", "ddonpach"},
        mame_infra_names=set(),
        known_bios_files=set(),
        inbox_dir=tmp_path / "Inbox",
        arcade_folder=arcade,
    )

    assert counts["collections_extracted"] == 1
    assert counts["collection_members"] == 4
    assert (arcade / "sf2.zip").exists()
    assert (arcade / "mvsc.zip").exists()
    assert (arcade / "mslug.zip").exists()
    assert (arcade / "ddonpach.zip").exists()
    assert not (arcade / "games").exists()  # nunca anidado por la carpeta interna
    assert not (unknown / "fbneo_1003_bestset.zip").exists()


def test_route_arcade_collection_flatten_skips_existing_by_basename(tmp_path: Path) -> None:
    """El chequeo de "ya existe" también debe mirar el nombre aplanado, no la
    ruta interna del ZIP (que nunca existirá en un destino plano)."""
    unknown = tmp_path / "Unknown"
    unknown.mkdir()
    _make_zip(
        unknown / "bestset.zip",
        {"games/cps1/sf2.zip": b"nuevo", "games/cps2/mvsc.zip": b"nuevo2"},
    )
    arcade = tmp_path / "arcade"
    arcade.mkdir()
    (arcade / "sf2.zip").write_bytes(b"ya existia")

    scan = _scan(tmp_path)
    counts = _route_identified(
        scan,
        arcade_names={"sf2", "mvsc"},
        mame_infra_names=set(),
        known_bios_files=set(),
        inbox_dir=tmp_path / "Inbox",
        arcade_folder=arcade,
    )

    assert counts["collections_extracted"] == 1
    assert counts["collection_members"] == 1  # solo mvsc.zip, sf2.zip ya existía
    assert (arcade / "sf2.zip").read_bytes() == b"ya existia"  # nunca sobreescrito
    assert (arcade / "mvsc.zip").read_bytes() == b"nuevo2"


def test_route_console_and_romhacks_go_to_inbox(tmp_path: Path) -> None:
    """Consola identificada y romhacks → al Inbox para el pipeline."""
    unknown = tmp_path / "Unknown"
    unknown.mkdir()
    rom = b"rom-conocido"
    _make_zip(unknown / "Wild Guns (Japan).zip", {"wg.sfc": rom})
    _make_zip(unknown / "Goemon [T-En].zip", {"g.nes": b"parche"})
    crc_index = {f"{zlib.crc32(rom):08X}": ("Wild Guns (USA)", "snes.dat", "SNES")}

    scan = _scan(tmp_path, crc_index=crc_index)
    inbox = tmp_path / "Inbox"
    counts = _route_identified(scan, set(), set(), set(), inbox, tmp_path / "arcade")

    assert counts["zips_to_inbox"] == 2
    assert (inbox / "Wild Guns (Japan).zip").exists()
    assert (inbox / "Goemon [T-En].zip").exists()
    assert not any(unknown.iterdir())
