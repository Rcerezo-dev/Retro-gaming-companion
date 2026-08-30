from __future__ import annotations

from pathlib import Path

import pytest

import rom_manager.converters.chd_converter as chd_converter
from rom_manager.converters.chd_converter import (
    ConversionSummary,
    convert_bin_to_chd,
    convert_directory,
    find_bare_bin_files,
    find_cue_files,
    parse_bins_from_cue,
)
from tests.test_ra_hash_psx import _build_psx_image

_CHDMAN = Path(__file__).resolve().parent.parent / "tools" / "chdman.exe"


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


def test_parse_bins_from_cue_resolves_stale_absolute_path_by_basename(tmp_path: Path) -> None:
    """Regression (found against the real library): 'Crash 2.cue' carried
    'FILE "C:\\CRASH 2.BIN" BINARY' -- an absolute path from a different
    machine/tool. Only the basename must be trusted, matched against the
    real sibling file."""
    cue = tmp_path / "game.cue"
    real_bin = tmp_path / "GAME.BIN"
    real_bin.touch()
    cue.write_text('FILE "C:\\some\\other\\machine\\GAME.BIN" BINARY\nTRACK 01 MODE2/2352\n')

    result = parse_bins_from_cue(cue)

    assert result == [real_bin]


def test_find_bare_bin_files_excludes_bins_claimed_by_a_cue(tmp_path: Path) -> None:
    claimed_bin = tmp_path / "claimed.bin"
    claimed_bin.touch()
    _write_cue(tmp_path / "game.cue", [claimed_bin.name])
    _build_psx_image(tmp_path)
    (tmp_path / "game.bin").rename(tmp_path / "Loose Game (USA).bin")

    found = find_bare_bin_files(tmp_path)

    assert found == [tmp_path / "Loose Game (USA).bin"]


def test_find_bare_bin_files_excludes_files_with_no_filesystem(tmp_path: Path) -> None:
    """An orphan audio-track .bin (or any garbage file) has no ISO9660
    filesystem and must never be guessed at as a convertible disc."""
    (tmp_path / "not_a_disc.bin").write_bytes(b"just some random bytes, not a cd image")

    assert find_bare_bin_files(tmp_path) == []


@pytest.mark.skipif(not _CHDMAN.exists(), reason="chdman.exe no disponible en tools/")
def test_convert_bin_to_chd_end_to_end(tmp_path: Path) -> None:
    _build_psx_image(tmp_path)
    bin_path = tmp_path / "Test Game (USA).bin"
    (tmp_path / "game.bin").rename(bin_path)

    result = convert_bin_to_chd(bin_path, chdman=str(_CHDMAN), delete_source=True)

    assert result.success, result.error
    assert result.chd_path.exists()
    assert not bin_path.exists()


@pytest.mark.skipif(not _CHDMAN.exists(), reason="chdman.exe no disponible en tools/")
def test_convert_directory_apply_picks_up_bare_bins(tmp_path: Path) -> None:
    _build_psx_image(tmp_path)
    (tmp_path / "game.bin").rename(tmp_path / "Test Game (USA).bin")

    summary = convert_directory(tmp_path, chdman=str(_CHDMAN), delete_source=True, dry_run=False)

    assert summary.converted == 1
    assert summary.failed == 0
    assert (tmp_path / "Test Game (USA).chd").exists()
    assert not (tmp_path / "Test Game (USA).bin").exists()


@pytest.mark.skipif(not _CHDMAN.exists(), reason="chdman.exe no disponible en tools/")
def test_convert_bin_to_chd_rejects_on_ra_hash_mismatch(tmp_path: Path, monkeypatch) -> None:
    """If the disc's RA hash doesn't match before/after conversion, the
    original must be left untouched and the bad .chd removed -- this is the
    safety net a lossy or buggy conversion would trip."""
    _build_psx_image(tmp_path)
    bin_path = tmp_path / "Test Game (USA).bin"
    (tmp_path / "game.bin").rename(bin_path)

    real_hash = chd_converter.compute_psx_ra_hash
    monkeypatch.setattr(
        chd_converter,
        "compute_psx_ra_hash",
        lambda path, **kw: "0" * 32 if str(path).endswith(".chd") else real_hash(path, **kw),
    )

    result = convert_bin_to_chd(bin_path, chdman=str(_CHDMAN), delete_source=True)

    assert not result.success
    assert "no coincide" in result.error
    assert bin_path.exists()  # original untouched
    assert not result.chd_path.exists()  # bad chd removed
