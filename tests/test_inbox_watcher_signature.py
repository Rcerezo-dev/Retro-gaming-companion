"""El watcher no debe relanzar el pipeline por archivos que ya vio y no consume."""

from rom_manager.web.daemons import _inbox_pending, _pending_signature


def test_pending_ignora_saves_part_y_ocultos(tmp_path):
    for name in ("a.torrent", "b.zip", "c.sav", "d.zip.part", ".oculto", "_x.zip"):
        (tmp_path / name).write_bytes(b"1")
    (tmp_path / "carpeta").mkdir()

    found = {p.name for p in _inbox_pending(tmp_path, frozenset({".sav"}))}

    assert found == {"b.zip"}


def test_signature_estable_y_cambia_con_el_contenido(tmp_path):
    f = tmp_path / "a.torrent"
    f.write_bytes(b"1")
    first = _pending_signature([f])
    assert _pending_signature([f]) == first

    f.write_bytes(b"22")  # cambia el tamaño
    assert _pending_signature([f]) != first
