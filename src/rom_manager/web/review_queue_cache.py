"""REVIEW-QUEUE-PERF-1e: caché de la cola de revisión de copias.

Construir la cola cuesta varios segundos (recorre toda la biblioteca). Se reutiliza
mientras no cambien las bases de datos de las que sale: cualquier acción de la app
(escanear, descartar, excluir, aplicar) las modifica y por tanto la invalida. La BD
está en modo WAL, así que la huella incluye también el fichero ``-wal``. Un TTL corto
acota el desfase si alguien cambia archivos fuera de la app.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any


class ReviewQueueCache:
    def __init__(self, ttl: float = 120.0, clock: Callable[[], float] = time.monotonic) -> None:
        self._ttl = ttl
        self._clock = clock
        self._lock = threading.Lock()
        self._key: tuple | None = None
        self._stored_at = 0.0
        self._value: Any = None

    @staticmethod
    def _fingerprint(repos: tuple, extra: str) -> tuple:
        parts: list = [extra]
        for repo in repos:
            db = Path(repo.database_path)
            for path in (db, db.with_name(db.name + "-wal")):
                try:
                    st = path.stat()
                    parts.append((str(path), st.st_mtime_ns, st.st_size))
                except OSError:
                    parts.append((str(path), None, None))
        return tuple(parts)

    def get_or_build(self, repos: tuple, build: Callable[[], Any], extra: str = "") -> Any:
        """Devuelve la cola cacheada si la huella sigue igual y no ha caducado; si no, la construye."""
        key = self._fingerprint(repos, extra)  # antes de construir: un cambio durante la
        with self._lock:  # construcción invalida la siguiente petición
            fresh = self._key == key and self._clock() - self._stored_at < self._ttl
            if fresh:
                return self._value
            value = build()
            self._key, self._value, self._stored_at = key, value, self._clock()
            return value
