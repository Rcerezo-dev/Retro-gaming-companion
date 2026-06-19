"""RPT-A1: a PSX `.bin` + `.cue` set must not be flagged as mixed_ext or gap.

`.cue` (and other sidecars) accompany the disc image; they're neither a second
image format nor a separate disc number.
"""

from __future__ import annotations

from pathlib import Path

from rom_manager.utils.multidisc_verifier import verify_multidisc


def _touch(directory: Path, *names: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for n in names:
        (directory / n).write_bytes(b"")


def _types(summary) -> set[str]:
    return {i.issue_type for i in summary.issues}


def test_bin_cue_set_is_clean(tmp_path: Path) -> None:
    psx = tmp_path / "psx"
    _touch(
        psx,
        "Driver 2 (Disc 1).bin",
        "Driver 2 (Disc 1).cue",
        "Driver 2 (Disc 2).bin",
        "Driver 2 (Disc 2).cue",
    )
    summary = verify_multidisc(tmp_path)
    assert summary.groups_with_issues == 0
    assert summary.groups_ok == 1
    assert _types(summary) == set()


def test_two_real_image_formats_flags_mixed_ext(tmp_path: Path) -> None:
    psx = tmp_path / "psx"
    _touch(psx, "Mix (Disc 1).bin", "Mix (Disc 2).iso")
    summary = verify_multidisc(tmp_path)
    assert "mixed_ext" in _types(summary)


def test_real_gap_still_detected(tmp_path: Path) -> None:
    psx = tmp_path / "psx"
    # Discs 1 and 3 present (each as .bin + .cue) — disc 2 genuinely missing.
    _touch(
        psx,
        "Game (Disc 1).bin",
        "Game (Disc 1).cue",
        "Game (Disc 3).bin",
        "Game (Disc 3).cue",
    )
    summary = verify_multidisc(tmp_path)
    types = _types(summary)
    assert "gap" in types
    assert "mixed_ext" not in types  # .bin + .cue is still not a mixed-ext issue
    gap = next(i for i in summary.issues if i.issue_type == "gap")
    assert "[2]" in gap.detail
