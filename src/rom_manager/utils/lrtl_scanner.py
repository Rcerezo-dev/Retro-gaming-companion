"""RetroArch ``.lrtl`` playtime-log scanner (JUEGOS-UX-6).

RetroArch escribe un JSON por juego en ``playlists/logs/<Core>/<rom>.lrtl``::

    {"version": "1.0", "runtime": "0:31:37", "last_played": "2023-01-01 12:00:00"}

``runtime`` es el tiempo TOTAL acumulado (no la última sesión), por lo que el
consumidor debe hacer upsert con semántica MAX, nunca sumar. Solo stdlib.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

_logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LrtlEntry:
    stem: str  # nombre del ROM sin extensión — clave de matching contra games
    minutes: int  # runtime acumulado en minutos
    last_played: str | None  # "YYYY-MM-DDTHH:MM:SS" (hora local del dispositivo)


def parse_runtime(runtime: str) -> int:
    """``"H:MM:SS"`` → minutos totales (las horas pueden superar 24)."""
    parts = runtime.strip().split(":")
    if len(parts) != 3:
        raise ValueError(f"runtime inválido: {runtime!r}")
    h, m, s = (int(p) for p in parts)
    return h * 60 + m + (1 if s >= 30 else 0)


def parse_lrtl(path: Path) -> LrtlEntry | None:
    """Parse a single ``.lrtl`` file; None si está corrupto o vacío."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        minutes = parse_runtime(str(data.get("runtime", "")))
    except (OSError, ValueError, json.JSONDecodeError):
        _logger.warning("No se pudo parsear %s", path, exc_info=True)
        return None
    raw_lp = str(data.get("last_played", "")).strip()
    # ponytail: la hora es local del dispositivo que escribió el log, sin tz;
    # suficiente para "última sesión" — normalizar a UTC si algún día importa
    last_played = raw_lp.replace(" ", "T") if raw_lp else None
    return LrtlEntry(stem=path.stem, minutes=minutes, last_played=last_played)


def scan_lrtl_dir(logs_dir: Path) -> list[LrtlEntry]:
    """Recorre ``logs_dir`` (recursivo — hay un subdir por core) y parsea cada .lrtl.

    Si el mismo stem aparece bajo varios cores, se queda con el de más minutos
    (mismo criterio MAX que el upsert).
    """
    best: dict[str, LrtlEntry] = {}
    for f in sorted(logs_dir.rglob("*.lrtl")):
        entry = parse_lrtl(f)
        if entry is None:
            continue
        prev = best.get(entry.stem.lower())
        if prev is None or entry.minutes > prev.minutes:
            best[entry.stem.lower()] = entry
    return list(best.values())
