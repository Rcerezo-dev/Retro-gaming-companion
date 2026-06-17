"""Duplicate-detection response builders + RetroAchievements annotation.

Pure functions: typed params → JSON-ready dicts. No global job state.
"""

from __future__ import annotations

import logging

from rom_manager.config import AppConfig
from rom_manager.database.repository import LibraryRepository

_logger = logging.getLogger(__name__)


def _annotate_conflicts_with_ra(conflict_ops, repository, config) -> list[dict]:
    """Return conflict rows annotated with RA achievement counts and winner/loser roles.

    Fields added per row:
    - ra_achievements: int | null    — achievements for the source file
    - ra_target_achievements: int | null — (disk only) achievements for the blocker file
    - ra_role: "winner" | "loser" | null — predicted outcome if "Resolver con RA" is applied
    """
    import json as _json
    from collections import defaultdict
    from pathlib import Path as _Path

    def base_row(op):
        return {
            "game_id": op.game.id,
            "source_name": op.source_path.name,
            "target_name": op.target_path.name,
            "source_path": str(op.source_path),
            "reason": op.conflict_reason,
            "ra_achievements": None,
            "ra_target_achievements": None,
            "ra_role": None,
        }

    if config is None or not conflict_ops:
        return [base_row(op) for op in conflict_ops]

    try:
        from rom_manager.retroachievements.ra_client import _parse_game_list
        from rom_manager.retroachievements.ra_platform_ids import get_ra_console_id
    except Exception:
        _logger.debug(
            "Módulos de RetroAchievements no disponibles; conflictos sin anotar RA", exc_info=True
        )
        return [base_row(op) for op in conflict_ops]

    cache_dir = _Path(config.project_root) / ".rommgr" / "ra_cache"
    _hash_lib_cache: dict[str, dict] = {}

    def _hash_lib_for(plat: str) -> dict:
        if plat in _hash_lib_cache:
            return _hash_lib_cache[plat]
        console_id = get_ra_console_id(plat or "")
        if not console_id:
            _hash_lib_cache[plat] = {}
            return {}
        cache_file = cache_dir / f"ra_hashes_{console_id}.json"
        if not cache_file.exists():
            _hash_lib_cache[plat] = {}
            return {}
        try:
            lib = _parse_game_list(_json.loads(cache_file.read_text(encoding="utf-8")))
        except Exception:
            _logger.warning("Caché RA corrupta o ilegible: %s", cache_file, exc_info=True)
            lib = {}
        _hash_lib_cache[plat] = lib
        return lib

    def _ra_for_path(path: _Path) -> int:
        """Return achievement count (-1 = no data)."""
        try:
            with repository.connect() as _c:
                row = _c.execute(
                    "SELECT md5, platform FROM games WHERE source_path = ?", (str(path),)
                ).fetchone()
            if not row:
                return -1
            md5 = (row["md5"] or "").lower()
            plat = row["platform"] or ""
        except Exception:
            _logger.debug("Consulta RA por ruta falló: %s", path, exc_info=True)
            return -1
        if not md5:
            return -1
        entry = _hash_lib_for(plat).get(md5)
        return entry.achievements if entry else -1

    # Pre-compute RA scores for all source paths
    ra_scores: dict[str, int] = {}
    for op in conflict_ops:
        key = str(op.source_path)
        if key not in ra_scores:
            ra_scores[key] = _ra_for_path(op.source_path)

    # For disk conflicts, also score the target path (the blocker file)
    for op in conflict_ops:
        if op.conflict_reason == "disk":
            key = str(op.target_path)
            if key not in ra_scores:
                ra_scores[key] = _ra_for_path(op.target_path)

    # Determine collision winners (highest RA per target group)
    collision_winners: set[str] = set()
    collision_groups: dict[str, list] = defaultdict(list)
    for op in conflict_ops:
        if op.conflict_reason == "collision":
            collision_groups[str(op.target_path)].append(op)
    for ops in collision_groups.values():
        scored = [
            (op, ra_scores.get(str(op.source_path), -1)) for op in ops if op.source_path.exists()
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        if scored and scored[0][1] > 0:
            collision_winners.add(str(scored[0][0].source_path))

    rows = []
    for op in conflict_ops:
        row = base_row(op)
        src_ra = ra_scores.get(str(op.source_path), -1)
        row["ra_achievements"] = src_ra if src_ra >= 0 else None

        if op.conflict_reason == "disk":
            tgt_ra = ra_scores.get(str(op.target_path), -1)
            row["ra_target_achievements"] = tgt_ra if tgt_ra >= 0 else None
            if src_ra > 0 or tgt_ra > 0:
                row["ra_role"] = "winner" if src_ra > tgt_ra else "loser"
        elif op.conflict_reason == "collision":
            if str(op.source_path) in collision_winners:
                row["ra_role"] = "winner"
            elif src_ra >= 0:
                row["ra_role"] = "loser"
        rows.append(row)
    return rows


def _annotate_duplicates_with_ra(title_groups: list[dict], config: AppConfig) -> list[dict]:
    """B1-4: Annotate title_groups entries with RA achievements count if available."""
    import json as _json

    from rom_manager.retroachievements.ra_client import _parse_game_list
    from rom_manager.retroachievements.ra_platform_ids import get_ra_console_id

    cache_dir = config.project_root / ".rommgr" / "ra_cache"

    # Build platform → {md5 → achievements} map
    platform_hash_map: dict[str, dict[str, int]] = {}
    for group in title_groups:
        plat = group.get("platform") or "unknown"
        if plat in platform_hash_map:
            continue
        console_id = get_ra_console_id(plat)
        if not console_id:
            continue
        cache_file = cache_dir / f"ra_hashes_{console_id}.json"
        if not cache_file.exists():
            continue
        try:
            data = _json.loads(cache_file.read_text(encoding="utf-8"))
            hash_lib = _parse_game_list(data)
            platform_hash_map[plat] = {md5: game.achievements for md5, game in hash_lib.items()}
        except Exception:
            _logger.warning("Caché RA corrupta o ilegible: %s", cache_file, exc_info=True)
            continue

    # Get MD5 mapping: id → md5 from database
    id_to_md5: dict[int, str] = {}
    try:
        from rom_manager.database.repository import LibraryRepository

        repo = LibraryRepository(config.project_root)
        with repo.connect() as conn:
            rows = conn.execute("SELECT id, md5 FROM games").fetchall()
            id_to_md5 = {r["id"]: r["md5"] for r in rows}
    except Exception:
        _logger.warning("Consulta id→md5 para duplicados RA falló", exc_info=True)

    # Annotate each entry
    result = []
    for group in title_groups:
        plat = group.get("platform")
        hash_map = platform_hash_map.get(plat, {})
        annotated_entries = []
        for entry in group.get("entries", []):
            md5 = id_to_md5.get(entry["id"], "")
            md5_lower = (md5 or "").lower()
            achievements = hash_map.get(md5_lower, 0)
            annotated_entry = {**entry, "ra_achievements": achievements}
            annotated_entries.append(annotated_entry)
        result.append({**group, "entries": annotated_entries})

    return result


def _build_duplicates(
    repository: LibraryRepository,
    config: AppConfig,
    source_root: str | None = None,
    pc_root: str | None = None,
    ab_root: str | None = None,
) -> dict:
    import os as _os

    from rom_manager.database.repository import DuplicateGroup

    def _norm(p: str) -> str:
        return _os.path.normcase(_os.path.normpath(p)).rstrip(_os.sep) + _os.sep

    groups = repository.get_duplicate_groups()
    if source_root:
        root_norm = _norm(source_root)
        filtered = []
        for g in groups:
            entries = [
                e for e in g.entries if _os.path.normcase(e.source_path).startswith(root_norm)
            ]
            if len(entries) >= 2:
                filtered.append(DuplicateGroup(sha1=g.sha1, entries=entries))
        groups = filtered
    elif pc_root and ab_root:
        pc_norm = _norm(pc_root)
        ab_norm = _norm(ab_root)
        filtered = []
        for g in groups:
            pc_entries = [
                e for e in g.entries if _os.path.normcase(e.source_path).startswith(pc_norm)
            ]
            ab_entries = [
                e for e in g.entries if _os.path.normcase(e.source_path).startswith(ab_norm)
            ]
            if len(pc_entries) >= 2 or len(ab_entries) >= 2:
                filtered.append(g)
        groups = filtered
    elif pc_root:
        pc_norm = _norm(pc_root)
        filtered = []
        for g in groups:
            entries = [e for e in g.entries if _os.path.normcase(e.source_path).startswith(pc_norm)]
            if len(entries) >= 2:
                filtered.append(DuplicateGroup(sha1=g.sha1, entries=entries))
        groups = filtered
    groups = sorted(groups, key=lambda g: g.wasted_bytes, reverse=True)
    total_files = sum(len(g.entries) for g in groups)
    total_wasted = sum(g.wasted_bytes for g in groups)

    # Semantic duplicates: same canonical_title+platform but different SHA1
    title_groups = repository.get_title_duplicate_groups()

    # Annotate title_groups with RA achievements if available
    title_groups = _annotate_duplicates_with_ra(title_groups, config)

    return {
        "groups": [
            {
                "sha1": g.sha1,
                "canonical_title": g.entries[0].canonical_title,
                "platform": g.entries[0].platform,
                "wasted_bytes": g.wasted_bytes,
                "entries": [
                    {"id": e.id, "source_path": e.source_path, "size_bytes": e.size_bytes}
                    for e in g.entries
                ],
            }
            for g in groups
        ],
        "total_files": total_files,
        "wasted_bytes": total_wasted,
        "title_groups": title_groups,
    }


def _build_duplicates_two_repos(
    repository: LibraryRepository,
    repository_android: LibraryRepository,
    config: AppConfig,
    source_root: str | None = None,
    pc_root: str | None = None,
    ab_root: str | None = None,
) -> dict:
    """Two-DB version of duplicate detection."""
    import os as _os

    from rom_manager.database.repository import DuplicateGroup

    def _norm(p: str) -> str:
        return _os.path.normcase(_os.path.normpath(p)).rstrip(_os.sep) + _os.sep

    if repository_android is repository:
        return _build_duplicates(
            repository, config, source_root=source_root, pc_root=pc_root, ab_root=ab_root
        )

    pc_groups = repository.get_duplicate_groups()
    android_groups = repository_android.get_duplicate_groups()

    if source_root:
        root_norm = _norm(source_root)
        filtered_pc = []
        for g in pc_groups:
            entries = [
                e for e in g.entries if _os.path.normcase(e.source_path).startswith(root_norm)
            ]
            if len(entries) >= 2:
                filtered_pc.append(DuplicateGroup(sha1=g.sha1, entries=entries))
        filtered_android = []
        for g in android_groups:
            entries = [
                e for e in g.entries if _os.path.normcase(e.source_path).startswith(root_norm)
            ]
            if len(entries) >= 2:
                filtered_android.append(DuplicateGroup(sha1=g.sha1, entries=entries))
        all_groups = sorted(
            filtered_pc + filtered_android, key=lambda g: g.wasted_bytes, reverse=True
        )
        total_files = sum(len(g.entries) for g in all_groups)
        total_wasted = sum(g.wasted_bytes for g in all_groups)
        return {
            "groups": [
                {
                    "sha1": g.sha1,
                    "canonical_title": g.entries[0].canonical_title,
                    "platform": g.entries[0].platform,
                    "wasted_bytes": g.wasted_bytes,
                    "entries": [
                        {"id": e.id, "source_path": e.source_path, "size_bytes": e.size_bytes}
                        for e in g.entries
                    ],
                }
                for g in all_groups
            ],
            "total_files": total_files,
            "wasted_bytes": total_wasted,
        }

    combined: list[DuplicateGroup] = []

    if pc_root:
        pc_norm = _norm(pc_root)
        for g in pc_groups:
            entries = [e for e in g.entries if _os.path.normcase(e.source_path).startswith(pc_norm)]
            if len(entries) >= 2:
                combined.append(DuplicateGroup(sha1=g.sha1, entries=entries))
    else:
        combined.extend(pc_groups)

    if ab_root:
        ab_norm = _norm(ab_root)
        for g in android_groups:
            entries = [e for e in g.entries if _os.path.normcase(e.source_path).startswith(ab_norm)]
            if len(entries) >= 2:
                combined.append(DuplicateGroup(sha1=g.sha1, entries=entries))
    else:
        combined.extend(android_groups)

    seen: set[str] = set()
    deduped: list[DuplicateGroup] = []
    for g in combined:
        if g.sha1 not in seen:
            seen.add(g.sha1)
            deduped.append(g)

    deduped = sorted(deduped, key=lambda g: g.wasted_bytes, reverse=True)
    total_files = sum(len(g.entries) for g in deduped)
    total_wasted = sum(g.wasted_bytes for g in deduped)
    return {
        "groups": [
            {
                "sha1": g.sha1,
                "canonical_title": g.entries[0].canonical_title,
                "platform": g.entries[0].platform,
                "wasted_bytes": g.wasted_bytes,
                "entries": [
                    {"id": e.id, "source_path": e.source_path, "size_bytes": e.size_bytes}
                    for e in g.entries
                ],
            }
            for g in deduped
        ],
        "total_files": total_files,
        "wasted_bytes": total_wasted,
    }


def _build_ra_duplicates(repository: LibraryRepository, config: AppConfig) -> dict:
    """B1-4: Find title-based duplicates where one version has RA support and another doesn't.

    Conserva automáticamente la versión con logros activos en RetroAchievements.
    Las versiones sin logros se marcan como candidatas a eliminar.
    """
    import json as _json
    from collections import defaultdict
    from pathlib import Path as _Path

    from rom_manager.retroachievements.ra_checker import _normalize_title
    from rom_manager.retroachievements.ra_client import _parse_game_list
    from rom_manager.retroachievements.ra_platform_ids import get_ra_console_id

    cache_dir = config.project_root / ".rommgr" / "ra_cache"

    with repository.connect() as conn:
        rows = conn.execute(
            "SELECT id, original_filename, source_path, platform, md5, canonical_title, size_bytes "
            "FROM games WHERE file_type = 'rom' ORDER BY platform, original_filename"
        ).fetchall()

    platform_hash_map: dict[str, dict[str, int]] = {}
    platforms_seen = {r["platform"] for r in rows if r["platform"]}
    for plat in platforms_seen:
        console_id = get_ra_console_id(plat or "")
        if not console_id:
            continue
        cache_file = cache_dir / f"ra_hashes_{console_id}.json"
        if not cache_file.exists():
            continue
        try:
            data = _json.loads(cache_file.read_text(encoding="utf-8"))
            hash_lib = _parse_game_list(data)
            platform_hash_map[plat] = {md5: game.achievements for md5, game in hash_lib.items()}
        except Exception:
            _logger.warning("Caché RA corrupta o ilegible: %s", cache_file, exc_info=True)
            continue

    if not platform_hash_map:
        return {
            "groups": [],
            "total_groups": 0,
            "wasted_bytes": 0,
            "note": "No hay caché de RetroAchievements. Ejecuta primero la comprobación RA en Tools.",
        }

    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        plat = row["platform"] or "unknown"
        title = row["canonical_title"] or _Path(row["original_filename"]).stem
        key = (plat, _normalize_title(title))
        groups[key].append(
            {
                "id": row["id"],
                "filename": row["original_filename"],
                "source_path": row["source_path"],
                "platform": row["platform"],
                "md5": row["md5"],
                "size_bytes": int(row["size_bytes"]),
            }
        )

    result_groups = []
    for (plat, norm_title), entries in groups.items():
        if len(entries) < 2:
            continue
        hash_map = platform_hash_map.get(plat)
        if not hash_map:
            continue

        annotated = []
        for e in entries:
            md5_lower = (e["md5"] or "").lower()
            achievements = hash_map.get(md5_lower, -1)
            annotated.append(
                {**e, "ra_achievements": achievements, "ra_supported": achievements > 0}
            )

        has_supported = any(a["ra_supported"] for a in annotated)
        has_unsupported = any(not a["ra_supported"] for a in annotated)
        if not (has_supported and has_unsupported):
            continue

        _SPANISH_TAGS = {"spain", "es", "spa", "español", "spanish", "s"}

        def _is_spanish(filename: str) -> bool:
            import re as _re

            tags = _re.findall(r"\(([^)]+)\)", filename.lower())
            return any(
                any(t.strip() == s for s in _SPANISH_TAGS) for tag in tags for t in tag.split(",")
            )

        def _sort_key(entry: dict) -> tuple:
            ra_tier = 0 if entry["ra_supported"] else 1
            lang_tier = 0 if _is_spanish(entry["filename"]) else 1
            return (ra_tier, lang_tier, entry["filename"])

        annotated.sort(key=_sort_key)
        wasted = sum(a["size_bytes"] for a in annotated if not a["ra_supported"])
        result_groups.append(
            {
                "platform": plat,
                "normalized_title": norm_title,
                "entries": annotated,
                "wasted_bytes": wasted,
            }
        )

    result_groups.sort(key=lambda g: g["wasted_bytes"], reverse=True)
    return {
        "groups": result_groups,
        "total_groups": len(result_groups),
        "wasted_bytes": sum(g["wasted_bytes"] for g in result_groups),
    }
