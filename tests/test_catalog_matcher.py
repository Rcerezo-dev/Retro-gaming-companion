from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from rom_manager.catalog.matcher import CatalogMatcher, MatchResult, _platform_from_dat_name


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
    assert result.platform == "Game Boy"  # INBOX-FIX-2: derived from the DAT filename


def test_match_redump(catalog_dirs: tuple[Path, Path]) -> None:
    nointro, redump = catalog_dirs
    matcher = CatalogMatcher(nointro, redump)
    result = matcher.match("112233112233112233112233112233112233112233")
    assert isinstance(result, MatchResult)
    assert result.title == "Metal Gear Solid (USA)"
    assert "PlayStation" in result.catalog_source
    assert result.platform == "PlayStation"


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


# ---------------------------------------------------------------------------
# Name-based fallback tests
# ---------------------------------------------------------------------------


def test_name_fallback_medium_confidence(catalog_dirs: tuple[Path, Path]) -> None:
    """SHA1 miss + unique normalised name → medium confidence."""
    nointro, redump = catalog_dirs
    matcher = CatalogMatcher(nointro, redump)
    # Unknown SHA1, but filename normalises to "tetris" → matches "Tetris (World)"
    result = matcher.match("0" * 40, "tetris (world) [!].gb")
    assert result is not None
    assert result.title == "Tetris (World)"
    assert result.confidence == "medium"
    assert result.ambiguous is False


def test_name_fallback_medium_no_extension(catalog_dirs: tuple[Path, Path]) -> None:
    """Filename without extension still matches."""
    nointro, redump = catalog_dirs
    matcher = CatalogMatcher(nointro, redump)
    result = matcher.match("0" * 40, "Tetris (World)")
    assert result is not None
    assert result.confidence == "medium"


def test_name_fallback_low_confidence_ambiguous(tmp_path: Path) -> None:
    """Two titles with the same normalised key → low confidence, ambiguous=True."""
    nointro = tmp_path / "nointro"
    redump = tmp_path / "redump"
    nointro.mkdir()
    redump.mkdir()
    _write_dat(
        nointro / "test.dat",
        [
            ("Tetris (World)", "AA" * 20, "MD1", "C1", 1024),
            ("Tetris (Japan)", "BB" * 20, "MD2", "C2", 1024),
        ],
    )
    matcher = CatalogMatcher(nointro, redump)
    # Both titles normalize to "tetris", so the filename "tetris.gb" is ambiguous
    result = matcher.match("0" * 40, "tetris.gb")
    assert result is not None
    assert result.confidence == "low"
    assert result.ambiguous is True


def test_name_fallback_no_hit_returns_none(catalog_dirs: tuple[Path, Path]) -> None:
    """Unknown SHA1 + unknown name → None."""
    nointro, redump = catalog_dirs
    matcher = CatalogMatcher(nointro, redump)
    result = matcher.match("0" * 40, "completelydifferentgame.gb")
    assert result is None


def test_sha1_takes_priority_over_name(catalog_dirs: tuple[Path, Path]) -> None:
    """SHA1 match always wins even when filename would also match."""
    nointro, redump = catalog_dirs
    matcher = CatalogMatcher(nointro, redump)
    sha1 = "AABBCCAABBCCAABBCCAABBCCAABBCCAABBCCAABBCC"
    result = matcher.match(sha1, "tetris (world).gb")
    assert result is not None
    assert result.confidence == "high"


def test_name_fallback_underscore_filename(catalog_dirs: tuple[Path, Path]) -> None:
    """Filename with parentheses as underscores/annotations → matches catalog."""
    nointro, redump = catalog_dirs
    matcher = CatalogMatcher(nointro, redump)
    # "tetris_(world).gb" → normalize → "tetris"; "Tetris (World)" → "tetris" ✓
    result = matcher.match("0" * 40, "tetris_(world).gb")
    assert result is not None
    assert result.confidence == "medium"


def test_no_filename_returns_none_on_sha1_miss(catalog_dirs: tuple[Path, Path]) -> None:
    """Without filename argument, SHA1 miss → None (no name fallback)."""
    nointro, redump = catalog_dirs
    matcher = CatalogMatcher(nointro, redump)
    result = matcher.match("0" * 40)
    assert result is None


def test_name_fallback_also_sets_platform(catalog_dirs: tuple[Path, Path]) -> None:
    """INBOX-FIX-2: platform is derived on the name-fallback path too, not just SHA1."""
    nointro, redump = catalog_dirs
    matcher = CatalogMatcher(nointro, redump)
    result = matcher.match("0" * 40, "tetris (world).gb")
    assert result is not None
    assert result.platform == "Game Boy"


# ---------------------------------------------------------------------------
# INBOX-FIX-2: DAT filename → platform keyword matching
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("dat_name", "expected"),
    [
        ("Nintendo - Super Nintendo Entertainment System (2026).dat", "SNES"),
        ("Nintendo - Nintendo Entertainment System (Headered) (2026).dat", "NES"),
        ("Nintendo - Game Boy Advance (2026).dat", "Game Boy Advance"),
        ("Nintendo - Game Boy Color (2026).dat", "Game Boy Color"),
        ("Nintendo - Game Boy (2026).dat", "Game Boy"),
        ("Nintendo - Nintendo 3DS (Digital) (CDN).dat", "Nintendo 3DS"),
        ("Nintendo - New Nintendo 3DS (Deprecated).dat", "Nintendo 3DS"),
        ("Nintendo - Nintendo DS (Decrypted).dat", "Nintendo DS"),
        ("Sony - PlayStation 2 - Datfile.dat", "PlayStation 2"),
        ("Sony - PlayStation Portable (PSN).dat", "PSP"),
        ("Sony - PlayStation - Datfile.dat", "PlayStation"),
        ("Sega - Mega Drive - Genesis.dat", "Sega Mega Drive"),
        ("NEC - PC Engine - TurboGrafx-16.dat", "PC Engine"),
        ("Bandai - WonderSwan Color.dat", "WonderSwan Color"),
        ("Bandai - WonderSwan.dat", "WonderSwan"),
        ("SNK - Neo Geo Pocket Color.dat", "Neo Geo Pocket Color"),
    ],
)
def test_platform_from_dat_name_keyword_priority(dat_name: str, expected: str) -> None:
    """Longer/more-specific keywords (e.g. SNES) must win over substrings they contain (NES)."""
    assert _platform_from_dat_name(dat_name) == expected


def test_platform_from_dat_name_unmapped_platform_returns_none() -> None:
    """Obscure DATs this project doesn't route to a folder stay unmapped, not guessed."""
    assert _platform_from_dat_name("Apple - IIGS (A2R) (2022).dat") is None
    assert _platform_from_dat_name("Microsoft - Xbox 360 (Digital).dat") is None


# ---------------------------------------------------------------------------
# MATCH-FIX-1 — arcade antes que el fallback por título para nombres MAME
# ---------------------------------------------------------------------------


def _write_fbneo_dat(path: Path, games: list[tuple[str, str]]) -> None:
    """FBNeo/Logiqx DAT: [(set_name, description), ...]."""
    root = ET.Element("datafile")
    for name, desc in games:
        ET.SubElement(root, "game", name=name, description=desc, year="1984", manufacturer="Sega")
    ET.ElementTree(root).write(path, encoding="unicode", xml_declaration=False)


@pytest.fixture()
def dirs_with_arcade(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Caso real de MATCH-FIX-1: 'flicky' existe como título en un catálogo
    No-Intro de plataforma ajena Y como set arcade en FBNeo."""
    nointro = tmp_path / "nointro"
    redump = tmp_path / "redump"
    arcade = tmp_path / "arcade"
    nointro.mkdir()
    redump.mkdir()
    arcade.mkdir()
    _write_dat(
        nointro / "Fujitsu - FM-7.dat",
        [("Flicky", "F17A11" * 7, "MD5F", "CRCF", 65536)],
    )
    _write_fbneo_dat(arcade / "FBNeo Arcade.dat", [("flicky", "Flicky (128k Version)")])
    return nointro, redump, arcade


def test_mame_style_zip_prefers_arcade_over_title_fallback(
    dirs_with_arcade: tuple[Path, Path, Path],
) -> None:
    """flicky.zip (sin región) debe matchear el catálogo arcade, no FM-7."""
    nointro, redump, arcade = dirs_with_arcade
    matcher = CatalogMatcher(nointro, redump, arcade_dir=arcade)
    result = matcher.match("00" * 20, filename="flicky.zip")
    assert result is not None
    assert result.title == "Flicky (128k Version)"
    assert result.platform == "FBNeo"


def test_zip_with_region_tag_keeps_title_fallback_first(
    dirs_with_arcade: tuple[Path, Path, Path],
) -> None:
    """Un nombre con '(Región)' no es estilo MAME: sigue mandando el índice de títulos."""
    nointro, redump, arcade = dirs_with_arcade
    matcher = CatalogMatcher(nointro, redump, arcade_dir=arcade)
    result = matcher.match("00" * 20, filename="Flicky (Japan).zip")
    assert result is not None
    assert "FM-7" in result.catalog_source


def test_non_zip_without_region_keeps_title_fallback_first(
    dirs_with_arcade: tuple[Path, Path, Path],
) -> None:
    """Una ROM de consola renombrada sin región (.d77) no debe tratarse como arcade."""
    nointro, redump, arcade = dirs_with_arcade
    matcher = CatalogMatcher(nointro, redump, arcade_dir=arcade)
    result = matcher.match("00" * 20, filename="Flicky.d77")
    assert result is not None
    assert "FM-7" in result.catalog_source


def test_mame_style_zip_falls_back_to_title_index_when_not_in_arcade(
    dirs_with_arcade: tuple[Path, Path, Path],
) -> None:
    """Un .zip sin región que el catálogo arcade no conoce conserva el fallback por título."""
    nointro, redump, _arcade = dirs_with_arcade
    matcher = CatalogMatcher(nointro, redump)  # sin catálogo arcade
    result = matcher.match("00" * 20, filename="flicky.zip")
    assert result is not None
    assert "FM-7" in result.catalog_source


# ---------------------------------------------------------------------------
# ZIP-ROUTE-1 — índice CRC32 para identificar ZIPs por el header
# ---------------------------------------------------------------------------


def test_crc_index_maps_title_dat_and_platform(catalog_dirs: tuple[Path, Path]) -> None:
    nointro, redump = catalog_dirs
    matcher = CatalogMatcher(nointro, redump)
    index = matcher.crc_index()
    assert index["CRC1"] == ("Tetris (World)", "Nintendo - Game Boy.dat", "Game Boy")
    assert index["CRC2"][0] == "Metal Gear Solid (USA)"


def test_crc_index_drops_cross_dat_collisions(tmp_path: Path) -> None:
    """Un CRC reclamado por dos títulos (DAT recopilatorio tipo Evercade) es
    ambiguo y se descarta: nunca adivinar la plataforma."""
    nointro = tmp_path / "nointro"
    redump = tmp_path / "redump"
    nointro.mkdir()
    redump.mkdir()
    _write_dat(
        nointro / "Atari - Atari 2600.dat",
        [("Asteroids (USA)", "AA" * 20, "M1", "46DF91AD", 4096)],
    )
    _write_dat(
        nointro / "Blaze Entertainment - Evercade.dat",
        [("Super Pocket - The Atari Collection (World)", "BB" * 20, "M2", "46DF91AD", 4096)],
    )
    matcher = CatalogMatcher(nointro, redump)
    assert "46DF91AD" not in matcher.crc_index()


def test_load_nointro_dat_empty_size_attr(tmp_path: Path) -> None:
    """INICIO-FIX-1: un DAT real trae <rom size=""> — no debe reventar int('')."""
    from rom_manager.catalog.catalog_loader import load_nointro_dat

    dat = tmp_path / "x.dat"
    dat.write_text(
        '<datafile><game name="G"><rom name="g.rom" size="" sha1="AB12"/></game></datafile>'
    )
    entries = load_nointro_dat(dat)
    assert entries["AB12"].size_bytes == 0
