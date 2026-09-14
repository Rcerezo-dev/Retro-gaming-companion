"""Traduce una ruta relativa de PC a su equivalente canónico en Android."""

from __future__ import annotations

from rom_manager.detection.platform_detector import PLATFORM_BY_FOLDER


def canonical_rel_posix(rel_posix: str, es_platform_folders: dict[str, str]) -> str:
    """Traduce el primer segmento (carpeta de plataforma) a su slug canónico.

    Si el primer segmento no coincide con ningún alias/nombre conocido, se
    devuelve tal cual — no inventa una carpeta nueva para algo que no
    reconoce (p. ej. carpetas de sistema como ``BIOS/`` o ``saves/``).
    """
    parts = rel_posix.split("/", 1)
    if len(parts) < 2:
        return rel_posix
    folder, rest = parts
    canonical = PLATFORM_BY_FOLDER.get(folder.lower(), folder)
    slug = es_platform_folders.get(canonical, folder)
    return f"{slug}/{rest}"
