"""MATCH-STALE-LOW-1: `match --include-low` reevalúa filas 'low' obsoletas (anteriores a MATCH-FIX-3)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import rom_manager.cli as cli
from rom_manager.database.repository import LibraryRepository

_TS = "2024-01-01T00:00:00"


class _FakeMatcher:
    """Solo 'Still Matches (USA).nes' casa; el resto, como el matcher actual con nombres ambiguos."""

    nointro_entries = redump_entries = 0

    def __init__(self, **_kw) -> None: ...

    def match(self, sha1, filename=None, source_path=None):
        if filename == "Still Matches (USA).nes":
            return SimpleNamespace(
                title="Still Matches (USA)",
                confidence="medium",
                catalog_source="dat",
                platform="NES",
            )
        return None


def _seed(repo: LibraryRepository, tmp: Path, name: str, title: str) -> str:
    path = tmp / name
    path.write_bytes(b"x")
    repo.upsert_game(
        original_filename=name, source_path=str(path), platform="NES", file_type="rom",
        relative_parent="", region=None, extension=".nes", size_bytes=1, mtime=0,
        sha1=name.upper()[:40].ljust(40, "0"), md5="M" * 32, crc32="C" * 8, set_type="single",
        timestamp=_TS,
    )  # fmt: skip
    repo.update_match(
        str(path), canonical_title=title, match_confidence="low", catalog_source="dat"
    )
    return str(path)


def _row(repo: LibraryRepository, path: str):
    with repo.connect() as c:
        return c.execute(
            "SELECT canonical_title, match_confidence FROM games WHERE source_path = ?", (path,)
        ).fetchone()


@pytest.fixture
def library(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "CatalogMatcher", _FakeMatcher)
    repo = LibraryRepository(tmp_path / ".rommgr" / "library_pc.db")
    stale = _seed(repo, tmp_path, "BurgerTime (USA).nes", "BurgerTime (Japan) (En)")
    good = _seed(repo, tmp_path, "Still Matches (USA).nes", "Old Title")
    return repo, stale, good


def test_plain_match_ignores_low_rows(library) -> None:
    repo, stale, _good = library
    assert cli.main(["match"]) == 0
    assert _row(repo, stale)["canonical_title"] == "BurgerTime (Japan) (En)"


def test_include_low_dry_run_writes_nothing(library, capsys) -> None:
    repo, stale, good = library
    assert cli.main(["match", "--include-low", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "pasarían a sin match: 1" in out and "cambiarían de título: 1" in out
    assert _row(repo, stale)["canonical_title"] == "BurgerTime (Japan) (En)"
    assert _row(repo, good)["canonical_title"] == "Old Title"


def test_include_low_clears_stale_and_keeps_valid(library) -> None:
    repo, stale, good = library
    assert cli.main(["match", "--include-low"]) == 0
    assert _row(repo, stale)["canonical_title"] is None
    assert _row(repo, stale)["match_confidence"] is None
    assert _row(repo, good)["canonical_title"] == "Still Matches (USA)"
