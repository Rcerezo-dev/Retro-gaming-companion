"""DUP-VARIANT: prereleases and older revisions go; regions, hacks, translations stay."""

from __future__ import annotations

from pathlib import Path

from rom_manager.database.repository import LibraryRepository
from rom_manager.services.ra_duplicates_service import (
    plan_variant_duplicates,
    resolve_cluster_duplicates,
)


def _group(*names: str, platform: str = "NES") -> dict:
    return {
        "platform": platform,
        "entries": [{"source_path": f"/lib/{n}", "filename": n} for n in names],
    }


def _plan(*names: str, platform: str = "NES") -> dict[str, list[str]]:
    return {
        Path(k["source_path"]).name: [Path(e["source_path"]).name for e in ls]
        for k, ls in plan_variant_duplicates(_group(*names, platform=platform))
    }


def test_prerelease_discarded_when_final_exists() -> None:
    plan = _plan("Game (USA).nes", "Game (USA) (Beta).nes", "Game (Japan) (Proto 1).nes")
    assert plan == {"Game (USA).nes": ["Game (USA) (Beta).nes", "Game (Japan) (Proto 1).nes"]}


def test_lone_prerelease_is_kept() -> None:
    assert _plan("Game (USA) (Beta).nes", "Other (USA).nes") == {}


def test_older_revision_discarded_per_region() -> None:
    plan = _plan("Game (USA).nes", "Game (USA) (Rev 1).nes", "Game (USA) (Rev 2).nes")
    assert plan == {"Game (USA) (Rev 2).nes": ["Game (USA).nes", "Game (USA) (Rev 1).nes"]}


def test_single_region_europe_then_usa_then_japan() -> None:
    assert _plan("Game (Japan).nes", "Game (USA).nes", "Game (Europe).nes") == {
        "Game (Europe).nes": ["Game (Japan).nes", "Game (USA).nes"]
    }
    assert _plan("Game (Japan).nes", "Game (USA, Europe).nes") == {
        "Game (USA, Europe).nes": ["Game (Japan).nes"]
    }
    assert _plan("Game (Japan).nes", "Game (World).nes", "Game (Europe).nes") == {
        "Game (World).nes": ["Game (Japan).nes", "Game (Europe).nes"]
    }


def test_region_rule_edge_cases() -> None:
    # same region stays, a lone unknown region stays, an untagged file is never a loser
    assert _plan("Game (USA).nes", "Game (USA) (Virtual Console).nes") == {}
    assert _plan("Game (Brazil).nes", "Other (USA).nes") == {}
    assert _plan("Game.nes", "Game (USA).nes") == {}


def test_revision_and_region_combine() -> None:
    plan = _plan("Game (Europe).nes", "Game (USA) (Rev 1).nes", "Game (USA).nes")
    assert plan == {"Game (Europe).nes": ["Game (USA).nes", "Game (USA) (Rev 1).nes"]}


def test_protected_variants_untouched() -> None:
    names = (
        "Game (USA).nes",
        "Game (USA) (Unl).nes",
        "Game (USA) (Hack).nes",
        "Game (USA) [T-En].nes",
    )
    assert _plan(*names) == {}
    assert _plan("Game (USA) (Rev 1).nes", "Game (USA) (Rev 2) (Aftermarket).nes") == {}


def test_randomizer_and_versioned_hacks_untouched() -> None:
    names = (
        "Game (Europe).nes",
        "Game (USA) (Item Randomizer) (v1.41) (clymax).nes",
        "Game (USA) (v1.2).nes",
    )
    assert _plan(*names) == {}


def test_arcade_and_unknown_platform_ignored() -> None:
    assert _plan("Game (USA).zip", "Game (USA) (Beta).zip", platform="MAME") == {}
    assert _plan("Game (USA).nes", "Game (USA) (Beta).nes", platform="unknown") == {}


def test_resolve_discards_without_carrying_saves(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    final = tmp_path / "Game (USA).nes"
    beta = tmp_path / "Game (USA) (Beta).nes"
    for p in (final, beta):
        p.write_bytes(b"x")
        repo.upsert_game(
            original_filename=p.name, source_path=str(p), platform="NES", file_type="rom",
            relative_parent="", region=None, extension=".nes", size_bytes=1, mtime=1, sha1="",
            md5="", crc32="", set_type="single", timestamp="2026-01-01T00:00:00",
        )  # fmt: skip
    group = {
        "platform": "NES",
        "entries": [
            {"source_path": str(final), "filename": final.name},
            {"source_path": str(beta), "filename": beta.name},
        ],
    }
    result = resolve_cluster_duplicates(
        lambda _p: repo,
        [group],
        save_extensions=frozenset({".sav"}),
        planner=plan_variant_duplicates,
        carry_saves=False,
    )
    assert result["resolved"] == 1 and final.exists() and not beta.exists()

    # a loser with its own save is never discarded
    beta.write_bytes(b"x")
    (tmp_path / "Game (USA) (Beta).sav").write_bytes(b"s")
    result = resolve_cluster_duplicates(
        lambda _p: repo,
        [group],
        save_extensions=frozenset({".sav"}),
        planner=plan_variant_duplicates,
        carry_saves=False,
    )
    assert result["resolved"] == 0 and beta.exists()
    assert any("saves propios" in e for e in result["errors"])
