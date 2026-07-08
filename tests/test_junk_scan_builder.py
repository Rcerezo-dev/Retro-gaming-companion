"""Tests de _build_junk_scan (web/builders/folders.py) — MEJ-6."""

from __future__ import annotations

from pathlib import Path

from rom_manager.web.builders.folders import _build_junk_scan


def _make_tree(root: Path) -> None:
    (root / "roms").mkdir()
    (root / "roms" / "juego.gba").write_bytes(b"x" * 10)  # gaming → no basura
    (root / "config.cfg").write_bytes(b"x")  # config → no basura
    (root / "doc.pdf").write_bytes(b"x" * 100)
    (root / "roms" / "script.py").write_bytes(b"x" * 50)
    (root / ".oculto").mkdir()
    (root / ".oculto" / "otro.pdf").write_bytes(b"x")  # dir oculto → ignorado


def test_junk_scan_classifies_and_exposes_all_paths(tmp_path: Path) -> None:
    _make_tree(tmp_path)
    result = _build_junk_scan(str(tmp_path))

    assert result["total_junk_files"] == 2
    assert result["total_junk_bytes"] == 150
    cats = {c["category"]: c for c in result["categories"]}
    assert set(cats) == {"PDFs", "Scripts Python"}

    # `paths` lleva la lista completa de rutas absolutas (files se corta a 50)
    pdf = cats["PDFs"]
    assert pdf["count"] == len(pdf["paths"]) == 1
    assert pdf["paths"][0] == str(tmp_path / "doc.pdf")
    assert pdf["files"][0]["path"] == "doc.pdf"


def test_junk_scan_paths_beyond_display_cap(tmp_path: Path) -> None:
    for i in range(60):
        (tmp_path / f"f{i}.pdf").write_bytes(b"x")
    result = _build_junk_scan(str(tmp_path))

    (pdf,) = result["categories"]
    assert pdf["count"] == 60
    assert len(pdf["files"]) == 50  # cap de visualización
    assert len(pdf["paths"]) == 60  # lista completa para junk-delete


def test_junk_scan_missing_folder(tmp_path: Path) -> None:
    result = _build_junk_scan(str(tmp_path / "no-existe"))
    assert "error" in result


def test_junk_scan_gaming_false_positives(tmp_path: Path) -> None:
    """JUNK-FIX-1/2: .rvz, .ml1, .sms y savestates numerados no son basura."""
    (tmp_path / "juego.rvz").write_bytes(b"x")
    (tmp_path / "save.ml1").write_bytes(b"x")
    (tmp_path / "Phantasy Star.sms").write_bytes(b"x")
    (tmp_path / "doa2.state1").write_bytes(b"x")
    (tmp_path / "doa2.state23").write_bytes(b"x")
    result = _build_junk_scan(str(tmp_path))
    assert result["total_junk_files"] == 0


def test_junk_scan_skips_saves_bios_android_trees(tmp_path: Path) -> None:
    """JUNK-FIX-1/2: saves/, BIOS/ y Android/ no se escanean (a cualquier nivel)."""
    (tmp_path / "saves" / "nds").mkdir(parents=True)
    (tmp_path / "saves" / "nds" / "raro.dsv").write_bytes(b"x")
    (tmp_path / "gba" / "Saves").mkdir(parents=True)
    (tmp_path / "gba" / "Saves" / "otro.xyz").write_bytes(b"x")
    (tmp_path / "BIOS" / "scummvm").mkdir(parents=True)
    (tmp_path / "BIOS" / "scummvm" / "gui-icons.dat").write_bytes(b"x")
    (tmp_path / "Android").mkdir()
    (tmp_path / "Android" / "algo.apk").write_bytes(b"x")
    (tmp_path / "gba" / "doc.pdf").write_bytes(b"x")  # fuera de árboles excluidos → sí
    result = _build_junk_scan(str(tmp_path))
    assert result["total_junk_files"] == 1
    assert result["categories"][0]["category"] == "PDFs"
