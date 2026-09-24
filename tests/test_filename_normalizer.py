from __future__ import annotations

import pytest

from rom_manager.detection.filename_normalizer import (
    is_non_canonical_variant,
    normalize_for_match,
    sanitize_filename,
)


@pytest.mark.parametrize(
    "value, expected",
    [
        # Invalid Windows characters replaced with underscore
        ("Game: The Adventure", "Game_ The Adventure"),
        ("Game/Sub", "Game_Sub"),
        ("Game\\Sub", "Game_Sub"),
        ('Game "Title"', "Game _Title_"),
        ("Game<Name>", "Game_Name_"),
        ("Game|Name", "Game_Name"),
        ("Game?Name", "Game_Name"),
        ("Game*Name", "Game_Name"),
        # Trailing dots stripped
        ("Game Title.", "Game Title"),
        ("Game Title...", "Game Title"),
        # Leading/trailing spaces stripped
        ("  Game Title  ", "Game Title"),
        # Multiple internal spaces collapsed
        ("Game   Title", "Game Title"),
        # Mixed: spaces + invalid chars
        ("  Game: Title  ", "Game_ Title"),
        # Empty string
        ("", ""),
        # Only invalid chars
        ("???", "___"),
        # Normal name unchanged
        ("Super Mario World [USA]", "Super Mario World [USA]"),
    ],
)
def test_sanitize_filename(value: str, expected: str) -> None:
    assert sanitize_filename(value) == expected


@pytest.mark.parametrize(
    "name, expected",
    [
        # Extension stripped
        ("tetris.gb", "tetris"),
        ("game.bin", "game"),
        ("game.iso", "game"),
        # Parentheses stripped (region, rev, flags)
        ("Tetris (World).gb", "tetris"),
        ("Tetris (World) (Rev 1).gb", "tetris"),
        ("Super Mario Land (World).gb", "super mario land"),
        # Brackets stripped (GoodTools flags)
        ("Tetris (World) [!].gb", "tetris"),
        ("Tetris (W) [b1].gb", "tetris"),
        # Underscores → spaces
        ("tetris_world.gb", "tetris world"),
        ("super_mario_land.gb", "super mario land"),
        # Hyphens → spaces
        ("super-mario.gb", "super mario"),
        # Catalog title without extension (no change to base)
        ("Tetris (World)", "tetris"),
        ("Metal Gear Solid (USA)", "metal gear solid"),
        # Empty annotations leave empty key
        ("(World).gb", ""),
        # Whitespace collapse
        ("  Tetris   (World) .gb", "tetris"),
        # Mixed underscores and parens
        ("tetris_(world)_[!].gb", "tetris"),
        # Accented characters → stripped combining marks (NFKD)
        ("Pokémon Red (World).gb", "pokemon red"),
        ("Donkey Kong Español.sfc", "donkey kong espanol"),
    ],
)
def test_normalize_for_match(name: str, expected: str) -> None:
    assert normalize_for_match(name) == expected


@pytest.mark.parametrize(
    "filename",
    [
        # romhacking.net translation-patch tags (found live: 22 Zelda
        # variants across a dozen languages, 2026-09-09)
        "Legend of Zelda, The (U) [T-Spa1.2v_Firionel].nes",
        "Legend of Zelda, The (U) (PRG0) [T+Fre.95].nes",
        "Digital Devil Story - Megami Tensei II (Japan) [T-Eng v1.3].nes",
        "Phantasy Star Adventure (Japan) [T-En by Aeon Genesis v1.00].gg",
        # explicit "(hack" tag
        "growl (hack, spanish).bin",
        "aladdin (hack, spanish).bin",
        # ROM hack subset
        "Wizardry - Proving Grounds of the Mad Overlord [Subset - Item Drops].nes",
        # No-Intro "hack" flag
        "Some Game (U) [h1].nes",
        "Some Game (U) [h].nes",
    ],
)
def test_is_non_canonical_variant_true(filename: str) -> None:
    assert is_non_canonical_variant(filename) is True


@pytest.mark.parametrize(
    "filename",
    [
        # plain region/revision/verified-dump tags must NOT trigger this
        "Legend of Zelda, The (USA) (Rev A).nes",
        "Legend of Zelda, The (U) [!].nes",
        "Tetris (World) [!].gb",
        "Tetris (W) [b1].gb",
        "Super Mario Bros. 2 (U) (PRG0) [!].nes",
        "Growl (USA)(1991)(Taito).bin",
        "Aladdin (Europe).zip",
        "",
    ],
)
def test_is_non_canonical_variant_false(filename: str) -> None:
    assert is_non_canonical_variant(filename) is False
