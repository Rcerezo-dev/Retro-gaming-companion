from __future__ import annotations

import zlib
from pathlib import Path

import pytest

import rom_manager.converters.chd_converter as chd_converter
from rom_manager.converters.chd_converter import (
    ConversionSummary,
    bin_size_is_sector_aligned,
    convert_bin_to_chd,
    convert_directory,
    convert_to_chd,
    find_bare_bin_files,
    find_bins_matching_arcade_crc,
    find_bins_needing_cue,
    find_cue_files,
    find_pre_migration_orphan_cues,
    generate_missing_cues,
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


def test_find_pre_migration_orphan_cues_flags_cue_with_matching_subfolder(tmp_path: Path) -> None:
    (tmp_path / "psx" / "Game").mkdir(parents=True)
    orphan = tmp_path / "psx" / "Game.cue"
    orphan.touch()

    found = find_pre_migration_orphan_cues(tmp_path)
    assert found == [orphan]


def test_find_pre_migration_orphan_cues_ignores_cue_without_subfolder(tmp_path: Path) -> None:
    (tmp_path / "psx").mkdir(parents=True)
    (tmp_path / "psx" / "Game.cue").touch()

    assert find_pre_migration_orphan_cues(tmp_path) == []


def test_find_pre_migration_orphan_cues_ignores_cue_already_inside_its_subfolder(
    tmp_path: Path,
) -> None:
    """The normal post-migration shape (`psx/Game/Game.cue`) must not be
    flagged -- there's no *sibling* `Game/` next to it, `Game.cue` lives
    inside `Game/` itself."""
    game_dir = tmp_path / "psx" / "Game"
    game_dir.mkdir(parents=True)
    (game_dir / "Game.cue").touch()

    assert find_pre_migration_orphan_cues(tmp_path) == []


def test_find_bins_matching_arcade_crc_flags_misplaced_arcade_chip(tmp_path: Path) -> None:
    content = b"arcade rom chip data"
    bin_path = tmp_path / "stray.bin"
    bin_path.write_bytes(content)
    crc = f"{zlib.crc32(content) & 0xFFFFFFFF:08X}"

    hits = find_bins_matching_arcade_crc(tmp_path, {crc: {"pacman"}})

    assert hits == {bin_path: {"pacman"}}


def test_find_bins_matching_arcade_crc_ignores_bins_claimed_by_a_cue(tmp_path: Path) -> None:
    content = b"arcade rom chip data"
    bin_path = tmp_path / "claimed.bin"
    bin_path.write_bytes(content)
    _write_cue(tmp_path / "game.cue", [bin_path.name])
    crc = f"{zlib.crc32(content) & 0xFFFFFFFF:08X}"

    assert find_bins_matching_arcade_crc(tmp_path, {crc: {"pacman"}}) == {}


def test_find_bins_matching_arcade_crc_empty_index_returns_nothing(tmp_path: Path) -> None:
    (tmp_path / "stray.bin").write_bytes(b"data")

    assert find_bins_matching_arcade_crc(tmp_path, {}) == {}


def test_find_bins_matching_arcade_crc_no_hit_returns_nothing(tmp_path: Path) -> None:
    (tmp_path / "stray.bin").write_bytes(b"data")

    assert find_bins_matching_arcade_crc(tmp_path, {"DEADBEEF": {"other_set"}}) == {}


def test_bin_size_is_sector_aligned_2352() -> None:
    assert bin_size_is_sector_aligned(2352 * 100) is True


def test_bin_size_is_sector_aligned_2048() -> None:
    assert bin_size_is_sector_aligned(2048 * 50) is True


def test_bin_size_is_sector_aligned_rejects_2336_only() -> None:
    """MODE2/2336 is a geometry `detect_bin_cue_mode` accepts, but 2336 isn't
    2352 or 2048 -- a size that's only a multiple of 2336 must be flagged as
    non-standard, not silently treated as aligned."""
    size = 2336 * 10
    assert size % 2352 != 0 and size % 2048 != 0
    assert bin_size_is_sector_aligned(size) is False


def test_bin_size_is_sector_aligned_rejects_arbitrary_size() -> None:
    assert bin_size_is_sector_aligned(12345) is False


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


def test_find_bins_needing_cue_includes_geometry_valid_bins_without_ra_hash(
    tmp_path: Path,
) -> None:
    """A real disc whose RA hash can't be computed (e.g. no readable
    SYSTEM.CNF) must still get a .cue sidecar -- unlike find_bare_bin_files,
    which requires a verified RA hash before treating a .bin as safe for
    automatic CHD conversion."""
    bin_path = tmp_path / "Loose Game (USA).bin"
    bin_path.write_bytes(b"\x00" * (2352 * 4))  # sector-aligned, no filesystem

    assert find_bare_bin_files(tmp_path) == []
    assert find_bins_needing_cue(tmp_path) == [bin_path]


def test_find_bins_needing_cue_excludes_bins_claimed_by_a_cue(tmp_path: Path) -> None:
    claimed_bin = tmp_path / "claimed.bin"
    claimed_bin.write_bytes(b"\x00" * (2352 * 4))
    _write_cue(tmp_path / "game.cue", [claimed_bin.name])

    assert find_bins_needing_cue(tmp_path) == []


def test_generate_missing_cues_dry_run_writes_nothing(tmp_path: Path) -> None:
    bin_path = tmp_path / "Loose Game (USA).bin"
    bin_path.write_bytes(b"\x00" * (2352 * 4))

    written = generate_missing_cues(tmp_path, dry_run=True)

    assert written == [bin_path.with_suffix(".cue")]
    assert not written[0].exists()


def test_generate_missing_cues_apply_writes_sidecar_only(tmp_path: Path) -> None:
    bin_path = tmp_path / "Loose Game (USA).bin"
    bin_path.write_bytes(b"\x00" * (2352 * 4))

    written = generate_missing_cues(tmp_path, dry_run=False)

    cue_path = bin_path.with_suffix(".cue")
    assert written == [cue_path]
    assert cue_path.exists()
    assert bin_path.exists()
    assert bin_path.read_bytes() == b"\x00" * (2352 * 4)  # untouched
    assert 'FILE "Loose Game (USA).bin" BINARY' in cue_path.read_text()


def test_generate_missing_cues_apply_handles_non_ascii_filename(tmp_path: Path) -> None:
    """Regression: No-Intro/Redump canonical names routinely carry accents
    (e.g. "Pokémon"). Writing the .cue as ascii used to raise
    UnicodeEncodeError -- but only after Path.write_text had already
    truncated/created the file, leaving a permanent 0-byte .cue that the
    cue_path.exists() guard would then skip forever on every re-run."""
    bin_path = tmp_path / "Pokémon (Europe).bin"
    bin_path.write_bytes(b"\x00" * (2352 * 4))

    written = generate_missing_cues(tmp_path, dry_run=False)

    cue_path = bin_path.with_suffix(".cue")
    assert written == [cue_path]
    assert cue_path.stat().st_size > 0
    assert 'FILE "Pokémon (Europe).bin" BINARY' in cue_path.read_text(encoding="utf-8")


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
def test_convert_to_chd_keeps_source_when_hash_cannot_be_verified(tmp_path: Path) -> None:
    """Regression: a .cue pointing at a bin with no computable RA hash (e.g.
    one 'generate-cues' wrote a sidecar for, since it deliberately doesn't
    require a hash -- see find_bins_needing_cue) must NOT have its source
    deleted by --delete-source just because chdman could still build a .chd
    from the raw bytes. Without a verified hash match there is no proof the
    .chd is a faithful copy, so deleting the only-verified original would be
    silent, unrecoverable data loss."""
    bin_path = tmp_path / "Unverifiable Game (USA).bin"
    bin_path.write_bytes(b"\x00" * (2352 * 4))  # sector-aligned, no real filesystem
    cue_path = tmp_path / "Unverifiable Game (USA).cue"
    _write_cue(cue_path, [bin_path.name])

    result = convert_to_chd(cue_path, chdman=str(_CHDMAN), delete_source=True)

    assert result.success, result.error
    assert result.chd_path.exists()
    assert bin_path.exists()  # NOT deleted -- hash was never verified
    assert cue_path.exists()


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
