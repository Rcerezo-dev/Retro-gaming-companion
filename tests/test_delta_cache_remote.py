from rom_manager.sync.delta_cache import DeltaCache


def test_cambio_de_remote_invalida_el_cache(tmp_path):
    save = tmp_path / "a.srm"
    save.write_bytes(b"x")
    cache = DeltaCache(tmp_path)
    cache.bind_remote("dropbox:/saves", None)
    cache.mark_synced("a.srm", save, "upload")
    assert not cache.content_changed("a.srm", save)

    cache = DeltaCache(tmp_path)  # recarga desde disco, mismo remote → se conserva
    cache.bind_remote("dropbox:/saves", None)
    assert not cache.content_changed("a.srm", save)

    cache = DeltaCache(tmp_path)
    cache.bind_remote("gdrive:/saves", None)  # otro remote → hay que subir de nuevo
    assert cache.content_changed("a.srm", save)
