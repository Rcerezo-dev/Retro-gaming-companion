from __future__ import annotations

from pathlib import Path

from rom_manager.converters.chd_converter import (
    ConversionSummary,
    convert_directory,
    find_cue_files,
    parse_bins_from_cue,
)


def _write_cue(path: Path, bins: list[str]) -> None:
    lines = []
    for i, name in enumerate(bins, start=1):
        lines.append(f'FILE "{name}" BINARY')
        lines.append(f"  TRACK {i:02d} MODE2/2352")
        lines.append("    INDEX 01 00:00:00")
    path.write_text("\n".join(lines), encoding="utf-8")


def test_find_cue_files(tmp_path: Path) -> None:
    (tmp_path / "game.cue").touch()
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "other.cue").touch()
    (tmp_path / "readme.txt").touch()

    found = find_cue_files(tmp_path)
    assert len(found) == 2
    assert all(p.suffix == ".cue" for p in found)


def test_parse_bins_from_cue(tmp_path: Path) -> None:
    cue = tmp_path / "game.cue"
    bin1 = tmp_path / "game.bin"
    bin2 = tmp_path / "game (Track 2).bin"
    bin1.touch()
    bin2.touch()
    _write_cue(cue, [bin1.name, bin2.name])

    result = parse_bins_from_cue(cue)
    assert len(result) == 2
    assert bin1 in result
    assert bin2 in result


def test_parse_bins_missing_file(tmp_path: Path) -> None:
    # parse_bins_from_cue returns all referenced bins regardless of existence
    cue = tmp_path / "game.cue"
    _write_cue(cue, ["missing.bin"])
    result = parse_bins_from_cue(cue)
    assert len(result) == 1
    assert result[0].name == "missing.bin"


def test_convert_directory_dry_run(tmp_path: Path) -> None:
    cue = tmp_path / "Metal Gear Solid (USA).cue"
    bin_file = tmp_path / "Metal Gear Solid (USA).bin"
    bin_file.touch()
    _write_cue(cue, [bin_file.name])

    summary = convert_directory(tmp_path, dry_run=True)

    assert isinstance(summary, ConversionSummary)
    assert summary.converted == 1
    assert summary.skipped == 0
    assert summary.failed == 0
    # Dry run: nothing actually converted
    assert not cue.with_suffix(".chd").exists()
    assert cue.exists()
    assert bin_file.exists()


def test_convert_directory_dry_run_skips_existing_chd(tmp_path: Path) -> None:
    cue = tmp_path / "game.cue"
    _write_cue(cue, [])
    (tmp_path / "game.chd").touch()

    summary = convert_directory(tmp_path, dry_run=True)
    assert summary.skipped == 1
    assert summary.converted == 0


def test_convert_directory_dry_run_flags_missing_bins(tmp_path: Path) -> None:
    # PSX-FIX-1: a .cue referencing a .bin that doesn't exist must not be
    # reported as "convertible" just because no .chd exists yet.
    cue = tmp_path / "Broken Game (USA).cue"
    _write_cue(cue, ["Broken Game (USA) (Track 01).bin"])

    summary = convert_directory(tmp_path, dry_run=True)

    assert summary.converted == 0
    assert summary.failed == 1
    assert "not found" in summary.results[0].error


def test_convert_directory_apply_chdman_not_found(tmp_path: Path) -> None:
    cue = tmp_path / "game.cue"
    _write_cue(cue, [])

    summary = convert_directory(
        tmp_path,
        chdman="nonexistent_chdman_binary",
        dry_run=False,
    )
    assert summary.failed == 1
    assert "not found" in summary.results[0].error
