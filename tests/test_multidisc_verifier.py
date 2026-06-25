"""Tests for multidisc_verifier.py — RPT-A1 regression coverage."""

from __future__ import annotations

from pathlib import Path

from rom_manager.utils.multidisc_verifier import verify_multidisc


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x00" * 16)
    return path


class TestMixedExtFalsePositives:
    def test_bin_cue_not_flagged_as_mixed_ext(self, tmp_path: Path) -> None:
        """RPT-A1: a .bin+.cue PSX set must not raise mixed_ext."""
        for disc in [1, 2]:
            _touch(tmp_path / f"Driver 2 (Disc {disc}).bin")
            _touch(tmp_path / f"Driver 2 (Disc {disc}).cue")

        result = verify_multidisc(tmp_path)

        mixed = [i for i in result.issues if i.issue_type == "mixed_ext"]
        assert mixed == [], "bin+cue should not be flagged as mixed extension"

    def test_m3u_sidecar_not_flagged(self, tmp_path: Path) -> None:
        for disc in [1, 2]:
            _touch(tmp_path / f"Grandia (Disc {disc}).bin")
        _touch(tmp_path / "Grandia.m3u")
        # m3u doesn't match _DISC_RE so it's not included in groups; verify no mixed_ext
        result = verify_multidisc(tmp_path)
        mixed = [i for i in result.issues if i.issue_type == "mixed_ext"]
        assert mixed == []

    def test_genuine_mixed_images_flagged(self, tmp_path: Path) -> None:
        """A group with both .bin and .iso (two image types) must still flag mixed_ext."""
        _touch(tmp_path / "Game (Disc 1).bin")
        _touch(tmp_path / "Game (Disc 2).iso")

        result = verify_multidisc(tmp_path)

        mixed = [i for i in result.issues if i.issue_type == "mixed_ext"]
        assert len(mixed) == 1
        assert ".bin" in mixed[0].detail
        assert ".iso" in mixed[0].detail

    def test_homogeneous_bin_group_ok(self, tmp_path: Path) -> None:
        _touch(tmp_path / "Parasite Eve (Disc 1).bin")
        _touch(tmp_path / "Parasite Eve (Disc 2).bin")

        result = verify_multidisc(tmp_path)

        mixed = [i for i in result.issues if i.issue_type == "mixed_ext"]
        assert mixed == []

    def test_ccd_sbi_sidecars_not_flagged(self, tmp_path: Path) -> None:
        for disc in [1, 2]:
            _touch(tmp_path / f"Game (Disc {disc}).bin")
            _touch(tmp_path / f"Game (Disc {disc}).ccd")
            _touch(tmp_path / f"Game (Disc {disc}).sbi")

        result = verify_multidisc(tmp_path)

        mixed = [i for i in result.issues if i.issue_type == "mixed_ext"]
        assert mixed == []


class TestGapFalsePositives:
    """RPT-B2: sidecar files (.cue/.m3u) must not inflate disc_numbers and cause false gaps."""

    def test_bin_cue_two_discs_no_false_gap(self, tmp_path: Path) -> None:
        for disc in [1, 2]:
            _touch(tmp_path / f"Driver 2 (Disc {disc}).bin")
            _touch(tmp_path / f"Driver 2 (Disc {disc}).cue")

        result = verify_multidisc(tmp_path)

        gaps = [i for i in result.issues if i.issue_type == "gap"]
        assert gaps == [], "bin+cue per disc should not cause a false gap"

    def test_real_gap_still_detected(self, tmp_path: Path) -> None:
        _touch(tmp_path / "Koudelka (Disc 1).bin")
        _touch(tmp_path / "Koudelka (Disc 3).bin")  # disc 2 missing

        result = verify_multidisc(tmp_path)

        gaps = [i for i in result.issues if i.issue_type == "gap"]
        assert len(gaps) == 1
        assert "2" in gaps[0].detail


class TestMissingM3U:
    """RPT-B1: groups without an .m3u file must be flagged as missing_m3u."""

    def test_missing_m3u_flagged(self, tmp_path: Path) -> None:
        _touch(tmp_path / "Parasite Eve (Disc 1).bin")
        _touch(tmp_path / "Parasite Eve (Disc 2).bin")

        result = verify_multidisc(tmp_path)

        m3u_issues = [i for i in result.issues if i.issue_type == "missing_m3u"]
        assert len(m3u_issues) == 1
        assert m3u_issues[0].base_name == "Parasite Eve"

    def test_existing_m3u_not_flagged(self, tmp_path: Path) -> None:
        _touch(tmp_path / "Grandia (Disc 1).bin")
        _touch(tmp_path / "Grandia (Disc 2).bin")
        _touch(tmp_path / "Grandia.m3u")

        result = verify_multidisc(tmp_path)

        m3u_issues = [i for i in result.issues if i.issue_type == "missing_m3u"]
        assert m3u_issues == []

    def test_missing_m3u_detail_contains_filename(self, tmp_path: Path) -> None:
        _touch(tmp_path / "Driver 2 (Disc 1).bin")
        _touch(tmp_path / "Driver 2 (Disc 2).bin")

        result = verify_multidisc(tmp_path)

        m3u_issues = [i for i in result.issues if i.issue_type == "missing_m3u"]
        assert any("Driver 2.m3u" in i.detail for i in m3u_issues)
