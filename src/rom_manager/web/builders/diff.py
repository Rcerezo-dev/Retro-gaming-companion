"""Two-repository (PC ↔ Android) library-diff response builder.

Pure function: typed params → JSON-ready dict. No global job state.
"""

from __future__ import annotations

import logging

from rom_manager.config import AppConfig
from rom_manager.database.repository import LibraryRepository

_logger = logging.getLogger(__name__)


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
