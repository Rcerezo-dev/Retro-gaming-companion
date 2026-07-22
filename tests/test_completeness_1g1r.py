"""AUD-5 — completitud de colección por plataforma en modo 1G1R.

El índice de títulos agrupa por título base (``normalize_for_match`` quita
región/revisión), así "Sonic (USA)" y "Sonic (Europe)" cuentan como un solo
juego; el cruce contra ``games`` da tenidos/faltantes por DAT.
"""

from __future__ import annotations

from pathlib import Path

from rom_manager.config import load_config
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.handlers.games import _dat_title_index, _owned_title_keys

_DAT_NAME = "Sega - Mega Drive - Genesis.dat"
_DAT_XML = """<?xml version="1.0"?>
<datafile>
  <header><name>No-Intro: Sega - Mega Drive - Genesis</name></header>
  <game name="Sonic The Hedgehog (USA)">
    <rom name="s1.md" size="1" crc="AAAAAAAA" sha1="{a}"/>
  </game>
  <game name="Sonic The Hedgehog (Europe)">
    <rom name="s2.md" size="1" crc="BBBBBBBB" sha1="{b}"/>
  </game>
  <game name="Tetris (World)">
    <rom name="t.md" size="1" crc="CCCCCCCC" sha1="{c}"/>
  </game>
</datafile>
""".format(a="A" * 40, b="B" * 40, c="C" * 40)


def _make_config(tmp_path: Path):
    cfg = load_config()
    cfg.catalogs_nointro_dir = tmp_path / "nointro"
    cfg.catalogs_redump_dir = tmp_path / "redump"
    cfg.catalogs_arcade_dir = tmp_path / "arcade"
    cfg.catalogs_nointro_dir.mkdir()
    (cfg.catalogs_nointro_dir / _DAT_NAME).write_text(_DAT_XML, encoding="utf-8")
    return cfg


def test_dat_title_index_groups_regions_1g1r(tmp_path: Path) -> None:
    index = _dat_title_index(_make_config(tmp_path))
    raw_total, titles = index[_DAT_NAME]
    assert raw_total == 3  # dumps brutos
    assert len(titles) == 2  # títulos base: sonic + tetris
    assert "sonic the hedgehog" in titles
    assert titles["tetris"] == "Tetris (World)"


def test_owned_vs_dat_gives_missing_titles(tmp_path: Path) -> None:
    cfg = _make_config(tmp_path)
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    repo.upsert_game(
        original_filename="sonic.md",
        source_path=str(tmp_path / "sonic.md"),
        platform="Sega Mega Drive",
        file_type="rom",
        relative_parent="",
        region="Europe",
        extension=".md",
        size_bytes=1,
        mtime=0,
        sha1="B" * 40,
        md5="M" * 32,
        crc32="BBBBBBBB",
        set_type="single",
        timestamp="2026-07-12T00:00:00",
    )
    with repo.connect() as conn:
        conn.execute(
            "UPDATE games SET canonical_title=?, catalog_source=?",
            ("Sonic The Hedgehog (Europe)", _DAT_NAME),
        )
        conn.commit()

    owned = _owned_title_keys(repo)
    assert owned == {_DAT_NAME: {"sonic the hedgehog"}}

    _raw, titles = _dat_title_index(cfg)[_DAT_NAME]
    missing = sorted(titles[k] for k in set(titles) - owned[_DAT_NAME])
    assert missing == ["Tetris (World)"]  # tienes Sonic (cualquier región) — 1/2 (50 %)
