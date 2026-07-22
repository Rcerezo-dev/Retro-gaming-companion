"""Tests for gamelist_writer._deduplicate — multi-disc dedup logic."""

from __future__ import annotations

from rom_manager.scraper.gamelist_writer import _deduplicate


def _entry(filename: str, title: str = "Final Fantasy VII") -> dict:
    return {"filename": filename, "title": title}


def test_m3u_collapses_all_discs_of_same_set() -> None:
    """An .m3u playlist represents the whole set — individual discs must
    disappear from the gamelist once it's present."""
    entries = [
        _entry("Final Fantasy VII (Disc 1).cue"),
        _entry("Final Fantasy VII (Disc 2).cue"),
        _entry("Final Fantasy VII (Disc 3).cue"),
        _entry("Final Fantasy VII.m3u"),
    ]

    result = _deduplicate(entries)

    assert len(result) == 1
    assert result[0]["filename"] == "Final Fantasy VII.m3u"


def test_distinct_discs_without_m3u_are_not_collapsed() -> None:
    """REV43-29: without an .m3u, ScreenScraper commonly assigns the *same*
    title to every disc of a set — the old dedup key was title-only, so
    Disc 2/3 silently vanished from gamelist.xml, not just the "mixed
    .m3u vs .cue" case the dedup was originally meant to handle."""
    entries = [
        _entry("Final Fantasy VII (Disc 1).cue"),
        _entry("Final Fantasy VII (Disc 2).cue"),
        _entry("Final Fantasy VII (Disc 3).cue"),
    ]

    result = _deduplicate(entries)

    filenames = {e["filename"] for e in result}
    assert filenames == {
        "Final Fantasy VII (Disc 1).cue",
        "Final Fantasy VII (Disc 2).cue",
        "Final Fantasy VII (Disc 3).cue",
    }


def test_same_disc_duplicate_representations_still_collapse() -> None:
    """Two representations of the *same* disc (e.g. .cue and .chd) must still
    collapse to the higher-priority one — this is the original bug the
    dedup was meant to fix, and must not regress."""
    entries = [
        _entry("Final Fantasy VII (Disc 1).cue"),
        _entry("Final Fantasy VII (Disc 1).chd"),
    ]

    result = _deduplicate(entries)

    assert len(result) == 1
    assert result[0]["filename"] == "Final Fantasy VII (Disc 1).chd"


def test_single_disc_game_unaffected() -> None:
    entries = [_entry("Chrono Trigger.sfc", title="Chrono Trigger")]

    result = _deduplicate(entries)

    assert result == entries
