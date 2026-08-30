"""Tests for _build_review_queue (TABS-FIX-6): fuses SHA1/title/RA duplicates
and plan conflicts into a single queue grouped by game."""

from __future__ import annotations

import json
from pathlib import Path

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.builders.duplicates import _build_review_queue

_TS = "2026-01-01T00:00:00"


def _insert_game(
    repo: LibraryRepository,
    *,
    source_path: str,
    sha1: str,
    md5: str = "m" * 32,
    original_filename: str = "game.gb",
    platform: str | None = "Game Boy",
    canonical_title: str | None = None,
    size_bytes: int = 1024,
) -> None:
    repo.upsert_game(
        original_filename=original_filename,
        source_path=source_path,
        platform=platform,
        file_type="rom",
        relative_parent="",
        region="USA",
        extension=".gb",
        size_bytes=size_bytes,
        mtime=0,
        sha1=sha1,
        md5=md5,
        crc32="CCCCCCCC",
        set_type="single",
        timestamp=_TS,
    )
    if canonical_title:
        repo.update_match(
            source_path,
            canonical_title=canonical_title,
            match_confidence="high",
            catalog_source="test.dat",
        )


def _write_ra_cache(project_root: Path, console_id: int, hashes: dict[str, int]) -> None:
    cache_dir = project_root / ".rommgr" / "ra_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    games = [
        {"ID": i, "Title": f"g{i}", "NumAchievements": n, "Hashes": [h]}
        for i, (h, n) in enumerate(hashes.items(), start=1)
    ]
    (cache_dir / f"ra_hashes_{console_id}.json").write_text(json.dumps(games), encoding="utf-8")


def test_sha1_duplicate_group(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path="/roms/a.gb", sha1="A" * 40, original_filename="tetris.gb")
    _insert_game(
        repo, source_path="/roms/backup/a.gb", sha1="A" * 40, original_filename="tetris.gb"
    )

    result = _build_review_queue(repo, repo, None)

    assert result["total_groups"] == 1
    group = result["groups"][0]
    assert group["reasons"] == ["sha1"]
    assert len(group["entries"]) == 2


def test_no_duplicates_no_groups(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path="/roms/a.gb", sha1="A" * 40)
    _insert_game(repo, source_path="/roms/b.gb", sha1="B" * 40, original_filename="other.gb")

    result = _build_review_queue(repo, repo, None)

    assert result["groups"] == []


def test_title_duplicate_same_exact_canonical_title(tmp_path: Path) -> None:
    """Two different dumps (distinct sha1) of the exact same canonical_title
    -> 'title'. This is the narrow, safe case; see the region-tags test below
    for the broader case that must NOT merge."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    path_a = str(tmp_path / "tetris_good_dump.gb")
    path_b = str(tmp_path / "tetris_bad_dump.gb")
    _insert_game(
        repo,
        source_path=path_a,
        sha1="A" * 40,
        original_filename="tetris_good_dump.gb",
        canonical_title="Tetris (USA)",
    )
    _insert_game(
        repo,
        source_path=path_b,
        sha1="B" * 40,
        original_filename="tetris_bad_dump.gb",
        canonical_title="Tetris (USA)",
    )

    result = _build_review_queue(repo, repo, None)

    assert result["total_groups"] == 1
    group = result["groups"][0]
    # Both dumps also want the same canonical target -> legitimately a
    # "collision" too, not asserted away here; the test only cares about "title".
    assert "title" in group["reasons"]
    assert {e["source_path"] for e in group["entries"]} == {path_a, path_b}


def test_misplaced_duplicate_loses_tie_to_correct_folder(tmp_path: Path) -> None:
    """INBOX-ORPHAN-4: with RA unsupported on both sides (true for every disc
    format today, INBOX-RA-HASH-GAP) and an identical filename, the old
    tiebreak fell through to insertion order — a misplaced duplicate could win
    just by being scanned first. The entry outside its platform folder must
    now lose the tie even when it has the lower row id."""
    from types import SimpleNamespace

    repo = LibraryRepository(tmp_path / "lib.sqlite")
    misplaced = str(tmp_path / "Game (USA)" / "Game (USA).rvz")
    correct = str(tmp_path / "gamecube" / "Game (USA).rvz")
    # Misplaced copy inserted FIRST -> lower row id, would have won pre-fix.
    _insert_game(
        repo,
        source_path=misplaced,
        sha1="A" * 40,
        original_filename="Game (USA).rvz",
        platform="GameCube",
        canonical_title="Game (USA)",
    )
    _insert_game(
        repo,
        source_path=correct,
        sha1="B" * 40,
        original_filename="Game (USA).rvz",
        platform="GameCube",
        canonical_title="Game (USA)",
    )

    config = SimpleNamespace(project_root=tmp_path, library_root=tmp_path)
    result = _build_review_queue(repo, repo, config)

    assert result["total_groups"] == 1
    recommended = next(e for e in result["groups"][0]["entries"] if e["recommended"])
    assert recommended["source_path"] == correct


def test_different_regions_are_not_merged(tmp_path: Path) -> None:
    """Regression (found against a real PSX library, see the multi-disc test
    below for the worse variant): region tags must NOT be stripped when
    deciding "same game" for the union — "Tetris (USA)" and "Tetris (Europe)"
    are different canonical_title strings and must stay separate groups.
    Merging them by a fuzzy normalized title merged 18 distinct regional PSX
    releases of Final Fantasy VII into one "duplicate" group in production
    data — a false negative here is far cheaper than a false positive that
    invites bulk-discarding a legitimate release."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(
        repo,
        source_path="/roms/tetris_usa.gb",
        sha1="A" * 40,
        canonical_title="Tetris (USA)",
    )
    _insert_game(
        repo,
        source_path="/roms/tetris_eu.gb",
        sha1="B" * 40,
        canonical_title="Tetris (Europe)",
    )

    result = _build_review_queue(repo, repo, None)

    assert result["groups"] == []


def test_ra_mixed_reason_and_recommendation(tmp_path: Path) -> None:
    """Two dumps of the exact same canonical_title, only one has RA
    achievements -> reason 'ra' added on top of 'title', and the RA-supported
    entry is recommended (same criterion the old '/api/ra-duplicates' view
    already used)."""
    config = load_config(tmp_path)
    _write_ra_cache(tmp_path, console_id=4, hashes={"m" * 32: 10})
    repo = LibraryRepository(config.database_path)
    path_a = str(tmp_path / "tetris_good.gb")
    path_b = str(tmp_path / "tetris_bad.gb")
    _insert_game(
        repo,
        source_path=path_a,
        sha1="A" * 40,
        md5="m" * 32,
        original_filename="tetris_good.gb",
        canonical_title="Tetris (USA)",
        platform="Game Boy Advance",
    )
    _insert_game(
        repo,
        source_path=path_b,
        sha1="B" * 40,
        md5="n" * 32,
        original_filename="tetris_bad.gb",
        canonical_title="Tetris (USA)",
        platform="Game Boy Advance",
    )

    result = _build_review_queue(repo, repo, config)

    assert result["total_groups"] == 1
    group = result["groups"][0]
    assert "ra" in group["reasons"]
    assert "title" in group["reasons"]  # distinct sha1 + same canonical_title also flags "title"
    recommended = next(e for e in group["entries"] if e["recommended"])
    assert recommended["source_path"] == path_a


def test_excluded_group_is_hidden(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(repo, source_path="/roms/a.gb", sha1="A" * 40, original_filename="tetris.gb")
    _insert_game(
        repo, source_path="/roms/backup/a.gb", sha1="A" * 40, original_filename="tetris.gb"
    )

    before = _build_review_queue(repo, repo, None)
    assert before["total_groups"] == 1
    group_key = before["groups"][0]["group_key"]

    repo.exclude_duplicate_group(group_key)
    after = _build_review_queue(repo, repo, None)

    assert after["groups"] == []


def test_plan_disk_conflict_single_entry_group(tmp_path: Path) -> None:
    """A 'disk' conflict has only one tracked DB row (the blocker on disk isn't
    a games row) — it must still surface, unlike sha1/title/ra groups which
    need >=2 entries to mean anything."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    (tmp_path / "Tetris (World).gb").touch()  # blocker: untracked file on disk
    messy = tmp_path / "messy_tetris.gb"
    messy.touch()
    _insert_game(
        repo,
        source_path=str(messy),
        sha1="A" * 40,
        canonical_title="Tetris (World)",
        platform="Game Boy",
    )

    result = _build_review_queue(repo, repo, None)

    disk_groups = [g for g in result["groups"] if "disk" in g["reasons"]]
    assert len(disk_groups) == 1
    assert len(disk_groups[0]["entries"]) == 1
    assert disk_groups[0]["entries"][0]["source_path"] == str(messy)
    assert disk_groups[0]["entries"][0]["target_name"] == "Tetris (World).gb"


def test_disk_conflict_mixed_into_title_group_does_not_crash_sort(tmp_path: Path) -> None:
    """Regression (found by hitting the real server): a disk-conflict entry
    (has 'conflict_role') can land in the same union-find cluster as a plain
    title-duplicate entry (no 'conflict_role') — e.g. a second dump of a ROM
    already correctly placed on disk. Sorting the mixed list must not raise
    str-vs-int."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    correct = tmp_path / "Tetris (USA).gb"
    correct.write_bytes(b"good dump")
    _insert_game(
        repo,
        source_path=str(correct),
        sha1="A" * 40,
        original_filename="Tetris (USA).gb",
        canonical_title="Tetris (USA)",
        platform="Game Boy",
    )
    messy = tmp_path / "tetris_bad_dump.gb"
    messy.write_bytes(b"bad dump")
    _insert_game(
        repo,
        source_path=str(messy),
        sha1="B" * 40,
        original_filename="tetris_bad_dump.gb",
        canonical_title="Tetris (USA)",  # same exact title -> "title" union
        platform="Game Boy",
    )
    # `correct` already occupies the canonical target -> messy's rename is a
    # "disk" conflict against it, while `correct` itself has no conflict_role.

    result = _build_review_queue(repo, repo, None)  # must not raise

    group = next(g for g in result["groups"] if "title" in g["reasons"])
    assert "disk" in group["reasons"]
    assert {e["source_path"] for e in group["entries"]} == {str(correct), str(messy)}


def test_multidisc_set_is_not_flagged_as_title_duplicate(tmp_path: Path) -> None:
    """Regression (found against a real PSX library): No-Intro/Redump DATs give
    every disc of a multi-disc game the SAME canonical_title (it doesn't encode
    the disc number) — "Final Fantasy VII (Disc 1/2/3).cue" all normalize to one
    cluster with 3 distinct sha1s, which looks exactly like a title-duplicate
    group. Without the disc-tag guard, 'Aplicar recomendación' would discard
    the other two discs as if they were alternate copies of the same disc.

    They *do* still collide in the plan (pre-existing planner gap: identical
    canonical_title across discs means identical rename target — tracked
    separately in the backlog, out of scope here) — this test only asserts
    the "title" false-positive is gone, not that the collision disappears.
    """
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    for i in range(1, 4):
        _insert_game(
            repo,
            source_path=str(tmp_path / "psx" / f"Final Fantasy VII (Disc {i}).cue"),
            sha1=chr(64 + i) * 40,
            original_filename=f"Final Fantasy VII (Disc {i}).cue",
            canonical_title="Final Fantasy VII (Europe)",
            platform="PSX",
        )

    result = _build_review_queue(repo, repo, None)

    assert not any("title" in g["reasons"] for g in result["groups"])


def test_gamecube_multi_disc_collision_flagged_as_risk(tmp_path: Path) -> None:
    """GAMECUBE-DISC-BUG-1a/1d/UX: a "collision" conflict on a platform that
    can have real multi-disc sets (here GameCube — excluded from the
    per-game-subfolder set since INBOX-ORPHAN-3, but still ships multi-disc
    titles) must carry the "multi_disc_risk" reason so the review UI can
    explain it instead of showing a plain, misleading "conflict"."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    for i in (1, 2):
        _insert_game(
            repo,
            source_path=str(tmp_path / "gamecube" / f"Twin Snakes (Disc {i}).rvz"),
            sha1=chr(64 + i) * 40,
            original_filename=f"Twin Snakes (Disc {i}).rvz",
            # Same canonical_title on purpose (GAMECUBE-DISC-BUG-1e): the
            # matcher used to assign Disc 1's DAT entry to every disc.
            canonical_title="Metal Gear Solid - The Twin Snakes (USA) (Disc 1)",
            platform="GameCube",
        )

    result = _build_review_queue(repo, repo, None)

    group = next(g for g in result["groups"] if "collision" in g["reasons"])
    assert "multi_disc_risk" in group["reasons"]


def test_non_disc_platform_collision_not_flagged_as_risk(tmp_path: Path) -> None:
    """Sanity check: a plain name collision on a platform with no real
    multi-disc concept (Game Boy) must NOT get the multi-disc explanation."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    for i in (1, 2):
        _insert_game(
            repo,
            source_path=str(tmp_path / f"tetris_{i}.gb"),
            sha1=chr(64 + i) * 40,
            original_filename=f"tetris_{i}.gb",
            canonical_title="Tetris (World)",
            platform="Game Boy",
        )

    result = _build_review_queue(repo, repo, None)

    group = next(g for g in result["groups"] if "collision" in g["reasons"])
    assert "multi_disc_risk" not in group["reasons"]
