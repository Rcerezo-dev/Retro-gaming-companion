"""Tests for m3u_generator.py — multi-disc playlist generation."""

from __future__ import annotations

from pathlib import Path

from rom_manager.utils.m3u_generator import (
    find_disc_groups,
    generate_m3u_playlists,
    write_m3u,
)


def _make_disc(root: Path, name: str) -> Path:
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"\x00")
    return p


class TestFindDiscGroups:
    def test_two_disc_set_found(self, tmp_path: Path) -> None:
        _make_disc(tmp_path, "psx/Final Fantasy VII (USA) (Disc 1).chd")
        _make_disc(tmp_path, "psx/Final Fantasy VII (USA) (Disc 2).chd")
        groups = find_disc_groups(tmp_path)
        assert len(groups) == 1
        assert groups[0].base_name == "Final Fantasy VII (USA)"
        assert len(groups[0].discs) == 2

    def test_three_disc_set(self, tmp_path: Path) -> None:
        for i in range(1, 4):
            _make_disc(tmp_path, f"psx/Xenogears (USA) (Disc {i}).chd")
        groups = find_disc_groups(tmp_path)
        assert len(groups) == 1
        assert len(groups[0].discs) == 3

    def test_single_disc_not_grouped(self, tmp_path: Path) -> None:
        _make_disc(tmp_path, "psx/Suikoden (USA) (Disc 1).chd")
        groups = find_disc_groups(tmp_path)
        assert groups == []

    def test_disc_vs_disk_variants(self, tmp_path: Path) -> None:
        _make_disc(tmp_path, "saturn/Game (Disk 1).chd")
        _make_disc(tmp_path, "saturn/Game (Disk 2).chd")
        groups = find_disc_groups(tmp_path)
        assert len(groups) == 1

    def test_track_files_not_grouped(self, tmp_path: Path) -> None:
        """PSX multi-track .bin files — "(Disc 1) (Track 2)" must NOT match."""
        _make_disc(tmp_path, "psx/Game (Disc 1) (Track 1).bin")
        _make_disc(tmp_path, "psx/Game (Disc 1) (Track 2).bin")
        groups = find_disc_groups(tmp_path)
        assert groups == []

    def test_discs_sorted_by_number(self, tmp_path: Path) -> None:
        _make_disc(tmp_path, "psx/Game (Disc 3).chd")
        _make_disc(tmp_path, "psx/Game (Disc 1).chd")
        _make_disc(tmp_path, "psx/Game (Disc 2).chd")
        groups = find_disc_groups(tmp_path)
        discs = groups[0].discs
        nums = [int(d.stem.split("Disc ")[-1].rstrip(")")) for d in discs]
        assert nums == sorted(nums)

    def test_two_independent_sets(self, tmp_path: Path) -> None:
        _make_disc(tmp_path, "psx/FF7 (Disc 1).chd")
        _make_disc(tmp_path, "psx/FF7 (Disc 2).chd")
        _make_disc(tmp_path, "saturn/Panzer Dragoon (Disc 1).chd")
        _make_disc(tmp_path, "saturn/Panzer Dragoon (Disc 2).chd")
        groups = find_disc_groups(tmp_path)
        assert len(groups) == 2

    def test_m3u_path_in_same_dir(self, tmp_path: Path) -> None:
        _make_disc(tmp_path, "psx/Game (Disc 1).chd")
        _make_disc(tmp_path, "psx/Game (Disc 2).chd")
        groups = find_disc_groups(tmp_path)
        assert groups[0].m3u_path == tmp_path / "psx" / "Game.m3u"

    def test_platform_is_parent_folder_name(self, tmp_path: Path) -> None:
        _make_disc(tmp_path, "saturn/Game (Disc 1).chd")
        _make_disc(tmp_path, "saturn/Game (Disc 2).chd")
        groups = find_disc_groups(tmp_path)
        assert groups[0].platform == "saturn"

    def test_non_sequential_discs_still_grouped(self, tmp_path: Path) -> None:
        """Disc 1 and Disc 3 without Disc 2 — still grouped (no gap validation)."""
        _make_disc(tmp_path, "psx/Game (Disc 1).chd")
        _make_disc(tmp_path, "psx/Game (Disc 3).chd")
        groups = find_disc_groups(tmp_path)
        assert len(groups) == 1
        assert len(groups[0].discs) == 2

    def test_empty_directory(self, tmp_path: Path) -> None:
        assert find_disc_groups(tmp_path) == []

    def test_trailing_tag_after_disc_number_still_grouped(self, tmp_path: Path) -> None:
        """PSX-ORPHAN-3: '(Disc N)' followed by another tag, e.g. '(Rev 1)',
        was never matched before — the old regex required it to be the last tag."""
        _make_disc(tmp_path, "psx/Game (Disc 1) (Rev 1).chd")
        _make_disc(tmp_path, "psx/Game (Disc 2) (Rev 1).chd")
        groups = find_disc_groups(tmp_path)
        assert len(groups) == 1
        assert len(groups[0].discs) == 2

    def test_track_files_still_excluded_with_trailing_tag_support(self, tmp_path: Path) -> None:
        """Relaxing the end anchor for PSX-ORPHAN-3 must not resurrect the
        track-file false positive the original anchor was there to prevent."""
        _make_disc(tmp_path, "psx/Game (Disc 1) (Track 1).bin")
        _make_disc(tmp_path, "psx/Game (Disc 1) (Track 2).bin")
        groups = find_disc_groups(tmp_path)
        assert groups == []

    def test_non_disc_extension_never_grouped(self, tmp_path: Path) -> None:
        """PSX-ORPHAN-3: a save sharing the '(Disc N)' naming (e.g. from a
        renamed-with-saves ROM) must never be treated as part of a disc set —
        real case: a stray .srm produced a false 'Metal Gear Solid' group."""
        _make_disc(tmp_path, "psx/Metal Gear Solid (USA) (Disc 1).srm")
        _make_disc(tmp_path, "psx/Metal Gear Solid (USA) (Disc 2).srm")
        groups = find_disc_groups(tmp_path)
        assert groups == []

    def test_disc_image_and_save_do_not_cross_contaminate(self, tmp_path: Path) -> None:
        """A real 2-disc set alongside same-named saves: only the images group."""
        _make_disc(tmp_path, "psx/Metal Gear Solid (USA) (Disc 1).chd")
        _make_disc(tmp_path, "psx/Metal Gear Solid (USA) (Disc 2).chd")
        _make_disc(tmp_path, "psx/Metal Gear Solid (USA) (Disc 1).srm")
        groups = find_disc_groups(tmp_path)
        assert len(groups) == 1
        assert all(d.suffix == ".chd" for d in groups[0].discs)


class TestWriteM3u:
    def test_dry_run_returns_true_no_file_created(self, tmp_path: Path) -> None:
        _make_disc(tmp_path, "Game (Disc 1).chd")
        _make_disc(tmp_path, "Game (Disc 2).chd")
        groups = find_disc_groups(tmp_path)
        result = write_m3u(groups[0], dry_run=True)
        assert result is True
        assert not groups[0].m3u_path.exists()

    def test_apply_creates_m3u_file(self, tmp_path: Path) -> None:
        _make_disc(tmp_path, "Game (Disc 1).chd")
        _make_disc(tmp_path, "Game (Disc 2).chd")
        groups = find_disc_groups(tmp_path)
        write_m3u(groups[0], dry_run=False)
        assert groups[0].m3u_path.exists()

    def test_m3u_contains_disc_filenames(self, tmp_path: Path) -> None:
        _make_disc(tmp_path, "FF7 (Disc 1).chd")
        _make_disc(tmp_path, "FF7 (Disc 2).chd")
        groups = find_disc_groups(tmp_path)
        write_m3u(groups[0], dry_run=False)
        content = groups[0].m3u_path.read_text()
        assert "FF7 (Disc 1).chd" in content
        assert "FF7 (Disc 2).chd" in content

    def test_existing_m3u_returns_false(self, tmp_path: Path) -> None:
        _make_disc(tmp_path, "Game (Disc 1).chd")
        _make_disc(tmp_path, "Game (Disc 2).chd")
        groups = find_disc_groups(tmp_path)
        write_m3u(groups[0], dry_run=False)
        # Second call: file exists → should return False
        result = write_m3u(groups[0], dry_run=False)
        assert result is False


class TestGenerateM3uPlaylists:
    def test_summary_created_count(self, tmp_path: Path) -> None:
        for i in range(1, 3):
            _make_disc(tmp_path, f"psx/FF7 (Disc {i}).chd")
        for i in range(1, 3):
            _make_disc(tmp_path, f"saturn/Game (Disc {i}).chd")
        summary = generate_m3u_playlists(tmp_path, dry_run=False)
        assert summary.created == 2
        assert summary.skipped == 0

    def test_dry_run_no_files_written(self, tmp_path: Path) -> None:
        _make_disc(tmp_path, "Game (Disc 1).chd")
        _make_disc(tmp_path, "Game (Disc 2).chd")
        summary = generate_m3u_playlists(tmp_path, dry_run=True)
        assert summary.created == 1
        assert not list(tmp_path.glob("*.m3u"))

    def test_skipped_when_m3u_exists(self, tmp_path: Path) -> None:
        _make_disc(tmp_path, "Game (Disc 1).chd")
        _make_disc(tmp_path, "Game (Disc 2).chd")
        generate_m3u_playlists(tmp_path, dry_run=False)
        summary = generate_m3u_playlists(tmp_path, dry_run=False)
        assert summary.skipped == 1
        assert summary.created == 0
