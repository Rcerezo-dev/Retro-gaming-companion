"""Los índices de catálogo del junk-scan no se reparsean mientras los DAT no cambien."""

from types import SimpleNamespace

import rom_manager.catalog.mame_loader as mame_loader
import rom_manager.catalog.matcher as matcher
from rom_manager.web.handlers.esde import maintenance


def test_catalog_inputs_se_memoiza_y_se_invalida(tmp_path, monkeypatch):
    arcade = tmp_path / "arcade"
    arcade.mkdir()
    dat = arcade / "mame.dat"
    dat.write_text("a")
    calls = []

    def fake_dir(path):
        calls.append(path)
        return {"bagman"}

    monkeypatch.setattr(mame_loader, "load_arcade_dir", fake_dir)
    monkeypatch.setattr(mame_loader, "load_arcade_infra_names", lambda p: {"neogeo"})
    monkeypatch.setattr(mame_loader, "load_arcade_crc_index", lambda p: {})
    monkeypatch.setattr(
        matcher,
        "CatalogMatcher",
        lambda **kw: SimpleNamespace(crc_index=lambda: {}),
    )
    monkeypatch.setattr(maintenance, "_catalog_inputs_cache", None)
    cfg = SimpleNamespace(
        catalogs_arcade_dir=arcade, catalogs_nointro_dir=None, catalogs_redump_dir=None
    )

    first = maintenance._catalog_inputs(cfg)
    assert maintenance._catalog_inputs(cfg) is first
    assert len(calls) == 1

    dat.write_text("cambiado")  # cambia el tamaño → firma distinta
    maintenance._catalog_inputs(cfg)
    assert len(calls) == 2
