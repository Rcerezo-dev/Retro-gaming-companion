"""Tests de mame_loader: load_arcade_infra_names (JUNK-SMART-2) y
load_arcade_crc_index (ZIP-ROUTE-2)."""

from __future__ import annotations

from pathlib import Path

from rom_manager.catalog.mame_loader import (
    load_arcade_crc_index,
    load_arcade_infra_names,
    load_arcade_manifest,
    load_mame_xml,
)

_XML = """<?xml version="1.0"?>
<mame>
  <machine name="sf2"><description>Street Fighter II</description></machine>
  <machine name="neogeo" isbios="yes"><description>Neo-Geo BIOS</description></machine>
  <machine name="kb_pcat101" isdevice="yes"><description>PC/AT Keyboard</description></machine>
  <machine name="qsound" runnable="no"><description>QSound</description></machine>
</mame>
"""


def test_infra_names_are_the_ones_load_mame_xml_skips(tmp_path: Path) -> None:
    xml = tmp_path / "mame.xml"
    xml.write_text(_XML, encoding="utf-8")

    playable = load_mame_xml(xml)
    infra = load_arcade_infra_names(tmp_path)

    assert set(playable) == {"sf2"}
    assert infra == {"neogeo", "kb_pcat101", "qsound"}
    assert not (infra & set(playable))


def test_infra_names_missing_dir_is_empty() -> None:
    assert load_arcade_infra_names(Path("no-existe")) == set()


def test_load_mame_xml_reads_game_tag_under_mame_root(tmp_path: Path) -> None:
    """ARCADE-RENAME-BUG-1a: MAME 2003-Plus.dat real tiene root.tag=='mame'
    pero hijos <game>, no <machine> -- antes devolvía 0 machines en silencio."""
    xml = tmp_path / "mame2003plus.dat"
    xml.write_text(
        '<?xml version="1.0"?>\n<mame>\n'
        '  <game name="sf2"><description>Street Fighter II</description></game>\n'
        "</mame>\n",
        encoding="utf-8",
    )
    assert set(load_mame_xml(xml)) == {"sf2"}


_DAT = """<?xml version="1.0"?>
<datafile>
  <game name="lemmings">
    <rom name="lem_01.bin" size="1024" crc="aabb0001"/>
    <rom name="lem_02.bin" size="1024" crc="aabb0002"/>
  </game>
  <game name="lemmingsj">
    <rom name="lem_01.bin" size="1024" crc="aabb0001"/>
    <rom name="lem_03.bin" size="1024" crc="aabb0003"/>
  </game>
</datafile>
"""


def test_arcade_crc_index_maps_crc_to_sets(tmp_path: Path) -> None:
    """ZIP-ROUTE-2: crc→{sets}; un CRC compartido (parent/clon) lista ambos."""
    (tmp_path / "MAME.dat").write_text(_DAT, encoding="utf-8")
    (tmp_path / "mame.xml").write_text(_XML, encoding="utf-8")  # los .xml se ignoran

    index = load_arcade_crc_index(tmp_path)

    assert index["AABB0001"] == {"lemmings", "lemmingsj"}
    assert index["AABB0002"] == {"lemmings"}
    assert index["AABB0003"] == {"lemmingsj"}


def test_arcade_crc_index_missing_dir_is_empty() -> None:
    assert load_arcade_crc_index(Path("no-existe")) == {}


def test_arcade_crc_index_ignores_console_only_fbneo_dats(tmp_path: Path) -> None:
    """ARCADE-DAT-CONTAMINATION: un DAT "X only" de FBNeo que no sea Arcade
    (Game Gear, SNES, Master System…) no debe contaminar el índice — un ZIP
    de esa consola no puede votar como "set arcade completo". Reproducido en
    real 2026-09-02: 23 ZIPs de Amiga se movieron a arcade/ por esto."""
    console_dat = """<?xml version="1.0"?>
<datafile>
  <game name="sonic">
    <rom name="sonic.md" size="524288" crc="deadbeef"/>
  </game>
</datafile>
"""
    (tmp_path / "FinalBurn Neo (ClrMame Pro XML, Megadrive only).dat").write_text(
        console_dat, encoding="utf-8"
    )
    (tmp_path / "FinalBurn Neo (ClrMame Pro XML, Arcade only).dat").write_text(
        _DAT, encoding="utf-8"
    )

    index = load_arcade_crc_index(tmp_path)

    assert "DEADBEEF" not in index
    assert index["AABB0001"] == {"lemmings", "lemmingsj"}


def test_arcade_manifest_lists_expected_roms_per_machine(tmp_path: Path) -> None:
    """ARCADE-RECON-1: machine -> roms esperados, para calcular cobertura."""
    (tmp_path / "MAME.dat").write_text(_DAT, encoding="utf-8")

    manifest = load_arcade_manifest(tmp_path)

    assert manifest["lemmings"] == [
        ("lem_01.bin", "AABB0001", 1024),
        ("lem_02.bin", "AABB0002", 1024),
    ]
    assert manifest["lemmingsj"] == [
        ("lem_01.bin", "AABB0001", 1024),
        ("lem_03.bin", "AABB0003", 1024),
    ]


def test_arcade_manifest_missing_dir_is_empty() -> None:
    assert load_arcade_manifest(Path("no-existe")) == {}


def test_arcade_manifest_ignores_console_only_fbneo_dats(tmp_path: Path) -> None:
    """Mismo filtro que load_arcade_crc_index — ARCADE-RECON no debe poder
    reconstruir un "set arcade" a partir de chips de un DAT de consola."""
    console_dat = """<?xml version="1.0"?>
<datafile>
  <game name="sonic">
    <rom name="sonic.md" size="524288" crc="deadbeef"/>
  </game>
</datafile>
"""
    (tmp_path / "FinalBurn Neo (ClrMame Pro XML, Game Gear only).dat").write_text(
        console_dat, encoding="utf-8"
    )

    manifest = load_arcade_manifest(tmp_path)

    assert "sonic" not in manifest


def test_arcade_manifest_dedupes_same_machine_across_dat_sources(tmp_path: Path) -> None:
    """Un mismo set (p.ej. rtype2) puede definirse tanto en el DAT de MAME
    como en el de FBNeo, con roms idénticos — no debe contarse dos veces
    (bloquearía ARCADE-RECON exigiendo dos copias físicas del mismo chip)."""
    dat = """<?xml version="1.0"?>
<datafile>
  <game name="rtype2">
    <rom name="ic5" size="279" crc="21ede612"/>
  </game>
</datafile>
"""
    (tmp_path / "MAME.dat").write_text(dat, encoding="utf-8")
    (tmp_path / "FBNeo.dat").write_text(dat, encoding="utf-8")

    manifest = load_arcade_manifest(tmp_path)

    assert manifest["rtype2"] == [("ic5", "21EDE612", 279)]


def test_infra_names_memoized_until_files_change(tmp_path: Path, monkeypatch) -> None:
    """INICIO-FIX-2: el listxml real pesa cientos de MB — la segunda llamada
    con los mismos archivos no re-parsea; modificar el XML invalida la caché."""
    import rom_manager.catalog.mame_loader as ml

    xml = tmp_path / "mame.xml"
    xml.write_text(_XML, encoding="utf-8")
    calls: list[Path] = []
    real_parse = ml.ET.parse
    monkeypatch.setattr(ml.ET, "parse", lambda p: calls.append(p) or real_parse(p))

    expected = {"neogeo", "kb_pcat101", "qsound"}
    assert ml.load_arcade_infra_names(tmp_path) == expected
    assert ml.load_arcade_infra_names(tmp_path) == expected
    assert len(calls) == 1  # segunda llamada servida de caché

    xml.write_text(_XML.replace('name="qsound"', 'name="qsound2"'), encoding="utf-8")
    assert "qsound2" in ml.load_arcade_infra_names(tmp_path)
    assert len(calls) == 2  # firma distinta → re-parseo
