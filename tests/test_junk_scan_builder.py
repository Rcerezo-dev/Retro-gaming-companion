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


def test_junk_scan_gaming_false_positives_2(tmp_path: Path) -> None:
    """JUNK-FIX-3: savestates VBA, NVRAM arcade, saves Sega CD, FDS, C64, shaders, hiscores."""
    (tmp_path / "pokemon.sgm").write_bytes(b"x")
    (tmp_path / "pacman.nv").write_bytes(b"x")
    (tmp_path / "lunar.brm").write_bytes(b"x")
    (tmp_path / "lunar.brmc").write_bytes(b"x")
    (tmp_path / "zelda.fds").write_bytes(b"x")
    (tmp_path / "commando.crt").write_bytes(b"x")
    (tmp_path / "commando.prg").write_bytes(b"x")
    (tmp_path / "crt-royale.fx").write_bytes(b"x")
    (tmp_path / "pacman.hi").write_bytes(b"x")
    result = _build_junk_scan(str(tmp_path))
    assert result["total_junk_files"] == 0


def test_junk_scan_zip_in_platform_folder_is_not_junk(tmp_path: Path) -> None:
    """JUNK-FIX-4: a .zip inside a recognized platform folder IS the ROM, not junk.

    Found on the real library: 2.982 legitimate arcade romsets in arcade\\ plus
    thousands more across snes\\/gba\\/etc. were all flagged as "ZIPs no-ROM" —
    deleting that category would have wiped the arcade collection.
    """
    (tmp_path / "snes" / "Chrono Trigger (USA).zip").parent.mkdir(parents=True)
    (tmp_path / "snes" / "Chrono Trigger (USA).zip").write_bytes(b"x")
    (tmp_path / "arcade" / "pacman.zip").parent.mkdir(parents=True)
    (tmp_path / "arcade" / "pacman.zip").write_bytes(b"x")
    (tmp_path / "cps3" / "fbneo" / "jojoba.fs").parent.mkdir(parents=True)
    (tmp_path / "cps3" / "fbneo" / "jojoba.fs").write_bytes(b"x")
    (tmp_path / "ps2" / "Some Game.part1.rar").parent.mkdir(parents=True)
    (tmp_path / "ps2" / "Some Game.part1.rar").write_bytes(b"x")
    result = _build_junk_scan(str(tmp_path))
    assert result["total_junk_files"] == 0


def test_junk_scan_zip_outside_platform_folder_still_junk(tmp_path: Path) -> None:
    """A .zip loose in an unrecognized folder (e.g. Unknown\\) still needs review."""
    (tmp_path / "Unknown" / "Nintendo - SNES.zip").parent.mkdir(parents=True)
    (tmp_path / "Unknown" / "Nintendo - SNES.zip").write_bytes(b"x")
    result = _build_junk_scan(str(tmp_path))
    assert result["total_junk_files"] == 1
    assert result["categories"][0]["category"] == "ZIPs no-ROM"


def test_junk_scan_chip_tier_off_without_matched_paths(tmp_path: Path) -> None:
    """JUNK-SMART-1: sin matched_paths (setup pipeline) los .bin/.rom nunca se marcan."""
    (tmp_path / "u082.bin").write_bytes(b"x" * 10)
    result = _build_junk_scan(str(tmp_path))
    assert result["total_junk_files"] == 0


def test_junk_scan_chip_tier_flags_unmatched_chips(tmp_path: Path) -> None:
    """JUNK-SMART-1: chip suelto = sin match en BD + nombre de chip + sin .cue + ≤8 MB."""
    unknown = tmp_path / "Unknown"
    unknown.mkdir()
    (unknown / "u082.bin").write_bytes(b"x" * 10)
    (unknown / "mpr-12345a.rom").write_bytes(b"x" * 10)
    (unknown / "ic12.bin").write_bytes(b"x" * 10)
    result = _build_junk_scan(str(tmp_path), matched_paths=set())

    (cat,) = result["categories"]
    assert cat["category"] == "Chips sueltos (sin match en catálogo)"
    assert cat["count"] == 3


def test_junk_scan_chip_tier_respects_evidence(tmp_path: Path) -> None:
    """JUNK-SMART-1: match en BD, nombre de juego, .cue hermano o >8 MB → no es chip."""
    import os

    unknown = tmp_path / "Unknown"
    unknown.mkdir()
    # 1. Nombre de chip pero con match de catálogo en la BD
    matched_chip = unknown / "c1.bin"
    matched_chip.write_bytes(b"x" * 10)
    # 2. Nombre de juego real (patrón No-Intro) — nunca parece chip
    (unknown / "Alien Crush (Japan) (En).bin").write_bytes(b"x" * 10)
    # 3. Nombre de chip pero con .cue en la misma carpeta (set de disco)
    disc = tmp_path / "psx-game"
    disc.mkdir()
    (disc / "track01.cue").write_bytes(b"x")
    (disc / "01.bin").write_bytes(b"x" * 10)
    # 4. Nombre de chip pero >8 MB (los chips reales eran todos ≤8 MB)
    (unknown / "u999.bin").write_bytes(b"x" * (8 * 1024 * 1024 + 1))

    matched = {os.path.normpath(str(matched_chip)).lower()}
    result = _build_junk_scan(str(tmp_path), matched_paths=matched)
    assert result["total_junk_files"] == 0


def test_junk_scan_skips_system_volume_information(tmp_path: Path) -> None:
    (tmp_path / "System Volume Information").mkdir()
    (tmp_path / "System Volume Information" / "WPSettings.dat").write_bytes(b"x")
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
