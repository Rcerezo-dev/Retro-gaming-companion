"""Test for _loads_lenient: ScreenScraper sometimes appends garbage after the JSON."""

import pytest

from rom_manager.scraper.screenscraper import _loads_lenient


def test_parses_clean_json():
    assert _loads_lenient('{"response": {"jeu": {"id": 1}}}') == {"response": {"jeu": {"id": 1}}}


def test_tolerates_trailing_garbage():
    assert _loads_lenient('{"ok": true}\nAPI closed for maintenance') == {"ok": True}


def test_tolerates_leading_whitespace():
    assert _loads_lenient('  \n{"ok": true}') == {"ok": True}


def test_invalid_json_still_raises():
    with pytest.raises(ValueError):
        _loads_lenient("not json at all")
