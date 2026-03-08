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


def normalize_extension(path: Path) -> str:
    return path.suffix.lower()


def is_rom_file(path: Path) -> bool:
    extension = normalize_extension(path)
    if extension in PLATFORM_CONTEXT_BY_EXTENSION:
        return _has_platform_context(path, PLATFORM_CONTEXT_BY_EXTENSION[extension])
    return extension in ROM_EXTENSIONS


def detect_platform(path: Path) -> str | None:
    extension = normalize_extension(path)
    if extension in PLATFORM_CONTEXT_BY_EXTENSION:
        if _has_platform_context(path, PLATFORM_CONTEXT_BY_EXTENSION[extension]):
            return "Sega Genesis"
        return None
    return PLATFORM_BY_EXTENSION.get(extension)


def _has_platform_context(path: Path, valid_names: set[str]) -> bool:
    path_names = {part.casefold() for part in path.parts}
    return any(name in path_names for name in valid_names)
