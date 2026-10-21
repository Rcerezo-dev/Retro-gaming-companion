"""DUP-CHD-RAW-1b: aparta de la consola los .chd PSX que son el mismo disco que otro .chd.

Mismo motor de agrupado/verificación que la cola de duplicados (razón ``chd_raw``: mismo
``rawsha1`` en la cabecera CHD, verificado de nuevo por ADB), pero con descarte
RECUPERABLE: cada .chd se mueve (``mv``, mismo volumen, instantáneo) a
``<volumen>/_descartados/dup_chd_raw_<fecha>/<ruta relativa>`` -- fuera de ``ROMs/``, así
ningún launcher lo escanea -- y solo entonces se borra su fila de ``library_android.db``.
``AdbTransport.remove()`` (lo que usa ``resolve_duplicate_ra`` en rutas de consola) hace
``rm -f`` y NO es recuperable. Un manifiesto CSV permite deshacerlo a mano.

Se conserva la copia que recomienda la política DUP-CHD-KEEP-1 (sin etiqueta Demo/Proto/...
y más cerca de la raíz). Se aborta al primer movimiento que no se pueda verificar.

Uso (con la consola conectada; haz antes una copia de ``.rommgr/library_android.db``)::

    python scripts/dup_chd_raw_apply.py            # solo plan, no toca nada
    python scripts/dup_chd_raw_apply.py --apply    # aparta los ficheros
"""

# ruff: noqa: E402  (sys.path se ajusta antes de importar rom_manager)
from __future__ import annotations

import argparse
import csv
import shlex
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rom_manager.database.repositories.games import (
    cascade_delete_games_by_source_path,
)
from rom_manager.database.repository import LibraryRepository
from rom_manager.services.ra_duplicates_service import verify_group_by_disc_hash
from rom_manager.sync.adb_transport import resolve_single_device_transport
from rom_manager.web.builders.duplicates import _build_review_queue


def build_plan(repo: LibraryRepository, transport, roms_root: str) -> list[dict]:
    """Un dict por .chd verificado (``keep``, ``src``, ``size``, ``raw``)."""
    with tempfile.TemporaryDirectory() as tmp:
        empty = LibraryRepository(Path(tmp) / "empty.db")
        cfg = SimpleNamespace(project_root=ROOT, library_root=ROOT, chdman=None)
        queue = _build_review_queue(empty, repo, cfg)
    plan: list[dict] = []
    for group in queue["groups"]:
        if "chd_raw" not in group["reasons"]:
            continue
        keep = next(e for e in group["entries"] if e.get("recommended"))
        if not keep["source_path"].lower().endswith(".chd"):
            continue
        cands = [
            e
            for e in group["entries"]
            if e is not keep and e["source_path"].lower().endswith(".chd")
        ]
        if not cands:
            continue
        result = verify_group_by_disc_hash(
            keep["source_path"],
            [e["source_path"] for e in cands],
            chdman="no-chdman",  # solo se acepta por rawsha1; el resto queda sin verificar
            adb_transport=transport,
        )
        sizes = {e["source_path"]: e["size_bytes"] for e in cands}
        for path in result["safe_discard_paths"]:
            assert path != keep["source_path"] and path.startswith(roms_root)
            plan.append(
                {
                    "keep": keep["source_path"],
                    "src": path,
                    "size": sizes[path],
                    "raw": result.get("keep_raw_sha1"),
                }
            )
    return plan


def apply_plan(
    repo: LibraryRepository, transport, plan: list[dict], roms_root: str, dest_root: str
):
    q = shlex.quote
    backup_dir = ROOT / ".rommgr" / f"backup_dup_chd_raw_{time.strftime('%Y%m%d')}"
    backup_dir.mkdir(exist_ok=True)
    manifest = backup_dir / "manifest.csv"
    done = moved = 0
    with manifest.open("w", encoding="utf-8-sig", newline="") as f:
        out = csv.writer(f, delimiter=";")
        out.writerow(["conservado", "origen", "destino", "bytes", "rawsha1", "hora"])
        for x in plan:
            src, keep = x["src"], x["keep"]
            dest = dest_root + src[len(roms_root) :]
            if not (transport.file_exists(keep) and transport.file_exists(src)):
                print("ABORTO: falta el archivo a conservar o el origen:", src)
                break
            if transport.file_exists(dest):
                print("ABORTO: el destino ya existe:", dest)
                break
            transport._shell(f"mkdir -p {q(dest.rsplit('/', 1)[0])} && mv {q(src)} {q(dest)}")
            size = transport._shell(f"stat -c %s {q(dest)}").strip()
            if transport.file_exists(src) or size != str(x["size"]):
                print("ABORTO: movimiento sin verificar:", src, size, x["size"])
                break
            with repo.connect() as conn:
                cascade_delete_games_by_source_path(conn, src)
                conn.commit()
            out.writerow([keep, src, dest, x["size"], x["raw"], time.strftime("%H:%M:%S")])
            f.flush()
            done += 1
            moved += x["size"]
    print(f"movidos {done}/{len(plan)} ficheros, {moved / 1024**3:.2f} GB -> {dest_root}")
    print("manifiesto:", manifest)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--apply", action="store_true", help="mover de verdad (por defecto solo plan)")
    ap.add_argument("--roms-root", default="/storage/521D-04EA/ROMs/")
    args = ap.parse_args()

    repo = LibraryRepository(ROOT / ".rommgr" / "library_android.db")
    transport = resolve_single_device_transport(str(ROOT / "tools" / "adb.exe"))
    if transport is None:
        sys.exit("No hay exactamente una consola conectada por ADB.")
    plan = build_plan(repo, transport, args.roms_root)
    total = sum(x["size"] for x in plan)
    print(
        f"plan: {len(plan)} ficheros, {total / 1024**3:.2f} GB, "
        f"grupos: {len({x['keep'] for x in plan})}"
    )
    if args.apply:
        volume = "/".join(args.roms_root.rstrip("/").split("/")[:3])  # /storage/521D-04EA
        dest_root = f"{volume}/_descartados/dup_chd_raw_{time.strftime('%Y%m%d')}/"
        # Antes de mover nada: comprobar que el destino se puede crear en la consola.
        transport._shell(f"mkdir -p {shlex.quote(dest_root)}")
        if not transport.file_exists(dest_root):
            sys.exit(f"No se pudo crear el destino {dest_root}; no se ha movido nada.")
        apply_plan(repo, transport, plan, args.roms_root, dest_root)


if __name__ == "__main__":
    main()
