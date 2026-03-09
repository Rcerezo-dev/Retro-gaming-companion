from __future__ import annotations

# Mapping from our platform names → ScreenScraper system IDs.
# https://www.screenscraper.fr/api2/systemesListe.php?output=json
PLATFORM_TO_SS_ID: dict[str, int] = {
    # Nintendo
    "NES": 3,
    "Famicom": 3,
    "SNES": 4,
    "Super Famicom": 4,
    "Nintendo 64": 14,
    "GameCube": 13,
    "Wii": 16,
    "Game Boy": 9,
    "Game Boy Color": 10,
    "Game Boy Advance": 12,
    "Nintendo DS": 15,
    "Nintendo 3DS": 17,
    "Virtual Boy": 11,
    "Famicom Disk System": 106,
    # Sega
    "Sega Master System": 2,
    "Sega Mega Drive": 1,
    "Mega Drive": 1,
    "Genesis": 1,
    "Sega 32X": 19,
    "Sega CD": 20,
    "Sega Game Gear": 21,
    "Game Gear": 21,
    "Sega Saturn": 22,
    "Saturn": 22,
    "Dreamcast": 23,
    # Sony
    "PlayStation": 57,
    "PlayStation 2": 58,
    "PSP": 61,
    # Arcade
    "Arcade": 75,
    "MAME": 75,
    "FBNeo": 75,
    "Neo Geo": 142,
    "CPS1": 6,
    "CPS2": 7,
    "CPS3": 8,
    # Atari
    "Atari 2600": 26,
    "Atari 5200": 40,
    "Atari 7800": 41,
    "Atari Lynx": 28,
    "Atari Jaguar": 27,
    "Atari ST": 42,
    # NEC
    "PC Engine": 31,
    "TurboGrafx-16": 31,
    "PC Engine CD": 114,
    # SNK
    "Neo Geo Pocket": 25,
    "Neo Geo Pocket Color": 82,
    # Misc
    "MSX": 113,
    "MSX2": 116,
    "Commodore 64": 66,
    "Amiga": 64,
    "DOS": 135,
    "ZX Spectrum": 76,
    "Amstrad CPC": 65,
    "Colecovision": 48,
    "Intellivision": 115,
    "Vectrex": 102,
    "3DO": 29,
    "WonderSwan": 45,
    "WonderSwan Color": 46,
    "Bandai WonderSwan": 45,
}


def get_system_id(platform: str | None) -> int | None:
    """Return the ScreenScraper system ID for the given platform name, or None."""
    if not platform:
        return None
    return PLATFORM_TO_SS_ID.get(platform)
