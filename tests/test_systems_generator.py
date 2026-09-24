"""Tests for esde/systems_generator.py — DEVPROFILE-1d core catalog migration."""

from __future__ import annotations

from pathlib import Path

from rom_manager.detection.platform_detector import pc_cores_by_system
from rom_manager.esde.systems_generator import _SYSTEMS, _find_core, generate_es_systems_xml

# Original hardcoded `cores` lists before DEVPROFILE-1d moved them into
# platforms.toml's [cores.pc] — kept here only to assert the migration didn't
# change any value.
_ORIGINAL_CORES: dict[str, list[str]] = {
    "nes": ["fceumm", "nestopia", "mesen"],
    "snes": ["snes9x", "bsnes", "mesen-s"],
    "n64": ["mupen64plus_next", "parallel_n64"],
    "gamecube": ["dolphin"],
    "wii": ["dolphin"],
    "gb": ["gambatte", "mgba", "sameboy"],
    "gbc": ["gambatte", "mgba", "sameboy"],
    "gba": ["mgba", "vba_next", "gpsp"],
    "nds": ["melonds", "desmume"],
    "3ds": ["citra", "citra2018"],
    "megadrive": ["genesis_plus_gx", "picodrive"],
    "mastersystem": ["genesis_plus_gx", "picodrive"],
    "gamegear": ["genesis_plus_gx"],
    "dreamcast": ["flycast"],
    "psx": ["duckstation", "pcsx_rearmed", "mednafen_psx_hw", "mednafen_psx"],
    "ps2": ["pcsx2"],
    "psp": ["ppsspp"],
    "mame": ["mame", "mame2003_plus", "mame2010", "mame2015"],
    "fbneo": ["fbneo"],
    "neogeo": ["fbneo", "mame"],
}


def test_pc_cores_by_system_matches_pre_migration_values() -> None:
    cores = pc_cores_by_system()
    assert cores == _ORIGINAL_CORES


def test_every_system_has_a_core_entry() -> None:
    cores = pc_cores_by_system()
    for sys_def in _SYSTEMS:
        assert sys_def["name"] in cores, f"missing cores.pc entry for {sys_def['name']}"


def test_mame_and_fbneo_keep_distinct_core_lists() -> None:
    """Regression guard: mame/fbneo share canonical platform "Arcade" but must
    not be merged into one candidate list (Roadmap-DEVPROFILE-1-4.md §2)."""
    cores = pc_cores_by_system()
    assert cores["mame"] != cores["fbneo"]
    assert "fbneo" not in cores["mame"]


def test_generate_es_systems_xml_still_matches_installed_cores(tmp_path: Path) -> None:
    cores_dir = tmp_path / "cores"
    cores_dir.mkdir()
    (cores_dir / "mgba_libretro.dll").touch()
    (cores_dir / "fbneo_libretro.dll").touch()

    result = generate_es_systems_xml(
        cores_dir=cores_dir,
        output_path=tmp_path / "es_systems.xml",
        write=False,
    )

    matched_names = {s.name for s in result.generated_systems}
    assert "gba" in matched_names  # mgba is gba's first candidate
    assert "fbneo" in matched_names
    assert "mame" not in matched_names  # no mame*_libretro.dll installed
    assert _find_core(cores_dir, pc_cores_by_system()["neogeo"]) == "fbneo_libretro.dll"
