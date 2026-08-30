"""Tests for save_consolidator.py — SAVE-CONSOLIDATOR-1 fragmentation scanner."""

from __future__ import annotations

from pathlib import Path

from rom_manager.sync.save_consolidator import scan_save_groups

SAVE_EXTS = (".srm", ".sav")


def _save(root: Path, name: str, content: bytes) -> Path:
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return p


class TestGrouping:
    def test_single_copy_is_status_single(self, tmp_path: Path) -> None:
        _save(tmp_path, "snes/Chrono Trigger.srm", b"progress")
        (group,) = scan_save_groups(tmp_path, SAVE_EXTS)
        assert group.status == "single"
        assert len(group.entries) == 1

    def test_copy_suffix_and_folder_merge_into_one_group(self, tmp_path: Path) -> None:
        """Same shape as the Earthbound case in the SAVES-FRAGMENT-1 report:
        per-core folder + RetroArch's " (1)" suffix, same game."""
        _save(tmp_path, "saves/Snes9x/Earthbound (1).srm", b"real-progress")
        _save(tmp_path, "saves/snes/Earthbound.srm", b"real-progress")
        (group,) = scan_save_groups(tmp_path, SAVE_EXTS)
        assert group.stem == "Earthbound"
        assert len(group.entries) == 2

    def test_different_games_stay_in_different_groups(self, tmp_path: Path) -> None:
        _save(tmp_path, "a.srm", b"aaa")
        _save(tmp_path, "b.srm", b"bbb")
        groups = scan_save_groups(tmp_path, SAVE_EXTS)
        assert {g.stem for g in groups} == {"a", "b"}

    def test_non_save_extension_ignored(self, tmp_path: Path) -> None:
        _save(tmp_path, "readme.txt", b"not a save")
        assert scan_save_groups(tmp_path, SAVE_EXTS) == []


class TestStatus:
    def test_identical_content_is_dedup_safe(self, tmp_path: Path) -> None:
        _save(tmp_path, "saves/core_a/game.srm", b"same-progress")
        _save(tmp_path, "saves/core_b/game.srm", b"same-progress")
        (group,) = scan_save_groups(tmp_path, SAVE_EXTS)
        assert group.status == "identical"

    def test_divergent_content_flagged_for_manual_review(self, tmp_path: Path) -> None:
        _save(tmp_path, "saves/Snes9x/Earthbound (1).srm", b"newest-progress")
        _save(tmp_path, "saves/snes/Earthbound (1).srm", b"older-different-progress")
        (group,) = scan_save_groups(tmp_path, SAVE_EXTS)
        assert group.status == "divergent"

    def test_all_blank_group_is_safe_to_discard(self, tmp_path: Path) -> None:
        blank = b"\xff" * 8192
        _save(tmp_path, "saves/gba/Pokemon Red.sav", blank)
        _save(tmp_path, "saves/VBA Next/Pokemon Red.srm", blank)
        (group,) = scan_save_groups(tmp_path, SAVE_EXTS)
        assert group.status == "blank"

    def test_one_real_copy_beats_a_blank_one(self, tmp_path: Path) -> None:
        """A single non-blank copy alongside a blank template is an obvious
        winner, not a divergent case — the report calls this out (§5) as
        distinct from the 8 genuinely divergent groups."""
        blank = b"\xff" * 8192
        _save(tmp_path, "saves/gba/Megaman Zero.sav", b"real-progress-here")
        _save(tmp_path, "saves/VBA Next/Megaman Zero.srm", blank)
        (group,) = scan_save_groups(tmp_path, SAVE_EXTS)
        assert group.status == "identical"

    def test_uniform_fill_other_than_0xff_is_still_blank(self, tmp_path: Path) -> None:
        _save(tmp_path, "saves/nds/game.sav", b"\x00" * 1024)
        (group,) = scan_save_groups(tmp_path, SAVE_EXTS)
        assert group.status == "blank"

    def test_structured_data_is_not_mistaken_for_blank(self, tmp_path: Path) -> None:
        """The report's Metal Gear Solid false positive (§5): a real memcard
        starts with a 'MC' signature and varied bytes, and must never be
        flagged blank just because it shares a hash with other saves."""
        memcard = b"MC" + bytes(range(256)) * 4
        _save(tmp_path, "saves/psx/Metal Gear Solid (USA).srm", memcard)
        _save(tmp_path, "saves/Unknown/Metal Gear Solid (USA).srm", memcard)
        (group,) = scan_save_groups(tmp_path, SAVE_EXTS)
        assert group.status == "identical"
        assert not any(e.is_blank for e in group.entries)

    def test_lone_blank_save_flagged_even_without_a_duplicate(self, tmp_path: Path) -> None:
        _save(tmp_path, "saves/nds/Never Played.sav", b"\xff" * 1024)
        (group,) = scan_save_groups(tmp_path, SAVE_EXTS)
        assert group.status == "blank"
