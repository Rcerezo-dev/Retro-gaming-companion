from __future__ import annotations

from pathlib import Path


PLATFORM_BY_EXTENSION = {
    ".nes": "NES",
    ".sfc": "SNES",
    ".smc": "SNES",
    ".n64": "Nintendo 64",
    ".z64": "Nintendo 64",
    ".v64": "Nintendo 64",
    ".gb": "Game Boy",
    ".gbc": "Game Boy Color",
    ".gba": "Game Boy Advance",
    ".nds": "Nintendo DS",
    ".3ds": "Nintendo 3DS",
    ".cia": "Nintendo 3DS",
    ".gcm": "GameCube",
    ".wbfs": "Wii",
    ".wud": "Wii U",
    ".wux": "Wii U",
    ".nsp": "Nintendo Switch",
    ".xci": "Nintendo Switch",
    ".sms": "Master System",
    ".gg": "Game Gear",
    ".gen": "Sega Genesis",
    ".cdi": "Dreamcast",
    ".gdi": "Dreamcast",
    ".pbp": "PlayStation",
    ".cso": "PSP",
    ".vpk": "PS Vita",
    ".a26": "Atari 2600",
    ".a52": "Atari 5200",
    ".a78": "Atari 7800",
    ".lnx": "Atari Lynx",
    ".j64": "Atari Jaguar",
    ".jag": "Atari Jaguar",
}

AMBIGUOUS_EXTENSIONS = {
    ".md",
    ".bin",
    ".cue",
    ".iso",
    ".zip",
    ".chd",
    ".img",
    ".ecm",
    ".mdf",
    ".mds",
    ".ccd",
    ".sub",
    ".7z",
}

ROM_EXTENSIONS = set(PLATFORM_BY_EXTENSION) | AMBIGUOUS_EXTENSIONS

PLATFORM_CONTEXT_BY_EXTENSION = {
    ".md": {
        "megadrive",
        "genesis",
        "sega genesis",
        "md",
    },
}

# Folder names (lowercase) → platform name.
# Used as fallback for ambiguous extensions (.zip, .bin, .iso, etc.)
PLATFORM_BY_FOLDER: dict[str, str] = {
    # Nintendo
    "famicom": "NES",
    "nes": "NES",
    "snes": "SNES",
    "superfamicom": "SNES",
    "gb": "Game Boy",
    "gameboy": "Game Boy",
    "gbc": "Game Boy Color",
    "gba": "Game Boy Advance",
    "gameboyadvance": "Game Boy Advance",
    "nds": "Nintendo DS",
    "ds": "Nintendo DS",
    "3ds": "Nintendo 3DS",
    "n64": "Nintendo 64",
    "nintendo64": "Nintendo 64",
    "ngc": "GameCube",
    "gamecube": "GameCube",
    "wii": "Wii",
    "wiiu": "Wii U",
    # Sony
    "psx": "PlayStation",
    "ps1": "PlayStation",
    "playstation": "PlayStation",
    "ps2": "PlayStation 2",
    "ps3": "PlayStation 3",
    "psp": "PSP",
    "psvita": "PS Vita",
    "vita": "PS Vita",
    # Sega
    "megadrive": "Sega Mega Drive",
    "genesis": "Sega Mega Drive",
    "mastersystem": "Master System",
    "sms": "Master System",
    "gamegear": "Game Gear",
    "gg": "Game Gear",
    "saturn": "Sega Saturn",
    "segasaturn": "Sega Saturn",
    "dreamcast": "Dreamcast",
    "dc": "Dreamcast",
    # SNK
    "neogeo": "Neo Geo",
    "neogeopocket": "Neo Geo Pocket Color",
    "ngpc": "Neo Geo Pocket Color",
    # Arcade
    "mame": "Arcade",
    "cps1": "Arcade",
    "cps2": "Arcade",
    "cps3": "Arcade",
    "arcade": "Arcade",
    "fbneo": "Arcade",
    # Atari
    "atari2600": "Atari 2600",
    "atari5200": "Atari 5200",
    "atari7800": "Atari 7800",
    "atarilynx": "Atari Lynx",
    "lynx": "Atari Lynx",
    "jaguar": "Atari Jaguar",
}


def normalize_extension(path: Path) -> str:
    return path.suffix.lower()


def is_rom_file(path: Path) -> bool:
    extension = normalize_extension(path)
    if extension in PLATFORM_CONTEXT_BY_EXTENSION:
        return _has_platform_context(path, PLATFORM_CONTEXT_BY_EXTENSION[extension])
    return extension in ROM_EXTENSIONS


def detect_platform(path: Path) -> str | None:
    extension = normalize_extension(path)

    # .md requires folder context to distinguish from Markdown files
    if extension in PLATFORM_CONTEXT_BY_EXTENSION:
        if _has_platform_context(path, PLATFORM_CONTEXT_BY_EXTENSION[extension]):
            return "Sega Mega Drive"
        return None

    # Non-ambiguous: extension alone is sufficient
    platform = PLATFORM_BY_EXTENSION.get(extension)
    if platform:
        return platform

    # Ambiguous extension (.zip, .bin, .iso, …): infer from folder name
    if extension in AMBIGUOUS_EXTENSIONS:
        for part in path.parts:
            plat = PLATFORM_BY_FOLDER.get(part.lower())
            if plat:
                return plat

    return None


def _has_platform_context(path: Path, valid_names: set[str]) -> bool:
    path_names = {part.casefold() for part in path.parts}
    return any(name in path_names for name in valid_names)
