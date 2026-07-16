"""Tests de mame_loader: load_arcade_infra_names (JUNK-SMART-2) y
load_arcade_crc_index (ZIP-ROUTE-2)."""

from __future__ import annotations

from pathlib import Path

from rom_manager.catalog.mame_loader import (
    load_arcade_crc_index,
    load_arcade_infra_names,
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
