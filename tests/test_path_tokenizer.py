"""Tests for services/path_tokenizer.py (DEVPROFILE-3)."""

from __future__ import annotations

from pathlib import Path

from rom_manager.services.path_tokenizer import resolve, tokenize


def _roots(tmp_path: Path) -> tuple[Path, Path, Path]:
    roms = tmp_path / "roms"
    saves = tmp_path / "roms" / "saves"  # nested inside roms, on purpose
    system = tmp_path / "system"
    for d in (roms, saves, system):
        d.mkdir(parents=True, exist_ok=True)
    return roms, saves, system


def test_tokenize_roundtrips_through_resolve(tmp_path: Path) -> None:
    roms, saves, system = _roots(tmp_path)
    path = roms / "nes" / "game.zip"

    token = tokenize(path, roms, saves, system)

    assert token == "{ROMS}/nes/game.zip"
    assert resolve(token, roms, saves, system) == path


def test_tokenize_prefers_more_specific_nested_root(tmp_path: Path) -> None:
    roms, saves, system = _roots(tmp_path)
    path = saves / "psx" / "game.srm"

    token = tokenize(path, roms, saves, system)

    assert token == "{SAVES}/psx/game.srm"


def test_tokenize_root_itself_has_no_trailing_slash(tmp_path: Path) -> None:
    roms, saves, system = _roots(tmp_path)
    assert tokenize(roms, roms, saves, system) == "{ROMS}"


def test_tokenize_path_outside_all_roots_returned_unchanged(tmp_path: Path) -> None:
    roms, saves, system = _roots(tmp_path)
    outside = tmp_path / "duckstation" / "settings.ini"

    assert tokenize(outside, roms, saves, system) == str(outside)


def test_resolve_untokenized_path_returned_as_path(tmp_path: Path) -> None:
    roms, saves, system = _roots(tmp_path)
    raw = str(tmp_path / "duckstation" / "settings.ini")

    assert resolve(raw, roms, saves, system) == Path(raw)


def test_resolve_uses_target_device_roots() -> None:
    # Same token, different device → different absolute path (the whole point).
    pc_roms = Path("E:/ROMs")
    android_roms = Path("/storage/emulated/0/RetroArch/roms")

    assert resolve("{ROMS}/nes/game.zip", pc_roms, pc_roms, pc_roms) == pc_roms / "nes" / "game.zip"
    assert (
        resolve("{ROMS}/nes/game.zip", android_roms, android_roms, android_roms)
        == android_roms / "nes" / "game.zip"
    )
