"""Tests for orphan_finder.py — saves without matching ROMs."""

from __future__ import annotations

from pathlib import Path

from rom_manager.utils.orphan_finder import find_orphaned_saves

SAVE_EXTS = frozenset({".sav", ".srm", ".state", ".rtc"})


def _rom(root: Path, name: str) -> Path:
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"\x00" * 64)
    return p


def _save(root: Path, name: str, size: int = 32) -> Path:
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"\x00" * size)
    return p


class TestFindOrphanedSaves:
    def test_no_orphans_when_rom_exists(self, tmp_path: Path) -> None:
        _rom(tmp_path, "game.gba")
        _save(tmp_path, "game.sav")
        assert find_orphaned_saves(tmp_path, SAVE_EXTS) == []

    def test_orphan_detected_when_no_rom(self, tmp_path: Path) -> None:
        _save(tmp_path, "game.sav")
        orphans = find_orphaned_saves(tmp_path, SAVE_EXTS)
        assert len(orphans) == 1
        assert orphans[0].stem == "game"
        assert orphans[0].extension == ".sav"

    def test_multiple_save_exts_for_same_game(self, tmp_path: Path) -> None:
        """If ROM is present, neither .sav nor .srm should be orphaned."""
        _rom(tmp_path, "game.nes")
        _save(tmp_path, "game.sav")
        _save(tmp_path, "game.srm")
        assert find_orphaned_saves(tmp_path, SAVE_EXTS) == []

    def test_all_saves_orphaned_no_roms(self, tmp_path: Path) -> None:
        _save(tmp_path, "alpha.sav")
        _save(tmp_path, "beta.srm")
        orphans = find_orphaned_saves(tmp_path, SAVE_EXTS)
        assert len(orphans) == 2

    def test_sorted_by_path(self, tmp_path: Path) -> None:
        _save(tmp_path, "z_game.sav")
        _save(tmp_path, "a_game.sav")
        orphans = find_orphaned_saves(tmp_path, SAVE_EXTS)
        paths = [o.save_path for o in orphans]
        assert paths == sorted(paths)

    def test_size_bytes_correct(self, tmp_path: Path) -> None:
        _save(tmp_path, "game.sav", size=128)
        orphans = find_orphaned_saves(tmp_path, SAVE_EXTS)
        assert orphans[0].size_bytes == 128

    def test_case_insensitive_extension_matching(self, tmp_path: Path) -> None:
        _save(tmp_path, "game.SAV")
        orphans = find_orphaned_saves(tmp_path, SAVE_EXTS)
        assert len(orphans) == 1
        assert orphans[0].extension == ".sav"

    def test_save_in_subdirectory_no_rom(self, tmp_path: Path) -> None:
        """Save in subdirectory — not paired with ROM in parent dir."""
        _rom(tmp_path, "game.gba")
        _save(tmp_path, "subfolder/game.sav")
        orphans = find_orphaned_saves(tmp_path, SAVE_EXTS)
        assert len(orphans) == 1  # save in subfolder has no sibling ROM

    def test_rom_and_save_in_subfolder(self, tmp_path: Path) -> None:
        _rom(tmp_path, "gba/Metroid.gba")
        _save(tmp_path, "gba/Metroid.sav")
        assert find_orphaned_saves(tmp_path, SAVE_EXTS) == []

    def test_empty_directory(self, tmp_path: Path) -> None:
        assert find_orphaned_saves(tmp_path, SAVE_EXTS) == []

    def test_multiple_roms_only_no_orphans(self, tmp_path: Path) -> None:
        _rom(tmp_path, "game1.gba")
        _rom(tmp_path, "game2.nes")
        assert find_orphaned_saves(tmp_path, SAVE_EXTS) == []

    def test_state_extension_orphan(self, tmp_path: Path) -> None:
        _save(tmp_path, "game.state")
        orphans = find_orphaned_saves(tmp_path, SAVE_EXTS)
        assert len(orphans) == 1

    def test_non_save_extension_ignored(self, tmp_path: Path) -> None:
        _save(tmp_path, "game.txt")
        assert find_orphaned_saves(tmp_path, SAVE_EXTS) == []


class TestExcludedDirectories:
    """RPT-A2: BIOS/, hidden dirs and _descartados/ must be skipped."""

    def test_bios_dir_skipped(self, tmp_path: Path) -> None:
        _save(tmp_path, "BIOS/SCPH1001.sav")
        assert find_orphaned_saves(tmp_path, SAVE_EXTS) == []

    def test_bios_dir_case_insensitive(self, tmp_path: Path) -> None:
        _save(tmp_path, "bios/some.srm")
        assert find_orphaned_saves(tmp_path, SAVE_EXTS) == []

    def test_system_volume_information_skipped(self, tmp_path: Path) -> None:
        _save(tmp_path, "System Volume Information/tracking.sav")
        assert find_orphaned_saves(tmp_path, SAVE_EXTS) == []

    def test_descartados_skipped(self, tmp_path: Path) -> None:
        _save(tmp_path, "_descartados/old_game.srm")
        assert find_orphaned_saves(tmp_path, SAVE_EXTS) == []

    def test_hidden_dir_skipped(self, tmp_path: Path) -> None:
        _save(tmp_path, ".retroarch/game.sav")
        assert find_orphaned_saves(tmp_path, SAVE_EXTS) == []

    def test_normal_subdir_still_scanned(self, tmp_path: Path) -> None:
        """Non-excluded subdirectories must still be traversed."""
        _save(tmp_path, "psx/game.sav")
        orphans = find_orphaned_saves(tmp_path, SAVE_EXTS)
        assert len(orphans) == 1

    def test_save_outside_excluded_dir_detected(self, tmp_path: Path) -> None:
        """A save alongside ROMs must still be found even if sibling BIOS/ exists."""
        _save(tmp_path, "BIOS/bios.sav")
        _save(tmp_path, "psx/orphan.sav")
        orphans = find_orphaned_saves(tmp_path, SAVE_EXTS)
        assert len(orphans) == 1
        assert "orphan" in orphans[0].stem


class TestDefaultSaveExtensions:
    """RPT-A3: .dat and .fs must not be in the default save_extensions."""

    def test_dat_not_in_default_extensions(self, tmp_path: Path) -> None:
        from rom_manager.config import load_config

        cfg = load_config(tmp_path)
        assert ".dat" not in cfg.save_extensions

    def test_fs_not_in_default_extensions(self, tmp_path: Path) -> None:
        from rom_manager.config import load_config

        cfg = load_config(tmp_path)
        assert ".fs" not in cfg.save_extensions
