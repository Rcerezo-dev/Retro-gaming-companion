"""Response-builder functions for the Retro Vault web server.

All functions here are pure — they take typed parameters and return dicts
ready to be JSON-serialised. They do NOT access any global job state.

Extracted from server.py (Session 18) to reduce the monolith size.
"""

from __future__ import annotations

import logging
from pathlib import Path

from rom_manager.config import AppConfig
from rom_manager.database.repository import LibraryRepository

# SRP-1a: these helpers now live in builders/common.py; re-exported here as a thin
# façade so existing `from rom_manager.web.response_builders import _X` imports keep working.
from rom_manager.web.builders.common import (  # noqa: F401  (re-export)
    _json_response,
    _list_drives,
    _parse_format_opts,
    _repo_for_path,
    _test_path,
    _utc_now_str,
)
from rom_manager.web.builders.library import (  # noqa: F401  (re-export)
    _build_games,
    _build_library_report,
    _build_plan,
    _build_status,
    _count_companion_saves,
)

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Response builders — library / games
# ---------------------------------------------------------------------------


def _build_junk_scan(folder_path: str) -> dict:
    """Scan a folder and classify non-gaming files as junk."""
    import os as _os
    from pathlib import Path as _Path

    _GAMING_EXTS = {
        ".gba",
        ".gb",
        ".gbc",
        ".nes",
        ".sfc",
        ".smc",
        ".md",
        ".smd",
        ".gen",
        ".n64",
        ".z64",
        ".v64",
        ".nds",
        ".3ds",
        ".iso",
        ".chd",
        ".cue",
        ".bin",
        ".cdi",
        ".gdi",
        ".pbp",
        ".gcm",
        ".nsp",
        ".xci",
        ".pce",
        ".ws",
        ".wsc",
        ".ngc",
        ".ngp",
        ".gg",
        ".lynx",
        ".a26",
        ".a52",
        ".a78",
        ".col",
        ".vb",
        ".img",
        ".mdf",
        ".ecm",
        ".nrg",
        ".ccd",
        ".rom",
        ".bios",
        ".sav",
        ".srm",
        ".state",
        ".sta",
        ".mcr",
        ".mc",
        ".mem",
        ".rtc",
        ".xml",
        ".m3u",
        ".png",
        ".jpg",
        ".jpeg",
        ".mp4",
        ".webp",
    }
    _CONFIG_EXTS = {
        ".cfg",
        ".ini",
        ".toml",
        ".json",
        ".txt",
        ".sh",
        ".bat",
        ".conf",
        ".opt",
        ".ovr",
        ".rmp",
    }
    _JUNK_CATEGORIES: dict[str, str] = {
        ".ipynb": "Jupyter Notebooks",
        ".py": "Scripts Python",
        ".js": "Scripts JavaScript",
        ".xlsx": "Excel",
        ".xls": "Excel",
        ".docx": "Word",
        ".doc": "Word",
        ".pptx": "PowerPoint",
        ".ppt": "PowerPoint",
        ".pdf": "PDFs",
        ".zip": "ZIPs no-ROM",
        ".rar": "RARs",
        ".7z": "7-Zips",
        ".tar": "Tarballs",
        ".gz": "Tarballs",
        ".bz2": "Tarballs",
        ".exe": "Ejecutables",
        ".dll": "Ejecutables",
        ".apk": "APKs Android",
        ".mp3": "Audio",
        ".flac": "Audio",
        ".ogg": "Audio",
        ".wav": "Audio",
        ".avi": "Vídeo (no-gaming)",
        ".mkv": "Vídeo (no-gaming)",
        ".mov": "Vídeo (no-gaming)",
        ".psd": "Imágenes editables",
        ".ai": "Imágenes editables",
        ".svg": "SVGs",
        ".html": "HTML/Web",
        ".css": "HTML/Web",
        ".log": "Logs",
        ".db": "Bases de datos",
        ".sqlite": "Bases de datos",
    }

    p = _Path(folder_path)
    if not p.is_dir():
        return {"error": f"Carpeta no encontrada: {folder_path}"}

    categories: dict[str, list[dict]] = {}
    total_junk_bytes = 0

    for dirpath, dirs, files in _os.walk(p):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in files:
            fpath = _Path(dirpath) / fname
            ext = fpath.suffix.lower()
            if ext in _GAMING_EXTS or ext in _CONFIG_EXTS:
                continue
            cat = _JUNK_CATEGORIES.get(ext, f"Otros ({ext or 'sin extensión'})")
            try:
                size = fpath.stat().st_size
            except OSError:
                size = 0
            total_junk_bytes += size
            if cat not in categories:
                categories[cat] = []
            try:
                rel = str(fpath.relative_to(p))
            except ValueError:
                rel = str(fpath)
            categories[cat].append({"path": rel, "full_path": str(fpath), "size_bytes": size})

    cat_list = []
    for cat, files_list in sorted(
        categories.items(), key=lambda x: -sum(f["size_bytes"] for f in x[1])
    ):
        total = sum(f["size_bytes"] for f in files_list)
        cat_list.append(
            {
                "category": cat,
                "count": len(files_list),
                "total_bytes": total,
                "files": sorted(files_list, key=lambda f: -f["size_bytes"])[:50],
            }
        )

    return {
        "folder": folder_path,
        "total_junk_files": sum(c["count"] for c in cat_list),
        "total_junk_bytes": total_junk_bytes,
        "categories": cat_list,
    }


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


def _build_library_diff(
    repository: LibraryRepository,
    repository_android: LibraryRepository,
    config: AppConfig,
    platform: str | None = None,
) -> dict:
    """Compare PC vs Android libraries by SHA1 and return three-way diff with conflict detection.

    Args:
        platform: If provided, filter results to this platform only.
    """

    def _fetch_roms(repo: LibraryRepository) -> dict[str, dict]:
        result: dict[str, dict] = {}
        with repo.connect() as conn:
            query = (
                "SELECT sha1, platform, canonical_title, original_filename, source_path "
                "FROM games WHERE file_type = 'rom' AND sha1 IS NOT NULL AND sha1 != ''"
            )
            if platform:
                query += " AND platform = ?"
                rows = conn.execute(query, (platform,)).fetchall()
            else:
                rows = conn.execute(query).fetchall()
        for row in rows:
            sha1, plat, title, fname, spath = row
            result[sha1] = {
                "platform": plat or "",
                "title": title or fname or "",
                "source_path": spath or "",
            }
        return result

    pc_roms = _fetch_roms(repository)
    and_roms = _fetch_roms(repository_android)
    pc_sha1s = set(pc_roms)
    and_sha1s = set(and_roms)

    # Detect conflicts: same (platform, canonical_title) but different SHA1
    pc_by_title = {}
    for s in pc_sha1s - and_sha1s:
        entry = pc_roms[s]
        title = entry.get("title", "")
        plat = entry.get("platform", "")
        if title:
            key = (plat, title)
            pc_by_title.setdefault(key, []).append({"sha1": s, **entry})

    and_by_title = {}
    for s in and_sha1s - pc_sha1s:
        entry = and_roms[s]
        title = entry.get("title", "")
        plat = entry.get("platform", "")
        if title:
            key = (plat, title)
            and_by_title.setdefault(key, []).append({"sha1": s, **entry})

    # Find conflict keys (same title/platform in both)
    conflict_keys = set(pc_by_title.keys()) & set(and_by_title.keys())
    conflicts = sorted(
        [
            {
                "platform": key[0],
                "title": key[1],
                "pc": pc_by_title[key],
                "android": and_by_title[key],
            }
            for key in conflict_keys
        ],
        key=lambda x: (x["platform"], x["title"]),
    )

    # Remove conflicted entries from only_pc/only_and
    conflicted_pc_sha1s = {e["sha1"] for k in conflict_keys for e in pc_by_title[k]}
    conflicted_and_sha1s = {e["sha1"] for k in conflict_keys for e in and_by_title[k]}
    only_pc = sorted(
        [
            {"sha1": s, **pc_roms[s], "location": "pc"}
            for s in (pc_sha1s - and_sha1s)
            if s not in conflicted_pc_sha1s
        ],
        key=lambda x: (x["platform"], x["title"]),
    )
    only_and = sorted(
        [
            {"sha1": s, **and_roms[s], "location": "android"}
            for s in (and_sha1s - pc_sha1s)
            if s not in conflicted_and_sha1s
        ],
        key=lambda x: (x["platform"], x["title"]),
    )

    # in_both: include both PC and Android source paths
    in_both = sorted(
        [
            {
                "sha1": s,
                **pc_roms[s],
                "android_source_path": and_roms[s]["source_path"],
                "location": "both",
            }
            for s in pc_sha1s & and_sha1s
        ],
        key=lambda x: (x["platform"], x["title"]),
    )

    return {
        "only_pc": only_pc,
        "only_android": only_and,
        "in_both": in_both,
        "conflicts": conflicts,
        "total_pc": len(pc_roms),
        "total_android": len(and_roms),
        "parity": len(only_pc) == 0 and len(only_and) == 0 and len(conflicts) == 0,
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


def _build_folder_analysis(folder_path: str, config: AppConfig) -> dict:
    """Analyse a folder: count extensions, find broken PSX sets, flag conversion needs."""
    from collections import Counter
    from pathlib import Path as _Path

    _ROM_EXTS = {
        ".gba",
        ".gb",
        ".gbc",
        ".nes",
        ".snes",
        ".sfc",
        ".md",
        ".smd",
        ".gen",
        ".n64",
        ".z64",
        ".v64",
        ".nds",
        ".3ds",
        ".psx",
        ".ps1",
        ".iso",
        ".chd",
        ".cue",
        ".bin",
        ".cdi",
        ".gdi",
        ".pbp",
        ".elf",
        ".gcm",
        ".nkit",
        ".rvz",
        ".wbfs",
        ".nsp",
        ".xci",
    }
    _SAVE_EXTS = {".sav", ".srm", ".state", ".sta", ".mcr", ".mc"}
    _NEEDS_CONVERSION = {
        ".img": "imagen de disco — puede ser CD-ROM (.img/.ccd) o HDD; verificar si acompaña .ccd/.sub",
        ".mdf": "imagen Alcohol 120% — convertir a .chd o .cue/.bin con mdf2iso",
        ".mds": "descriptor Alcohol 120% — acompaña .mdf",
        ".ccd": "CloneCD descriptor — convertir a .chd con chdman",
        ".sub": "datos de subcódigo CloneCD — acompaña .ccd/.img",
        ".nrg": "imagen Nero — convertir a .iso o .chd",
        ".ecm": "Error Code Modeler — descomprimir con ecmtools antes de convertir a CHD",
    }

    p = _Path(folder_path)
    if not p.is_dir():
        return {
            "error": f"Carpeta no encontrada: {folder_path}",
            "extensions": [],
            "cue_missing_bin": [],
            "bin_orphan": [],
            "needs_conversion": [],
        }

    ext_counter: Counter[str] = Counter()
    cue_files: list[_Path] = []
    bin_files: set[str] = set()

    for f in p.rglob("*"):
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        ext_counter[ext] += 1
        if ext == ".cue":
            cue_files.append(f)
        elif ext == ".bin":
            bin_files.add(f.stem.lower())

    extensions = []
    for ext, count in sorted(ext_counter.items(), key=lambda x: -x[1]):
        if ext in _ROM_EXTS:
            cat = "rom"
        elif ext in _SAVE_EXTS:
            cat = "save"
        elif ext in _NEEDS_CONVERSION:
            cat = "needs_conversion"
        elif ext in {".jpg", ".jpeg", ".png", ".webp", ".xml", ".txt", ".cfg", ".db"}:
            cat = "asset/meta"
        else:
            cat = "unknown"
        extensions.append({"ext": ext or "(sin extensión)", "count": count, "category": cat})

    import re as _re

    cue_missing_bin: list[str] = []
    for cue in cue_files:
        try:
            text = cue.read_text(errors="replace")
            bins_referenced = _re.findall(r'FILE\s+"?([^"]+\.bin)"?', text, _re.IGNORECASE)
            for bin_name in bins_referenced:
                if not (cue.parent / bin_name).exists():
                    cue_missing_bin.append(cue.name)
                    break
        except OSError:
            pass

    cue_stems = {c.stem.lower() for c in cue_files}
    bin_orphan = [
        f.name for f in p.rglob("*.bin") if f.is_file() and f.stem.lower() not in cue_stems
    ]
    needs_conversion = [
        {"ext": ext, "note": note} for ext, note in _NEEDS_CONVERSION.items() if ext in ext_counter
    ]

    return {
        "folder": folder_path,
        "extensions": extensions,
        "cue_missing_bin": sorted(cue_missing_bin),
        "bin_orphan": sorted(bin_orphan),
        "needs_conversion": needs_conversion,
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


def _build_assets(repository: LibraryRepository, source_root: str | None = None) -> dict:
    return {"stats": repository.get_asset_platform_stats(source_root=source_root)}


def _build_sync_log(repository: LibraryRepository) -> dict:
    entries = repository.get_sync_log(limit=200)
    return {"entries": entries}


def _build_config(config: AppConfig) -> dict:
    from rom_manager.config import validate as _validate_config

    def _db_size(p: Path) -> int | None:
        try:
            return p.stat().st_size if p.exists() else 0
        except OSError:
            return None

    return {
        "warnings": _validate_config(config),
        "library_root": str(config.library_root) if config.library_root else None,
        "anbernic_root": config.anbernic_root or "",
        "device_name": config.device_name or "Consola Android",
        "rclone_remote": config.rclone_remote or None,
        "web_host": config.web_host,
        "web_port": config.web_port,
        "screenscraper_user": config.screenscraper_user or None,
        "screenscraper_pass_set": bool(config.screenscraper_pass),
        "screenscraper_dev_id": config.screenscraper_dev_id or None,
        "screenscraper_dev_pass_set": bool(config.screenscraper_dev_pass),
        "chdman": config.chdman,
        "adb": config.adb,
        "ra_api_key_set": bool(config.ra_api_key),
        "ra_username": config.ra_username or None,
        "pc_db_path": str(config.database_path),
        "pc_db_size": _db_size(config.database_path),
        "android_db_path": str(config.database_path_android),
        "android_db_size": _db_size(config.database_path_android),
        "inbox_path": config.inbox_path or "",
        "inbox_target_root": config.inbox_target_root or "",
        "inbox_auto_process": config.inbox_auto_process,
        "inbox_delete_source": config.inbox_delete_source,
        "sync_sources": [
            {"name": s.name, "local_dir": s.local_dir, "remote": s.remote, "sync_all": s.sync_all}
            for s in config.sync_sources
        ],
        "retroarch_path": config.retroarch_path or "",
        "launcher_cores": config.launcher_cores or {},
        "backup_saves_enabled": config.backup_saves_enabled,
        "backup_saves_keep_n": config.backup_saves_keep_n,
        "notify_desktop": config.notify_desktop,
        "saves_remote": config.saves_remote or "",
        "states_remote": config.states_remote or "",
    }


def _build_scrape_summary(repository: LibraryRepository) -> dict:
    return {"platforms": repository.get_scraped_platform_summary()}


def _build_cable_sync_preview(qs: dict, config: AppConfig) -> dict:
    """Count saves on PC and Android side for a quick pre-sync summary."""
    import os as _os

    mode = qs.get("mode", ["sd"])[0]
    direction = qs.get("direction", ["pc_to_anbernic"])[0]
    pc_path_s = (qs.get("pc_path", [None])[0] or "").strip() or str(config.library_root or "")
    ab_path_s = (qs.get("ab_path", [None])[0] or "").strip()

    save_exts: frozenset[str] = frozenset(config.save_extensions)

    def _count_saves(root: Path) -> int:
        count = 0
        try:
            for dirpath, dirs, files in _os.walk(root):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for fname in files:
                    if Path(fname).suffix.lower() in save_exts:
                        count += 1
        except OSError:
            pass
        return count

    pc_saves: int | None = None
    if pc_path_s:
        pc_root = Path(pc_path_s)
        if pc_root.is_dir():
            pc_saves = _count_saves(pc_root)

    android_saves: int | None = None
    android_message: str | None = None

    if mode == "adb":
        android_message = "no accesible en modo ADB (conecta y detecta el dispositivo)"
    elif ab_path_s:
        ab_root = Path(ab_path_s)
        if ab_root.is_dir():
            android_saves = _count_saves(ab_root)
        else:
            android_message = f"ruta no encontrada: {ab_path_s}"
    else:
        android_message = "introduce la ruta de la tarjeta SD / consola Android"

    to_copy: int | None = None
    if direction in ("pc_to_anbernic",) and pc_saves is not None and android_saves is not None:
        to_copy = max(0, pc_saves - android_saves)
    elif direction == "anbernic_to_pc" and pc_saves is not None and android_saves is not None:
        to_copy = max(0, android_saves - pc_saves)
    elif direction == "newest" and pc_saves is not None and android_saves is not None:
        to_copy = abs(pc_saves - android_saves)

    return {
        "pc_saves": pc_saves,
        "android_saves": android_saves,
        "android_message": android_message,
        "to_copy": to_copy,
        "mode": mode,
        "direction": direction,
    }
