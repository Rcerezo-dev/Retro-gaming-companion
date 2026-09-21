"""Tests for _build_review_queue (TABS-FIX-6): fuses SHA1/title/RA duplicates
and plan conflicts into a single queue grouped by game."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.builders.duplicates import (
    _build_review_queue,
    _find_rescue_candidate_in_trash,
    _is_broken_disc_entry,
)

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
    extension: str = ".gb",
) -> None:
    repo.upsert_game(
        original_filename=original_filename,
        source_path=source_path,
        platform=platform,
        file_type="rom",
        relative_parent="",
        region="USA",
        extension=extension,
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


def test_broken_cue_loses_to_intact_chd(tmp_path: Path) -> None:
    """REPAIR-TOOL-4: a `.cue` referencing a missing `.bin` must never outrank
    an intact `.chd` of the same game just because it wins the region/RA/
    folder tiebreaks — 11 of 31 real PSX-STRUCTURE-1 cases were exactly this.
    Without the integrity tier, the tie falls through to filename ordering
    and "(Europe).cue" < "(USA).chd" alphabetically would pick the broken one."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")

    cue_path = tmp_path / "psx" / "Game (Europe).cue"
    cue_path.parent.mkdir(parents=True)
    cue_path.write_text('FILE "Game (Europe).bin" BINARY\n', encoding="utf-8")
    # .bin deliberately not created -> broken cue/bin set

    chd_path = tmp_path / "psx" / "Game (USA).chd"
    chd_path.write_bytes(b"fake chd")

    _insert_game(
        repo,
        source_path=str(cue_path),
        sha1="A" * 40,
        original_filename="Game (Europe).cue",
        platform="PlayStation",
        canonical_title="Game",
    )
    _insert_game(
        repo,
        source_path=str(chd_path),
        sha1="B" * 40,
        original_filename="Game (USA).chd",
        platform="PlayStation",
        canonical_title="Game",
    )

    result = _build_review_queue(repo, repo, None)

    assert result["total_groups"] == 1
    recommended = next(e for e in result["groups"][0]["entries"] if e["recommended"])
    assert recommended["source_path"] == str(chd_path)


def test_find_rescue_candidate_in_trash_finds_local_match(tmp_path: Path) -> None:
    """REPAIR-TOOL-3: a different region/edition already discarded by a
    previous resolve-duplicates run counts as a rescue candidate -- fuzzy
    title match (region tag stripped) is intentional here."""
    broken = tmp_path / "psx" / "Game (Europe).cue"
    broken.parent.mkdir(parents=True)
    broken.touch()
    trash_dir = broken.parent / "_descartados"
    trash_dir.mkdir()
    healthy = trash_dir / "Game (USA).chd"
    healthy.write_bytes(b"fake chd")

    result = _find_rescue_candidate_in_trash(str(broken), "PlayStation", None)

    assert result == str(healthy)


def test_find_rescue_candidate_in_trash_finds_platform_wide_match(tmp_path: Path) -> None:
    """A subfolder-per-game layout (`psx/Game/Game.cue`) has no *local*
    `_descartados/` sibling with the rescue copy -- it's in the platform
    root's trash instead."""
    library_root = tmp_path
    broken = library_root / "psx" / "Game" / "Game (Europe).cue"
    broken.parent.mkdir(parents=True)
    broken.touch()
    platform_trash = library_root / "psx" / "_descartados"
    platform_trash.mkdir()
    healthy = platform_trash / "Game (USA).chd"
    healthy.write_bytes(b"fake chd")

    result = _find_rescue_candidate_in_trash(str(broken), "PlayStation", library_root)

    assert result == str(healthy)


def test_find_rescue_candidate_in_trash_returns_none_without_match(tmp_path: Path) -> None:
    broken = tmp_path / "psx" / "Game (Europe).cue"
    broken.parent.mkdir(parents=True)
    broken.touch()

    assert _find_rescue_candidate_in_trash(str(broken), "PlayStation", None) is None


def test_find_rescue_candidate_in_trash_skips_a_candidate_that_is_itself_broken(
    tmp_path: Path,
) -> None:
    broken = tmp_path / "psx" / "Game (Europe).cue"
    broken.parent.mkdir(parents=True)
    broken.touch()
    trash_dir = broken.parent / "_descartados"
    trash_dir.mkdir()
    # Same title in the trash, but it's a broken cue/bin set itself -- not a
    # real rescue candidate.
    also_broken = trash_dir / "Game (USA).cue"
    also_broken.write_text('FILE "Game (USA).bin" BINARY\n', encoding="utf-8")

    assert _find_rescue_candidate_in_trash(str(broken), "PlayStation", None) is None


def test_broken_entry_gets_rescue_candidate_via_review_queue(tmp_path: Path) -> None:
    """End-to-end: _build_review_queue annotates a broken entry with the
    rescue candidate found in trash; the intact entry is left untouched
    (no rescue_candidate key at all)."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")

    broken_cue = tmp_path / "psx" / "Game (Europe).cue"
    broken_cue.parent.mkdir(parents=True)
    broken_cue.write_text('FILE "Game (Europe).bin" BINARY\n', encoding="utf-8")
    # .bin deliberately not created -> broken

    intact = tmp_path / "psx" / "Game (Japan).chd"
    intact.write_bytes(b"fake chd")

    trash_dir = broken_cue.parent / "_descartados"
    trash_dir.mkdir()
    rescue = trash_dir / "Game (USA).chd"
    rescue.write_bytes(b"fake chd")

    _insert_game(
        repo,
        source_path=str(broken_cue),
        sha1="A" * 40,
        original_filename="Game (Europe).cue",
        platform="PlayStation",
        canonical_title="Game",
    )
    _insert_game(
        repo,
        source_path=str(intact),
        sha1="B" * 40,
        original_filename="Game (Japan).chd",
        platform="PlayStation",
        canonical_title="Game",
    )

    result = _build_review_queue(repo, repo, None)

    entries = {e["source_path"]: e for e in result["groups"][0]["entries"]}
    assert entries[str(broken_cue)]["rescue_candidate"] == str(rescue)
    assert "rescue_candidate" not in entries[str(intact)]


def test_different_regions_are_not_merged_on_disc_platforms(tmp_path: Path) -> None:
    """Regression (found against a real PSX library, see the multi-disc test
    below for the worse variant): on _MULTI_DISC_RISK_PLATFORMS, region tags
    must NOT be stripped when deciding "same game" for the fuzzy region union
    (DUP-REGION-1) — "Tetris (USA)" and "Tetris (Europe)" are different
    canonical_title strings and must stay separate groups. Merging them by a
    fuzzy normalized title merged 18 distinct regional PSX releases of Final
    Fantasy VII into one "duplicate" group in production data — a false
    negative here is far cheaper than a false positive that invites
    bulk-discarding a legitimate release. Single-file cart platforms (Game
    Boy, GBA, ...) don't carry this risk — see
    test_same_title_cross_region_flagged_for_review below."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(
        repo,
        source_path="/roms/tetris_usa.chd",
        sha1="A" * 40,
        canonical_title="Tetris (USA)",
        platform="PlayStation",
        original_filename="Tetris (USA).chd",
        extension=".chd",
    )
    _insert_game(
        repo,
        source_path="/roms/tetris_eu.chd",
        sha1="B" * 40,
        canonical_title="Tetris (Europe)",
        platform="PlayStation",
        original_filename="Tetris (Europe).chd",
        extension=".chd",
    )

    result = _build_review_queue(repo, repo, None)

    assert result["groups"] == []


def test_same_title_cross_region_flagged_for_review(tmp_path: Path) -> None:
    """DUP-REGION-1: on a single-file cart platform, the same game released
    under different No-Intro regions ("Tetris (USA)" vs "Tetris (Spain)") is
    flagged as a "region" duplicate group for manual review — never
    auto-merged or deleted, just surfaced with a recommendation. Per the
    user's tie-break rule: RA achievements decide first (only one version
    having achievements wins outright); language is only the fallback when
    both or neither have achievements."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(
        repo,
        source_path="/roms/tetris_usa.gb",
        sha1="A" * 40,
        canonical_title="Tetris (USA)",
        original_filename="Tetris (USA).gb",
    )
    _insert_game(
        repo,
        source_path="/roms/tetris_spain.gb",
        sha1="B" * 40,
        canonical_title="Tetris (Spain)",
        original_filename="Tetris (Spain).gb",
    )

    result = _build_review_queue(repo, repo, None)

    assert len(result["groups"]) == 1
    group = result["groups"][0]
    assert "region" in group["reasons"]
    entries = {e["filename"]: e for e in group["entries"]}
    assert entries["Tetris (Spain).gb"]["recommended"] is True
    assert entries["Tetris (USA).gb"]["recommended"] is False


def test_keep_both_regions_config_suppresses_region_groups(tmp_path: Path) -> None:
    """DUP-REGION-2: config.duplicates.keep_both_regions=True means the user
    deliberately keeps every region of every game -- the "region" reason must
    never fire, not even as an unrecommended group."""
    from types import SimpleNamespace

    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(
        repo,
        source_path="/roms/tetris_usa.gb",
        sha1="A" * 40,
        canonical_title="Tetris (USA)",
        original_filename="Tetris (USA).gb",
    )
    _insert_game(
        repo,
        source_path="/roms/tetris_spain.gb",
        sha1="B" * 40,
        canonical_title="Tetris (Spain)",
        original_filename="Tetris (Spain).gb",
    )

    config = SimpleNamespace(
        project_root=tmp_path,
        library_root=tmp_path,
        duplicates=SimpleNamespace(keep_both_regions=True, preferred_regions=["Spain", "Europe"]),
    )
    result = _build_review_queue(repo, repo, config)

    assert result["groups"] == []


def test_preferred_regions_config_overrides_default_ranking(tmp_path: Path) -> None:
    """DUP-REGION-2: preferred_regions is user-configurable, not hardcoded to
    Spain-then-Europe -- a user who prioritises Europe over Spain gets the
    European release recommended instead."""
    from types import SimpleNamespace

    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(
        repo,
        source_path="/roms/tetris_spain.gb",
        sha1="A" * 40,
        canonical_title="Tetris (Spain)",
        original_filename="Tetris (Spain).gb",
    )
    _insert_game(
        repo,
        source_path="/roms/tetris_eu.gb",
        sha1="B" * 40,
        canonical_title="Tetris (Europe)",
        original_filename="Tetris (Europe).gb",
    )

    config = SimpleNamespace(
        project_root=tmp_path,
        library_root=tmp_path,
        duplicates=SimpleNamespace(keep_both_regions=False, preferred_regions=["Europe", "Spain"]),
    )
    result = _build_review_queue(repo, repo, config)

    assert len(result["groups"]) == 1
    entries = {e["filename"]: e for e in result["groups"][0]["entries"]}
    assert entries["Tetris (Europe).gb"]["recommended"] is True
    assert entries["Tetris (Spain).gb"]["recommended"] is False


def test_title_union_skips_translation_variant(tmp_path: Path) -> None:
    """CATALOG-MATCH-VARIANT-1, hallazgo real 2026-09-09: un parche de
    traducción y el original comparten canonical_title (sea porque un fix
    futuro de matcher.py todavía no ha corregido esa fila, o porque cualquier
    otro camino se lo asignó) — nunca deben tratarse como el mismo archivo
    solo por eso. Un solo NES real (Zelda) llegó a tener 22 "duplicados" así.
    sha1 distinto = contenido realmente distinto, sin relación aparte del
    título."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(
        repo,
        source_path=str(tmp_path / "zelda_original.nes"),
        sha1="A" * 40,
        original_filename="Legend of Zelda, The (USA).nes",
        canonical_title="Legend of Zelda, The (USA)",
        platform="NES",
    )
    _insert_game(
        repo,
        source_path=str(tmp_path / "zelda_translated.nes"),
        sha1="B" * 40,
        original_filename="Legend of Zelda, The (U) [T-Spa1.2v_Firionel].nes",
        canonical_title="Legend of Zelda, The (USA)",
        platform="NES",
    )

    result = _build_review_queue(repo, repo, None)

    assert result["groups"] == []


def test_sha1_union_still_links_identical_variant_copies(tmp_path: Path) -> None:
    """El guard de CATALOG-MATCH-VARIANT-1 solo bloquea la unión por título —
    dos copias BYTE-IDÉNTICAS del mismo hack/traducción siguen siendo un
    duplicado real entre sí y deben seguir agrupándose por sha1."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(
        repo,
        source_path=str(tmp_path / "growl_hack_1.bin"),
        sha1="A" * 40,
        original_filename="growl (hack, spanish).bin",
        platform="Sega Mega Drive",
    )
    _insert_game(
        repo,
        source_path=str(tmp_path / "backup" / "growl_hack_1.bin"),
        sha1="A" * 40,
        original_filename="growl (hack, spanish).bin",
        platform="Sega Mega Drive",
    )

    result = _build_review_queue(repo, repo, None)

    assert result["total_groups"] == 1
    assert result["groups"][0]["reasons"] == ["sha1"]


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


def test_ra_cross_platform_group_scores_each_entry_by_its_own_platform(tmp_path: Path) -> None:
    """MATCH-FIX-4: a byte-identical ROM stranded under two different
    platform labels (e.g. a Game Boy Color game whose only other copy sits
    in a stray Game Boy bulk-pack folder) must score each entry's RA support
    against ITS OWN platform's hash cache. Scoring the whole group with a
    single shared platform (the first member's) blinded every other
    member's real RA support -- confirmed live 2026-09-12: 3 GBC games
    correctly marked/sent to the Anbernic for their achievements lost the
    discard tiebreak to junk bulk-pack .gb duplicates because the group
    picked "Game Boy" and looked up the .gbc file's hash there instead of
    in the Game Boy Color cache where it actually lives."""
    config = load_config(tmp_path)
    _write_ra_cache(tmp_path, console_id=6, hashes={"m" * 32: 12})  # Game Boy Color
    # Game Boy (console 5) has no cache file at all -- same as production,
    # where the stray bulk-pack copy was never independently RA-verified.
    repo = LibraryRepository(config.database_path)
    path_gb = str(tmp_path / "0001_bulk_pack.gb")
    path_gbc = str(tmp_path / "Tony Hawk's Pro Skater.gbc")
    _insert_game(
        repo,
        source_path=path_gb,
        sha1="A" * 40,
        md5="m" * 32,
        original_filename="0001_bulk_pack.gb",
        canonical_title="Tony Hawk's Pro Skater (USA, Europe)",
        platform="Game Boy",
        extension=".gb",
    )
    _insert_game(
        repo,
        source_path=path_gbc,
        sha1="A" * 40,
        md5="m" * 32,
        original_filename="Tony Hawk's Pro Skater.gbc",
        canonical_title="Tony Hawk's Pro Skater (USA, Europe)",
        platform="Game Boy Color",
        extension=".gbc",
    )

    result = _build_review_queue(repo, repo, config)

    assert result["total_groups"] == 1
    group = result["groups"][0]
    entries_by_path = {e["source_path"]: e for e in group["entries"]}
    assert entries_by_path[path_gbc]["ra_supported"] is True
    assert entries_by_path[path_gbc]["ra_achievements"] == 12
    assert entries_by_path[path_gb]["ra_supported"] is False
    recommended = next(e for e in group["entries"] if e["recommended"])
    assert recommended["source_path"] == path_gbc


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


def test_crossfmt_duplicate_same_disc_different_extension(tmp_path: Path) -> None:
    """DUP-CROSSFMT-1: a `.zip` and a `.chd` of the same disc never share a
    sha1 (different container bytes) and the `.zip` side is typically
    unmatched (no canonical_title) — the fuzzy cross-format title (region
    tag kept, disc tag stripped) is the only link that can catch this."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(
        repo,
        source_path=str(tmp_path / "psx" / "Crash Bandicoot (USA).chd"),
        sha1="A" * 40,
        original_filename="Crash Bandicoot (USA).chd",
        canonical_title="Crash Bandicoot (USA)",
        platform="PSX",
    )
    _insert_game(
        repo,
        source_path=str(tmp_path / "Unknown" / "Crash Bandicoot (USA).zip"),
        sha1="B" * 40,
        original_filename="Crash Bandicoot (USA).zip",
        canonical_title=None,  # nunca emparejado por catálogo, caso real
        platform="PSX",
    )

    result = _build_review_queue(repo, repo, None)

    assert result["total_groups"] == 1
    group = result["groups"][0]
    assert "crossfmt" in group["reasons"]
    assert len(group["entries"]) == 2


def test_crossfmt_different_regions_are_not_merged(tmp_path: Path) -> None:
    """Same guard as the exact-title union (test_different_regions_are_not_merged)
    but for the fuzzy cross-format link: region tags are kept as tokens, so a
    USA `.zip` and a Europe `.chd` sharing the rest of the title must NOT be
    treated as the same disc in two formats."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(
        repo,
        source_path=str(tmp_path / "psx" / "Crash Bandicoot (Europe).chd"),
        sha1="A" * 40,
        original_filename="Crash Bandicoot (Europe).chd",
        canonical_title="Crash Bandicoot (Europe)",
        platform="PSX",
    )
    _insert_game(
        repo,
        source_path=str(tmp_path / "Unknown" / "Crash Bandicoot (USA).zip"),
        sha1="B" * 40,
        original_filename="Crash Bandicoot (USA).zip",
        canonical_title=None,
        platform="PSX",
    )

    result = _build_review_queue(repo, repo, None)

    assert result["groups"] == []


def test_crossfmt_skips_translation_variant(tmp_path: Path) -> None:
    """Mismo guard que test_title_union_skips_translation_variant pero para
    la unión crossfmt (dos extensiones distintas) — un parche de traducción
    en un formato distinto al original no debe fusionarse con él solo porque
    el título fuzzy cruzando formatos colapsa igual."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(
        repo,
        source_path=str(tmp_path / "gamegear" / "Phantasy Star Adventure (Japan).bin"),
        sha1="A" * 40,
        original_filename="phantasy star adventure (japan).bin",
        canonical_title=None,
        platform="Game Gear",
    )
    _insert_game(
        repo,
        source_path=str(
            tmp_path / "gamegear" / "Phantasy Star Adventure (Japan) [T-En by Aeon Genesis].gg"
        ),
        sha1="B" * 40,
        original_filename="Phantasy Star Adventure (Japan) [T-En by Aeon Genesis].gg",
        canonical_title=None,
        platform="Game Gear",
    )

    result = _build_review_queue(repo, repo, None)

    assert result["groups"] == []


def test_crossfmt_multidisc_set_is_not_flagged(tmp_path: Path) -> None:
    """A `.zip` (Disc 1) and a `.chd` (Disc 2) of a real multi-disc game must
    not be flagged 'crossfmt' — same _is_disc_set guard the exact-title union
    already relies on for this."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(
        repo,
        source_path=str(tmp_path / "Unknown" / "Xenogears (Disc 1).zip"),
        sha1="A" * 40,
        original_filename="Xenogears (Disc 1).zip",
        canonical_title=None,
        platform="PSX",
    )
    _insert_game(
        repo,
        source_path=str(tmp_path / "psx" / "Xenogears (Disc 2).chd"),
        sha1="B" * 40,
        original_filename="Xenogears (Disc 2).chd",
        canonical_title="Xenogears (Disc 2)",
        platform="PSX",
    )

    result = _build_review_queue(repo, repo, None)

    assert not any("crossfmt" in g["reasons"] for g in result["groups"])


def test_crossfmt_same_extension_not_flagged(tmp_path: Path) -> None:
    """Two `.zip`s with the exact same fuzzy cross-format title but no
    canonical_title/sha1 link between them: not a cross-*format* case (both
    sides are the same container), so no group should surface at all — this
    is what the sha1/exact-title links are for, not the new fuzzy one."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(
        repo,
        source_path=str(tmp_path / "Unknown" / "Crash Bandicoot (USA) copy1.zip"),
        sha1="A" * 40,
        original_filename="Crash Bandicoot (USA).zip",
        canonical_title=None,
        platform="PSX",
    )
    _insert_game(
        repo,
        source_path=str(tmp_path / "Unknown2" / "Crash Bandicoot (USA) copy2.zip"),
        sha1="B" * 40,
        original_filename="Crash Bandicoot (USA).zip",
        canonical_title=None,
        platform="PSX",
    )

    result = _build_review_queue(repo, repo, None)

    assert result["groups"] == []


def test_crossfmt_multidisc_with_per_disc_siblings_not_flagged(tmp_path: Path) -> None:
    """DUP-CROSSFMT-2 (patrón 1): un set real de 2 discos donde cada disco
    tiene también un `.cue` además de su `.chd` (6→4 miembros compartiendo
    número de disco) no debe tratarse como duplicado — caso real: Parasite
    Eve II (Spain) Disc 1/Disc 2, cada uno con `.chd`+`.cue`. Antes del fix,
    `_is_disc_set` exigía un archivo por número de disco y devolvía False
    aquí, dejando "Aplicar recomendación" recomendar descartar el Disc 2
    completo."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    for i, name in enumerate(
        [
            "Parasite Eve II (Spain) (Disc 1).chd",
            "Parasite Eve II (Spain) (Disc 1).cue",
            "Parasite Eve II (Spain) (Disc 2).chd",
            "Parasite Eve II (Spain) (Disc 2).cue",
        ]
    ):
        _insert_game(
            repo,
            source_path=str(tmp_path / "psx" / name),
            sha1=chr(ord("A") + i) * 40,
            original_filename=name,
            canonical_title=None,
            platform="PSX",
        )

    result = _build_review_queue(repo, repo, None)

    assert result["groups"] == []


def test_crossfmt_cue_bin_sibling_pair_not_flagged(tmp_path: Path) -> None:
    """DUP-CROSSFMT-2 (patrón 2): un `.cue`+`.bin` hermanos (mismo directorio,
    mismo nombre base) no son dos copias alternativas del mismo disco — el
    `.bin` es el fichero de datos que el `.cue` referencia, no un formato
    autocontenido. Caso real: Wipeout 3 (Japan), Wild Arms (USA), Rayman
    (Japan) — agrupados como 'crossfmt' y recomendados para descartar el
    `.cue`, dejando el `.bin` huérfano e ilegible en la mayoría de emuladores."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    psx_dir = tmp_path / "psx"
    psx_dir.mkdir()
    cue_path = psx_dir / "Wipeout 3 (Japan).cue"
    bin_path = psx_dir / "Wipeout 3 (Japan).bin"
    cue_path.write_text('FILE "Wipeout 3 (Japan).bin" BINARY\n', encoding="utf-8")
    bin_path.write_bytes(b"\x00" * 16)
    _insert_game(
        repo,
        source_path=str(cue_path),
        sha1="A" * 40,
        original_filename=cue_path.name,
        canonical_title=None,
        platform="PSX",
    )
    _insert_game(
        repo,
        source_path=str(bin_path),
        sha1="B" * 40,
        original_filename=bin_path.name,
        canonical_title=None,
        platform="PSX",
    )

    result = _build_review_queue(repo, repo, None)

    assert result["groups"] == []


def test_crossfmt_ccd_img_sibling_pair_not_flagged(tmp_path: Path) -> None:
    """DUP-CROSSFMT-5: same bug as the .cue/.bin case above, for CloneCD
    sidecars — `.img` is the `.ccd`'s own data, not an independent copy.
    Found live 2026-09-09: Resident Evil 2 CD1/CD2, Rival Schools Evolution,
    clocktower2, NEW all had this exact pattern in the real library."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    psx_dir = tmp_path / "psx"
    psx_dir.mkdir()
    ccd_path = psx_dir / "clocktower2.ccd"
    img_path = psx_dir / "clocktower2.img"
    ccd_path.write_text("[CloneCD]\nVersion=3\n", encoding="utf-8")
    img_path.write_bytes(b"\x00" * 16)
    _insert_game(
        repo,
        source_path=str(ccd_path),
        sha1="A" * 40,
        original_filename=ccd_path.name,
        canonical_title=None,
        platform="PSX",
    )
    _insert_game(
        repo,
        source_path=str(img_path),
        sha1="B" * 40,
        original_filename=img_path.name,
        canonical_title=None,
        platform="PSX",
    )

    result = _build_review_queue(repo, repo, None)

    assert result["groups"] == []


@pytest.mark.skipif(
    os.name != "nt",
    reason="is_device_path's bare '/' heuristic only applies on Windows -- see test_paths.py",
)
def test_android_device_ccd_img_sub_trio_not_flagged(tmp_path: Path) -> None:
    """ANDROID-DUP-1: same as test_crossfmt_ccd_img_sibling_pair_not_flagged
    above, but for an ADB-scanned row (no real file on this PC's disk to
    call .exists() on -- see is_device_path) and the real 3-file CloneCD
    shape (.ccd+.img+.sub, not just .ccd+.img). Confirmed live on the RG556
    (Crash Bandicoot [U] [SCUS-94900]): Path.exists() being unconditionally
    False for a /storage/... path disabled the sibling guard entirely, and
    the tool recommended keeping the 790-byte .ccd cue sheet while
    discarding the .img (632 MB, the actual disc data) and .sub (25.8 MB)."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    base = "/storage/521D-04EA/ROMs/psx/Crash Bandicoot [U] [SCUS-94900]"
    for ext, size in ((".ccd", 790), (".img", 632083536), (".sub", 25799328)):
        _insert_game(
            repo,
            source_path=f"{base}{ext}",
            sha1="",
            original_filename=f"Crash Bandicoot [U] [SCUS-94900]{ext}",
            canonical_title=None,
            platform="PlayStation",
            size_bytes=size,
            extension=ext,
        )

    result = _build_review_queue(repo, repo, None)

    assert result["groups"] == []


@pytest.mark.skipif(
    os.name != "nt",
    reason="is_device_path's bare '/' heuristic only applies on Windows -- see test_paths.py",
)
def test_android_device_bin_cue_chd_prefers_chd_not_alphabetical(tmp_path: Path) -> None:
    """ANDROID-DUP-1: an ADB-scanned .bin+.cue+.chd trio of the same PSX disc
    used to (1) never exclude the .bin as the .cue's own sibling (same
    Path.exists() gap as the CCD case above), landing all three in one
    group, and (2) fall through every tier to a plain alphabetical filename
    sort, which picked the raw .bin over the project's own chosen canonical
    PSX format (DUP-DISC-RA-2: "usa CHD como formato de PSX") -- confirmed
    live: Crash Bandicoot (USA) recommended keeping the .bin and discarding
    the .chd."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    base = "/storage/521D-04EA/ROMs/psx/Crash Bandicoot (USA)"
    for ext, sha1 in ((".bin", "A" * 40), (".cue", "B" * 40), (".chd", "C" * 40)):
        _insert_game(
            repo,
            source_path=f"{base}{ext}",
            sha1=sha1,
            original_filename=f"Crash Bandicoot (USA){ext}",
            canonical_title="Crash Bandicoot (USA)",
            platform="PlayStation",
            extension=ext,
        )

    result = _build_review_queue(repo, repo, None)

    assert len(result["groups"]) == 1
    group = result["groups"][0]
    paths = {e["source_path"] for e in group["entries"]}
    # the .bin must never appear as an independent candidate -- it's the
    # .cue's own data, not an alternate copy
    assert f"{base}.bin" not in paths
    assert paths == {f"{base}.cue", f"{base}.chd"}
    winner = next(e for e in group["entries"] if e["recommended"])
    assert winner["source_path"] == f"{base}.chd"


@pytest.mark.skipif(
    os.name != "nt",
    reason="is_device_path's bare '/' heuristic only applies on Windows -- see test_paths.py",
)
def test_is_broken_disc_entry_device_cue_with_sibling_bin_not_broken() -> None:
    """ANDROID-DUP-1: is_broken_cue_set() reads the .cue's own text to find
    which .bin(s) it references -- impossible for an ADB-scanned row -- and
    its own cue_path.exists() check made every Android .cue 'broken'
    unconditionally, regardless of whether its .bin sat right next to it."""
    known = frozenset(
        {
            "/storage/521d-04ea/roms/psx/wild arms (usa).cue",
            "/storage/521d-04ea/roms/psx/wild arms (usa).bin",
        }
    )
    assert _is_broken_disc_entry("/storage/521D-04EA/ROMs/psx/Wild Arms (USA).cue", known) is False


@pytest.mark.skipif(
    os.name != "nt",
    reason="is_device_path's bare '/' heuristic only applies on Windows -- see test_paths.py",
)
def test_is_broken_disc_entry_device_cue_without_sibling_bin_is_broken() -> None:
    known = frozenset({"/storage/521d-04ea/roms/psx/wild arms (usa).cue"})
    assert _is_broken_disc_entry("/storage/521D-04EA/ROMs/psx/Wild Arms (USA).cue", known) is True


def test_title_union_cue_bin_sibling_pair_not_flagged(tmp_path: Path) -> None:
    """DUP-CROSSFMT-3: same bug as the crossfmt test above, but via the exact
    canonical_title union instead — the catalog matches both the `.cue` and
    its own `.bin` sibling to the same canonical_title (real case: the DAT
    matches a disc by its data track regardless of which sidecar found it).
    `_is_cue_sibling_bin` only gated the crossfmt union, not this one, so the
    pair still landed in one cluster (distinct sha1 + same canonical_title)
    and the alphabetical filename tiebreak always picked the `.bin` over the
    `.cue`, recommending the `.cue` for discard and orphaning the `.bin`.
    Confirmed live against the real library: 26 PSX games hit this in a
    `resolve-duplicates` dry run before this fix."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    psx_dir = tmp_path / "psx"
    psx_dir.mkdir()
    cue_path = psx_dir / "Wild Arms (USA).cue"
    bin_path = psx_dir / "Wild Arms (USA).bin"
    cue_path.write_text('FILE "Wild Arms (USA).bin" BINARY\n', encoding="utf-8")
    bin_path.write_bytes(b"\x00" * 16)
    _insert_game(
        repo,
        source_path=str(cue_path),
        sha1="A" * 40,
        original_filename=cue_path.name,
        canonical_title="Wild Arms (USA)",
        platform="PSX",
        extension=".cue",
    )
    _insert_game(
        repo,
        source_path=str(bin_path),
        sha1="B" * 40,
        original_filename=bin_path.name,
        canonical_title="Wild Arms (USA)",
        platform="PSX",
        extension=".bin",
    )

    result = _build_review_queue(repo, repo, None)

    assert result["groups"] == []


def _write_nds_rom(path: Path, game_code: str, size: int = 1024) -> None:
    data = bytearray(max(size, 0x10))
    data[0x0C : 0x0C + len(game_code)] = game_code.encode("ascii")
    path.write_bytes(bytes(data))


def test_header_union_rescues_unmatched_translation_patch(tmp_path: Path) -> None:
    """MATCH-HEADER-1: a translation patch/bad dump with no sha1/title link
    to the real game (real case: a 128 MiB "(BAHAMUT)" Spanish patch of
    "Kirby Super Star Ultra (Europe)") is invisible to every other union —
    different bytes, different (or no) canonical_title. Reading the NDS
    header's game code straight from the file links it to its real
    counterpart anyway, surfacing it in the review queue instead of leaving
    it silently unmatched forever."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    nds_dir = tmp_path / "nds"
    nds_dir.mkdir()
    real_path = nds_dir / "Kirby Super Star Ultra (Europe).nds"
    patch_path = nds_dir / "4186 - Kirby Super Star Ultra (EU)(M5)(BAHAMUT).nds"
    _write_nds_rom(real_path, "YKWP", size=134_217_728)
    _write_nds_rom(patch_path, "YKWP", size=140_000_000)
    _insert_game(
        repo,
        source_path=str(real_path),
        sha1="A" * 40,
        original_filename=real_path.name,
        canonical_title="Kirby Super Star Ultra (Europe)",
        platform="Nintendo DS",
        extension=".nds",
    )
    _insert_game(
        repo,
        source_path=str(patch_path),
        sha1="B" * 40,
        original_filename=patch_path.name,
        canonical_title=None,
        platform="Nintendo DS",
        extension=".nds",
    )

    result = _build_review_queue(repo, repo, None)

    assert result["total_groups"] == 1
    group = result["groups"][0]
    assert "header" in group["reasons"]
    paths = {e["source_path"] for e in group["entries"]}
    assert paths == {str(real_path), str(patch_path)}


def test_header_union_skips_different_games(tmp_path: Path) -> None:
    """Two unrelated NDS games (different game codes) must never be unioned
    just for sharing a platform — the whole point of the game code is that
    it's specific to one release."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    nds_dir = tmp_path / "nds"
    nds_dir.mkdir()
    a_path = nds_dir / "Game A.nds"
    b_path = nds_dir / "Game B.nds"
    _write_nds_rom(a_path, "AAAA")
    _write_nds_rom(b_path, "BBBB")
    _insert_game(
        repo,
        source_path=str(a_path),
        sha1="A" * 40,
        original_filename=a_path.name,
        canonical_title=None,
        platform="Nintendo DS",
        extension=".nds",
    )
    _insert_game(
        repo,
        source_path=str(b_path),
        sha1="B" * 40,
        original_filename=b_path.name,
        canonical_title=None,
        platform="Nintendo DS",
        extension=".nds",
    )

    result = _build_review_queue(repo, repo, None)

    assert result["groups"] == []


def test_header_union_not_claimed_when_already_explained_by_sha1(tmp_path: Path) -> None:
    """A group already unioned by an exact sha1 match must not also carry a
    redundant 'header' reason on top of 'sha1' — the header link added
    nothing new here."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    nds_dir = tmp_path / "nds"
    nds_dir.mkdir()
    a_path = nds_dir / "Game (USA).nds"
    b_path = nds_dir / "Game (Copy).nds"
    _write_nds_rom(a_path, "ABCD")
    _write_nds_rom(b_path, "ABCD")
    _insert_game(
        repo,
        source_path=str(a_path),
        sha1="SAME" * 10,
        original_filename=a_path.name,
        canonical_title="Game (USA)",
        platform="Nintendo DS",
        extension=".nds",
    )
    _insert_game(
        repo,
        source_path=str(b_path),
        sha1="SAME" * 10,
        original_filename=b_path.name,
        canonical_title="Game (USA)",
        platform="Nintendo DS",
        extension=".nds",
    )

    result = _build_review_queue(repo, repo, None)

    assert result["total_groups"] == 1
    group = result["groups"][0]
    assert "sha1" in group["reasons"]
    assert "header" not in group["reasons"]


def _gb_checksum(data: bytes) -> int:
    x = 0
    for byte in data[0x134:0x14D]:
        x = (x - byte - 1) & 0xFF
    return x


def _write_gb_rom(path: Path, title: str, size: int = 1024, *, rom_size_field: int = 0) -> None:
    data = bytearray(max(size, 0x14E))
    data[0x134 : 0x134 + len(title)] = title.encode("ascii")
    data[0x148] = rom_size_field
    data[0x14D] = _gb_checksum(bytes(data))
    path.write_bytes(bytes(data))


def test_gb_header_union_rescues_unmatched_translation_patch(tmp_path: Path) -> None:
    """MATCH-FIX-14: same rescue as NDS/GBA (see
    test_header_union_rescues_unmatched_translation_patch), now for GB/GBC —
    the title+checksum combination is a strong enough signal to auto-union."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    gb_dir = tmp_path / "gb"
    gb_dir.mkdir()
    real_path = gb_dir / "Pokemon Red (USA).gb"
    patch_path = gb_dir / "Pokemon Red (Randomizer Hack).gb"
    _write_gb_rom(real_path, "POKEMON RED")
    _write_gb_rom(patch_path, "POKEMON RED")
    _insert_game(
        repo,
        source_path=str(real_path),
        sha1="A" * 40,
        original_filename=real_path.name,
        canonical_title="Pokemon Red (USA)",
        platform="Game Boy",
        extension=".gb",
    )
    _insert_game(
        repo,
        source_path=str(patch_path),
        sha1="B" * 40,
        original_filename=patch_path.name,
        canonical_title=None,
        platform="Game Boy",
        extension=".gb",
    )

    result = _build_review_queue(repo, repo, None)

    assert result["total_groups"] == 1
    group = result["groups"][0]
    assert "header" in group["reasons"]
    paths = {e["source_path"] for e in group["entries"]}
    assert paths == {str(real_path), str(patch_path)}


def test_gb_header_union_skips_same_truncated_title_different_game(tmp_path: Path) -> None:
    """Two GB games that happen to share the same (truncated) 16-char title
    but differ in cart config (ROM size field here) must NOT be unioned —
    the whole point of MATCH-FIX-14 is that the title alone isn't trusted,
    only title+checksum together."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    gb_dir = tmp_path / "gb"
    gb_dir.mkdir()
    a_path = gb_dir / "Game A.gb"
    b_path = gb_dir / "Game B.gb"
    _write_gb_rom(a_path, "SAME TITLE", rom_size_field=0x00)
    _write_gb_rom(b_path, "SAME TITLE", rom_size_field=0x05)
    _insert_game(
        repo,
        source_path=str(a_path),
        sha1="A" * 40,
        original_filename=a_path.name,
        canonical_title=None,
        platform="Game Boy",
        extension=".gb",
    )
    _insert_game(
        repo,
        source_path=str(b_path),
        sha1="B" * 40,
        original_filename=b_path.name,
        canonical_title=None,
        platform="Game Boy",
        extension=".gb",
    )

    result = _build_review_queue(repo, repo, None)

    assert result["groups"] == []


def test_size_tier_prefers_catalog_verified_size_over_bad_dump(tmp_path: Path) -> None:
    """MATCH-FIX-14: within a group already united by canonical_title, an
    entry whose size doesn't match the size of the group's sha1-verified
    (match_confidence="high") member is very likely a bad/incomplete dump —
    it must not be recommended over the catalog-verified one."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    gb_dir = tmp_path / "gb"
    gb_dir.mkdir()
    good_path = gb_dir / "Zzz Bad Name (USA).gb"  # sorts after on filename alone
    bad_path = gb_dir / "Aaa Good Name (USA).gb"  # would win the filename tiebreak
    _insert_game(
        repo,
        source_path=str(good_path),
        sha1="GOOD" * 10,
        original_filename=good_path.name,
        canonical_title="Same Game (USA)",
        platform="Game Boy",
        extension=".gb",
        size_bytes=32_768,
    )
    _insert_game(
        repo,
        source_path=str(bad_path),
        sha1="BAD1" * 10,
        original_filename=bad_path.name,
        canonical_title=None,
        platform="Game Boy",
        extension=".gb",
        size_bytes=16_384,
    )
    # Fuzzy title fallback match (no sha1 verification) -- unlike the "good"
    # entry above, its size was never checked against the catalog.
    repo.update_match(
        str(bad_path),
        canonical_title="Same Game (USA)",
        match_confidence="medium",
        catalog_source="test.dat",
    )

    result = _build_review_queue(repo, repo, None)

    assert result["total_groups"] == 1
    group = result["groups"][0]
    assert group["entries"][0]["source_path"] == str(good_path)


def test_disc_hash_union_links_legacy_dump_with_no_catalog_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DUP-DISC-RA-1b parte 2: a legacy CloneCD-style dump (serial in the
    name, never catalog-matched -> no canonical_title, no crossfmt title
    overlap with the canonical release) is still the same disc release as
    the canonical .chd once RA's disc hash agrees -- ANDROID-DUP-1's real
    "Crash Bandicoot (USA)" case (3 formats, only one had a title match)."""
    from types import SimpleNamespace

    monkeypatch.setattr(
        "rom_manager.retroachievements.ra_disc_hash_cache.get_psx_disc_hash",
        lambda source_path, cache_dir, chdman_path: "SAMEDISCHASH",
    )

    repo = LibraryRepository(tmp_path / "lib.sqlite")
    canonical = str(tmp_path / "psx" / "Crash Bandicoot (USA).chd")
    legacy = str(tmp_path / "psx" / "Crash Bandicoot [U] [SCUS-94900]" / "track.img")
    _insert_game(
        repo,
        source_path=canonical,
        sha1="A" * 40,
        original_filename="Crash Bandicoot (USA).chd",
        canonical_title="Crash Bandicoot (USA)",
        platform="PSX",
    )
    _insert_game(
        repo,
        source_path=legacy,
        sha1="B" * 40,
        original_filename="track.img",
        canonical_title=None,
        platform="PSX",
    )

    config = SimpleNamespace(project_root=tmp_path, library_root=tmp_path)
    result = _build_review_queue(repo, repo, config)

    assert result["total_groups"] == 1
    group = result["groups"][0]
    assert "disc_hash" in group["reasons"]
    assert {e["source_path"] for e in group["entries"]} == {canonical, legacy}


def test_disc_hash_union_skips_when_hashes_differ(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Different real discs must never be merged just for sharing a
    platform -- only an actual matching RA disc hash links them."""
    from types import SimpleNamespace

    def _fake_hash(source_path, cache_dir, chdman_path):
        return "HASH_A" if "a.chd" in source_path else "HASH_B"

    monkeypatch.setattr(
        "rom_manager.retroachievements.ra_disc_hash_cache.get_psx_disc_hash", _fake_hash
    )

    repo = LibraryRepository(tmp_path / "lib.sqlite")
    _insert_game(
        repo,
        source_path=str(tmp_path / "psx" / "a.chd"),
        sha1="A" * 40,
        original_filename="a.chd",
        canonical_title=None,
        platform="PSX",
    )
    _insert_game(
        repo,
        source_path=str(tmp_path / "psx" / "b.chd"),
        sha1="B" * 40,
        original_filename="b.chd",
        canonical_title=None,
        platform="PSX",
    )

    config = SimpleNamespace(project_root=tmp_path, library_root=tmp_path)
    result = _build_review_queue(repo, repo, config)

    assert result["groups"] == []
