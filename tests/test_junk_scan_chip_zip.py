"""JUNK-ZIP-PIEZA-1: una pieza arcade suelta solo es borrable si su set tiene ZIP."""

from rom_manager.web.builders.folders import _build_junk_scan

CHIPS = {("u2", 4): frozenset({"setok"}), ("u3", 4): frozenset({"setfalta"})}


def _cats(tmp_path):
    for name in ("u2", "u3", "readme_raro"):
        (tmp_path / name).write_bytes(b"1234")
    (tmp_path / "setok.zip").write_bytes(b"x")
    scan = _build_junk_scan(str(tmp_path), arcade_chip_index=CHIPS)
    return {c["category"]: (c["confidence"], c["count"]) for c in scan["categories"]}


def test_pieza_con_zip_sigue_safe_delete_y_sin_zip_pasa_a_review(tmp_path):
    cats = _cats(tmp_path)
    assert cats["Otros (sin extensión)"] == ("safe_delete", 1)  # u2: setok.zip existe
    assert cats["Chips arcade sin su ZIP (reconstruir, no borrar)"] == ("review", 1)  # u3
    assert cats["Sin identificar (revisar)"] == ("review", 1)  # readme_raro


def test_sin_indice_el_comportamiento_no_cambia(tmp_path):
    (tmp_path / "u3").write_bytes(b"1234")
    scan = _build_junk_scan(str(tmp_path))
    assert [(c["category"], c["confidence"]) for c in scan["categories"]] == [
        ("Otros (sin extensión)", "safe_delete")
    ]
