"""ES-DE custom_systems/es_systems.xml generator.

Scans a RetroArch cores/ directory for installed libretro DLLs and generates
an ES-DE custom_systems/es_systems.xml that assigns the correct core to each
detected system.  Only systems with at least one available core are emitted.

Usage::

    from rom_manager.esde.systems_generator import generate_es_systems_xml
    result = generate_es_systems_xml(cores_dir=Path("C:/RetroArch/cores"),
                                     output_path=Path("%APPDATA%/ES-DE/custom_systems/es_systems.xml"))
    # result.generated_systems  → list of GeneratedSystem
    # result.missing_systems    → list of system names without a core
    # result.xml                → str with full XML content
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

# ── System catalogue ──────────────────────────────────────────────────────────
# Each entry defines one ES-DE system.  `cores` is an ordered list of candidate
# core DLL prefixes — the first one found on disk wins.

_SYSTEMS: list[dict] = [
    {
        "name": "nes",
        "fullname": "Nintendo Entertainment System",
        "path": "%ROMPATH%/nes",
        "extension": ".nes .unf .unif .zip .7z .NES .ZIP .7Z",
        "platform": "nes",
        "theme": "nes",
        "cores": ["fceumm", "nestopia", "mesen"],
    },
    {
        "name": "snes",
        "fullname": "Super Nintendo Entertainment System",
        "path": "%ROMPATH%/snes",
        "extension": ".sfc .smc .swc .fig .zip .7z .SFC .SMC .ZIP .7Z",
        "platform": "snes",
        "theme": "snes",
        "cores": ["snes9x", "bsnes", "mesen-s"],
    },
    {
        "name": "n64",
        "fullname": "Nintendo 64",
        "path": "%ROMPATH%/n64",
        "extension": ".n64 .z64 .v64 .ndd .zip .7z .N64 .Z64 .ZIP .7Z",
        "platform": "n64",
        "theme": "n64",
        "cores": ["mupen64plus_next", "parallel_n64"],
    },
    {
        "name": "gamecube",
        "fullname": "Nintendo GameCube",
        "path": "%ROMPATH%/gc",
        "extension": ".iso .rvz .gcm .gcz .ciso .wbfs .zip .7z .ISO .RVZ .ZIP .7Z",
        "platform": "gamecube",
        "theme": "gc",
        "cores": ["dolphin"],
    },
    {
        "name": "wii",
        "fullname": "Nintendo Wii",
        "path": "%ROMPATH%/wii",
        "extension": ".iso .rvz .gcm .gcz .ciso .wbfs .zip .7z .ISO .RVZ .WBFS .ZIP .7Z",
        "platform": "wii",
        "theme": "wii",
        "cores": ["dolphin"],
    },
    {
        "name": "gb",
        "fullname": "Nintendo Game Boy",
        "path": "%ROMPATH%/gb",
        "extension": ".gb .gbc .zip .7z .GB .ZIP .7Z",
        "platform": "gb",
        "theme": "gb",
        "cores": ["gambatte", "mgba", "sameboy"],
    },
    {
        "name": "gbc",
        "fullname": "Nintendo Game Boy Color",
        "path": "%ROMPATH%/gbc",
        "extension": ".gbc .gb .zip .7z .GBC .ZIP .7Z",
        "platform": "gbc",
        "theme": "gbc",
        "cores": ["gambatte", "mgba", "sameboy"],
    },
    {
        "name": "gba",
        "fullname": "Nintendo Game Boy Advance",
        "path": "%ROMPATH%/gba",
        "extension": ".gba .zip .7z .GBA .ZIP .7Z",
        "platform": "gba",
        "theme": "gba",
        "cores": ["mgba", "vba_next", "gpsp"],
    },
    {
        "name": "nds",
        "fullname": "Nintendo DS",
        "path": "%ROMPATH%/nds",
        "extension": ".nds .zip .7z .NDS .ZIP .7Z",
        "platform": "nds",
        "theme": "nds",
        "cores": ["melonds", "desmume"],
    },
    {
        "name": "3ds",
        "fullname": "Nintendo 3DS",
        "path": "%ROMPATH%/3ds",
        "extension": ".3ds .3dsx .cia .app .cci .zip .7z .3DS .ZIP .7Z",
        "platform": "3ds",
        "theme": "3ds",
        "cores": ["citra", "citra2018"],
    },
    {
        "name": "megadrive",
        "fullname": "Sega Mega Drive",
        "path": "%ROMPATH%/megadrive",
        "extension": ".md .bin .smd .gen .68k .zip .7z .MD .BIN .ZIP .7Z",
        "platform": "megadrive",
        "theme": "megadrive",
        "cores": ["genesis_plus_gx", "picodrive"],
    },
    {
        "name": "mastersystem",
        "fullname": "Sega Master System",
        "path": "%ROMPATH%/mastersystem",
        "extension": ".sms .bin .zip .7z .SMS .ZIP .7Z",
        "platform": "mastersystem",
        "theme": "mastersystem",
        "cores": ["genesis_plus_gx", "picodrive"],
    },
    {
        "name": "gamegear",
        "fullname": "Sega Game Gear",
        "path": "%ROMPATH%/gamegear",
        "extension": ".gg .bin .zip .7z .GG .ZIP .7Z",
        "platform": "gamegear",
        "theme": "gamegear",
        "cores": ["genesis_plus_gx"],
    },
    {
        "name": "dreamcast",
        "fullname": "Sega Dreamcast",
        "path": "%ROMPATH%/dreamcast",
        "extension": ".gdi .cdi .chd .iso .zip .7z .GDI .CDI .CHD .ZIP .7Z",
        "platform": "dreamcast",
        "theme": "dreamcast",
        "cores": ["flycast"],
    },
    {
        "name": "psx",
        "fullname": "Sony PlayStation",
        "path": "%ROMPATH%/psx",
        "extension": ".bin .cue .img .iso .chd .pbp .m3u .zip .7z .BIN .CUE .CHD .ZIP .7Z",
        "platform": "psx",
        "theme": "psx",
        "cores": ["duckstation", "pcsx_rearmed", "mednafen_psx_hw", "mednafen_psx"],
    },
    {
        "name": "ps2",
        "fullname": "Sony PlayStation 2",
        "path": "%ROMPATH%/ps2",
        "extension": ".iso .bin .img .mdf .chd .cso .gz .zip .7z .ISO .CHD .ZIP .7Z",
        "platform": "ps2",
        "theme": "ps2",
        "cores": ["pcsx2"],
    },
    {
        "name": "psp",
        "fullname": "Sony PlayStation Portable",
        "path": "%ROMPATH%/psp",
        "extension": ".iso .cso .pbp .elf .prx .zip .7z .ISO .CSO .ZIP .7Z",
        "platform": "psp",
        "theme": "psp",
        "cores": ["ppsspp"],
    },
    {
        "name": "mame",
        "fullname": "MAME",
        "path": "%ROMPATH%/mame",
        "extension": ".zip .7z .ZIP .7Z",
        "platform": "arcade",
        "theme": "mame",
        "cores": ["mame", "mame2003_plus", "mame2010", "mame2015"],
    },
    {
        "name": "fbneo",
        "fullname": "FBNeo - Arcade Games",
        "path": "%ROMPATH%/fbneo",
        "extension": ".zip .7z .ZIP .7Z",
        "platform": "arcade",
        "theme": "neogeo",
        "cores": ["fbneo"],
    },
    {
        "name": "neogeo",
        "fullname": "SNK Neo Geo",
        "path": "%ROMPATH%/neogeo",
        "extension": ".zip .7z .ZIP .7Z",
        "platform": "neogeo",
        "theme": "neogeo",
        "cores": ["fbneo", "mame"],
    },
]


# ── Data classes ──────────────────────────────────────────────────────────────


@dataclass(slots=True)
class GeneratedSystem:
    name: str
    fullname: str
    core_dll: str  # e.g. "mgba_libretro.dll"
    core_label: str  # e.g. "mGBA"


@dataclass(slots=True)
class GeneratorResult:
    generated_systems: list[GeneratedSystem] = field(default_factory=list)
    missing_systems: list[str] = field(default_factory=list)
    xml: str = ""
    output_path: str = ""
    written: bool = False
    error: str = ""


# ── Core lookup ───────────────────────────────────────────────────────────────


def _find_core(cores_dir: Path, candidates: list[str]) -> str | None:
    """Return the first matching *_libretro.dll filename found in *cores_dir*."""
    for prefix in candidates:
        for dll in cores_dir.glob(f"{prefix}*_libretro.dll"):
            return dll.name
        # Some cores don't have a secondary word (e.g. "mame_libretro.dll")
        direct = cores_dir / f"{prefix}_libretro.dll"
        if direct.exists():
            return direct.name
    return None


def _core_label(dll_name: str) -> str:
    """Turn 'mgba_libretro.dll' → 'mGBA' (best-effort human label)."""
    _LABELS: dict[str, str] = {
        "fceumm": "FCEUmm",
        "nestopia": "Nestopia",
        "mesen": "Mesen",
        "snes9x": "Snes9x",
        "bsnes": "bsnes",
        "mupen64plus_next": "Mupen64Plus-Next",
        "parallel_n64": "ParaLLEl N64",
        "dolphin": "Dolphin",
        "gambatte": "Gambatte",
        "mgba": "mGBA",
        "sameboy": "SameBoy",
        "vba_next": "VBA-Next",
        "gpsp": "gpSP",
        "melonds": "melonDS",
        "desmume": "DeSmuME",
        "citra": "Citra",
        "genesis_plus_gx": "Genesis Plus GX",
        "picodrive": "PicoDrive",
        "flycast": "Flycast",
        "duckstation": "DuckStation",
        "pcsx_rearmed": "PCSX-ReARMed",
        "mednafen_psx_hw": "Beetle PSX HW",
        "mednafen_psx": "Beetle PSX",
        "pcsx2": "PCSX2",
        "ppsspp": "PPSSPP",
        "mame": "MAME",
        "mame2003_plus": "MAME 2003-Plus",
        "mame2010": "MAME 2010",
        "mame2015": "MAME 2015",
        "fbneo": "FBNeo",
    }
    stem = dll_name.replace("_libretro.dll", "").replace("_libretro", "")
    return _LABELS.get(stem, stem)


# ── XML builder ───────────────────────────────────────────────────────────────


def _build_xml(systems: list[tuple[dict, str]]) -> str:
    """Build the es_systems.xml string from (system_def, core_dll) pairs."""
    root = ET.Element("systemList")

    for sys_def, core_dll in systems:
        sys_el = ET.SubElement(root, "system")

        def _sub(tag: str, text: str) -> None:
            el = ET.SubElement(sys_el, tag)
            el.text = text

        _sub("name", sys_def["name"])
        _sub("fullname", sys_def["fullname"])
        _sub("path", sys_def["path"])
        _sub("extension", sys_def["extension"])

        label = _core_label(core_dll)
        cmd_el = ET.SubElement(sys_el, "command")
        cmd_el.set("label", f"RetroArch {label}")
        cmd_el.text = f"%EMULATOR_RETROARCH% -L %CORE_RETROARCH%/{core_dll} %ROM%"

        _sub("platform", sys_def["platform"])
        _sub("theme", sys_def["theme"])

    ET.indent(root, space="  ")
    header = '<?xml version="1.0" encoding="UTF-8"?>\n<!-- Generated by Retro Vault -->\n'
    return header + ET.tostring(root, encoding="unicode")


# ── Public API ────────────────────────────────────────────────────────────────


def generate_es_systems_xml(
    cores_dir: Path,
    output_path: Path,
    *,
    write: bool = True,
) -> GeneratorResult:
    """Scan *cores_dir* for libretro DLLs and write a custom es_systems.xml.

    Args:
        cores_dir:   Path to RetroArch's ``cores/`` directory.
        output_path: Destination for the generated XML file.
                     Typically ``%APPDATA%/ES-DE/custom_systems/es_systems.xml``.
        write:       If True (default), create parent dirs and write the file.
                     Pass False to get a dry-run preview without writing.

    Returns:
        :class:`GeneratorResult` with generated/missing system lists, XML text,
        and whether the file was written successfully.
    """
    result = GeneratorResult(output_path=str(output_path))

    if not cores_dir.exists():
        result.error = f"Carpeta cores/ no encontrada: {cores_dir}"
        return result

    matched: list[tuple[dict, str]] = []

    for sys_def in _SYSTEMS:
        dll = _find_core(cores_dir, sys_def["cores"])
        if dll:
            matched.append((sys_def, dll))
            result.generated_systems.append(
                GeneratedSystem(
                    name=sys_def["name"],
                    fullname=sys_def["fullname"],
                    core_dll=dll,
                    core_label=_core_label(dll),
                )
            )
        else:
            result.missing_systems.append(sys_def["name"])

    if not matched:
        result.error = "No se encontraron cores instalados en la carpeta indicada."
        return result

    result.xml = _build_xml(matched)

    if write:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result.xml, encoding="utf-8")
            result.written = True
        except OSError as exc:
            result.error = f"No se pudo escribir el archivo: {exc}"

    return result
