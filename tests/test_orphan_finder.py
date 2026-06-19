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


class TestExclusions:
    """RPT-A2/A3: skip non-library folders and non-save data extensions."""

    # Includes .dat/.fs (emulator data) and .nv (real arcade NVRAM).
    EXTS = frozenset({".srm", ".nv", ".dat", ".fs"})

    def _names(self, orphans) -> set[str]:
        return {Path(o.save_path).name for o in orphans}

    def test_bios_folder_excluded(self, tmp_path: Path) -> None:
        _save(tmp_path, "BIOS/scummvm/theme/translations.dat")
        _save(tmp_path, "BIOS/mame2003-plus/hiscore.dat")
        assert find_orphaned_saves(tmp_path, self.EXTS) == []

    def test_system_volume_information_excluded(self, tmp_path: Path) -> None:
        _save(tmp_path, "System Volume Information/tracking.nv")
        assert find_orphaned_saves(tmp_path, self.EXTS) == []

    def test_hidden_and_discard_dirs_excluded(self, tmp_path: Path) -> None:
        _save(tmp_path, "_descartados/old.srm")
        _save(tmp_path, ".cache/tmp.srm")
        assert find_orphaned_saves(tmp_path, self.EXTS) == []

    def test_dat_and_fs_extensions_dropped(self, tmp_path: Path) -> None:
        _save(tmp_path, "CPS3/fbneo/sfiii.fs")
        _save(tmp_path, "saturn/theme.dat")
        _save(tmp_path, "cps2/ssf2.nv")  # real NVRAM save — still reported
        assert self._names(find_orphaned_saves(tmp_path, self.EXTS)) == {"ssf2.nv"}

    def test_real_orphan_in_normal_folder_still_found(self, tmp_path: Path) -> None:
        _save(tmp_path, "snes/Zelda.srm")
        assert self._names(find_orphaned_saves(tmp_path, self.EXTS)) == {"Zelda.srm"}
