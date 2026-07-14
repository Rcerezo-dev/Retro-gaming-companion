"""Motor compartido de sync PC<->Anbernic por filesystem (CABLE-UX-9b).

Generaliza walk + filtro + compare-por-mtime + copy-con-politicas de la rama
filesystem de ``web/handlers/sync_cable.py:_do_cable_sync``, para que manual
(CABLE-UX-9d) y SD-auto (CABLE-UX-9c) dejen de reimplementarlo cada uno a su
manera. No cubre el modo ADB (usa ``AdbTransport``, no ``shutil`` — ver
CABLE-UX-9e) ni las politicas de espejo (delete_extra) o dedup por SHA1, que
siguen siendo responsabilidad del caller.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

Direction = str  # "pc_to_anbernic" | "anbernic_to_pc" | "newest"


def iter_files(root: Path) -> Iterator[Path]:
    """Recorre *root* recursivamente, saltando directorios ocultos (dotfiles)."""
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in files:
            yield Path(dirpath) / fname


@dataclass(slots=True, frozen=True)
class CopyPlanItem:
    src: Path
    dst: Path
    arrow: str  # etiqueta legible para logs ("-> Anbernic", "<- PC (mas reciente)", ...)


def plan_direction(
    pc_root: Path,
    ab_root: Path,
    direction: Direction,
    wanted: Callable[[Path], bool],
) -> Iterator[CopyPlanItem]:
    """Decide que archivos copiar y en que sentido, sin tocar disco todavia."""
    if direction == "pc_to_anbernic":
        for src in iter_files(pc_root):
            if wanted(src):
                yield CopyPlanItem(src, ab_root / src.relative_to(pc_root), "-> Anbernic")
        return

    if direction == "anbernic_to_pc":
        for src in iter_files(ab_root):
            if wanted(src):
                try:
                    rel = src.relative_to(ab_root)
                except ValueError:
                    continue
                yield CopyPlanItem(src, pc_root / rel, "<- PC")
        return

    if direction == "newest":
        pc_files = {f.relative_to(pc_root): f for f in iter_files(pc_root) if wanted(f)}
        ab_files: dict[Path, Path] = {}
        for f in iter_files(ab_root):
            if wanted(f):
                try:
                    ab_files[f.relative_to(ab_root)] = f
                except ValueError:
                    pass

        for rel in sorted(set(pc_files) | set(ab_files), key=str):
            pc_f = pc_files.get(rel)
            ab_f = ab_files.get(rel)
            if pc_f and ab_f:
                pc_mt = pc_f.stat().st_mtime
                ab_mt = ab_f.stat().st_mtime
                if pc_mt > ab_mt:
                    yield CopyPlanItem(pc_f, ab_root / rel, "-> Anbernic (PC mas reciente)")
                elif ab_mt > pc_mt:
                    yield CopyPlanItem(ab_f, pc_root / rel, "<- PC (Anbernic mas reciente)")
                # mtimes iguales: nada que hacer, el caller cuenta esto como skip
            elif pc_f:
                yield CopyPlanItem(pc_f, ab_root / rel, "-> Anbernic (solo en PC)")
            elif ab_f:
                yield CopyPlanItem(ab_f, pc_root / rel, "<- PC (solo en Anbernic)")
        return

    raise ValueError(f"direccion desconocida: {direction!r}")


@dataclass(slots=True, frozen=True)
class CopyPolicy:
    dry_run: bool = False
    safe_mode: bool = False  # no sobreescribir si el destino ya existe
    skip_existing: bool = False  # no recopiar si el destino tiene el mismo tamano


# Tag devuelto por copy_item: que paso con ese archivo concreto.
CopyTag = str  # "COPY" | "DRYRUN" | "SAFE" | "SKIP" | "ERROR"


def copy_item(
    item: CopyPlanItem,
    policy: CopyPolicy,
    *,
    on_event: Callable[[CopyTag, CopyPlanItem, str], None] | None = None,
) -> tuple[CopyTag, int]:
    """Copia (o simula) un CopyPlanItem segun policy.

    Devuelve ``(tag, size)``. ``on_event(tag, item, note)`` se llama para cada
    resultado -- el motor no sabe de logging ni de job_manager, eso es del
    caller.
    """

    def _emit(tag: CopyTag, note: str = "") -> tuple[CopyTag, int]:
        if on_event:
            on_event(tag, item, note)
        return tag, 0

    try:
        size = item.src.stat().st_size
    except OSError as exc:
        return _emit("ERROR", str(exc))

    if policy.safe_mode and item.dst.exists():
        return _emit("SAFE", "destino existe - omitido por modo seguro")

    if policy.skip_existing and item.dst.exists():
        try:
            if item.dst.stat().st_size == size:
                return _emit("SKIP", "mismo tamano")
        except OSError:
            pass

    try:
        if not policy.dry_run:
            item.dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item.src, item.dst)
        tag: CopyTag = "DRYRUN" if policy.dry_run else "COPY"
        if on_event:
            on_event(tag, item, "")
        return tag, size
    except OSError as exc:
        return _emit("ERROR", str(exc))
