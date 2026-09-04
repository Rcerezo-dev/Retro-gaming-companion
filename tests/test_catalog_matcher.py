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


def test_ambiguous_title_prefers_platform_matching_extension(tmp_path: Path) -> None:
    """MATCH-FIX-2: caso real (Final Fantasy III) — el mismo título normalizado
    existe en el DAT de NES y en el de Nintendo 3DS (Virtual Console). Sin el
    fix, siempre ganaba el primer hit por orden alfabético del .dat ("3DS" <
    "Entertainment System"), asignando la plataforma equivocada a un .nes real."""
    nointro = tmp_path / "nointro"
    redump = tmp_path / "redump"
    nointro.mkdir()
    redump.mkdir()
    # Mismo orden alfabético que reproduce el bug real: "3DS" antes que
    # "Entertainment System" en sorted(directory.glob("*.dat")).
    _write_dat(
        nointro / "Nintendo - Nintendo 3DS (Digital) (CDN).dat",
        [("Final Fantasy III (Japan) (Virtual Console)", "AA" * 20, "MD1", "C1", 1024)],
    )
    _write_dat(
        nointro / "Nintendo - Nintendo Entertainment System.dat",
        [("Final Fantasy III (Japan) (Virtual Console)", "BB" * 20, "MD2", "C2", 1024)],
    )
    matcher = CatalogMatcher(nointro, redump)
    result = matcher.match("0" * 40, "Final Fantasy III (J) [T+Eng1.0_ad0220].nes")
    assert result is not None
    assert result.ambiguous is True
    assert result.confidence == "low"
    assert result.platform == "NES"
    assert "Entertainment System" in result.catalog_source


def test_ambiguous_title_falls_back_to_first_hit_without_extension_signal(tmp_path: Path) -> None:
    """Sin extensión que desambigüe (p.ej. .zip) NI ruta real (source_path=None),
    se mantiene el comportamiento previo: el primer hit por orden de carga."""
    nointro = tmp_path / "nointro"
    redump = tmp_path / "redump"
    nointro.mkdir()
    redump.mkdir()
    _write_dat(
        nointro / "Nintendo - Nintendo 3DS (Digital) (CDN).dat",
        [("Final Fantasy III (Japan) (Virtual Console)", "AA" * 20, "MD1", "C1", 1024)],
    )
    _write_dat(
        nointro / "Nintendo - Nintendo Entertainment System.dat",
        [("Final Fantasy III (Japan) (Virtual Console)", "BB" * 20, "MD2", "C2", 1024)],
    )
    matcher = CatalogMatcher(nointro, redump)
    result = matcher.match("0" * 40, "Final Fantasy III (J) [T+Eng1.0_ad0220].zip")
    assert result is not None
    assert result.ambiguous is True
    assert result.platform == "Nintendo 3DS"


def test_ambiguous_extension_prefers_platform_of_containing_folder(tmp_path: Path) -> None:
    """CATALOG-MATCH-BUG-1 / GBA-MISPLACED-2: cuando el SHA1 no calza (típico de
    un .chd, que no es el hash crudo del disco) y la extensión es ambigua (no
    desambigua por sí sola), el fallback por título ya no debe quedarse siempre
    con el primer hit por orden de carga del .dat — debe preferir la entrada
    cuya plataforma coincide con la carpeta real del archivo (psx/, saturn/...),
    la misma señal que ``detect_platform()`` usa en el resto de la app."""
    nointro = tmp_path / "nointro"
    redump = tmp_path / "redump"
    nointro.mkdir()
    redump.mkdir()
    _write_dat(
        redump / "Sega - Dreamcast.dat",
        [("Same Title (USA)", "AA" * 20, "MD1", "C1", 1024)],
    )
    _write_dat(
        redump / "Sega - Saturn.dat",
        [("Same Title (USA)", "BB" * 20, "MD2", "C2", 1024)],
    )
    matcher = CatalogMatcher(nointro, redump)
    # Sin source_path: comportamiento previo, gana el primero por orden de carga.
    result_no_context = matcher.match("0" * 40, "Same Title (USA).chd")
    assert result_no_context is not None
    assert result_no_context.platform == "Dreamcast"

    # Con la ruta real en saturn/: debe elegir el DAT de Saturn, no el primero.
    result_with_context = matcher.match(
        "0" * 40,
        "Same Title (USA).chd",
        source_path="E:/Carpetas anbernic/saturn/Same Title (USA).chd",
    )
    assert result_with_context is not None
    assert result_with_context.platform == "Sega Saturn"
    assert result_with_context.ambiguous is True


def test_multi_disc_title_picks_matching_disc_entry(tmp_path: Path) -> None:
    """GAMECUBE-DISC-BUG-1e: caso real (Metal Gear Solid - The Twin Snakes,
    GameCube). normalize_for_match() borra "(Disc N)" junto con el resto de
    anotaciones, así que Disc 1 y Disc 2 colapsan a la misma clave del índice
    de títulos y ambos hits son de la misma plataforma (el desempate por
    extensión no los separa). Sin el fix, el Disc 2 real habría heredado el
    canonical_title del Disc 1 (siempre gana el primero en orden de carga),
    causando una colisión de nombre que hacía parecer duplicados a dos discos
    distintos."""
    nointro = tmp_path / "nointro"
    redump = tmp_path / "redump"
    nointro.mkdir()
    redump.mkdir()
    _write_dat(
        nointro / "Nintendo - GameCube.dat",
        [
            ("Metal Gear Solid - The Twin Snakes (USA) (Disc 1)", "AA" * 20, "MD1", "C1", 1024),
            ("Metal Gear Solid - The Twin Snakes (USA) (Disc 2)", "BB" * 20, "MD2", "C2", 1024),
        ],
    )
    matcher = CatalogMatcher(nointro, redump)

    result_disc1 = matcher.match("0" * 40, "Metal Gear Solid - The Twin Snakes (USA) (Disc 1).rvz")
    result_disc2 = matcher.match("0" * 40, "Metal Gear Solid - The Twin Snakes (USA) (Disc 2).rvz")

    assert result_disc1 is not None and result_disc2 is not None
    assert result_disc1.title == "Metal Gear Solid - The Twin Snakes (USA) (Disc 1)"
    assert result_disc2.title == "Metal Gear Solid - The Twin Snakes (USA) (Disc 2)"


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


def test_matcher_loads_clrmamepro_format_dat(tmp_path: Path) -> None:
    """CATALOG-MATCH-BUG-1: varios DAT reales de la biblioteca (Game Boy, NES,
    PS1...) vienen en formato clrmamepro (texto plano), no XML. El loader
    anterior (``load_nointro_dat``, solo XML) los descartaba en silencio —
    degradando el match SHA1 exacto a un fallback por título mucho menos
    fiable para esas plataformas. ``load_dat_file`` autodetecta el formato."""
    nointro = tmp_path / "nointro"
    redump = tmp_path / "redump"
    nointro.mkdir()
    redump.mkdir()
    sha1 = "AABBCCDDEEFF00112233445566778899AABBCCDD"
    (nointro / "Sony - PlayStation.dat").write_text(
        'clrmamepro (\n\tname "No-Intro: Sony - PlayStation"\n)\n\n'
        'game (\n\tname "Oddworld - Abe\'s Oddysee (USA)"\n'
        f'\trom ( name "Oddworld - Abe\'s Oddysee (USA).bin" size 622297088 '
        f"crc f26d7a0b md5 aabbccdd sha1 {sha1} )\n)\n"
    )
    matcher = CatalogMatcher(nointro, redump)
    result = matcher.match(sha1)
    assert result is not None
    assert result.title == "Oddworld - Abe's Oddysee (USA)"
    assert result.confidence == "high"


def test_psx_region_disambiguated_by_real_boot_serial(tmp_path: Path) -> None:
    """CATALOG-MATCH-REGION-1: "Tekken (USA)" y "Tekken (Europe)" colapsan a la
    misma clave de título normalizado, y el SHA1 de un .chd/.bin real nunca
    calza contra el DAT (hashea la pista cruda). El serial de arranque leído
    del disco real (SYSTEM.CNF) sí es contenido real -- comparado contra
    ``CatalogEntry.serial`` (Redump), desambigua sin adivinar candidates[0]."""
    from tests.test_ra_hash_psx import _build_psx_image

    nointro = tmp_path / "nointro"
    redump = tmp_path / "redump"
    nointro.mkdir()
    redump.mkdir()
    (redump / "Sony - PlayStation.dat").write_text(
        'game (\n\tname "Same Title (USA)"\n\tserial "TEST.EXE"\n'
        '\trom ( name "a.bin" size 1 crc AA md5 AA sha1 ' + "AA" * 20 + " )\n)\n"
        'game (\n\tname "Same Title (Europe)"\n\tserial "OTHER.EXE"\n'
        '\trom ( name "b.bin" size 1 crc BB md5 BB sha1 ' + "BB" * 20 + " )\n)\n"
    )
    matcher = CatalogMatcher(nointro, redump)

    psx_dir = tmp_path / "library" / "psx"
    psx_dir.mkdir(parents=True)
    bin_path = _build_psx_image(psx_dir)
    bin_path = bin_path.rename(psx_dir / "Same Title (USA).bin")

    result = matcher.match("0" * 40, bin_path.name, source_path=str(bin_path))
    assert result is not None
    assert result.title == "Same Title (USA)"
    assert result.confidence == "medium"
    assert result.ambiguous is False


def test_load_nointro_dat_empty_size_attr(tmp_path: Path) -> None:
    """INICIO-FIX-1: un DAT real trae <rom size=""> — no debe reventar int('')."""
    from rom_manager.catalog.catalog_loader import load_nointro_dat

    dat = tmp_path / "x.dat"
    dat.write_text(
        '<datafile><game name="G"><rom name="g.rom" size="" sha1="AB12"/></game></datafile>'
    )
    entries = load_nointro_dat(dat)
    assert entries["AB12"].size_bytes == 0
