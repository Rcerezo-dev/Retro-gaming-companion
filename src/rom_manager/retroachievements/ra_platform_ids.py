from __future__ import annotations

# Maps our internal platform string → RetroAchievements console ID.
# Source: https://retroachievements.org/API/API_GetConsoleIDs.php
_RA_CONSOLE_IDS: dict[str, int] = {
    # Nintendo
    "nes": 7, "famicom": 7,
    "snes": 3, "supernintendo": 3, "supernes": 3,
    "n64": 2, "nintendo64": 2,
    "gb": 5, "gameboy": 5,
    "gbc": 6, "gameboycolor": 6,
    "gba": 4, "gameboyadvance": 4,
    "nds": 18, "ds": 18, "nintendods": 18,
    "3ds": 24, "nintendo3ds": 24,
    "gamecube": 16, "gc": 16,
    "wii": 20,
    "virtualboy": 28,
    # Sega
    "megadrive": 1, "genesis": 1, "segamegadrive": 1,
    "mastersystem": 11, "sms": 11, "segamastersystem": 11,
    "gamegear": 15, "segagamegear": 15,
    "segacd": 9, "megacd": 9,
    "32x": 10, "sega32x": 10,
    "saturn": 33, "segasaturn": 33,
    "dreamcast": 40, "dc": 40,
    # Sony
    "psx": 12, "ps1": 12, "playstation": 12,
    "ps2": 21, "playstation2": 21,
    "psp": 41,
    # Atari
    "atari2600": 25, "2600": 25,
    "atari7800": 51, "7800": 51,
    "lynx": 13, "atarilynx": 13,
    "jaguar": 17, "atarijaguar": 17,
    # NEC
    "pce": 8, "pcengine": 8, "turbografx16": 8, "tg16": 8,
    "pcecd": 76, "pcenginecd": 76, "turbografxcd": 76,
    # SNK
    "neogeo": 142,
    "neogeopocket": 14, "ngp": 14,
    "neogeopocketcolor": 14, "ngpc": 14,
    # Other
    "wonderswan": 53,
    "wonderswancolor": 57,
}


def get_ra_console_id(platform: str) -> int | None:
    """Return the RA console ID for a given platform string, or None if unknown."""
    key = platform.lower().replace(" ", "").replace("-", "").replace("_", "")
    return _RA_CONSOLE_IDS.get(key)
