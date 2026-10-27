"""DUP-VARIANT-2 — descartar un archivo ya descartado no anida otra ``_descartados/``."""

from rom_manager.utils.trash import TRASH_DIR_NAME, discard_to_trash


def test_discard_inside_trash_is_noop(tmp_path):
    trash = tmp_path / TRASH_DIR_NAME
    trash.mkdir()
    f = trash / "a.nes"
    f.write_bytes(b"x")
    assert discard_to_trash(f) == f
    assert f.exists()
    assert not (trash / TRASH_DIR_NAME).exists()


def test_discard_normal_file_still_moves(tmp_path):
    f = tmp_path / "a.nes"
    f.write_bytes(b"x")
    dest = discard_to_trash(f)
    assert dest == tmp_path / TRASH_DIR_NAME / "a.nes" and dest.exists() and not f.exists()
