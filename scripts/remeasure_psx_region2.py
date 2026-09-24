"""Script de sesión — CATALOG-MATCH-REGION-2, re-medición en vivo (Día55).

Re-matchea las filas PSX (`platform = "PlayStation"`) que quedaron en
`match_confidence = "low"` tras CATALOG-MATCH-REGION-1 (PR #289), usando el
fix ya mergeado de CATALOG-MATCH-REGION-2 (PR #291, `matcher.py:337`,
desambiguación de serial por prefijo). `rommgr match` normal no sirve para
esto: `get_unresolved_games()` sin `include_low_confidence=True` nunca
re-encola filas `low` (MATCH-FIX-2), solo `NULL`.

Solo pensado para correr en la máquina con la biblioteca real
(`E:\\Carpetas anbernic` / `H:\\ROMs`, ver `config.toml` de esa máquina) —
no toca nada si no hay filas PSX en `low`. Hace backup del `.db` antes de
escribir nada.

Uso:
    python scripts/remeasure_psx_region2.py            # aplica los cambios
    python scripts/remeasure_psx_region2.py --dry-run   # solo informa
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rom_manager.catalog.matcher import CatalogMatcher  # noqa: E402
from rom_manager.config import load_config  # noqa: E402
from rom_manager.database import LibraryRepository  # noqa: E402

PLATFORM = "PlayStation"


def _backup_db(db_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d")
    backup_dir = db_path.parent / f"backup_region_remeasure_{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / db_path.name
    shutil.copy2(db_path, backup_path)
    return backup_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", help="Solo informa, no escribe en la base de datos"
    )
    parser.add_argument(
        "--log", default=None, help="Ruta del CSV con el detalle (default: junto al backup)"
    )
    args = parser.parse_args()

    config = load_config()
    db_path = config.database_path
    if not db_path.exists():
        print(f"No existe la base de datos: {db_path}")
        return 1

    repository = LibraryRepository(db_path)

    with repository.connect() as conn:
        rows = conn.execute(
            """
            SELECT original_filename, source_path, platform, region, sha1, canonical_title
            FROM games
            WHERE platform = ? AND match_confidence = 'low'
            ORDER BY original_filename
            """,
            (PLATFORM,),
        ).fetchall()

    if not rows:
        print(f"No hay filas de {PLATFORM} en match_confidence='low'. Nada que re-medir.")
        return 0

    print(f"{len(rows)} filas de {PLATFORM} en 'low' — re-matcheando con el fix de REGION-2…")

    matcher = CatalogMatcher(
        nointro_dir=config.catalogs_nointro_dir,
        redump_dir=config.catalogs_redump_dir,
        chdman_path=config.chdman,
    )
    matcher.nointro_entries  # fuerza la carga perezosa y reporta tamaño
    print(f"  No-Intro: {matcher.nointro_entries:,} entries")
    print(f"  Redump:   {matcher.redump_entries:,} entries")

    if not args.dry_run:
        backup_path = _backup_db(db_path)
        print(f"Backup de la BD: {backup_path}")

    resolved = 0
    still_low = 0
    unmatched = 0
    log_rows: list[list[str]] = []

    write_ctx = None if args.dry_run else repository.batch()
    conn = write_ctx.__enter__() if write_ctx is not None else None
    try:
        for row in rows:
            filename, source_path, platform, region, sha1, old_title = row
            result = matcher.match(sha1, filename, source_path)
            if result is None:
                unmatched += 1
                continue
            if result.confidence == "low":
                still_low += 1
                continue

            resolved += 1
            log_rows.append(
                [
                    source_path,
                    old_title or "",
                    "low",
                    result.title,
                    result.confidence,
                ]
            )
            if not args.dry_run:
                repository.update_match(
                    source_path,
                    canonical_title=result.title,
                    match_confidence=result.confidence,
                    catalog_source=result.catalog_source,
                    connection=conn,
                )
    finally:
        if write_ctx is not None:
            write_ctx.__exit__(None, None, None)

    print()
    print(f"Resueltos (low -> medium/high): {resolved}")
    print(f"Siguen en low (sin cambio):    {still_low}")
    print(f"Sin match:                     {unmatched}")
    if args.dry_run:
        print("\n(--dry-run: nada escrito en la base de datos)")

    if log_rows:
        stamp = datetime.now().strftime("%Y-%m-%d")
        log_path = Path(args.log) if args.log else db_path.parent / f"region2_remeasure_{stamp}.csv"
        with log_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["source_path", "old_title", "old_confidence", "new_title", "new_confidence"])
            writer.writerows(log_rows)
        print(f"\nDetalle de los {len(log_rows)} casos resueltos: {log_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
