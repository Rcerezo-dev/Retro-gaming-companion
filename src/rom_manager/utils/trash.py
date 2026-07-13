"""AUD-3 — Papelera unificada (soft-discard a ``_descartados/``).

INBOX-FIX-5 demostró el coste de ``Path.unlink()`` en Windows: no pasa por la
Papelera y el archivo es irrecuperable. Todo borrado de archivos de biblioteca
de la app pasa por :func:`discard_to_trash`, que mueve el archivo a una carpeta
hermana ``_descartados/``. La purga automática (:func:`purge_trash`) elimina lo
que lleve descartado más de N días (``library.trash_purge_days``, default 30).

El mtime del archivo descartado se pone a la hora del descarte (``os.utime``):
``shutil.move`` conserva el mtime original, que puede tener años, y la purga
por antigüedad lo borraría al instante.
"""

from __future__ import annotations

import logging
import os
import shutil
import stat
import time
from pathlib import Path

_logger = logging.getLogger(__name__)

TRASH_DIR_NAME = "_descartados"


def discard_to_trash(path: Path) -> Path:
    """Move *path* into a sibling ``_descartados/`` folder and return the new path.

    Collision-safe: a same-named file already in the trash gets a numeric
    suffix — nothing is ever overwritten or permanently deleted here.
    Clears the read-only attribute first (WinError 5 on console-formatted SDs).
    """
    trash_dir = path.parent / TRASH_DIR_NAME
    trash_dir.mkdir(parents=True, exist_ok=True)
    dest = trash_dir / path.name
    n = 1
    while dest.exists():
        dest = trash_dir / f"{path.stem} ({n}){path.suffix}"
        n += 1
    try:
        shutil.move(str(path), str(dest))
    except PermissionError:
        os.chmod(str(path), stat.S_IWRITE)
        shutil.move(str(path), str(dest))
    try:
        os.utime(dest)  # mtime = momento del descarte → base de la purga por edad
    except OSError:
        pass
    return dest


def _iter_trash_files(roots: list[Path]):
    """Yield every file inside any ``_descartados/`` dir under *roots*."""
    seen: set[Path] = set()
    for root in roots:
        if not root or not root.is_dir():
            continue
        root = root.resolve()
        if root in seen:
            continue
        seen.add(root)
        for dirpath, dirnames, filenames in os.walk(root):
            if Path(dirpath).name == TRASH_DIR_NAME:
                dirnames[:] = []  # no anidar
                for fname in filenames:
                    yield Path(dirpath) / fname


def trash_stats(roots: list[Path]) -> dict:
    """Return ``{"files": n, "bytes": total}`` for everything in the trash."""
    files = 0
    total = 0
    for f in _iter_trash_files(roots):
        try:
            total += f.stat().st_size
            files += 1
        except OSError:
            continue
    return {"files": files, "bytes": total}


def purge_trash(roots: list[Path], older_than_days: float = 0) -> dict:
    """Delete trashed files older than *older_than_days* (0 = everything).

    Also removes ``_descartados/`` dirs left empty. Returns
    ``{"deleted": n, "bytes": freed}``.
    """
    cutoff = time.time() - older_than_days * 86400
    deleted = 0
    freed = 0
    dirs: set[Path] = set()
    for f in _iter_trash_files(roots):
        dirs.add(f.parent)
        try:
            st = f.stat()
            if st.st_mtime <= cutoff:
                f.unlink()
                deleted += 1
                freed += st.st_size
        except OSError:
            _logger.debug("No se pudo purgar %s", f, exc_info=True)
    for d in dirs:
        try:
            d.rmdir()  # solo si quedó vacía
        except OSError:
            pass
    return {"deleted": deleted, "bytes": freed}


def trash_roots(config) -> list[Path]:
    """The places where ``_descartados/`` folders can appear: biblioteca e inbox."""
    roots = []
    if config.library_root:
        roots.append(Path(config.library_root))
    if config.inbox.path:
        roots.append(Path(config.inbox.path))
    return roots
