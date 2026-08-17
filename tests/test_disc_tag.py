from __future__ import annotations

import pytest

from rom_manager.utils.disc_tag import find_disc_number, find_disc_tag, has_disc_tag


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("Final Fantasy VII (Disc 2).cue", 2),
        ("Final Fantasy VII (Disc2).cue", 2),
        ("Final Fantasy VII Disc1.cue", 1),
        ("Final Fantasy VII Disc 1.cue", 1),
        ("Final Fantasy VII-cd2.cue", 2),
        ("Final Fantasy VII (Disk 3).cue", 3),
        ("Final Fantasy VII Disco 2.cue", 2),
        ("Final Fantasy VII.cue", None),
        ("Discworld (USA).cue", None),  # "Disc" not followed by a number → no false match
    ],
)
def test_find_disc_number(filename: str, expected: int | None) -> None:
    assert find_disc_number(filename) == expected


def test_find_disc_tag_normalizes_to_canonical_form() -> None:
    assert find_disc_tag("Final Fantasy VII Disc1.cue") == "(Disc 1)"
    assert find_disc_tag("Final Fantasy VII.cue") is None


def test_has_disc_tag() -> None:
    assert has_disc_tag("Final Fantasy VII (Disc 1)") is True
    assert has_disc_tag("Final Fantasy VII (Europe)") is False
