from __future__ import annotations

import pytest
from rom_manager.detection.region_parser import parse_region_from_name


@pytest.mark.parametrize(
    "filename, expected",
    [
        # No-Intro parentheses style
        ("Tetris (USA).gb", "USA"),
        ("Super Mario World (Europe).sfc", "Europe"),
        ("Final Fantasy (Japan).nes", "Japan"),
        ("Tetris (World).gb", "World"),
        ("Castlevania (Spain).nes", "Spain"),
        ("Sonic the Hedgehog (Germany).md", "Germany"),
        ("Asterix (France).snes", "France"),
        ("Super Mario Bros (Italy).nes", "Italy"),
        ("Bubble Bobble (Korea).gba", "Korea"),
        ("Street Fighter (Brazil).sfc", "Brazil"),
        ("Donkey Kong (Australia).gbc", "Australia"),
        # Multi-region: first detected wins
        ("Game (USA, Europe).sfc", "USA"),
        ("Game (Europe, Japan).sfc", "Europe"),
        # GoodTools bracket codes
        ("Tetris [U].gb", "USA"),
        ("Super Mario [E].sfc", "Europe"),
        ("Final Fantasy [J].nes", "Japan"),
        # Case insensitive
        ("Game (usa).gb", "USA"),
        ("Game (EUROPE).sfc", "Europe"),
        # Plain-text fallbacks
        ("Game Japan Edition.sfc", "Japan"),
        ("Game JPN Version.gb", "Japan"),
        ("Game PAL Version.sfc", "Europe"),
        # No region
        ("Unknown Game.gb", "UNK"),
        ("ROM without any hint.sfc", "UNK"),
        # Extension-only filename edge case
        ("game.gb", "UNK"),
    ],
)
def test_parse_region_from_name(filename: str, expected: str) -> None:
    assert parse_region_from_name(filename) == expected


def test_returns_string_never_none() -> None:
    result = parse_region_from_name("completely unknown file.rom")
    assert isinstance(result, str)
    assert result == "UNK"


def test_goodtools_no_false_positive_on_long_bracket() -> None:
    # "[Gauntlet]" contains "[g]" as substring but must NOT match Germany.
    assert parse_region_from_name("Game [Gauntlet].gb") == "UNK"


def test_goodtools_no_false_positive_on_hack_code() -> None:
    # "[h C]" (hack) and "[!]" (verified) must not produce a region.
    assert parse_region_from_name("Game [h C].gb") == "UNK"
    assert parse_region_from_name("Game [!].gb") == "UNK"


def test_goodtools_mixed_with_other_codes() -> None:
    # "[U][!]" — USA code plus verified marker; must return USA.
    assert parse_region_from_name("Tetris [U][!].gb") == "USA"
