from __future__ import annotations

import pytest
from rom_manager.detection.filename_normalizer import normalize_for_match, sanitize_filename


@pytest.mark.parametrize(
    "value, expected",
    [
        # Invalid Windows characters replaced with underscore
        ('Game: The Adventure', 'Game_ The Adventure'),
        ('Game/Sub', 'Game_Sub'),
        ('Game\\Sub', 'Game_Sub'),
        ('Game "Title"', 'Game _Title_'),
        ('Game<Name>', 'Game_Name_'),
        ('Game|Name', 'Game_Name'),
        ('Game?Name', 'Game_Name'),
        ('Game*Name', 'Game_Name'),
        # Trailing dots stripped
        ('Game Title.', 'Game Title'),
        ('Game Title...', 'Game Title'),
        # Leading/trailing spaces stripped
        ('  Game Title  ', 'Game Title'),
        # Multiple internal spaces collapsed
        ('Game   Title', 'Game Title'),
        # Mixed: spaces + invalid chars
        ('  Game: Title  ', 'Game_ Title'),
        # Empty string
        ('', ''),
        # Only invalid chars
        ('???', '___'),
        # Normal name unchanged
        ('Super Mario World [USA]', 'Super Mario World [USA]'),
    ],
)
def test_sanitize_filename(value: str, expected: str) -> None:
    assert sanitize_filename(value) == expected


@pytest.mark.parametrize(
    "name, expected",
    [
        # Extension stripped
        ("tetris.gb",                      "tetris"),
        ("game.bin",                       "game"),
        ("game.iso",                       "game"),
        # Parentheses stripped (region, rev, flags)
        ("Tetris (World).gb",              "tetris"),
        ("Tetris (World) (Rev 1).gb",      "tetris"),
        ("Super Mario Land (World).gb",    "super mario land"),
        # Brackets stripped (GoodTools flags)
        ("Tetris (World) [!].gb",          "tetris"),
        ("Tetris (W) [b1].gb",             "tetris"),
        # Underscores → spaces
        ("tetris_world.gb",               "tetris world"),
        ("super_mario_land.gb",           "super mario land"),
        # Hyphens → spaces
        ("super-mario.gb",                "super mario"),
        # Catalog title without extension (no change to base)
        ("Tetris (World)",                "tetris"),
        ("Metal Gear Solid (USA)",        "metal gear solid"),
        # Empty annotations leave empty key
        ("(World).gb",                    ""),
        # Whitespace collapse
        ("  Tetris   (World) .gb",        "tetris"),
        # Mixed underscores and parens
        ("tetris_(world)_[!].gb",         "tetris"),
    ],
)
def test_normalize_for_match(name: str, expected: str) -> None:
    assert normalize_for_match(name) == expected
