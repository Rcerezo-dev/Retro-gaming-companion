"""Sync Doctor (AUD-1) — diagnóstico del sync de saves por cable.

La resolución de conflictos del sync es "mtime gana": si el reloj de la
consola va desviado, el lado equivocado gana silenciosamente en cada sync.
Este módulo detecta los síntomas antes de que cuesten progreso:

- Desviación de reloj PC↔consola (``adb shell date +%s`` vs ``time.time()``).
- Saves con mtime en el futuro (síntoma directo de reloj mal puesto).
- Saves presentes solo en un lado.
- Último sync registrado por save (tabla ``save_sync_log``).

``analyze_saves`` es pura (testeable sin dispositivo); ``build_sync_doctor``
hace la E/S (ADB + BD) y la usa.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.sync.adb_transport import AdbFileInfo
    from rom_manager.sync.save_syncer import LocalSave

_MAX_LIST = 100  # cap de archivos listados por sección en la respuesta


def analyze_saves(
    *,
    pc_epoch: float,
    device_epoch: int,
    threshold_s: int,
    local_saves: list[LocalSave],
    remote_files: list[AdbFileInfo],
    android_root: str,
) -> dict:
    """Cruza ambos lados y devuelve el diagnóstico. Pura: sin E/S."""
    skew = device_epoch - pc_epoch
    prefix = android_root.rstrip("/") + "/"

    future_cutoff = pc_epoch + threshold_s
    future_local = [
        {"path": s.relative, "mtime": s.mtime.timestamp()}
        for s in local_saves
        if s.mtime.timestamp() > future_cutoff
    ]
    future_remote = [
        {"path": f.android_path.removeprefix(prefix), "mtime": f.mtime}
        for f in remote_files
        if f.mtime > future_cutoff
    ]

    local_rels = {s.relative for s in local_saves}
    remote_rels = {f.android_path.removeprefix(prefix) for f in remote_files}
    only_local = sorted(local_rels - remote_rels)
    only_remote = sorted(remote_rels - local_rels)

    return {
        "clock": {
            "device_epoch": device_epoch,
            "pc_epoch": pc_epoch,
            "skew_seconds": round(skew, 1),
            "threshold_s": threshold_s,
            "exceeded": abs(skew) > threshold_s,
        },
        "future_local": future_local[:_MAX_LIST],
        "future_local_total": len(future_local),
        "future_remote": future_remote[:_MAX_LIST],
        "future_remote_total": len(future_remote),
        "only_local": only_local[:_MAX_LIST],
        "only_local_total": len(only_local),
        "only_remote": only_remote[:_MAX_LIST],
        "only_remote_total": len(only_remote),
        "local_total": len(local_saves),
        "remote_total": len(remote_files),
    }


def _last_sync_per_save(repository: LibraryRepository, limit: int = 50) -> list[dict]:
    """Último sync OK por save, más reciente primero."""
    with repository.connect() as conn:
        try:
            rows = conn.execute(
                """
                SELECT local_path, direction, MAX(created_at) AS last_sync
                FROM save_sync_log
                WHERE result = 'ok'
                GROUP BY local_path
                ORDER BY last_sync DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        except Exception:
            return []  # la tabla puede no existir en BDs antiguas
    return [
        {"local_path": r["local_path"], "direction": r["direction"], "last_sync": r["last_sync"]}
        for r in rows
    ]


def build_sync_doctor(qs: dict, config: AppConfig, repository: LibraryRepository) -> dict:
    """Handler-side: consulta el dispositivo por ADB y arma el diagnóstico."""
    serial = (qs.get("serial", [""])[0] or "").strip()
    if not serial:
        return {"error": "serial ADB requerido"}

    from rom_manager.sync.adb_transport import AdbTransport

    transport = AdbTransport(config.adb, serial)
    pc_epoch = time.time()
    try:
        device_epoch = transport.device_epoch()
    except Exception as exc:
        return {"error": f"No se pudo leer el reloj del dispositivo: {exc}"}

    threshold = config.sync.clock_skew_threshold

    if (qs.get("clock_only", ["0"])[0] or "") == "1":
        skew = device_epoch - pc_epoch
        return {
            "clock": {
                "device_epoch": device_epoch,
                "pc_epoch": pc_epoch,
                "skew_seconds": round(skew, 1),
                "threshold_s": threshold,
                "exceeded": abs(skew) > threshold,
            }
        }

    pc_path_s = (qs.get("pc_path", [""])[0] or "").strip() or str(config.library_root or "")
    android_path = (
        qs.get("android_path", [""])[0] or ""
    ).strip() or config.sync.auto_sync_android_path

    from rom_manager.sync.save_syncer import list_local_saves

    local_saves: list = []
    pc_root = Path(pc_path_s) if pc_path_s else None
    if pc_root is not None and pc_root.is_dir():
        local_saves = list_local_saves(pc_root, config.save_extensions)

    save_exts = frozenset(e.lower() for e in config.save_extensions)
    try:
        remote_files = transport.ls_recursive(android_path, wanted_extensions=save_exts)
    except Exception as exc:
        return {"error": f"No se pudo listar {android_path!r} en el dispositivo: {exc}"}

    result = analyze_saves(
        pc_epoch=pc_epoch,
        device_epoch=device_epoch,
        threshold_s=threshold,
        local_saves=local_saves,
        remote_files=remote_files,
        android_root=android_path,
    )
    result["pc_path"] = pc_path_s
    result["android_path"] = android_path
    result["last_sync"] = _last_sync_per_save(repository)
    return result
