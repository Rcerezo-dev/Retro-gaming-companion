"""``_dat_title_index`` no reparsea los DATs mientras no cambien en disco."""

from types import SimpleNamespace

import rom_manager.catalog.catalog_loader as loader
from rom_manager.web.handlers import games


def test_dat_index_se_memoiza_y_se_invalida_al_cambiar_el_dat(tmp_path, monkeypatch):
    dat = tmp_path / "snes.dat"
    dat.write_text("a")
    calls = []

    def fake_load(path):
        calls.append(path)
        return "label", {"k": SimpleNamespace(title="Sonic (USA)")}

    monkeypatch.setattr(loader, "_detect_dat_format", lambda p: "nointro")
    monkeypatch.setattr(loader, "load_nointro_dat_with_header", fake_load)
    monkeypatch.setattr(games, "_dat_index_cache", None)
    cfg = SimpleNamespace(
        catalogs_nointro_dir=tmp_path, catalogs_redump_dir=None, catalogs_arcade_dir=None
    )

    first = games._dat_title_index(cfg)
    assert games._dat_title_index(cfg) is first
    assert len(calls) == 1

    dat.write_text("cambiado")  # cambia el tamaño → firma distinta
    games._dat_title_index(cfg)
    assert len(calls) == 2
