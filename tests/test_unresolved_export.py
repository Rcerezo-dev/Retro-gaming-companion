from __future__ import annotations

import csv
from pathlib import Path

import pytest

from rom_manager.cli import main
from rom_manager.database.repository import LibraryRepository


def _seed_game(repo: LibraryRepository, name: str, platform: str, sha1: str) -> None:
    repo.upsert_game(
        original_filename=name,
        source_path=f"/roms/{platform}/{name}",
        platform=platform,
        file_type="rom",
        relative_parent=".",
        region="USA",
        extension=".nes",
        size_bytes=512,
        mtime=0,
        sha1=sha1,
        md5="aa" * 16,
        crc32="deadbeef",
        set_type="single",
        timestamp="2024-01-01T00:00:00",
    )


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "lib.sqlite"


def test_unresolved_export_csv(db_path: Path, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    repo = LibraryRepository(db_path)
    _seed_game(repo, "Castlevania.nes", "NES", "aa" * 20)
    _seed_game(repo, "Contra.nes", "NES", "bb" * 20)

    out_path = tmp_path / "unresolved.csv"
    # monkeypatch config so it uses our db
    import rom_manager.cli as cli_mod

    original_load = cli_mod.load_config

    def patched_load(*args, **kwargs):
        cfg = original_load(*args, **kwargs)
        from dataclasses import replace

        return replace(cfg, database_path=db_path)

    monkeypatch.setattr(cli_mod, "load_config", patched_load)
    ret = main(["unresolved", "--export", str(out_path)])
    assert ret == 0
    assert out_path.exists()

    rows = list(csv.DictReader(out_path.read_text(encoding="utf-8").splitlines()))
    assert len(rows) == 2
    filenames = {r["original_filename"] for r in rows}
    assert "Castlevania.nes" in filenames
    assert "Contra.nes" in filenames
    # Check expected columns
    assert "sha1" in rows[0]
    assert "platform" in rows[0]


def test_unresolved_export_empty(db_path: Path, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    import rom_manager.cli as cli_mod

    def patched_load(*args, **kwargs):
        cfg = cli_mod.__wrapped_load(*args, **kwargs)
        from dataclasses import replace

        return replace(cfg, database_path=db_path)

    # Just check that when no unresolved games, export flag is not needed
    LibraryRepository(db_path)
    original_load = cli_mod.load_config

    def patched2(*args, **kwargs):
        cfg = original_load(*args, **kwargs)
        from dataclasses import replace

        return replace(cfg, database_path=db_path)

    monkeypatch.setattr(cli_mod, "load_config", patched2)
    ret = main(["unresolved"])
    assert ret == 0
