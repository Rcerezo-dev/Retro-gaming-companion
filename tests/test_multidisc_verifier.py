"""Tests for multidisc_verifier.py — RPT-A1 regression coverage."""

from __future__ import annotations

from pathlib import Path

import pytest

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
