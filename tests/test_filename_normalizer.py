from __future__ import annotations

import pytest
from rom_manager.detection.filename_normalizer import sanitize_filename


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
