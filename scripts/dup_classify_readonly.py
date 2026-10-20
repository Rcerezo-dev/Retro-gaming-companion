"""DUP-CROSSFMT-8: clasifica los grupos de la cola de duplicados NES/Game Boy/Game Gear.

SOLO LECTURA. Trabaja sobre COPIAS temporales de library_pc.db/library_android.db
(abrir un LibraryRepository puede migrar el schema) y nunca toca ni aplica nada.

Uso: python scripts/dup_classify_readonly.py [--platforms NES "Game Boy" ...]
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from rom_manager.config import load_config  # noqa: E402
from rom_manager.database.repository import LibraryRepository  # noqa: E402
from rom_manager.detection.platform_detector import PLATFORM_BY_EXTENSION  # noqa: E402
from rom_manager.web.builders.duplicates import _build_review_queue  # noqa: E402

DEFAULT_PLATFORMS = ("NES", "Game Boy", "Game Gear")
# Hack / traducción / prototipo / dump malo: no son duplicados reales del original.
VARIANT_TAG = re.compile(
    r"hack|\[t[+-]|trad|transl|pirate|proto|beta|\(unl|sample|demo|bonus|\[[abfhop]\d*\]|subset",
    re.I,
)


def content_id(entry: dict) -> str | tuple:
    """sha1 del contenido real: el de la BD para crudos, el del interior para un zip de 1 archivo."""
    path = entry["source_path"]
    if path.lower().endswith(".zip"):
        try:
            with zipfile.ZipFile(path) as z:
                files = [i for i in z.infolist() if not i.is_dir()]
                if len(files) != 1:
                    return ("zip-multi", path)
                return hashlib.sha1(z.read(files[0])).hexdigest().upper()
        except (OSError, zipfile.BadZipFile):
            return ("zip-unreadable", path)
    return (entry["sha1"] or "").upper() or ("sin-sha1", path)


def classify(entries: list[dict]) -> tuple[str, int]:
    """Devuelve (categoría, archivos descartables por sub-duplicado verificado)."""
    clusters: dict = collections.defaultdict(list)
    for e in entries:
        clusters[content_id(e)].append(e)
    if any(not isinstance(k, str) for k in clusters):
        return "no-verificable", 0
    removable = sum(len(v) - 1 for v in clusters.values())
    if len(clusters) == 1:
        return "todo-identico", removable
    tagged = any(VARIANT_TAG.search(e["filename"]) for e in entries)
    base = "sub-duplicado+distintos" if removable else "todo-distinto"
    return base + ("(variante)" if tagged else ""), removable


def origin_counts(repo: LibraryRepository, platforms: tuple[str, ...]) -> collections.Counter:
    """Filas de las plataformas objetivo cuya ruta/extensión contradice la plataforma."""
    c: collections.Counter = collections.Counter()
    with repo.connect() as conn:
        rows = conn.execute(
            "SELECT platform, source_path FROM games WHERE file_type='rom' AND platform IN (%s)"
            % ",".join("?" * len(platforms)),
            platforms,
        ).fetchall()
    for plat, path in rows:
        low = path.lower().replace("\\", "/")
        if "/arcade/" in low:
            c[(plat, "ruta arcade/")] += 1
        if "/inbox/" in low:
            c[(plat, "ruta inbox/")] += 1
        ext_plat = PLATFORM_BY_EXTENSION.get(Path(path).suffix.lower())
        if ext_plat and ext_plat != plat:
            c[(plat, f"extensión de {ext_plat}")] += 1
    return c


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--platforms", nargs="+", default=list(DEFAULT_PLATFORMS))
    args = ap.parse_args()
    platforms = tuple(args.platforms)

    config = load_config(ROOT)
    with tempfile.TemporaryDirectory() as tmp:
        pc, an = Path(tmp) / "pc.db", Path(tmp) / "an.db"
        shutil.copy(config.database_path, pc)
        shutil.copy(config.database_path_android, an)
        repo_pc, repo_an = LibraryRepository(pc), LibraryRepository(an)
        queue = _build_review_queue(repo_pc, repo_an, config)
        origins = origin_counts(repo_pc, platforms)

    cats: dict = collections.defaultdict(collections.Counter)
    removable: collections.Counter = collections.Counter()
    conflict: collections.Counter = collections.Counter()
    for g in queue["groups"]:
        if g["platform"] not in platforms:
            continue
        cat, n = classify(g["entries"])
        cats[g["platform"]][cat] += 1
        # disk/collision se resuelven por apply_ra_conflicts (solo logros RA), no por resolve_duplicate_ra
        if set(g.get("reasons", ())) & {"disk", "collision"}:
            conflict[(g["platform"], cat)] += 1
        removable[g["platform"]] += n
    for plat in platforms:
        print(f"{plat}: {sum(cats[plat].values())} grupos, {removable[plat]} archivos descartables")
        for cat, n in cats[plat].most_common():
            print(f"    {cat}: {n} (con reason disk/collision: {conflict[(plat, cat)]})")
    print("Filas con origen sospechoso (plataforma contradice ruta/extensión):")
    for (plat, why), n in sorted(origins.items()):
        print(f"    {plat} / {why}: {n}")


if __name__ == "__main__":
    main()
