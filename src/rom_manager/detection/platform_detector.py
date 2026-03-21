from __future__ import annotations

import tomllib
from pathlib import Path

# ── Default bundled TOML ───────────────────────────────────────────────────────
_DEFAULT_TOML = Path(__file__).parent / "platforms.toml"


def _load_toml(user_override: Path | None = None) -> dict:
    """Load platform definitions from the bundled TOML, optionally merged with a user override."""
    try:
        with open(_DEFAULT_TOML, "rb") as f:
            data = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        data = {}

    if user_override and user_override.exists():
        try:
            with open(user_override, "rb") as f:
                override = tomllib.load(f)
            for section in ("extensions", "folders"):
                if section in override:
                    data.setdefault(section, {}).update(override[section])
            if "ambiguous" in override and "extensions" in override["ambiguous"]:
                existing = set(data.get("ambiguous", {}).get("extensions", []))
                data.setdefault("ambiguous", {})["extensions"] = sorted(
                    existing | set(override["ambiguous"]["extensions"])
                )
        except (OSError, tomllib.TOMLDecodeError):
            pass
    return data


def _build_tables(user_override: Path | None = None) -> tuple[dict, set, dict]:
    """Return (PLATFORM_BY_EXTENSION, AMBIGUOUS_EXTENSIONS, PLATFORM_BY_FOLDER)."""
    data = _load_toml(user_override)
    by_ext = {k.lower(): v for k, v in data.get("extensions", {}).items()}
    ambiguous = set(e.lower() for e in data.get("ambiguous", {}).get("extensions", []))
    by_folder = {k.lower(): v for k, v in data.get("folders", {}).items()}
    return by_ext, ambiguous, by_folder


# Module-level tables (built once at import time from bundled TOML + no user override yet)
PLATFORM_BY_EXTENSION, AMBIGUOUS_EXTENSIONS, PLATFORM_BY_FOLDER = _build_tables()

ROM_EXTENSIONS = set(PLATFORM_BY_EXTENSION) | AMBIGUOUS_EXTENSIONS

PLATFORM_CONTEXT_BY_EXTENSION: dict[str, set[str]] = {
    ".md": {"megadrive", "genesis", "sega genesis", "md"},
}


def reload_platforms(user_override: Path | None = None) -> None:
    """Reload platform tables from TOML (called after config is loaded)."""
    global PLATFORM_BY_EXTENSION, AMBIGUOUS_EXTENSIONS, PLATFORM_BY_FOLDER, ROM_EXTENSIONS
    PLATFORM_BY_EXTENSION, AMBIGUOUS_EXTENSIONS, PLATFORM_BY_FOLDER = _build_tables(user_override)
    ROM_EXTENSIONS = set(PLATFORM_BY_EXTENSION) | AMBIGUOUS_EXTENSIONS


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
            return "Sega Mega Drive"
        return None

    platform = PLATFORM_BY_EXTENSION.get(extension)
    if platform:
        return platform

    if extension in AMBIGUOUS_EXTENSIONS:
        for part in path.parts:
            plat = PLATFORM_BY_FOLDER.get(part.lower())
            if plat:
                return plat

    return None


def _has_platform_context(path: Path, valid_names: set[str]) -> bool:
    path_names = {part.casefold() for part in path.parts}
    return any(name in path_names for name in valid_names)
