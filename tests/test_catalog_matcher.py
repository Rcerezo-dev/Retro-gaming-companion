from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from rom_manager.catalog.matcher import CatalogMatcher, MatchResult


def _write_dat(path: Path, games: list[tuple[str, str, str, str, int]]) -> None:
    """Write a minimal Logiqx DAT file. games = [(title, sha1, md5, crc, size), ...]"""
    root = ET.Element("datafile")
    for title, sha1, md5, crc, size in games:
        game_el = ET.SubElement(root, "game", name=title)
        ET.SubElement(
            game_el,
            "rom",
            sha1=sha1,
            md5=md5,
            crc=crc,
            size=str(size),
            name=f"{title}.rom",
        )
    tree = ET.ElementTree(root)
    tree.write(path, encoding="unicode", xml_declaration=False)


@pytest.fixture()
def catalog_dirs(tmp_path: Path) -> tuple[Path, Path]:
    nointro = tmp_path / "nointro"
    redump = tmp_path / "redump"
    nointro.mkdir()
    redump.mkdir()

    _write_dat(
        nointro / "Nintendo - Game Boy.dat",
        [("Tetris (World)", "AABBCC" * 7, "MD5A", "CRC1", 32768)],
    )
    _write_dat(
        redump / "Sony - PlayStation.dat",
        [("Metal Gear Solid (USA)", "112233" * 7, "MD5B", "CRC2", 530000000)],
    )
    return nointro, redump


def test_match_nointro(catalog_dirs: tuple[Path, Path]) -> None:
    nointro, redump = catalog_dirs
    matcher = CatalogMatcher(nointro, redump)
    result = matcher.match("AABBCCAABBCCAABBCCAABBCCAABBCCAABBCCAABBCC")
    assert isinstance(result, MatchResult)
    assert result.title == "Tetris (World)"
    assert result.confidence == "high"
    assert "Game Boy" in result.catalog_source


def test_match_redump(catalog_dirs: tuple[Path, Path]) -> None:
    nointro, redump = catalog_dirs
    matcher = CatalogMatcher(nointro, redump)
    result = matcher.match("112233112233112233112233112233112233112233")
    assert isinstance(result, MatchResult)
    assert result.title == "Metal Gear Solid (USA)"
    assert "PlayStation" in result.catalog_source


def test_no_match_returns_none(catalog_dirs: tuple[Path, Path]) -> None:
    nointro, redump = catalog_dirs
    matcher = CatalogMatcher(nointro, redump)
    result = matcher.match("DEADBEEF" * 5 + "DEAD")
    assert result is None


def test_sha1_case_insensitive(catalog_dirs: tuple[Path, Path]) -> None:
    nointro, redump = catalog_dirs
    matcher = CatalogMatcher(nointro, redump)
    sha1_lower = "aabbccaabbccaabbccaabbccaabbccaabbccaabbcc"
    result = matcher.match(sha1_lower)
    assert result is not None
    assert result.title == "Tetris (World)"


def test_catalog_entry_counts(catalog_dirs: tuple[Path, Path]) -> None:
    nointro, redump = catalog_dirs
    matcher = CatalogMatcher(nointro, redump)
    assert matcher.nointro_entries == 1
    assert matcher.redump_entries == 1


def test_missing_catalog_dir(tmp_path: Path) -> None:
    matcher = CatalogMatcher(tmp_path / "no_such_dir", tmp_path / "also_missing")
    assert matcher.nointro_entries == 0
    assert matcher.redump_entries == 0
    assert matcher.match("AABBCC" * 7) is None
