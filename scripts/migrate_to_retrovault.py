"""Migra la biblioteca de esta máquina a la estructura RetroVault
(<destino>\\ROMS + EMULADORES + JUEGOS NATIVOS hermanas), reescribiendo
library_pc.db, config.toml y las configs de ES-DE/RetroArch/DuckStation/
PCSX2/PPSSPP/Dolphin que guardan su propia copia de la ruta absoluta.

Mismo procedimiento aplicado a mano en el PC principal — ver
Tareas/backlog.md NATIVE-SAVE-SYNC-1 para el detalle y los hallazgos
(archivos bloqueados por un juego/emulador abierto, etc.).

Uso:
    python scripts/migrate_to_retrovault.py --target "F:\\RetroVault\\ROMS"
    python scripts/migrate_to_retrovault.py --target "F:\\RetroVault\\ROMS" --apply

Dry-run por defecto (regla del proyecto: plan antes de apply). Cierra
RetroArch, ES-DE y cualquier emulador/juego nativo abierto antes de --apply.
Es seguro repetir --apply si algo se queda a medias (un archivo bloqueado):
robocopy retoma donde lo dejó.
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import subprocess
import sys
import tomllib
from datetime import datetime
from pathlib import Path

DB_PATH_COLUMNS = [
    ("games", "source_path"),
    ("saves", "original_path"),
    ("assets", "source_path"),
    ("file_operations", "source_path"),
    ("file_operations", "target_path"),
    ("save_sync_log", "local_path"),
    ("scan_runs", "source_root"),
    ("game_metadata", "box_art_path"),
    ("game_metadata", "wheel_path"),
    ("game_metadata", "screenshot_path"),
]

# Configs de frontend/emulador que guardan su propia copia de la ruta absoluta
# de la biblioteca y no se corrigen solas (confirmado en NATIVE-SAVE-SYNC-1).
KNOWN_CONFIG_FILES = [
    Path.home() / "ES-DE" / "settings" / "es_settings.xml",
    Path.home() / "Documents" / "DuckStation" / "settings.ini",
    Path.home() / "Documents" / "PCSX2" / "inis" / "PCSX2.ini",
    Path.home() / "Documents" / "PPSSPP" / "PSP" / "SYSTEM" / "ppsspp.ini",
    Path.home() / "Documents" / "Dolphin Emulator" / "Config" / "Dolphin.ini",
]


def load_toml(path: Path) -> dict:
    with open(path, "rb") as fh:
        return tomllib.load(fh)


def find_retroarch_cfg(cfg: dict) -> Path | None:
    retroarch_exe = cfg.get("launchers", {}).get("retroarch")
    if not retroarch_exe:
        return None
    candidate = Path(retroarch_exe).parent / "retroarch.cfg"
    return candidate if candidate.exists() else None


def ensure_retrovault_siblings(target_roms: Path) -> None:
    target_roms.mkdir(parents=True, exist_ok=True)
    for sibling in ("EMULADORES", "JUEGOS NATIVOS"):
        (target_roms.parent / sibling).mkdir(parents=True, exist_ok=True)


def backup(project_root: Path, files: list[Path]) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = project_root / ".rommgr" / "backup_pre_retrovault_move" / ts
    backup_dir.mkdir(parents=True, exist_ok=True)
    for f in files:
        if f and f.exists():
            shutil.copy2(f, backup_dir / f.name)
    return backup_dir


def rewrite_text_file(path: Path, old_root: str, new_root: str) -> int:
    """Reemplaza *old_root* por *new_root*, probando barra normal e invertida
    (Dolphin/PPSSPP guardan rutas con `/`, el resto con `\\`)."""
    if not path.exists():
        return 0
    text = path.read_text(encoding="utf-8")
    total = 0
    for o, n in ((old_root, new_root), (old_root.replace("\\", "/"), new_root.replace("\\", "/"))):
        count = text.count(o)
        if count:
            text = text.replace(o, n)
            total += count
    if total:
        path.write_text(text, encoding="utf-8")
    return total


def migrate_db(db_path: Path, old_root: str, new_root: str) -> int:
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("BEGIN")
    total = 0
    try:
        for table, col in DB_PATH_COLUMNS:
            cur.execute(
                f"UPDATE {table} SET {col} = ? || substr({col}, ?) WHERE {col} LIKE ?",  # noqa: S608
                (new_root, len(old_root) + 1, old_root + "%"),
            )
            total += cur.rowcount
        remaining = 0
        for table, col in DB_PATH_COLUMNS:
            cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} LIKE ?", (old_root + "%",))  # noqa: S608
            remaining += cur.fetchone()[0]
        if remaining:
            raise RuntimeError(f"Quedan {remaining} filas sin migrar -- abortando sin commit")
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    return total


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # consola Windows en cp1252 rompía los acentos
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--target", required=True, help=r'Nueva ruta de ROMS, p.ej. "F:\RetroVault\ROMS"')
    parser.add_argument("--apply", action="store_true", help="Ejecuta de verdad (por defecto: dry-run)")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / "config.toml"
    if not config_path.exists():
        print(f"No se encontró {config_path}", file=sys.stderr)
        return 1

    cfg = load_toml(config_path)
    old_root = Path(cfg["library"]["library_root"])
    new_root = Path(args.target)

    if not old_root.exists():
        print(f"library_root actual no existe: {old_root}", file=sys.stderr)
        return 1
    if old_root == new_root:
        print("El target es igual al library_root actual -- nada que hacer.")
        return 0

    db_path = project_root / ".rommgr" / "library_pc.db"
    retroarch_cfg = find_retroarch_cfg(cfg)

    print(f"Origen : {old_root}")
    print(f"Destino: {new_root}")
    print(f"BD     : {db_path} ({'existe' if db_path.exists() else 'no existe'})")
    print(f"retroarch.cfg: {retroarch_cfg or '(no detectado via [launchers] retroarch)'}")
    print("Configs de emulador que se revisarán si existen:")
    for f in KNOWN_CONFIG_FILES:
        print(f"  - {f} ({'existe' if f.exists() else 'no existe'})")
    print()

    if not args.apply:
        print("Dry-run -- no se ha tocado nada. Repite con --apply para ejecutar de verdad.")
        print("IMPORTANTE: cierra RetroArch, ES-DE y cualquier juego/emulador nativo abierto antes de --apply.")
        return 0

    backup_files = [config_path, db_path]
    if retroarch_cfg:
        backup_files.append(retroarch_cfg)
    backup_dir = backup(project_root, backup_files)
    print(f"Backup en {backup_dir}")

    ensure_retrovault_siblings(new_root)

    print("Moviendo biblioteca con robocopy (puede tardar)...")
    result = subprocess.run(
        ["robocopy", str(old_root), str(new_root), "/E", "/MOVE", "/R:2", "/W:2", "/NP", "/NDL", "/NFL"],
        capture_output=True,
        text=True,
    )
    # robocopy usa exit codes como bitmask -- 0-7 es éxito (con o sin extras),
    # 8+ significa que algo no se pudo copiar en absoluto.
    if result.returncode >= 8:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        print(f"robocopy falló (exit {result.returncode}) -- abortando antes de tocar la BD.", file=sys.stderr)
        return 1

    remaining_files = [p for p in old_root.rglob("*") if p.is_file()] if old_root.exists() else []
    if remaining_files:
        print(f"AVISO: {len(remaining_files)} archivo(s) no se pudieron mover (probablemente en uso):")
        for p in remaining_files[:20]:
            print(f"  - {p}")
        print("Ciérralos y vuelve a lanzar este mismo comando --apply -- es seguro repetirlo.")

    old_str, new_str = str(old_root), str(new_root)

    if db_path.exists():
        n = migrate_db(db_path, old_str, new_str)
        print(f"BD migrada: {n} filas reescritas")

    n = rewrite_text_file(config_path, old_str, new_str)
    print(f"config.toml: {n} reemplazos")

    if retroarch_cfg:
        n = rewrite_text_file(retroarch_cfg, old_str, new_str)
        print(f"retroarch.cfg: {n} reemplazos")

    for f in KNOWN_CONFIG_FILES:
        n = rewrite_text_file(f, old_str, new_str)
        if n:
            print(f"{f}: {n} reemplazos")

    print()
    print("Hecho. Arranca rommgr y confirma en Overview/Sync que la biblioteca aparece bien.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
