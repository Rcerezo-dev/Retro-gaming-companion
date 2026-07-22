"""Duplicate-detection response builders + RetroAchievements annotation.

Pure functions: typed params → JSON-ready dicts. No global job state.
"""

from __future__ import annotations

import json as _json
import logging
import os as _os
import re as _re_top
from collections import defaultdict
from pathlib import Path as _Path

from rom_manager.config import AppConfig
from rom_manager.database.repository import LibraryRepository
from rom_manager.utils.paths import is_device_path

_logger = logging.getLogger(__name__)

_SPANISH_TAGS = {"spain", "es", "spa", "español", "spanish", "s"}

_DISC_TAG_RE = _re_top.compile(r"\(disc\s*(\d+)\)", _re_top.IGNORECASE)


def _is_disc_set(members) -> bool:
    """True if every member is a distinct disc of the same multi-disc game
    (e.g. "Final Fantasy VII (Disc 1/2/3).cue") — companion discs share the
    DAT's canonical_title (it doesn't encode the disc number) and would
    otherwise look exactly like a title-duplicate cluster (TABS-FIX-6: found
    by hitting a real PSX library — without this guard, "Aplicar recomendación"
    would discard the other discs as if they were alternate copies)."""
    disc_nums = []
    for r in members:
        m = _DISC_TAG_RE.search(r["original_filename"])
        if not m:
            return False
        disc_nums.append(m.group(1))
    return len(set(disc_nums)) == len(disc_nums)


def _is_spanish_filename(filename: str) -> bool:
    import re as _re

    tags = _re.findall(r"\(([^)]+)\)", filename.lower())
    return any(any(t.strip() == s for s in _SPANISH_TAGS) for tag in tags for t in tag.split(","))


def _review_entry_sort_key(entry: dict) -> tuple[int, int, str]:
    """Recommendation order shared by every reason: RA support > Spanish > filename.

    Same criterion the RA-duplicates view already used (before TABS-FIX-6
    generalized it to all 4 review-queue sources). Every entry — including
    disk/collision ones, see ``_review_groups_for_repo`` — always carries
    ``ra_achievements``/``ra_supported``, computed once from the same RA hash
    cache; a plan-conflict entry's own ``conflict_role`` (see
    ``_annotate_conflicts_with_ra``) is display-only and deliberately NOT
    used here. It's derived from a *different* lookup that's gated on the
    source file existing on disk (`op.source_path.exists()`), so it can be
    `None` even when `ra_supported` correctly knows the winner — using it as
    the sort driver picked the wrong "recommended" entry in exactly that case.
    """
    ra_tier = 0 if entry["ra_supported"] else 1
    lang_tier = 0 if _is_spanish_filename(entry["filename"]) else 1
    return (ra_tier, lang_tier, entry["filename"])


def _load_ra_hash_map(
    cache_dir: _Path, platform: str, cache: dict[str, dict[str, int]]
) -> dict[str, int]:
    """md5(lower) → achievements for *platform*, from the RA hash cache on disk.

    Ignores a cache older than RA's own TTL (``ra_client._CACHE_TTL_SECONDS``) —
    stale data must not be treated as authoritative for duplicate resolution
    (REV43-53). *cache* is a per-call dict the caller owns so repeated
    platform lookups only touch disk once.
    """
    if platform in cache:
        return cache[platform]
    import time as _time

    from rom_manager.retroachievements.ra_client import _CACHE_TTL_SECONDS, _parse_game_list
    from rom_manager.retroachievements.ra_platform_ids import get_ra_console_id

    console_id = get_ra_console_id(platform or "")
    if not console_id:
        cache[platform] = {}
        return {}
    cache_file = cache_dir / f"ra_hashes_{console_id}.json"
    if not cache_file.exists() or _time.time() - cache_file.stat().st_mtime >= _CACHE_TTL_SECONDS:
        cache[platform] = {}
        return {}
    try:
        hash_lib = _parse_game_list(_json.loads(cache_file.read_text(encoding="utf-8")))
        result = {md5: game.achievements for md5, game in hash_lib.items()}
    except Exception:
        _logger.warning("Caché RA corrupta o ilegible: %s", cache_file, exc_info=True)
        result = {}
    cache[platform] = result
    return result


def _annotate_conflicts_with_ra(conflict_ops, repository, config) -> list[dict]:
    """Return conflict rows annotated with RA achievement counts and winner/loser roles.

    Fields added per row:
    - ra_achievements: int | null    — achievements for the source file
    - ra_target_achievements: int | null — (disk only) achievements for the blocker file
    - ra_role: "winner" | "loser" | null — predicted outcome if "Resolver con RA" is applied
    """

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

    cache_dir = _Path(config.project_root) / ".rommgr" / "ra_cache"
    _hash_lib_cache: dict[str, dict[str, int]] = {}

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
        return _load_ra_hash_map(cache_dir, plat, _hash_lib_cache).get(md5, -1)

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


def _annotate_duplicates_with_ra(
    title_groups: list[dict], config: AppConfig, repository: LibraryRepository
) -> list[dict]:
    """B1-4: Annotate title_groups entries with RA achievements count if available."""
    cache_dir = config.project_root / ".rommgr" / "ra_cache"

    # Build platform → {md5 → achievements} map
    platform_hash_map: dict[str, dict[str, int]] = {}
    for group in title_groups:
        plat = group.get("platform") or "unknown"
        _load_ra_hash_map(cache_dir, plat, platform_hash_map)

    # Get MD5 mapping: id → md5 from database
    id_to_md5: dict[int, str] = {}
    try:
        with repository.connect() as conn:
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
    title_groups = _annotate_duplicates_with_ra(title_groups, config, repository)

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
    from rom_manager.retroachievements.ra_checker import _normalize_title

    cache_dir = config.project_root / ".rommgr" / "ra_cache"

    with repository.connect() as conn:
        rows = conn.execute(
            "SELECT id, original_filename, source_path, platform, md5, canonical_title, size_bytes "
            "FROM games WHERE file_type = 'rom' ORDER BY platform, original_filename"
        ).fetchall()

    platform_hash_map: dict[str, dict[str, int]] = {}
    platforms_seen = {r["platform"] for r in rows if r["platform"]}
    for plat in platforms_seen:
        _load_ra_hash_map(cache_dir, plat, platform_hash_map)

    if not any(platform_hash_map.values()):
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

        annotated.sort(key=_review_entry_sort_key)
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


def _build_review_queue(
    repository: LibraryRepository, repository_android: LibraryRepository, config: AppConfig
) -> dict:
    """TABS-FIX-6: fuse SHA1/title/RA duplicates + plan conflicts into one queue.

    Delegates to :func:`_review_groups_for_repo` per repo — PC and Android are
    never merged into the same group (a copy on each device is expected, not a
    mistake; same convention the old duplicates view already used).
    """
    repos = [repository] if repository_android is repository else [repository, repository_android]
    cache_dir = _Path(config.project_root) / ".rommgr" / "ra_cache" if config else None
    hash_cache: dict[str, dict[str, int]] = {}
    excluded_keys = {
        row["group_key"] for repo in repos for row in repo.get_excluded_duplicate_groups()
    }

    result_groups: list[dict] = []
    for repo in repos:
        result_groups.extend(
            _review_groups_for_repo(repo, config, cache_dir, hash_cache, excluded_keys)
        )

    result_groups.sort(key=lambda g: g["wasted_bytes"], reverse=True)
    return {
        "groups": result_groups,
        "total_groups": len(result_groups),
        "wasted_bytes": sum(g["wasted_bytes"] for g in result_groups),
    }


def _review_groups_for_repo(
    repo: LibraryRepository,
    config: AppConfig,
    cache_dir: _Path | None,
    hash_cache: dict[str, dict[str, int]],
    excluded_keys: set[str],
) -> list[dict]:
    """Union-Find over one repo's ROM rows: two rows are "the same game" if they
    share a sha1 *or* a (platform, normalized title) — either link is enough,
    which is what lets a sha1-identical pair with different filenames and a
    title-only pair with different sha1s both surface as a single group.
    Plan conflicts (disk/collision) fold into the same clusters when the file
    is already a tracked row, adding their reason without creating a
    duplicate entry.
    """
    from rom_manager.planner.operation_planner import build_plan
    from rom_manager.retroachievements.ra_checker import _normalize_title

    with repo.connect() as conn:
        rows = conn.execute(
            "SELECT original_filename, source_path, platform, md5, sha1,"
            " canonical_title, size_bytes FROM games WHERE file_type = 'rom'"
        ).fetchall()
    if not rows:
        return []

    path_to_idx = {row["source_path"]: i for i, row in enumerate(rows)}
    parent = list(range(len(rows)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    first_by_sha1: dict[str, int] = {}
    first_by_title: dict[tuple[str, str], int] = {}
    for idx, row in enumerate(rows):
        if row["sha1"]:
            union(idx, first_by_sha1.setdefault(row["sha1"], idx))
        # EXACT canonical_title (not RA's fuzzy normalizer) — same key
        # get_title_duplicate_groups() already used. Tried the fuzzy
        # normalizer first (region tags stripped) to also catch "(USA)" vs
        # "(Europe)" pairs; against a real PSX library it merged 18 distinct
        # regional releases of Final Fantasy VII (different discs, different
        # languages) into a single "duplicate" group — exact match is the
        # only safe union key here, a false negative is far cheaper than a
        # false positive that invites bulk-discarding a legitimate release.
        if row["canonical_title"]:
            title_key = (row["platform"] or "unknown", row["canonical_title"])
            union(idx, first_by_title.setdefault(title_key, idx))

    # Plan conflicts: fold into the same clusters via the row they belong to
    # (the common case); a "collision" also unions its contenders together —
    # they may not otherwise share a sha1/title link at all.
    extra_reasons: dict[int, str] = {}
    extra_fields: dict[int, dict] = {}
    orphan_conflicts: list[dict] = []  # conflict row with no matching games row (rare)
    plan = build_plan(repo)
    if plan.conflicts:
        conflict_rows = _annotate_conflicts_with_ra(plan.conflicts, repo, config)
        collision_idxs: dict[str, list[int]] = defaultdict(list)
        for op, crow in zip(plan.conflicts, conflict_rows, strict=True):
            idx = path_to_idx.get(str(op.source_path))
            if idx is None:
                orphan_conflicts.append(crow)
                continue
            extra_reasons[idx] = crow["reason"]
            extra_fields[idx] = crow
            if crow["reason"] == "collision":
                collision_idxs[crow["target_name"]].append(idx)
        for idxs in collision_idxs.values():
            for other in idxs[1:]:
                union(idxs[0], other)

    clusters: dict[int, list[int]] = defaultdict(list)
    for idx in range(len(rows)):
        clusters[find(idx)].append(idx)

    result: list[dict] = []
    for idxs in clusters.values():
        members = [rows[i] for i in idxs]
        sha1_counts: dict[str, int] = defaultdict(int)
        for r in members:
            if r["sha1"]:
                sha1_counts[r["sha1"]] += 1
        distinct_sha1 = {r["sha1"] for r in members if r["sha1"]}
        has_sha1_dup = any(c > 1 for c in sha1_counts.values())
        has_title_dup = (
            len(distinct_sha1) > 1
            and any(r["canonical_title"] for r in members)
            and not _is_disc_set(members)
        )

        plat = next((r["platform"] for r in members if r["platform"]), None) or "unknown"
        hash_map = _load_ra_hash_map(cache_dir, plat, hash_cache) if cache_dir else {}
        scored = []
        for r in members:
            md5_lower = (r["md5"] or "").lower()
            achievements = hash_map.get(md5_lower, -1) if md5_lower else -1
            scored.append(achievements)
        has_ra_mix = any(a > 0 for a in scored) and any(a <= 0 for a in scored)

        reasons: set[str] = set()
        if has_sha1_dup:
            reasons.add("sha1")
        if has_title_dup:
            reasons.add("title")
        if has_ra_mix:
            reasons.add("ra")
        for idx in idxs:
            if idx in extra_reasons:
                reasons.add(extra_reasons[idx])
        if not reasons:
            # United by a coincidental title/sha1 match but nothing actually
            # duplicated (e.g. two unmatched files with the same filename stem
            # and no other signal) — don't invent a false positive.
            continue

        sample_title = next(
            (r["canonical_title"] for r in members if r["canonical_title"]),
            members[0]["original_filename"],
        )
        group_key = f"{plat}::{_normalize_title(sample_title)}"
        if group_key in excluded_keys:
            continue

        entries: dict[str, dict] = {}
        for idx, achievements in zip(idxs, scored, strict=True):
            r = rows[idx]
            entry = {
                "source_path": r["source_path"],
                "filename": r["original_filename"],
                "size_bytes": int(r["size_bytes"]),
                "sha1": r["sha1"],
                "ra_achievements": achievements if achievements >= 0 else None,
                "ra_supported": achievements > 0,
                "is_device": is_device_path(r["source_path"]),
            }
            extra = extra_fields.get(idx)
            if extra:
                entry["conflict_role"] = extra["ra_role"]
                if extra["reason"] == "disk":
                    # The blocking file itself isn't a tracked games row, so it
                    # can't be a second entry of its own — just extra context here.
                    entry["target_name"] = extra["target_name"]
                    entry["ra_target_achievements"] = extra["ra_target_achievements"]
            entries[entry["source_path"]] = entry

        entries_list = list(entries.values())
        entries_list.sort(key=_review_entry_sort_key)
        for i, entry in enumerate(entries_list):
            entry["recommended"] = i == 0
        wasted = sum(e["size_bytes"] or 0 for e in entries_list[1:])
        result.append(
            {
                "platform": plat,
                "canonical_title": sample_title,
                "group_key": group_key,
                "reasons": sorted(reasons),
                "wasted_bytes": wasted,
                "entries": entries_list,
            }
        )

    for crow in orphan_conflicts:
        plat = "unknown"
        title = _Path(crow["source_name"]).stem
        group_key = f"{plat}::{_normalize_title(title)}"
        if group_key in excluded_keys:
            continue
        entry = {
            "source_path": crow["source_path"],
            "filename": crow["source_name"],
            "size_bytes": None,
            "sha1": None,
            "ra_achievements": crow["ra_achievements"],
            "ra_supported": (crow["ra_achievements"] or 0) > 0,
            "is_device": is_device_path(crow["source_path"]),
            "conflict_role": crow["ra_role"],
            "recommended": True,
        }
        if crow["reason"] == "disk":
            entry["target_name"] = crow["target_name"]
            entry["ra_target_achievements"] = crow["ra_target_achievements"]
        result.append(
            {
                "platform": plat,
                "canonical_title": title,
                "group_key": group_key,
                "reasons": [crow["reason"]],
                "wasted_bytes": 0,
                "entries": [entry],
            }
        )

    return result
