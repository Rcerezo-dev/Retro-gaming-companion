"""LIBRARY-AUDIT-2/3/4/6 (issue #275): new headless CLI commands to fix a real
library — organize-source, decompress, resolve-duplicates."""

from __future__ import annotations

import zipfile
from pathlib import Path

from rom_manager.cli import main
from rom_manager.database.repository import LibraryRepository

_TS = "2024-01-01T00:00:00"


def _seed_game(
    repo: LibraryRepository, path: Path, *, platform: str, sha1: str, content: bytes = b"x"
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    repo.upsert_game(
        original_filename=path.name,
        source_path=str(path.resolve()),
        platform=platform,
        file_type="rom",
        relative_parent="",
        region="USA",
        extension=path.suffix.lower(),
        size_bytes=len(content),
        mtime=0,
        sha1=sha1,
        md5="M" * 32,
        crc32="CCCCCCCC",
        set_type="single",
        timestamp=_TS,
    )


def _db_path(tmp_path: Path) -> Path:
    return tmp_path / ".rommgr" / "library_pc.db"


# ── organize-source ─────────────────────────────────────────────────────────


def test_organize_source_dry_run_does_not_move(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "Unknown"
    (source / "game.gba").parent.mkdir(parents=True, exist_ok=True)
    (source / "game.gba").write_bytes(b"\x00" * 64)
    target_root = tmp_path / "library"
    target_root.mkdir()

    ret = main(["organize-source", str(source), "--target-root", str(target_root)])

    assert ret == 0
    assert (source / "game.gba").exists()
    assert not list(target_root.rglob("game.gba"))


def test_organize_source_apply_moves_and_removes_empty_source(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "Unknown"
    source.mkdir()
    (source / "game.gba").write_bytes(b"\x00" * 64)
    target_root = tmp_path / "library"
    target_root.mkdir()

    ret = main(
        ["organize-source", str(source), "--target-root", str(target_root), "--apply"]
    )

    assert ret == 0
    moved = list(target_root.rglob("game.gba"))
    assert len(moved) == 1
    assert not source.exists()


# ── decompress ───────────────────────────────────────────────────────────────


def test_decompress_extracts_console_zip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    platform_dir = tmp_path / "library" / "gba"
    platform_dir.mkdir(parents=True)
    zpath = platform_dir / "game.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("game.gba", b"\x00" * 64)

    ret = main(["decompress", str(platform_dir), "--apply"])

    assert ret == 0
    assert (platform_dir / "game.gba").exists()


def test_decompress_never_touches_arcade_folder(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    arcade_dir = tmp_path / "library" / "mame"
    arcade_dir.mkdir(parents=True)
    zpath = arcade_dir / "1943.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("rom.bin", b"\x00" * 64)

    ret = main(["decompress", str(arcade_dir), "--apply"])

    assert ret == 0
    assert zpath.exists()  # untouched, still zipped — the ZIP *is* the ROM
    assert not (arcade_dir / "rom.bin").exists()


# ── resolve-duplicates ────────────────────────────────────────────────────────


def test_resolve_duplicates_resolves_console_but_excludes_arcade(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    repo = LibraryRepository(_db_path(tmp_path))

    _seed_game(repo, tmp_path / "gb" / "tetris.gb", platform="Game Boy", sha1="A" * 40)
    _seed_game(
        repo, tmp_path / "gb" / "backup" / "tetris.gb", platform="Game Boy", sha1="A" * 40
    )
    _seed_game(repo, tmp_path / "mame" / "1943.zip", platform="MAME", sha1="B" * 40)
    _seed_game(
        repo, tmp_path / "mame" / "clone" / "1943.zip", platform="MAME", sha1="B" * 40
    )

    ret = main(["resolve-duplicates", "--apply"])

    assert ret == 0
    with repo.connect() as conn:
        platforms = [r["platform"] for r in conn.execute("SELECT platform FROM games").fetchall()]
    assert platforms.count("Game Boy") == 1  # resolved down to one copy
    assert platforms.count("MAME") == 2  # never touched

    excluded = repo.get_excluded_duplicate_groups()
    assert any(e["group_key"].startswith("MAME::") for e in excluded)


def test_resolve_duplicates_dry_run_never_shows_multi_disc_risk_as_plain_discard(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """A group whose reason includes disk/collision is never resolved via the
    plain keep/discard path (apply_all_review_recommendations defers it to
    apply_ra_conflicts, which skips _MULTI_DISC_RISK_PLATFORMS entirely) — the
    dry-run preview must not print it as if a disc were about to be discarded,
    that reads as data loss for a legitimate multi-disc game."""
    monkeypatch.chdir(tmp_path)
    import rom_manager.web.builders.duplicates as dup_builders

    fake_queue = {
        "groups": [
            {
                "platform": "Dreamcast",
                "group_key": "Dreamcast::shenmue ii",
                "reasons": ["collision", "multi_disc_risk"],
                "entries": [
                    {
                        "filename": "Shenmue II (Disc 1).chd",
                        "source_path": "/d/1.chd",
                        "recommended": True,
                    },
                    {
                        "filename": "Shenmue II (Disc 2).chd",
                        "source_path": "/d/2.chd",
                        "recommended": False,
                    },
                ],
            }
        ]
    }
    monkeypatch.setattr(dup_builders, "_build_review_queue", lambda *a, **kw: fake_queue)

    ret = main(["resolve-duplicates"])

    assert ret == 0
    out = capsys.readouterr().out
    assert "descartar: Shenmue II (Disc 2).chd" not in out
    assert "conflicto de nombre" in out


def test_resolve_duplicates_dry_run_does_not_change_db(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    repo = LibraryRepository(_db_path(tmp_path))
    _seed_game(repo, tmp_path / "gb" / "tetris.gb", platform="Game Boy", sha1="A" * 40)
    _seed_game(
        repo, tmp_path / "gb" / "backup" / "tetris.gb", platform="Game Boy", sha1="A" * 40
    )

    ret = main(["resolve-duplicates"])

    assert ret == 0
    with repo.connect() as conn:
        n = conn.execute("SELECT COUNT(*) AS n FROM games").fetchone()["n"]
    assert n == 2  # nothing discarded
