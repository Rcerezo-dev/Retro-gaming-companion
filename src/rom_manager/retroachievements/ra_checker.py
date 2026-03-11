from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from rom_manager.retroachievements.ra_client import RAGame, fetch_hash_library
from rom_manager.retroachievements.ra_platform_ids import get_ra_console_id


@dataclass(slots=True)
class RAGameResult:
    source_path: str
    original_filename: str
    platform: str
    our_md5: str
    # status values:
    #   "supported"             — our MD5 is in RA hash library
    #   "no_support_alternative" — not in RA, but alternative version exists
    #   "no_support"            — not in RA, no alternative found
    #   "no_md5"                — game has no MD5 calculated (needs full scan)
    #   "platform_unknown"      — platform not mapped to RA console
    status: str
    alternative: RAGame | None = None


@dataclass
class RACheckSummary:
    supported: int = 0
    no_support_alternative: int = 0
    no_support: int = 0
    no_md5: int = 0
    platform_unknown: int = 0
    total: int = 0
    results: list[RAGameResult] = field(default_factory=list)


def check_library(
    repository,  # LibraryRepository
    api_key: str,
    *,
    cache_dir: Path | None = None,
    progress_cb: Callable[[int, int, str], None] | None = None,
) -> RACheckSummary:
    """Cross-reference library games against the RetroAchievements hash database.

    For each game:
    - If its MD5 is in the RA hash library → "supported"
    - If not → try to find an alternative RA-compatible version by title
    - If alternative exists → "no_support_alternative" (actionable: user can swap)
    - Otherwise → "no_support"
    """
    summary = RACheckSummary()

    with repository.connect() as conn:
        rows = conn.execute(
            "SELECT source_path, original_filename, platform, md5, canonical_title "
            "FROM games WHERE platform != '' AND platform IS NOT NULL"
        ).fetchall()

    summary.total = len(rows)

    # Group by platform so we fetch each console library only once
    by_platform: dict[str, list] = {}
    for row in rows:
        plat = (row["platform"] or "").strip()
        by_platform.setdefault(plat, []).append(row)

    processed = 0
    for plat, games in by_platform.items():
        console_id = get_ra_console_id(plat)

        if console_id is None:
            for row in games:
                processed += 1
                if progress_cb:
                    progress_cb(processed, summary.total, row["original_filename"])
                summary.platform_unknown += 1
                summary.results.append(RAGameResult(
                    source_path=row["source_path"],
                    original_filename=row["original_filename"],
                    platform=plat,
                    our_md5=row["md5"] or "",
                    status="platform_unknown",
                ))
            continue

        # Fetch RA hash library for this console (cached)
        try:
            hash_lib = fetch_hash_library(console_id, api_key, cache_dir=cache_dir)
        except Exception:
            hash_lib = {}

        # Build normalized_title → [RAGame] index for alternative lookup
        title_index: dict[str, list[RAGame]] = {}
        seen_ids: set[int] = set()
        for game in hash_lib.values():
            if game.id not in seen_ids:
                seen_ids.add(game.id)
                key = _normalize_title(game.title)
                title_index.setdefault(key, []).append(game)

        for row in games:
            processed += 1
            if progress_cb:
                progress_cb(processed, summary.total, row["original_filename"])

            md5 = (row["md5"] or "").strip().lower()
            if not md5:
                summary.no_md5 += 1
                summary.results.append(RAGameResult(
                    source_path=row["source_path"],
                    original_filename=row["original_filename"],
                    platform=plat,
                    our_md5="",
                    status="no_md5",
                ))
                continue

            if md5 in hash_lib:
                summary.supported += 1
                summary.results.append(RAGameResult(
                    source_path=row["source_path"],
                    original_filename=row["original_filename"],
                    platform=plat,
                    our_md5=md5,
                    status="supported",
                    alternative=hash_lib[md5],
                ))
            else:
                alt = _find_alternative(
                    row["canonical_title"] or "",
                    row["original_filename"],
                    title_index,
                )
                if alt:
                    summary.no_support_alternative += 1
                    summary.results.append(RAGameResult(
                        source_path=row["source_path"],
                        original_filename=row["original_filename"],
                        platform=plat,
                        our_md5=md5,
                        status="no_support_alternative",
                        alternative=alt,
                    ))
                else:
                    summary.no_support += 1
                    summary.results.append(RAGameResult(
                        source_path=row["source_path"],
                        original_filename=row["original_filename"],
                        platform=plat,
                        our_md5=md5,
                        status="no_support",
                    ))

    return summary


def _normalize_title(title: str) -> str:
    """Normalize a title for fuzzy comparison (strips region/rev tags, punctuation)."""
    t = title.lower()
    t = re.sub(r"\s*\([^)]*\)", "", t)   # remove (USA), (Rev 1), etc.
    t = re.sub(r"\s*\[[^\]]*\]", "", t)   # remove [!], [b], etc.
    t = re.sub(r"[^a-z0-9 ]", " ", t)    # replace punctuation/dashes with space
    t = re.sub(r" +", " ", t).strip()    # collapse multiple spaces
    return t


def _find_alternative(
    canonical_title: str,
    original_filename: str,
    title_index: dict[str, list[RAGame]],
) -> RAGame | None:
    """Return the RA game with the most achievements that matches the title."""
    candidates = None

    if canonical_title:
        key = _normalize_title(canonical_title)
        candidates = title_index.get(key)

    if not candidates:
        # Fallback: try filename stem
        stem = Path(original_filename).stem
        key = _normalize_title(stem)
        candidates = title_index.get(key)

    if not candidates:
        return None
    return max(candidates, key=lambda g: g.achievements)


def to_csv(summary: RACheckSummary) -> str:
    """Export games with no RA support but an existing alternative to CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "platform", "original_filename", "our_md5",
        "ra_game_id", "ra_title", "ra_achievements", "ra_points",
    ])
    for r in summary.results:
        if r.status == "no_support_alternative" and r.alternative:
            writer.writerow([
                r.platform,
                r.original_filename,
                r.our_md5,
                r.alternative.id,
                r.alternative.title,
                r.alternative.achievements,
                r.alternative.points,
            ])
    return buf.getvalue()
