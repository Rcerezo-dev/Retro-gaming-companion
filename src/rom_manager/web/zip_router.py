"""ZIP-ROUTE-4: colocar en UN solo paso los ZIPs identificados por el junk-scan.

El junk-scan (ZIP-ROUTE-1/2/3/5) ya sabe qué es cada ZIP suelto; este módulo
ejecuta el destino sin pasos manuales intermedios:

- ROMs arcade (identificadas o con nombre de set correcto) → renombrar al set
  y mover a ``arcade\\`` DIRECTAMENTE. Nunca pasan por el Inbox: el pipeline
  las extraería y un set arcade extraído está roto (el ZIP es el ROM).
- Colecciones fuente → según sus miembros: mayoría de sets arcade → extraer
  directo a ``arcade\\``; mayoría BIOS/infra MAME → no tocar (revisar a mano);
  resto (juegos de consola) → extraer al Inbox. El contenedor se borra solo
  cuando todos los miembros están en disco (cero duplicados).
- ROMs de consola identificadas y romhacks → mover el ZIP al Inbox.
- Al final corre el pipeline del Inbox existente (extract → match → rename →
  organize → cleanup) con ``delete_source=True``: nada queda duplicado en el
  Inbox. Todo bajo el mismo job "inbox" que la UI ya sabe mostrar.
"""

from __future__ import annotations

import logging
import os
import shutil
import zipfile
from pathlib import Path

from rom_manager.config import AppConfig
from rom_manager.database.repository import LibraryRepository
from rom_manager.web.builders.folders import (
    _ZIP_CAT_ARCADE,
    _ZIP_CAT_ARCADE_IDENT,
    _ZIP_CAT_COLLECTION,
    _ZIP_CAT_CONSOLE,
    _ZIP_CAT_ROMHACK,
    _build_junk_scan,
)
from rom_manager.web.handlers.system import _ES_PLATFORM_FOLDERS

_logger = logging.getLogger(__name__)


def _majority(stems: list[str], names: set[str]) -> bool:
    hits = sum(1 for s in stems if s in names)
    return bool(stems) and hits * 2 >= len(stems)


def _extract_collection(zp: Path, dest_dir: Path) -> tuple[int, str]:
    """Extrae los miembros (saltando existentes) y borra el contenedor solo si
    todos quedaron en disco. Devuelve (extraídos, error)."""
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zp) as zf:
            members = [i for i in zf.infolist() if not i.is_dir()]
            needed = sum(i.file_size for i in members)
            free = shutil.disk_usage(dest_dir).free
            if needed > free:
                return 0, f"sin espacio en {dest_dir} ({needed / 1024**3:.1f} GB necesarios)"
            extracted = 0
            for m in members:
                if (dest_dir / m.filename).exists():
                    continue
                zf.extract(m, dest_dir)
                extracted += 1
            missing = sum(1 for m in members if not (dest_dir / m.filename).exists())
        if missing:
            return extracted, f"{missing} miembros no extraídos"
        zp.unlink()  # cero duplicados: contenedor fuera tras éxito
        return extracted, ""
    except (OSError, zipfile.BadZipFile) as exc:
        return 0, str(exc)


def _route_identified(
    scan: dict,
    arcade_names: set[str],
    mame_infra_names: set[str],
    known_bios_files: set[str],
    inbox_dir: Path,
    arcade_folder: Path,
) -> dict:
    """Fases previas al pipeline: mueve/extrae según la categoría del scan.

    Devuelve contadores + ``skipped`` (conflictos y decisiones que quedan para
    el usuario). Política de conflictos: si el destino existe, no se toca nada
    y se reporta — nunca sobreescribir.
    """
    counts: dict = {
        "arcade_moved": 0,
        "collections_extracted": 0,
        "collection_members": 0,
        "zips_to_inbox": 0,
        "route_skipped": [],
    }
    cats = {c["category"]: c for c in scan.get("categories", [])}

    def _move(src: Path, dest: Path) -> bool:
        if dest.exists():
            counts["route_skipped"].append(f"{src.name}: ya existe {dest}")
            return False
        try:
            shutil.move(str(src), str(dest))
            return True
        except OSError as exc:
            counts["route_skipped"].append(f"{src.name}: {exc}")
            return False

    # A. Arcade → directo a arcade\ (renombrando al set cuando hay identidad)
    arcade_folder.mkdir(parents=True, exist_ok=True)
    for f in cats.get(_ZIP_CAT_ARCADE_IDENT, {}).get("files", []):
        src = Path(f["full_path"])
        set_name = f.get("identified_as")
        if not src.exists() or not set_name:
            continue
        if _move(src, arcade_folder / f"{set_name}.zip"):
            counts["arcade_moved"] += 1
    for f in cats.get(_ZIP_CAT_ARCADE, {}).get("files", []):
        src = Path(f["full_path"])
        if src.exists() and _move(src, arcade_folder / src.name):
            counts["arcade_moved"] += 1

    # B. Colecciones → destino según los miembros
    for f in cats.get(_ZIP_CAT_COLLECTION, {}).get("files", []):
        src = Path(f["full_path"])
        if not src.exists():
            continue
        try:
            with zipfile.ZipFile(src) as zf:
                stems = [Path(n).stem.lower() for n in zf.namelist() if not n.endswith("/")]
                names = [Path(n).name.lower() for n in zf.namelist() if not n.endswith("/")]
        except (OSError, zipfile.BadZipFile) as exc:
            counts["route_skipped"].append(f"{src.name}: {exc}")
            continue
        if _majority(stems, mame_infra_names) or _majority(names, known_bios_files):
            # Pack de BIOS/infraestructura MAME: destino discutible (bios\ vs
            # junto a los ROMs según el core) → decisión del usuario
            counts["route_skipped"].append(f"{src.name}: pack BIOS/infra MAME — revisar a mano")
            continue
        dest = arcade_folder if _majority(stems, arcade_names) else inbox_dir / src.stem
        extracted, err = _extract_collection(src, dest)
        counts["collection_members"] += extracted
        if err:
            counts["route_skipped"].append(f"{src.name}: {err}")
        else:
            counts["collections_extracted"] += 1

    # C. Consola identificada y romhacks → al Inbox (el pipeline hace el resto)
    inbox_dir.mkdir(parents=True, exist_ok=True)
    for cat_name in (_ZIP_CAT_CONSOLE, _ZIP_CAT_ROMHACK):
        for f in cats.get(cat_name, {}).get("files", []):
            src = Path(f["full_path"])
            if src.exists() and _move(src, inbox_dir / src.name):
                counts["zips_to_inbox"] += 1

    return counts


def _run_zip_route_apply(
    library_root_str: str,
    repository: LibraryRepository,
    config: AppConfig,
    job_manager,
) -> None:
    """Job (bajo el nombre "inbox"): clasificar → mover/extraer → pipeline."""
    from rom_manager.catalog.mame_loader import (
        load_arcade_crc_index,
        load_arcade_dir,
        load_arcade_infra_names,
    )
    from rom_manager.catalog.matcher import CatalogMatcher
    from rom_manager.web.inbox_pipeline import _KNOWN_BIOS_MAP, _run_inbox_pipeline

    def _upd(step: str) -> None:
        job_manager.update_progress("inbox", {"step": step, "step_num": 0, "total_steps": 6})

    try:
        root = Path(library_root_str).resolve()
        inbox_dir = Path(config.inbox.path) if config.inbox.path else root / "Inbox"
        target_root = Path(
            config.inbox.target_root or (str(config.library_root) if config.library_root else root)
        )
        arcade_folder = target_root / _ES_PLATFORM_FOLDERS.get("Arcade", "arcade")

        _upd("Clasificando ZIPs sueltos (CRC de catálogos)")
        with repository.connect() as conn:
            rows = conn.execute(
                "SELECT source_path FROM games WHERE canonical_title IS NOT NULL"
            ).fetchall()
        matched = {os.path.normpath(r[0]).lower() for r in rows}
        arcade_cat_dir = config.catalogs_arcade_dir
        arcade_names = set(load_arcade_dir(arcade_cat_dir)) if arcade_cat_dir else set()
        infra_names = load_arcade_infra_names(arcade_cat_dir) if arcade_cat_dir else set()
        known_bios = {k for k in _KNOWN_BIOS_MAP if k.endswith(".zip")}
        crc_index = CatalogMatcher(
            nointro_dir=config.catalogs_nointro_dir,
            redump_dir=config.catalogs_redump_dir,
        ).crc_index()
        arcade_crcs = load_arcade_crc_index(arcade_cat_dir) if arcade_cat_dir else {}
        scan = _build_junk_scan(
            str(root),
            matched_paths=matched,
            arcade_names=arcade_names,
            mame_infra_names=infra_names,
            known_bios_files=known_bios,
            crc_index=crc_index,
            arcade_crc_index=arcade_crcs,
        )
        if "error" in scan:
            raise RuntimeError(scan["error"])

        _upd("Moviendo arcade y extrayendo colecciones")
        pre = _route_identified(
            scan, arcade_names, infra_names, known_bios, inbox_dir, arcade_folder
        )
        _logger.info("ZIP-ROUTE apply: %s", pre)
    except Exception as exc:
        _logger.exception("ZIP-ROUTE apply error: %s", exc)
        job_manager.finish("inbox", {"error": str(exc), "result_ts": ""})
        return

    # Fase final: el pipeline estándar organiza lo que dejamos en el Inbox y
    # cierra el job. delete_source=True: cero duplicados (requisito usuario).
    _run_inbox_pipeline(
        str(inbox_dir),
        str(target_root),
        True,
        repository,
        config,
        job_manager,
        extra_result=pre,
    )
    # Limpieza final: subcarpetas de colecciones ya vacías en el Inbox
    # (de la más profunda a la más superficial; rmdir solo borra vacías)
    for sub in sorted((p for p in inbox_dir.rglob("*") if p.is_dir()), reverse=True):
        if sub.name.startswith("_"):  # _processed y similares se respetan
            continue
        try:
            sub.rmdir()
        except OSError:
            pass
