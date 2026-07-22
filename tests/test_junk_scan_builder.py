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


def test_junk_scan_zip_classification_by_arcade_knowledge(tmp_path: Path) -> None:
    """JUNK-SMART-2: los ZIPs sueltos se separan por catálogo arcade / MAME / BIOS."""
    unknown = tmp_path / "Unknown"
    unknown.mkdir()
    (unknown / "sf2.zip").write_bytes(b"x")  # set arcade jugable
    (unknown / "kb_pcat101.zip").write_bytes(b"x")  # device MAME
    (unknown / "naomi.zip").write_bytes(b"x")  # BIOS conocida
    # colección fuente = contenedor de zips anidados (ZIP-ROUTE-5)
    _make_zip(unknown / "Nintendo - SNES.zip", {"a.zip": b"x", "b.zip": b"y"})
    (unknown / "misterio.zip").write_bytes(b"x")  # sin evidencia

    result = _build_junk_scan(
        str(tmp_path),
        matched_paths=set(),
        arcade_names={"sf2"},
        mame_infra_names={"kb_pcat101"},
        known_bios_files={"naomi.zip"},
    )
    by_cat = {c["category"]: [f["path"] for f in c["files"]] for c in result["categories"]}
    assert by_cat["ROMs arcade sin organizar (no borrar)"] == [str(Path("Unknown/sf2.zip"))]
    assert by_cat["Infraestructura MAME (bios/devices, no jugable)"] == [
        str(Path("Unknown/kb_pcat101.zip"))
    ]
    assert by_cat["BIOS conocidas (mover a bios/, no borrar)"] == [str(Path("Unknown/naomi.zip"))]
    assert by_cat["Colecciones fuente (revisar)"] == [str(Path("Unknown/Nintendo - SNES.zip"))]
    assert by_cat["ZIPs no-ROM"] == [str(Path("Unknown/misterio.zip"))]


def test_junk_scan_zip_tier_off_without_arcade_names(tmp_path: Path) -> None:
    """JUNK-SMART-2: sin arcade_names (setup pipeline) todo ZIP suelto sigue en 'ZIPs no-ROM'."""
    (tmp_path / "sf2.zip").write_bytes(b"x")
    result = _build_junk_scan(str(tmp_path), matched_paths=set())
    assert result["categories"][0]["category"] == "ZIPs no-ROM"


def test_junk_scan_zip_in_platform_folder_ignored_even_with_tier(tmp_path: Path) -> None:
    """JUNK-SMART-2: un ZIP dentro de carpeta de plataforma sigue sin ser basura."""
    (tmp_path / "arcade").mkdir()
    (tmp_path / "arcade" / "sf2.zip").write_bytes(b"x")
    result = _build_junk_scan(str(tmp_path), matched_paths=set(), arcade_names={"sf2"})
    assert result["total_junk_files"] == 0


def test_junk_scan_confidence_labels(tmp_path: Path) -> None:
    """JUNK-SMART-3: safe_delete por extensión; review con evidencia; misplaced = mover."""
    unknown = tmp_path / "Unknown"
    unknown.mkdir()
    (unknown / "doc.pdf").write_bytes(b"x")
    (unknown / "u082.bin").write_bytes(b"x")
    (unknown / "naomi.zip").write_bytes(b"x")
    result = _build_junk_scan(
        str(tmp_path),
        matched_paths=set(),
        arcade_names=set(),
        mame_infra_names=set(),
        known_bios_files={"naomi.zip"},
    )
    conf = {c["category"]: c["confidence"] for c in result["categories"]}
    assert conf["PDFs"] == "safe_delete"
    assert conf["Chips sueltos (sin match en catálogo)"] == "review"
    assert conf["BIOS conocidas (mover a bios/, no borrar)"] == "misplaced"


def _make_zip(path: Path, entries: dict[str, bytes]) -> None:
    import zipfile

    with zipfile.ZipFile(path, "w") as z:
        for name, data in entries.items():
            z.writestr(name, data)


def test_junk_scan_console_zip_identified_by_crc(tmp_path: Path) -> None:
    """ZIP-ROUTE-1: ZIP de una entrada con CRC en No-Intro/Redump → identidad
    exacta, aunque el nombre tenga ' - ' (antes caía en colecciones)."""
    import zlib

    unknown = tmp_path / "Unknown"
    unknown.mkdir()
    rom = b"contenido-rom"
    _make_zip(unknown / "Arkanoid - Doh It Again (Japan) [b].zip", {"game.sfc": rom})
    index = {f"{zlib.crc32(rom):08X}": ("Arkanoid - Doh It Again (USA)", "snes.dat", "SNES")}

    result = _build_junk_scan(
        str(tmp_path),
        matched_paths=set(),
        arcade_names=set(),
        mame_infra_names=set(),
        known_bios_files=set(),
        crc_index=index,
    )
    (cat,) = result["categories"]
    assert cat["category"] == "ROMs de consola identificadas (mover a su plataforma)"
    assert cat["confidence"] == "misplaced"
    assert cat["files"][0]["identified_as"] == "Arkanoid - Doh It Again (USA)"
    assert cat["files"][0]["platform"] == "SNES"


def test_junk_scan_console_zip_tier_off_without_crc_index(tmp_path: Path) -> None:
    """ZIP-ROUTE-1: sin crc_index no hay identidad exacta — pero la extensión
    interna (.sfc) sigue dando plataforma vía ZIP-ROUTE-3."""
    unknown = tmp_path / "Unknown"
    unknown.mkdir()
    _make_zip(unknown / "Arkanoid - Doh It Again (Japan) [b].zip", {"game.sfc": b"x"})
    result = _build_junk_scan(
        str(tmp_path), matched_paths=set(), arcade_names=set(), mame_infra_names=set()
    )
    (cat,) = result["categories"]
    assert cat["category"] == "ROMs/romhacks por extensión (mover a su plataforma)"
    assert "identified_as" not in cat["files"][0]  # sin índice no hay identidad


def test_junk_scan_collection_by_content_not_by_name(tmp_path: Path) -> None:
    """ZIP-ROUTE-5: colección = mayoría de .zip/.chd dentro; el nombre no cuenta.

    La heurística anterior (" - " en el nombre) daba ~39 falsos positivos de 56
    en la biblioteca real: romhacks tipo "Fire Emblem - ..." caían como colección.
    """
    unknown = tmp_path / "Unknown"
    unknown.mkdir()
    # romhack con " - " en el nombre pero una sola ROM dentro → NO es colección
    _make_zip(unknown / "Fire Emblem - The Binding Blade [T-En].zip", {"fe6.gba": b"x"})
    # contenedor de .chd sin " - " reconocible → SÍ es colección
    _make_zip(unknown / "turbografxcd.zip", {"Rondo.chd": b"a", "Ys IV.chd": b"b"})

    result = _build_junk_scan(
        str(tmp_path),
        matched_paths=set(),
        arcade_names=set(),
        mame_infra_names=set(),
        known_bios_files=set(),
        crc_index={},
    )
    by_cat = {c["category"]: [f["path"] for f in c["files"]] for c in result["categories"]}
    assert by_cat["Colecciones fuente (revisar)"] == [str(Path("Unknown/turbografxcd.zip"))]
    # el romhack no es colección: cae al pass por extensión (ZIP-ROUTE-3)
    assert by_cat["ROMs/romhacks por extensión (mover a su plataforma)"] == [
        str(Path("Unknown/Fire Emblem - The Binding Blade [T-En].zip"))
    ]


def test_junk_scan_crc_pass_never_guesses(tmp_path: Path) -> None:
    """ZIP-ROUTE-1: multi-entrada, CRC desconocido o zip corrupto → nunca consola."""
    import zlib

    unknown = tmp_path / "Unknown"
    unknown.mkdir()
    rom = b"contenido-rom"
    # multi-entrada de ROMs sueltas con CRC conocido → revisar, no identificar
    _make_zip(unknown / "Nintendo - SNES.zip", {"a.sfc": rom, "b.sfc": rom})
    # una entrada con CRC desconocido → ZIPs no-ROM
    _make_zip(unknown / "misterio.zip", {"algo.bin": b"otro"})
    # zip corrupto → ZIPs no-ROM, sin explotar
    (unknown / "roto.zip").write_bytes(b"esto no es un zip")

    index = {f"{zlib.crc32(rom):08X}": ("Juego (USA)", "snes.dat", "SNES")}
    result = _build_junk_scan(
        str(tmp_path),
        matched_paths=set(),
        arcade_names=set(),
        mame_infra_names=set(),
        known_bios_files=set(),
        crc_index=index,
    )
    by_cat = {c["category"]: sorted(f["path"] for f in c["files"]) for c in result["categories"]}
    assert by_cat["ZIPs no-ROM"] == [
        str(Path("Unknown/Nintendo - SNES.zip")),
        str(Path("Unknown/misterio.zip")),
        str(Path("Unknown/roto.zip")),
    ]


def test_junk_scan_arcade_set_identified_by_crc_voting(tmp_path: Path) -> None:
    """ZIP-ROUTE-2: un set arcade disfrazado con nombre No-Intro se identifica
    votando los CRC de sus chips; cobertura total → renombrar y mover."""
    import zlib

    unknown = tmp_path / "Unknown"
    unknown.mkdir()
    chips = {"lem_01.bin": b"chip-uno", "lem_02.bin": b"chip-dos"}
    _make_zip(unknown / "Lemmings (United Kingdom).zip", chips)
    index = {f"{zlib.crc32(d):08X}": {"lemmings"} for d in chips.values()}

    result = _build_junk_scan(
        str(tmp_path),
        matched_paths=set(),
        arcade_names=set(),
        mame_infra_names=set(),
        known_bios_files=set(),
        crc_index={},
        arcade_crc_index=index,
    )
    (cat,) = result["categories"]
    assert cat["category"] == "ROMs arcade identificadas (renombrar al set y mover)"
    assert cat["confidence"] == "misplaced"
    assert cat["files"][0]["identified_as"] == "lemmings"


def test_junk_scan_arcade_partial_coverage_is_review(tmp_path: Path) -> None:
    """ZIP-ROUTE-2: cobertura parcial = otra versión de romset → review con candidato."""
    import zlib

    unknown = tmp_path / "Unknown"
    unknown.mkdir()
    known = b"chip-conocido"
    _make_zip(unknown / "qix.zip", {"a.bin": known, "b.bin": b"chip-desconocido"})
    index = {f"{zlib.crc32(known):08X}": {"qix2"}}

    result = _build_junk_scan(
        str(tmp_path),
        matched_paths=set(),
        arcade_names=set(),
        mame_infra_names=set(),
        known_bios_files=set(),
        crc_index={},
        arcade_crc_index=index,
    )
    (cat,) = result["categories"]
    assert cat["category"] == "Sets arcade de otra versión (revisar)"
    assert cat["confidence"] == "review"
    assert cat["files"][0]["identified_as"] == "qix2"
    assert cat["files"][0]["coverage"] == 0.5


def test_junk_scan_romhack_platform_by_inner_extension(tmp_path: Path) -> None:
    """ZIP-ROUTE-3: sin CRC en ningún DAT pero una sola entrada .gba →
    plataforma por extensión (romhack/traducción parcheada)."""
    from rom_manager.detection.platform_detector import PLATFORM_BY_EXTENSION

    unknown = tmp_path / "Unknown"
    unknown.mkdir()
    _make_zip(unknown / "Fire Emblem - The Binding Blade [T-En].zip", {"fe6.gba": b"parche"})

    result = _build_junk_scan(
        str(tmp_path),
        matched_paths=set(),
        arcade_names=set(),
        mame_infra_names=set(),
        known_bios_files=set(),
        crc_index={},
        arcade_crc_index={},
    )
    (cat,) = result["categories"]
    assert cat["category"] == "ROMs/romhacks por extensión (mover a su plataforma)"
    assert cat["confidence"] == "misplaced"
    assert cat["files"][0]["platform"] == PLATFORM_BY_EXTENSION[".gba"]


def test_junk_scan_romhack_pass_skips_ambiguous_extensions(tmp_path: Path) -> None:
    """ZIP-ROUTE-3: .md (¿Mega Drive o markdown?) y extensiones desconocidas
    no dan plataforma — sin contexto de carpeta dentro de un ZIP, no adivinar."""
    unknown = tmp_path / "Unknown"
    unknown.mkdir()
    _make_zip(unknown / "docs.zip", {"README.md": b"# leeme"})
    _make_zip(unknown / "cosa.zip", {"algo.xyz": b"?"})

    result = _build_junk_scan(
        str(tmp_path),
        matched_paths=set(),
        arcade_names=set(),
        mame_infra_names=set(),
        known_bios_files=set(),
        crc_index={},
        arcade_crc_index={},
    )
    (cat,) = result["categories"]
    assert cat["category"] == "ZIPs no-ROM"
    assert cat["count"] == 2


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
