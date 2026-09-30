"""Found live 2026-09-29 auditing the Anbernic real device: 195 PSX titles
have a raw .cue/.bin sitting redundant next to an already-converted .chd of
the exact same name (Final Fantasy VII/VIII, Metal Gear Solid, Xenogears...).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from rom_manager.converters.chd_cleanup import (
    find_redundant_chd_sources,
    verify_and_clean_one,
)

_CHDMAN = Path(__file__).resolve().parent.parent / "tools" / "chdman.exe"
_skip_no_chdman = pytest.mark.skipif(
    not _CHDMAN.exists(), reason="chdman.exe no disponible en tools/"
)


def test_find_redundant_chd_sources_matches_same_stem() -> None:
    files = [
        "/storage/x/psx/Final Fantasy VIII (USA) (Disc 1).cue",
        "/storage/x/psx/Final Fantasy VIII (USA) (Disc 1).bin",
        "/storage/x/psx/Final Fantasy VIII (USA) (Disc 1).chd",
        "/storage/x/psx/Xenogears (USA) (Disc 1).cue",  # no matching .chd — not a candidate
        "/storage/x/psx/Xenogears (USA) (Disc 1).bin",
    ]

    candidates = find_redundant_chd_sources(files)

    assert len(candidates) == 1
    c = candidates[0]
    assert c.cue_path == "/storage/x/psx/Final Fantasy VIII (USA) (Disc 1).cue"
    assert c.chd_path == "/storage/x/psx/Final Fantasy VIII (USA) (Disc 1).chd"
    assert c.directory == "/storage/x/psx"


def test_find_redundant_chd_sources_ignores_different_region() -> None:
    """The exact mismatch that made GDI-ORGANIZE-1's "Europe" .cue broken —
    a same-title-different-tag .chd must never be treated as this .cue's
    match just because they share a folder."""
    files = [
        "/storage/x/psx/Metal Gear Solid (Spain) (Disc 1).cue",
        "/storage/x/psx/Metal Gear Solid (Spain) (Disc 1).bin",
        "/storage/x/psx/Metal Gear Solid (USA) (Disc 1).chd",
    ]

    assert find_redundant_chd_sources(files) == []


def _write_cue(path: Path, bin_name: str) -> None:
    path.write_text(
        f'FILE "{bin_name}" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n',
        encoding="utf-8",
    )


@_skip_no_chdman
def test_verify_and_clean_one_local_match_removes_source(tmp_path: Path) -> None:
    from tests.test_ra_hash_psx import _build_psx_image

    game_dir = tmp_path / "psx"
    game_dir.mkdir()
    bin_path = _build_psx_image(game_dir)  # writes game_dir/"game.bin"
    cue_path = game_dir / "game.cue"
    chd_path = game_dir / "game.chd"
    _write_cue(cue_path, bin_path.name)

    import subprocess

    from rom_manager.utils.subprocess_flags import NO_WINDOW

    subprocess.run(
        [str(_CHDMAN), "createcd", "-i", str(cue_path), "-o", str(chd_path)],
        check=True,
        capture_output=True,
        creationflags=NO_WINDOW,
    )

    from rom_manager.converters.chd_cleanup import RedundantChdSourceCandidate

    candidate = RedundantChdSourceCandidate(
        directory=str(game_dir), cue_path=str(cue_path), chd_path=str(chd_path)
    )
    removed: list[str] = []

    result = verify_and_clean_one(
        candidate,
        pull_to=game_dir,
        chdman=str(_CHDMAN),
        remove_remote=removed.append,
        pull_file=None,
        dry_run=False,
    )

    assert result.verified
    assert not result.error
    # remote_bins is built with PurePosixPath (correct for the real ADB use
    # case) -- compare by name only here, not by separator style.
    assert {Path(p).name for p in result.removed_paths} == {cue_path.name, bin_path.name}
    assert removed == result.removed_paths


@_skip_no_chdman
def test_verify_and_clean_one_dry_run_does_not_remove(tmp_path: Path) -> None:
    from tests.test_ra_hash_psx import _build_psx_image

    game_dir = tmp_path / "psx"
    game_dir.mkdir()
    bin_path = _build_psx_image(game_dir)  # writes game_dir/"game.bin"
    cue_path = game_dir / "game.cue"
    chd_path = game_dir / "game.chd"
    _write_cue(cue_path, bin_path.name)

    import subprocess

    from rom_manager.utils.subprocess_flags import NO_WINDOW

    subprocess.run(
        [str(_CHDMAN), "createcd", "-i", str(cue_path), "-o", str(chd_path)],
        check=True,
        capture_output=True,
        creationflags=NO_WINDOW,
    )

    from rom_manager.converters.chd_cleanup import RedundantChdSourceCandidate

    candidate = RedundantChdSourceCandidate(
        directory=str(game_dir), cue_path=str(cue_path), chd_path=str(chd_path)
    )
    removed: list[str] = []

    result = verify_and_clean_one(
        candidate,
        pull_to=game_dir,
        chdman=str(_CHDMAN),
        remove_remote=removed.append,
        pull_file=None,
        dry_run=True,
    )

    assert result.verified
    assert removed == []


def test_verify_and_clean_one_reports_missing_bin(tmp_path: Path) -> None:
    game_dir = tmp_path / "psx"
    game_dir.mkdir()
    cue_path = game_dir / "Game (USA).cue"
    chd_path = game_dir / "Game (USA).chd"
    _write_cue(cue_path, "Game (USA).bin")  # .bin never created
    chd_path.write_bytes(b"not a real chd")

    from rom_manager.converters.chd_cleanup import RedundantChdSourceCandidate

    candidate = RedundantChdSourceCandidate(
        directory=str(game_dir), cue_path=str(cue_path), chd_path=str(chd_path)
    )

    result = verify_and_clean_one(
        candidate,
        pull_to=game_dir,
        chdman="nonexistent_chdman_binary",
        remove_remote=lambda _p: None,
        pull_file=None,
        dry_run=False,
    )

    assert not result.verified
    assert "no encontrados" in result.error


def test_verify_and_clean_one_survives_broken_remote_bin_reference(tmp_path: Path) -> None:
    """Real shape found live 2026-09-29: "Lunar - Silver Star Story Complete
    (USA) (Disc 2).cue" references a (Track 3).bin that doesn't actually
    exist on the device -- a pull failure for ONE candidate must never crash
    the whole batch (it did, before this fix)."""
    game_dir = tmp_path / "psx"
    game_dir.mkdir()
    cue_path = game_dir / "Game (USA) (Disc 2).cue"
    chd_path = game_dir / "Game (USA) (Disc 2).chd"
    _write_cue(cue_path, "Game (USA) (Disc 2) (Track 3).bin")
    chd_path.write_text("placeholder", encoding="utf-8")  # never actually pulled

    from rom_manager.converters.chd_cleanup import RedundantChdSourceCandidate

    candidate = RedundantChdSourceCandidate(
        directory="/storage/x/psx",
        cue_path="/storage/x/psx/Game (USA) (Disc 2).cue",
        chd_path="/storage/x/psx/Game (USA) (Disc 2).chd",
    )

    def flaky_pull(src: str, dst: Path) -> None:
        if src.endswith(".cue"):
            dst.write_bytes(cue_path.read_bytes())
            return
        raise OSError(f"adb pull falló: failed to stat remote object '{src}'")

    result = verify_and_clean_one(
        candidate,
        pull_to=tmp_path / "staging",
        chdman="nonexistent_chdman_binary",
        remove_remote=lambda _p: None,
        pull_file=flaky_pull,
        dry_run=True,
    )

    assert not result.verified
    assert "pull falló" in result.error
    assert not (tmp_path / "staging").exists()  # cleaned up despite the failure
