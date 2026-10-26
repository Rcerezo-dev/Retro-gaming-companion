"""DUP-CROSSFMT-11c: `fix-platforms --mismatched` corrige plataformas obsoletas sin tocar lo ambiguo."""

from __future__ import annotations

from pathlib import Path

import rom_manager.cli as cli
from rom_manager.database.repository import LibraryRepository
from rom_manager.detection.platform_detector import (
    PLATFORM_BY_EXTENSION,
    detect_platform,
)

_TS = "2024-01-01T00:00:00"


def _seed(repo: LibraryRepository, path: Path, platform: str | None) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x")
    repo.upsert_game(
        original_filename=path.name, source_path=str(path), platform=platform, file_type="rom",
        relative_parent="", region=None, extension=path.suffix.lower(), size_bytes=1, mtime=0,
        sha1=path.name.upper()[:40].ljust(40, "0"), md5="M" * 32, crc32="C" * 8,
        set_type="single", timestamp=_TS,
    )  # fmt: skip
    return str(path)


def _platform(repo: LibraryRepository, path: str) -> str | None:
    with repo.connect() as c:
        return c.execute("SELECT platform FROM games WHERE source_path = ?", (path,)).fetchone()[0]


def test_stale_platform_is_fixed_and_ambiguous_left_alone(tmp_path: Path) -> None:
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    stale = _seed(repo, tmp_path / "nes" / "Final Fantasy VII (Europe).nes", "PlayStation")
    ok = _seed(repo, tmp_path / "nes" / "Mario (USA).nes", "NES")
    ambiguous = _seed(repo, tmp_path / "psx" / "Game (USA).bin", "NES")  # .bin: no es inequívoca
    null_row = _seed(repo, tmp_path / "nes" / "Nullrow.nes", None)

    dry = repo.fix_platform_mismatches(detect_platform, PLATFORM_BY_EXTENSION, dry_run=True)
    assert [c[0] for c in dry] == [stale] and dry[0][1:] == ("PlayStation", "NES")
    assert _platform(repo, stale) == "PlayStation"  # el dry-run no escribe

    repo.fix_platform_mismatches(detect_platform, PLATFORM_BY_EXTENSION, dry_run=False)
    assert _platform(repo, stale) == "NES"
    assert _platform(repo, ok) == "NES"
    assert _platform(repo, ambiguous) == "NES"  # extensión ambigua: intacta
    assert _platform(repo, null_row) is None  # NULL es cosa de backfill_platforms


def test_cli_mismatched_is_dry_run_unless_apply(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    repo = LibraryRepository(tmp_path / ".rommgr" / "library_pc.db")
    stale = _seed(repo, tmp_path / "nes" / "Zelda (USA).nes", "Wii")

    assert cli.main(["fix-platforms", "--mismatched"]) == 0
    assert "DRY RUN" in capsys.readouterr().out and _platform(repo, stale) == "Wii"

    assert cli.main(["fix-platforms", "--mismatched", "--apply"]) == 0
    assert _platform(repo, stale) == "NES"


def test_u1_is_ambiguous_not_64dd() -> None:
    """`.u1` es sufijo de chips arcade y de algún Game Gear: no pertenece solo a 64DD."""
    assert ".u1" not in PLATFORM_BY_EXTENSION
    assert detect_platform(Path("ROMS/gamegear/Shining Force Gaiden II (Japan).u1")) == "Game Gear"
    assert detect_platform(Path("ROMS/n64dd/game.ndd")) == "Nintendo 64DD"
