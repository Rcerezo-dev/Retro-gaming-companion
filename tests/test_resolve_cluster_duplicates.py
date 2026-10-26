"""DUP-CROSSFMT-11: discard only byte-identical copies, keep distinct regions/dumps."""

from __future__ import annotations

from pathlib import Path

from rom_manager.database.repository import LibraryRepository
from rom_manager.services.ra_duplicates_service import (
    plan_cluster_duplicates,
    resolve_cluster_duplicates,
)


def _entry(repo: LibraryRepository, path: Path, sha1: str, recommended: bool = False) -> dict:
    path.write_bytes(sha1.encode())
    repo.upsert_game(
        original_filename=path.name, source_path=str(path), platform="NES", file_type="rom",
        relative_parent="", region=None, extension=".nes", size_bytes=1, mtime=1, sha1=sha1,
        md5="", crc32="", set_type="single", timestamp="2026-01-01T00:00:00",
    )  # fmt: skip
    return {
        "source_path": str(path),
        "filename": path.name,
        "sha1": sha1,
        "recommended": recommended,
    }


def _count(repo: LibraryRepository) -> int:
    with repo.connect() as c:
        return c.execute("SELECT COUNT(*) FROM games").fetchone()[0]


def test_only_identical_copy_is_discarded(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    keep = _entry(repo, tmp_path / "Game (USA).nes", "A" * 40, recommended=True)
    dupe = _entry(repo, tmp_path / "Game (USA) copy.nes", "A" * 40)
    other = _entry(repo, tmp_path / "Game (Europe).nes", "B" * 40)
    group = {"platform": "NES", "entries": [keep, dupe, other]}

    result = resolve_cluster_duplicates(lambda _p: repo, [group])

    assert result["resolved"] == 1
    assert Path(keep["source_path"]).exists() and Path(other["source_path"]).exists()
    assert not Path(dupe["source_path"]).exists()
    assert _count(repo) == 2


def test_distinct_unverifiable_and_risky_platforms_untouched(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    a = _entry(repo, tmp_path / "a.nes", "A" * 40, recommended=True)
    b = _entry(repo, tmp_path / "b.nes", "B" * 40)
    assert plan_cluster_duplicates({"platform": "NES", "entries": [a, b]}) == []

    no_sha = {**a, "sha1": ""}
    no_sha2 = {**b, "sha1": ""}
    assert plan_cluster_duplicates({"platform": "NES", "entries": [no_sha, no_sha2]}) == []

    same = {**b, "sha1": "A" * 40}
    for platform in ("PlayStation", "MAME"):
        assert plan_cluster_duplicates({"platform": platform, "entries": [a, same]}) == []


def test_missing_keeper_discards_nothing(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    keep = _entry(repo, tmp_path / "k.nes", "A" * 40, recommended=True)
    dupe = _entry(repo, tmp_path / "d.nes", "A" * 40)
    Path(keep["source_path"]).unlink()

    result = resolve_cluster_duplicates(
        lambda _p: repo, [{"platform": "NES", "entries": [keep, dupe]}]
    )

    assert result["resolved"] == 0 and Path(dupe["source_path"]).exists()


_SAVE_EXTS = frozenset({".srm", ".sav"})


def test_loser_save_is_renamed_to_keeper(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    keep = _entry(repo, tmp_path / "Game (USA).nes", "A" * 40, recommended=True)
    dupe = _entry(repo, tmp_path / "nbajam.nes", "A" * 40)
    (tmp_path / "nbajam.srm").write_bytes(b"progress")

    result = resolve_cluster_duplicates(
        lambda _p: repo,
        [{"platform": "NES", "entries": [keep, dupe]}],
        save_extensions=_SAVE_EXTS,
    )

    assert result["resolved"] == 1 and result["saves_carried"] == 1
    assert (tmp_path / "Game (USA).srm").read_bytes() == b"progress"
    assert not (tmp_path / "nbajam.srm").exists()


def test_save_name_clash_keeps_loser_and_overwrites_nothing(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    keep = _entry(repo, tmp_path / "Game (USA).nes", "A" * 40, recommended=True)
    dupe = _entry(repo, tmp_path / "nbajam.nes", "A" * 40)
    (tmp_path / "nbajam.srm").write_bytes(b"old")
    (tmp_path / "Game (USA).srm").write_bytes(b"new")

    result = resolve_cluster_duplicates(
        lambda _p: repo,
        [{"platform": "NES", "entries": [keep, dupe]}],
        save_extensions=_SAVE_EXTS,
    )

    assert result["resolved"] == 0 and result["errors"]
    assert Path(dupe["source_path"]).exists()
    assert (tmp_path / "nbajam.srm").read_bytes() == b"old"
    assert (tmp_path / "Game (USA).srm").read_bytes() == b"new"


def test_identical_save_at_destination_is_not_a_conflict(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    keep = _entry(repo, tmp_path / "Game (USA).nes", "A" * 40, recommended=True)
    dupe = _entry(repo, tmp_path / "nbajam.nes", "A" * 40)
    (tmp_path / "nbajam.srm").write_bytes(b"same")
    (tmp_path / "Game (USA).srm").write_bytes(b"same")

    result = resolve_cluster_duplicates(
        lambda _p: repo,
        [{"platform": "NES", "entries": [keep, dupe]}],
        save_extensions=_SAVE_EXTS,
    )

    assert result["resolved"] == 1 and not result["errors"]
    assert not (tmp_path / "nbajam.srm").exists()
    assert (tmp_path / "Game (USA).srm").read_bytes() == b"same"


def test_save_stays_with_surviving_same_name_rom(tmp_path: Path) -> None:
    """Incidente 2026-10-26: el .zip descartado compartía nombre con otro .nds (otro dump)
    que se quedaba; su save no debe irse al nombre del keeper."""
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    keep = _entry(repo, tmp_path / "Game (USA) (conflicto).nes", "A" * 40, recommended=True)
    dupe = _entry(repo, tmp_path / "Game (USA).bin", "A" * 40)
    (tmp_path / "Game (USA).nes").write_bytes(b"other dump")  # sobrevive, mismo stem
    (tmp_path / "Game (USA).srm").write_bytes(b"progress")

    result = resolve_cluster_duplicates(
        lambda _p: repo,
        [{"platform": "NES", "entries": [keep, dupe]}],
        save_extensions=_SAVE_EXTS,
    )

    assert result["resolved"] == 1 and result["saves_carried"] == 0
    assert (tmp_path / "Game (USA).srm").read_bytes() == b"progress"
    assert not (tmp_path / "Game (USA) (conflicto).srm").exists()


def _e(path: str, sha1: str = "A" * 40, recommended: bool = False) -> dict:
    return {
        "source_path": path,
        "filename": Path(path).name,
        "sha1": sha1,
        "recommended": recommended,
    }


def test_groups_without_platform_are_never_planned() -> None:
    """DUP-CROSSFMT-11d: BIOS/utilidades (plataforma NULL) no son duplicados de ROM."""
    entries = [_e("E:/x/drastic_bios_arm7.bin", recommended=True), _e("E:/y/drastic_bios_arm7.bin")]
    assert plan_cluster_duplicates({"platform": "unknown", "entries": entries}) == []
    assert plan_cluster_duplicates({"platform": None, "entries": entries}) == []


def test_backup_trash_and_known_bios_entries_are_ignored() -> None:
    real = _e("E:/ROMS/nes/Game.nes", recommended=True)
    in_backup = _e("E:/ROMS/_backup_android_cleanup/nes/Game.nes")
    in_trash = _e("E:/ROMS/nes/_descartados/Game.nes")
    assert (
        plan_cluster_duplicates({"platform": "NES", "entries": [real, in_backup, in_trash]}) == []
    )

    # un duplicado normal sigue funcionando junto a esas entradas protegidas
    twin = _e("E:/ROMS/nes/Game copy.nes")
    plan = plan_cluster_duplicates({"platform": "NES", "entries": [real, twin, in_backup]})
    assert [(k["source_path"], [d["source_path"] for d in ls]) for k, ls in plan] == [
        (real["source_path"], [twin["source_path"]])
    ]

    bios_a, bios_b = _e("E:/a/scph1001.bin", recommended=True), _e("E:/b/scph1001.bin")
    assert plan_cluster_duplicates({"platform": "NES", "entries": [bios_a, bios_b]}) == []
