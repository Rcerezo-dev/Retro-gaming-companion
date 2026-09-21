"""Traduce una ruta relativa de PC a su equivalente canónico en Android."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import PurePosixPath
from typing import TypeVar

from rom_manager.detection.platform_detector import PLATFORM_BY_FOLDER

_T = TypeVar("_T")
_U = TypeVar("_U")


def reconcile_newest_by_name(
    pc_index: dict[str, _T], ab_index: dict[str, _U]
) -> Iterator[tuple[str | None, _T | None, str | None, _U | None]]:
    """Empareja entradas del PC con su contraparte en Android para "newest wins".

    CABLE-SYNC-SAVES-PREFIX-1/CABLE-SYNC-NEWEST-CANON-2: el dispositivo mezcla
    convenios para el mismo save (plano junto a la plataforma, ``saves/<plataforma>/``
    o ``saves/<core>/``), así que una ruta relativa exacta no basta. Empareja
    primero por clave exacta; si falla, por nombre de archivo — pero solo
    cuando hay un único candidato en Android con ese nombre (una colisión
    ambigua se deja sin emparejar en vez de adivinar).

    Genera ``(pc_key, pc_val, ab_key, ab_val)`` para cada entrada del PC (los
    campos de Android son ``None`` si no hay match), y luego
    ``(None, None, ab_key, ab_val)`` para las entradas de Android que no
    emparejaron con ninguna del PC.
    """
    ab_by_name: dict[str, list[str]] = {}
    for key in ab_index:
        ab_by_name.setdefault(PurePosixPath(key).name, []).append(key)

    matched: set[str] = set()
    for pc_key in sorted(pc_index):
        ab_key = pc_key if pc_key in ab_index else None
        if ab_key is None:
            candidates = ab_by_name.get(PurePosixPath(pc_key).name, ())
            if len(candidates) == 1:
                ab_key = candidates[0]
        if ab_key is not None:
            matched.add(ab_key)
            yield pc_key, pc_index[pc_key], ab_key, ab_index[ab_key]
        else:
            yield pc_key, pc_index[pc_key], None, None

    for ab_key, ab_val in ab_index.items():
        if ab_key not in matched:
            yield None, None, ab_key, ab_val


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


_DEVICE_WRAPPER_FOLDERS = frozenset({"saves", "states"})


def _is_known_platform_folder(folder: str, es_platform_folders: dict[str, str]) -> bool:
    lowered = folder.lower()
    if lowered in PLATFORM_BY_FOLDER:
        return True
    return lowered in {v.lower() for v in es_platform_folders.values()}


def canonical_download_rel_posix(rel_posix: str, es_platform_folders: dict[str, str]) -> str:
    """Traduce la ruta relativa de Android (para una *descarga*) a su destino
    canónico en el PC.

    CABLE-SYNC-DOWNLOAD-DEST-1: a diferencia de ``canonical_rel_posix()``
    (usado al subir, que solo traduce el primer segmento), muchos cores de
    RetroArch en Android anteponen ``saves/``/``states/`` antes de la
    plataforma (ver mapeo real en CABLE-SYNC-SAVES-PREFIX-1). Si el segmento
    siguiente SÍ es una plataforma reconocida, se descarta ese prefijo y se
    usa la plataforma real. Si no se reconoce (p. ej. ``saves/<core sin
    mapear>/...``), no se puede inferir con seguridad — se deja la ruta tal
    cual, mejor un archivo mal organizado que uno en el sitio equivocado.
    """
    parts = rel_posix.split("/", 1)
    if len(parts) == 2:
        folder, rest = parts
        if folder.lower() in _DEVICE_WRAPPER_FOLDERS:
            inner = rest.split("/", 1)
            if len(inner) == 2 and _is_known_platform_folder(inner[0], es_platform_folders):
                rel_posix = f"{inner[0]}/{inner[1]}"
    return canonical_rel_posix(rel_posix, es_platform_folders)
