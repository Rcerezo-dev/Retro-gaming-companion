"""Duplicate-detection response builders + RetroAchievements annotation.

Pure functions: typed params → JSON-ready dicts. No global job state.
"""

from __future__ import annotations

import json as _json
import logging
import os as _os
import re
from collections import defaultdict
from pathlib import Path as _Path

from rom_manager.config import AppConfig
from rom_manager.converters.chd_converter import is_broken_cue_set
from rom_manager.database.repository import LibraryRepository
from rom_manager.detection.filename_normalizer import is_non_canonical_variant
from rom_manager.detection.region_parser import parse_region_from_name
from rom_manager.detection.rom_header import extract_internal_id
from rom_manager.utils.disc_tag import (
    find_disc_number,
    normalize_title_cross_format,
)
from rom_manager.utils.paths import is_device_path
from rom_manager.utils.trash import TRASH_DIR_NAME
from rom_manager.web.handlers.system import _ES_PLATFORM_FOLDERS

_logger = logging.getLogger(__name__)

_SPANISH_TAGS = {"spain", "es", "spa", "español", "spanish", "s"}

# MATCH-HEADER-1: NDS/GBA carry a short, globally-unique product code
# (Nintendo-assigned, 4 chars) reliable enough to auto-union without a human
# looking at it first. GB/GBC only have a 16-char *title* field, which two
# genuinely different releases (a sequel, a revision with the distinguishing
# text truncated off) could share on its own — MATCH-FIX-14 combines it with
# the header checksum (folds in cart type/ROM+RAM size/region/version, see
# ``rom_header._read_gb_id``) before trusting it as a union key.
_HEADER_EXTENSIONS = frozenset({".nds", ".gba", ".gb", ".gbc"})

# ANDROID-DUP-1: explicit disc-image format preference for the "which entry
# wins" tiebreak, per DUP-DISC-RA-2's decision ("usa CHD como formato de
# PSX") — a single compact file, native to RetroArch/chdman. `.cue`/`.gdi`
# (needs its `.bin`/track siblings, but is the standard "raw tracks"
# container) ranks second. Legacy CloneCD (`.ccd`, needs its `.img`/`.sub`)
# ranks below that — no tool in this project writes it, it only ever shows
# up as a leftover from before this library existed. Every other extension
# (including single-file cart formats like `.gba`/`.nes`, where no such
# project-level format preference has ever been decided) stays at the
# untouched neutral tier so this never changes their relative order.
_DISC_FORMAT_TIER = {
    ".chd": 0,
    ".cue": 1,
    ".gdi": 1,
    ".ccd": 2,
}

# DUP-DISC-TRACK-1: a loose CD audio track (no ``.cue``/set grouping it with
# its siblings) can be byte-identical — a silent or generic intro/logo
# sting — across two completely unrelated games. Confirmed live (Día68,
# 2026-09-21): "Ninja - Shadow of Darkness (Europe) (Track 44).bin" ==
# "Ultraman Zearth (Japan).bin"; "Nestle Disney Demo (Europe).bin" ==
# "Magical World of Disney...(Track 3).bin". A track-tagged file never
# reliably identifies its game by content alone, so it's excluded from the
# sha1 union entirely rather than trusted as a duplicate signal.
_TRACK_TAG_RE = re.compile(r"\(track\s*\d+\)", re.IGNORECASE)


def _is_loose_track_file(filename: str) -> bool:
    return bool(_TRACK_TAG_RE.search(filename))


def _is_disc_set(members) -> bool:
    """True if the cluster spans more than one distinct disc number of the
    same multi-disc game (e.g. "Final Fantasy VII (Disc 1/2/3).cue") —
    companion discs share the DAT's canonical_title (it doesn't encode the
    disc number) and would otherwise look exactly like a title-duplicate
    cluster (TABS-FIX-6: found by hitting a real PSX library — without this
    guard, "Aplicar recomendación" would discard the other discs as if they
    were alternate copies).

    DUP-CROSSFMT-2: deliberately does NOT require one file per disc number.
    The common real shape is several files sharing a disc number (a
    ``.cue``+``.bin``+``.chd`` of the same disc, or the same disc tracked
    twice) — requiring uniqueness made the guard return False (treated as
    a title/crossfmt duplicate, safe to discard) on exactly the clusters
    that most need protecting: a real ``Disc 1``+``Disc 2`` set where each
    disc also has leftover sibling files. Only a single distinct disc
    number (every member is the same disc in different copies/formats) is
    a genuine duplicate, not a disc set — that case still returns False."""
    # DUP-DISC-SET-1: a member without a parseable disc number (e.g. a
    # single-disc regional edition with no "(Disc N)" tag, like a Japanese
    # release sharing a cluster with a USA "(Disc 1)"/"(Disc 2)" pair) used
    # to zero out the guard entirely — real case: Xenogears (Japan).chd
    # unioned with Xenogears (USA) (Disc 1/2).chd via crossfmt/sha1, and the
    # untagged member made this return False, so "Aplicar recomendación"
    # would have discarded a disc of the USA set. An untagged member is
    # simply excluded from the count instead: the guard now looks only at
    # the members that DO carry a disc tag, and still requires ≥2 distinct
    # numbers among those to call it a real multi-disc set.
    disc_nums = [
        num
        for num in (find_disc_number(r["original_filename"]) for r in members)
        if num is not None
    ]
    return len(set(disc_nums)) > 1


def _sibling_path_str(source_path: str, new_suffix: str) -> str:
    """Swap *source_path*'s extension for *new_suffix* via plain string
    splitting, never :mod:`pathlib`'s parent/name round-trip.

    ``str(Path("/storage/x/foo.bin").parent / "foo.cue")`` on Windows
    renders with backslashes (``WindowsPath`` normalizes the separator on
    ``__str__``), which would never match an ADB-scanned row's
    ``source_path`` again — those are stored exactly as ``adb shell``
    returned them, forward-slash POSIX form. This keeps whatever separator
    style *source_path* already uses.
    """
    last_sep = max(source_path.rfind("/"), source_path.rfind("\\"))
    directory = source_path[: last_sep + 1]
    filename = source_path[last_sep + 1 :]
    stem = filename.rsplit(".", 1)[0] if "." in filename else filename
    return f"{directory}{stem}{new_suffix}"


def _sibling_exists(source_path: str, new_suffix: str, known_paths: frozenset[str] | None) -> bool:
    """True if *source_path*'s sibling (same stem, extension *new_suffix*)
    exists.

    ANDROID-DUP-1: for an ADB-scanned row, ``Path(candidate).exists()`` is
    unconditionally False — it's a POSIX device path, invisible to the PC's
    own filesystem (same reasoning as ``is_device_path``'s docstring). Every
    caller of this went right on treating that as "no sibling", silently
    disabling the whole disc-sibling protection for the Android repo: a
    ``.bin``/``.cue``/``.ccd``/``.img``/``.sub`` from the device always
    looked like an independent, discardable "duplicate format" of its own
    companion. *known_paths* — every ``source_path`` already scanned into
    the same repo, lower-cased — is the actual source of truth for a device
    path; a local PC path keeps using the real filesystem check.
    """
    candidate = _sibling_path_str(source_path, new_suffix)
    if known_paths is not None and is_device_path(source_path):
        return candidate.lower() in known_paths
    return _Path(candidate).exists()


def _is_cue_sibling_bin(source_path: str, known_paths: frozenset[str] | None = None) -> bool:
    """DUP-CROSSFMT-2: True if *source_path* is a ``.bin`` sitting next to a
    ``.cue`` with the same stem — that ``.bin`` is the cue's data file, not
    a self-contained alternate format of the disc. Left in the crossfmt
    union, a ``.cue``+``.bin`` pair with no other copy anywhere else looked
    exactly like two independent duplicate formats of the same disc, and
    "Aplicar recomendación" would discard the ``.cue`` — leaving the ``.bin``
    orphaned and the disc unplayable in most emulators.

    *known_paths*: see ``_sibling_exists`` — required to keep working for an
    Android-scanned ``.bin`` (ANDROID-DUP-1).
    """
    path = _Path(source_path)
    if path.suffix.lower() != ".bin":
        return False
    return _sibling_exists(source_path, ".cue", known_paths)


def _is_ccd_sibling_data(source_path: str, known_paths: frozenset[str] | None = None) -> bool:
    """DUP-CROSSFMT-5: same reasoning as :func:`_is_cue_sibling_bin`, for the
    CloneCD sidecar format — ``.img``/``.sub`` are the ``.ccd``'s own data,
    not an independent copy. Found live in the real library (2026-09-09):
    ``Resident Evil 2 CD1/CD2``, ``Rival Schools Evolution``, ``clocktower2``,
    ``NEW`` all had their ``.img`` recommended for discard while keeping the
    ``.ccd`` that needs it — same failure mode DUP-CROSSFMT-2/3 fixed for
    ``.cue``/``.bin``, never extended to this format.

    *known_paths*: see ``_sibling_exists`` — required to keep working for an
    Android-scanned ``.img``/``.sub`` (ANDROID-DUP-1: confirmed live on the
    RG556, ``Crash Bandicoot [U] [SCUS-94900].ccd/.img/.sub``).
    """
    path = _Path(source_path)
    if path.suffix.lower() not in (".img", ".sub"):
        return False
    return _sibling_exists(source_path, ".ccd", known_paths)


def _is_disc_data_sibling(source_path: str, known_paths: frozenset[str] | None = None) -> bool:
    """True for any sidecar data file (``.cue``'s ``.bin``, ``.ccd``'s
    ``.img``/``.sub``) that must never be unioned/discarded on its own."""
    return _is_cue_sibling_bin(source_path, known_paths) or _is_ccd_sibling_data(
        source_path, known_paths
    )


def _is_spanish_filename(filename: str) -> bool:
    """True if any of *filename*'s parenthetical tags name an exact Spanish release.

    The general review-queue tie-break (sha1/title/crossfmt/header/disk/
    collision reasons) has only ever preferred an exact Spanish release, and
    changing that globally was never asked for. The "region" reason (fuzzy
    cross-region title match, see ``_review_groups_for_repo``) uses the
    user-configurable ``preferred_regions`` ranking instead — see
    ``_review_entry_sort_key``.
    """
    import re as _re

    tags = _re.findall(r"\(([^)]+)\)", filename.lower())
    return any(any(t.strip() in _SPANISH_TAGS for t in tag.split(",")) for tag in tags)


def _in_correct_platform_folder(source_path: str, platform: str | None, library_root) -> bool:
    """True if *source_path* already lives under its platform's canonical folder.

    Same check the misplaced-ROM health-check uses (``handlers/system.py``).
    """
    if not platform or not library_root:
        return False
    slug = _ES_PLATFORM_FOLDERS.get(platform, "")
    if not slug:
        return False
    return source_path.startswith(str(_Path(library_root) / slug))


def _is_broken_disc_entry(source_path: str, known_paths: frozenset[str] | None = None) -> bool:
    """REPAIR-TOOL-4: True if *source_path* is a ``.cue`` that references a
    ``.bin`` missing from disk (or is itself missing).

    Found by hitting a real PSX library: 11 of 31 ``PSX-STRUCTURE-1`` cases had
    ``resolve-duplicates`` keep a broken ``.cue``/``.bin`` set over an intact
    ``.chd`` of another region/dump, purely because the broken side won on
    RA/folder/filename — none of which say anything about whether the file
    actually plays. Deliberately narrow: only a ``.cue`` with a dangling
    reference is flagged. A ``.chd`` is not verified here (would need
    ``chdman``, external to this sort key and not always on PATH — see
    ``verify_chd()`` for that check when actually needed).

    DISC-HEALTH-1: the actual "is this cue broken" check now lives in
    ``converters/chd_converter.py::is_broken_cue_set`` — shared with the
    standalone health report so there's one definition of "broken", not two
    drifting in parallel.

    ANDROID-DUP-1: ``is_broken_cue_set`` reads the ``.cue``'s own text to
    resolve which ``.bin``(s) it references — impossible for an ADB-scanned
    row without pulling the file first. Worse than just failing closed: it
    called ``cue_path.exists()`` first, always False for a device path, so
    every Android ``.cue`` was unconditionally reported "broken" regardless
    of whether its ``.bin`` was sitting right next to it. Falls back to the
    same same-stem-``.bin``-exists heuristic ``_is_cue_sibling_bin`` already
    uses for the sibling check — not a content-accurate "broken" verdict
    (a cue naming a differently-stemmed bin would still pass), but a correct
    "not obviously missing its data" signal without an ADB round-trip just
    to rank a duplicate.
    """
    path = _Path(source_path)
    if path.suffix.lower() != ".cue":
        return False
    if known_paths is not None and is_device_path(source_path):
        return not _sibling_exists(source_path, ".bin", known_paths)
    return is_broken_cue_set(path)


def _find_rescue_candidate_in_trash(
    source_path: str, platform: str | None, library_root
) -> str | None:
    """REPAIR-TOOL-3: before a broken disc set (see ``_is_broken_disc_entry``)
    gets reported as a possible real loss, check whether a healthy copy of
    the same game is already sitting in ``_descartados/`` — discarded by a
    previous ``resolve-duplicates`` run, not gone. Checks both the trash
    folder right next to the broken file and the platform-wide one at the
    platform's canonical folder root. 11 of 31 real ``PSX-STRUCTURE-1`` cases
    had exactly this: a sound `.chd` a ``shutil.move`` away from "lost".

    Deliberately uses the *fuzzy* title normalizer (region/rev tags
    stripped) — unlike the exact-title union in ``_review_groups_for_repo``
    (see its comment on why fuzzy matching is unsafe for clustering "same
    game"), here a different region/edition already discarded is exactly
    the rescue candidate we want to surface, not a false positive to avoid.
    """
    from rom_manager.retroachievements.ra_checker import _normalize_title

    path = _Path(source_path)
    target = _normalize_title(path.stem)
    search_dirs = [path.parent / TRASH_DIR_NAME]
    if library_root and platform:
        slug = _ES_PLATFORM_FOLDERS.get(platform, "")
        if slug:
            search_dirs.append(_Path(library_root) / slug / TRASH_DIR_NAME)

    for trash_dir in search_dirs:
        if not trash_dir.is_dir():
            continue
        for candidate in sorted(trash_dir.iterdir()):
            if not candidate.is_file():
                continue
            if _normalize_title(candidate.stem) != target:
                continue
            if _is_broken_disc_entry(str(candidate)):
                continue
            return str(candidate)
    return None


def _reference_size_bytes(entries: list[dict]) -> int | None:
    """MATCH-FIX-14: the size of a group member the catalog matched with
    `confidence == "high"` (an exact SHA1 hit) — that entry's own size IS the
    DAT's expected size for this release, no separate catalog lookup needed.
    `None` if no member of the group has a high-confidence match."""
    for e in entries:
        if e.get("match_confidence") == "high":
            return e["size_bytes"]
    return None


def _review_entry_sort_key(
    entry: dict,
    platform: str | None = None,
    library_root=None,
    *,
    region_tiebreak: bool = False,
    preferred_regions: tuple[str, ...] = (),
    known_paths: frozenset[str] | None = None,
    reference_size_bytes: int | None = None,
) -> tuple[int, int, int, int, int, int, str]:
    """Recommendation order shared by every reason: intact > catalog size > disc format > RA support > correct folder > Spanish > filename.

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

    INBOX-ORPHAN-4: RA can't hash any disc-image format yet (INBOX-RA-HASH-GAP),
    so both sides of a disc duplicate always tie on ``ra_tier`` and the pick used
    to fall through to whatever order the DB query happened to return — a
    misplaced duplicate could win the tie purely by having a lower row id. A
    duplicate sitting outside its canonical platform folder is almost always the
    stale/misplaced one (INBOX-ORPHAN-3/4 incidents), so that check comes before
    the filename tiebreak.

    REPAIR-TOOL-4: integrity comes before all of the above — a broken
    ``.cue``/``.bin`` set must never be "recommended" over an intact copy just
    because it happens to win the region/RA/folder tiebreaks.

    DUP-REGION-2: *region_tiebreak* (only passed for the "region" reason —
    a fuzzy cross-region title match, see ``_review_groups_for_repo``) ranks
    by the user's own *preferred_regions* priority list (config.duplicates)
    instead of the plain Spanish-only tier every other reason uses — e.g.
    ``["Spain", "Europe"]`` keeps a Spanish release over a European one,
    which in turn beats USA/Japan/other, but still falls back down the list
    when a game has no release in the top region.

    ANDROID-DUP-1: *format_tier* (new) enforces ``DUP-DISC-RA-2``'s decision
    ("usa CHD como formato de PSX") explicitly, instead of leaving it to
    whatever the filename tiebreak happened to prefer alphabetically — which
    picked a raw ``.bin`` over a ``.chd`` of the exact same disc purely
    because "b" sorts before "c". ``known_paths`` (see ``_sibling_exists``)
    is threaded through to ``_is_broken_disc_entry`` so integrity still
    works for an Android-scanned ``.cue``.

    MATCH-FIX-14: *size_tier* — a dump whose size doesn't match the group's
    catalog-verified reference size (see ``_reference_size_bytes``) is a
    strong sign of a bad/incomplete/hacked dump, so it ranks right after
    integrity and before disc format/RA — a size mismatch is itself an
    integrity signal, just one that needs the rest of the group to detect
    (unlike ``_is_broken_disc_entry``, which spots a single broken file on
    its own). A neutral 0 for every entry when the group has no
    high-confidence member to reference against.
    """
    integrity_tier = 1 if _is_broken_disc_entry(entry["source_path"], known_paths) else 0
    size_tier = (
        1 if reference_size_bytes is not None and entry["size_bytes"] != reference_size_bytes else 0
    )
    format_tier = _DISC_FORMAT_TIER.get(_Path(entry["filename"]).suffix.lower(), 1)
    ra_tier = 0 if entry["ra_supported"] else 1
    folder_tier = (
        0 if _in_correct_platform_folder(entry["source_path"], platform, library_root) else 1
    )
    if region_tiebreak and preferred_regions:
        detected = parse_region_from_name(entry["filename"])
        lang_tier = (
            preferred_regions.index(detected)
            if detected in preferred_regions
            else len(preferred_regions)
        )
    else:
        lang_tier = 0 if _is_spanish_filename(entry["filename"]) else 1
    return (
        integrity_tier,
        size_tier,
        format_tier,
        ra_tier,
        folder_tier,
        lang_tier,
        entry["filename"],
    )


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
            "SELECT id, original_filename, source_path, platform, md5, canonical_title,"
            " size_bytes, match_confidence "
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
                "match_confidence": row["match_confidence"],
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

        _lib_root = getattr(config, "library_root", None)
        _ref_size = _reference_size_bytes(annotated)
        annotated.sort(
            key=lambda e: _review_entry_sort_key(
                e, e.get("platform"), _lib_root, reference_size_bytes=_ref_size
            )
        )
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
    share a sha1, a (platform, exact canonical_title), or — DUP-CROSSFMT-1 —
    a (platform, fuzzy cross-format title) across two different extensions.
    Any single link is enough, which is what lets a sha1-identical pair with
    different filenames, a title-only pair with different sha1s, and a
    same-disc-different-container pair (a `.zip` never matched to the same
    canonical_title as its `.chd` counterpart) all surface as one group.
    Plan conflicts (disk/collision) fold into the same clusters when the file
    is already a tracked row, adding their reason without creating a
    duplicate entry.
    """
    from rom_manager.planner.operation_planner import _MULTI_DISC_RISK_PLATFORMS, build_plan
    from rom_manager.retroachievements.ra_checker import _normalize_title

    with repo.connect() as conn:
        rows = conn.execute(
            "SELECT original_filename, source_path, platform, md5, sha1,"
            " canonical_title, size_bytes, match_confidence FROM games WHERE file_type = 'rom'"
        ).fetchall()
    if not rows:
        return []

    # ANDROID-DUP-1: the scanned rows themselves are the only source of
    # truth for "does this sibling exist" on a device path — see
    # _sibling_exists's docstring for why Path.exists() can't answer that.
    known_paths = frozenset(row["source_path"].lower() for row in rows if row["source_path"])

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
        # DUP-CROSSFMT-3/5: a .bin/.img/.sub with a .cue/.ccd sibling is that
        # sibling's own data file, not an independent candidate — see
        # _is_disc_data_sibling's docstring. The crossfmt union below already
        # skipped these; this exact-title union didn't, so a .cue and its
        # own .bin could still land in one cluster (same canonical_title,
        # different sha1) and get sorted against each other, discarding the
        # .cue and orphaning the .bin. Confirmed live: 26 real PSX games hit
        # this in a resolve-duplicates dry run before this fix.
        if _is_disc_data_sibling(row["source_path"], known_paths):
            continue
        if row["sha1"] and not _is_loose_track_file(row["original_filename"]):
            union(idx, first_by_sha1.setdefault(row["sha1"], idx))
        # EXACT canonical_title (not RA's fuzzy normalizer) — same key
        # get_title_duplicate_groups() already used. Tried the fuzzy
        # normalizer first (region tags stripped) to also catch "(USA)" vs
        # "(Europe)" pairs; against a real PSX library it merged 18 distinct
        # regional releases of Final Fantasy VII (different discs, different
        # languages) into a single "duplicate" group — exact match is the
        # only safe union key here, a false negative is far cheaper than a
        # false positive that invites bulk-discarding a legitimate release.
        # CATALOG-MATCH-VARIANT-1: a translation patch/hack/subset must never
        # be treated as interchangeable with the game it's based on, even
        # when it already carries a (possibly stale, pre-fix) canonical_title
        # equal to the original's — see is_non_canonical_variant()'s
        # docstring. Guards here rather than only at match time so already-
        # mismatched rows are protected immediately, without needing a
        # re-match. sha1 union above is untouched: two byte-identical copies
        # of the same hack are still a real duplicate of each other.
        if row["canonical_title"] and not is_non_canonical_variant(row["original_filename"]):
            title_key = (row["platform"] or "unknown", row["canonical_title"])
            union(idx, first_by_title.setdefault(title_key, idx))

    # DUP-CROSSFMT-1: same disc in two different container formats (a `.zip`
    # never matched to a canonical_title the same way a `.chd`/`.bin`/`.cue`
    # of the same content is) — SHA1/canonical_title alone can't catch it,
    # since a different container means different bytes and often no catalog
    # match at all for the zipped side. Union only across *different*
    # extensions sharing the fuzzy cross-format key; same-extension matches
    # are already covered by the sha1/exact-title links above and unioning
    # them here too would just be redundant, not additive.
    crossfmt_groups: dict[tuple[str, str], list[int]] = defaultdict(list)
    for idx, row in enumerate(rows):
        if _is_disc_data_sibling(row["source_path"], known_paths) or is_non_canonical_variant(
            row["original_filename"]
        ):
            continue
        stem = _Path(row["original_filename"]).stem
        cf_title = normalize_title_cross_format(stem)
        if cf_title:
            crossfmt_groups[(row["platform"] or "unknown", cf_title)].append(idx)
    crossfmt_linked_idxs: set[int] = set()
    for idxs in crossfmt_groups.values():
        exts = {_Path(rows[i]["original_filename"]).suffix.lower() for i in idxs}
        if len(exts) < 2:
            continue
        for other in idxs[1:]:
            union(idxs[0], other)
        crossfmt_linked_idxs.update(idxs)

    # DUP-REGION-1/2: same game across regions -- No-Intro's canonical_title
    # keeps the region tag ("... (USA)" vs "... (Europe)"), so the
    # exact-title union above never links them; needs the fuzzy
    # region-stripped normalizer instead. Deliberately excluded on
    # _MULTI_DISC_RISK_PLATFORMS -- the exact-title union's own comment
    # documents why broad fuzzy matching is unsafe there (18 distinct real
    # PSX Final Fantasy VII discs/languages merged into one false-positive
    # group the one time this was tried without that guard). GBA/GB/GBC/NES/
    # SNES/etc. are single-file carts with no disc-number concept, so a
    # fuzzy title match there really does mean "same game, different
    # region/revision release" -- confirmed against the real library
    # (2026-09-15): 94 GBA titles, 188 files, region pairs only, no
    # different-numbered sequel ever merged (e.g. Final Fantasy V/VI Advance
    # stayed in separate groups -- the region tag is always a full trailing
    # "(...)" group, never inside the title itself). DUP-REGION-2: the user
    # can opt out entirely (config.duplicates.keep_both_regions) when they
    # deliberately keep every region of every game -- skip detection rather
    # than detect-and-never-recommend, so those files never show up here at
    # all.
    _dup_cfg = getattr(config, "duplicates", None)
    _keep_both_regions = bool(_dup_cfg.keep_both_regions) if _dup_cfg else False
    _preferred_regions: tuple[str, ...] = (
        tuple(_dup_cfg.preferred_regions) if _dup_cfg else ("Spain", "Europe")
    )
    region_linked_idxs: set[int] = set()
    if not _keep_both_regions:
        region_groups: dict[tuple[str, str], list[int]] = defaultdict(list)
        for idx, row in enumerate(rows):
            plat_lower = (row["platform"] or "").lower()
            if plat_lower in _MULTI_DISC_RISK_PLATFORMS:
                continue
            if _is_disc_data_sibling(row["source_path"], known_paths) or is_non_canonical_variant(
                row["original_filename"]
            ):
                continue
            if not row["canonical_title"]:
                continue
            fuzzy_title = _normalize_title(row["canonical_title"])
            if fuzzy_title:
                region_groups[(row["platform"] or "unknown", fuzzy_title)].append(idx)
        for idxs in region_groups.values():
            if len(idxs) < 2:
                continue
            # Entries that already share the exact canonical_title are the
            # same release (already unioned above) -- only a genuine
            # cross-region link if at least two *different* exact titles are
            # present.
            if len({rows[i]["canonical_title"] for i in idxs}) < 2:
                continue
            for other in idxs[1:]:
                union(idxs[0], other)
            region_linked_idxs.update(idxs)

    # DUP-DISC-RA-1b parte 2: same disc release dumped in different
    # container formats/tools never shares a sha1 (different bytes) and
    # often not even a canonical_title (a legacy CloneCD/serial-named dump
    # rarely catalog-matches) -- but RA's disc hash (boot executable, not
    # file bytes) is identical across containers. Only PSX/GameCube/Wii have
    # a cached hash function today (ra_checker._DISC_HASH_CONSOLE_IDS);
    # Saturn/Dreamcast/PS2 fall through untouched, same as before. Confirmed
    # need: ANDROID-DUP-1's "Crash Bandicoot (USA)" existing as .bin+.cue,
    # .chd, and a legacy CloneCD folder simultaneously -- three sha1s, no
    # shared canonical_title on the CloneCD copy.
    from rom_manager.retroachievements.ra_checker import _DISC_HASH_CONSOLE_IDS
    from rom_manager.retroachievements.ra_disc_hash_cache import (
        get_gamecube_wii_disc_hash,
        get_psx_disc_hash,
    )
    from rom_manager.retroachievements.ra_platform_ids import get_ra_console_id

    disc_hash_linked_idxs: set[int] = set()
    if cache_dir is not None:
        _chdman = getattr(config, "chdman", None) if config else None
        chdman_path = _Path(_chdman) if _chdman else None
        disc_hash_groups: dict[tuple[str, str], list[int]] = defaultdict(list)
        for idx, row in enumerate(rows):
            if _is_disc_data_sibling(row["source_path"], known_paths):
                continue
            console_id = get_ra_console_id(row["platform"] or "")
            if console_id not in _DISC_HASH_CONSOLE_IDS:
                continue
            if console_id == 12:
                disc_hash = get_psx_disc_hash(row["source_path"], cache_dir, chdman_path)
            else:
                disc_hash = get_gamecube_wii_disc_hash(row["source_path"], cache_dir, console_id)
            if disc_hash:
                disc_hash_groups[(row["platform"] or "unknown", disc_hash)].append(idx)
        for idxs in disc_hash_groups.values():
            if len(idxs) < 2:
                continue
            for other in idxs[1:]:
                union(idxs[0], other)
            disc_hash_linked_idxs.update(idxs)

    # MATCH-HEADER-1: No-Intro DATs carry no serial, so a file whose SHA1
    # isn't in the catalog and whose filename doesn't fuzzy-match anything —
    # e.g. a translation patch or a bad/incomplete dump — is invisible to
    # every union above, however clearly it's a copy of a game already in
    # the library. NDS/GBA carts embed Nintendo's globally-unique 4-char
    # game code in the ROM itself — read straight from the file, not
    # guessed from the name. Deliberately NOT skipping
    # is_non_canonical_variant() filenames here (unlike the crossfmt pass
    # above): a hack/translation is exactly the case this is meant to catch
    # and surface for review, not silently ignore. Confirmed live
    # 2026-09-12: a 128 MiB "(BAHAMUT)" translation patch of "Kirby Super
    # Star Ultra (Europe)" had no sha1/title link to the real game at all
    # and never appeared in any group.
    header_groups: dict[tuple[str, str], list[int]] = defaultdict(list)
    for idx, row in enumerate(rows):
        ext = _Path(row["original_filename"]).suffix.lower()
        if ext not in _HEADER_EXTENSIONS:
            continue
        internal_id = extract_internal_id(_Path(row["source_path"]), ext)
        if internal_id:
            header_groups[(row["platform"] or "unknown", internal_id)].append(idx)
    header_linked_idxs: set[int] = set()
    for idxs in header_groups.values():
        if len(idxs) < 2:
            continue
        for other in idxs[1:]:
            union(idxs[0], other)
        header_linked_idxs.update(idxs)

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
        # DUP-DISC-SET-2: computed once and reused below — a real multi-disc
        # set (Disc 1/Disc 2/...) whose cluster also contains a genuine
        # byte-identical duplicate (e.g. a mislabeled regional release) needs
        # different handling than a plain duplicate cluster, see below.
        is_disc_set = _is_disc_set(members)
        has_title_dup = (
            len(distinct_sha1) > 1
            and any(r["canonical_title"] for r in members)
            and not is_disc_set
        )
        # DUP-CROSSFMT-1: only claim it for clusters that actually still span
        # >1 extension AND aren't a legitimate multi-disc set — a crossfmt
        # link into a cluster that turns out to be a real disc set (or that a
        # later sha1/title link already fully explains) shouldn't add a
        # separate, redundant "different format" claim.
        has_crossfmt_dup = (
            any(i in crossfmt_linked_idxs for i in idxs)
            and len({_Path(r["original_filename"]).suffix.lower() for r in members}) > 1
            and not is_disc_set
        )
        # MATCH-HEADER-1: only claim it when the header link actually added
        # something — a cluster already fully explained by sha1 or by two
        # members genuinely sharing the same canonical_title shouldn't get a
        # second, redundant "same internal ID" claim. Deliberately NOT
        # reusing has_title_dup here: it only checks that *some* member has
        # *a* canonical_title, which a header-only link (one matched, one
        # still None) already satisfies without the two ever agreeing on a
        # title — that loose check isn't precise enough to gate this on.
        _title_counts: dict[str, int] = defaultdict(int)
        for r in members:
            if r["canonical_title"]:
                _title_counts[r["canonical_title"]] += 1
        has_real_title_dup = any(c > 1 for c in _title_counts.values())
        has_header_dup = any(i in header_linked_idxs for i in idxs) and not (
            has_sha1_dup or has_real_title_dup
        )
        # DUP-REGION-1: same game, different No-Intro region release -- only
        # claim it for a cluster the fuzzy region_groups link actually built
        # (real disc sets are pre-excluded when region_linked_idxs is built).
        has_region_dup = any(i in region_linked_idxs for i in idxs) and not is_disc_set
        # DUP-DISC-RA-1b parte 2: only claim it for a cluster the disc-hash
        # link actually built and that isn't already a legitimate multi-disc
        # set (a real 2-disc release also shares... nothing here, since each
        # disc has its own distinct RA hash -- _is_disc_set stays as a
        # defensive match with the other reasons' pattern).
        has_disc_hash_dup = any(i in disc_hash_linked_idxs for i in idxs) and not is_disc_set

        plat = next((r["platform"] for r in members if r["platform"]), None) or "unknown"
        # MATCH-FIX-4: RA hash libraries are per-console (Game Boy and Game
        # Boy Color are different consoles with different hashes even for a
        # byte-identical ROM), so each row must be scored against its own
        # platform's cache — a shared group-level `plat` blinded every
        # member but the first to its own RA support in cross-platform
        # (same-content) groups. Confirmed live: 3 GB/GBC groups where the
        # correctly-named .gbc copy lost the discard tiebreak to a bulk-pack
        # .gb duplicate because its real achievements were looked up in the
        # wrong console's cache.
        scored = []
        for r in members:
            md5_lower = (r["md5"] or "").lower()
            if not md5_lower or not cache_dir:
                scored.append(-1)
                continue
            row_hash_map = _load_ra_hash_map(cache_dir, r["platform"] or plat, hash_cache)
            scored.append(row_hash_map.get(md5_lower, -1))
        has_ra_mix = any(a > 0 for a in scored) and any(a <= 0 for a in scored)
        score_by_idx = dict(zip(idxs, scored, strict=True))

        def emit_group(
            group_idxs: list[int], group_reasons: set[str], key_suffix: str = ""
        ) -> None:
            sample_title = next(
                (rows[i]["canonical_title"] for i in group_idxs if rows[i]["canonical_title"]),
                rows[group_idxs[0]]["original_filename"],
            )
            group_key = f"{plat}::{_normalize_title(sample_title)}{key_suffix}"
            if group_key in excluded_keys:
                return

            entries: dict[str, dict] = {}
            for idx in group_idxs:
                r = rows[idx]
                achievements = score_by_idx.get(idx, -1)
                entry = {
                    "source_path": r["source_path"],
                    "filename": r["original_filename"],
                    "size_bytes": int(r["size_bytes"]),
                    "sha1": r["sha1"],
                    "match_confidence": r["match_confidence"],
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
            _lib_root = getattr(config, "library_root", None)
            _region_tiebreak = "region" in group_reasons
            _ref_size = _reference_size_bytes(entries_list)
            entries_list.sort(
                key=lambda e: _review_entry_sort_key(
                    e,
                    plat,
                    _lib_root,
                    region_tiebreak=_region_tiebreak,
                    preferred_regions=_preferred_regions,
                    known_paths=known_paths,
                    reference_size_bytes=_ref_size,
                )
            )
            for i, entry in enumerate(entries_list):
                entry["recommended"] = i == 0
                if _is_broken_disc_entry(entry["source_path"]):
                    entry["rescue_candidate"] = _find_rescue_candidate_in_trash(
                        entry["source_path"], plat, _lib_root
                    )
            wasted = sum(e["size_bytes"] or 0 for e in entries_list[1:])
            result.append(
                {
                    "platform": plat,
                    "canonical_title": sample_title,
                    "group_key": group_key,
                    "reasons": sorted(group_reasons),
                    "wasted_bytes": wasted,
                    "entries": entries_list,
                }
            )

        if is_disc_set and has_sha1_dup:
            # DUP-DISC-SET-2: a real multi-disc set (>=2 distinct disc
            # numbers) whose cluster also contains a genuine byte-identical
            # duplicate (e.g. a mislabeled regional release sharing sha1 with
            # one specific disc) must never let the whole cluster compete as
            # one group -- that picks a single "recommended" survivor and
            # discards every other disc as if it were an alternate copy.
            # Confirmed live: Xenogears (Japan).chd == (USA) (Disc 1).chd by
            # sha1, but (USA) (Disc 2).chd is a real, undupe'd disc that the
            # old single-group logic still marked "descartar". Instead, only
            # the actual sha1-duplicate subsets become their own review
            # group; a disc with a unique sha1 in the cluster is a genuine,
            # non-duplicate file and never enters any group at all.
            dup_sha1_idxs: dict[str, list[int]] = defaultdict(list)
            for i in idxs:
                s = rows[i]["sha1"]
                if s:
                    dup_sha1_idxs[s].append(i)
            for sha1_val, sub_idxs in dup_sha1_idxs.items():
                if len(sub_idxs) < 2:
                    continue
                sub_reasons: set[str] = {"sha1"}
                for i in sub_idxs:
                    if i in extra_reasons:
                        sub_reasons.add(extra_reasons[i])
                if (
                    sub_reasons & {"disk", "collision"}
                    and plat.lower() in _MULTI_DISC_RISK_PLATFORMS
                ):
                    sub_reasons.add("multi_disc_risk")
                emit_group(sub_idxs, sub_reasons, key_suffix=f"#{sha1_val[:8]}")
            continue

        reasons: set[str] = set()
        if has_sha1_dup:
            reasons.add("sha1")
        if has_title_dup:
            reasons.add("title")
        if has_ra_mix:
            reasons.add("ra")
        if has_crossfmt_dup:
            reasons.add("crossfmt")
        if has_header_dup:
            reasons.add("header")
        if has_region_dup:
            reasons.add("region")
        if has_disc_hash_dup:
            reasons.add("disc_hash")
        for idx in idxs:
            if idx in extra_reasons:
                reasons.add(extra_reasons[idx])
        # GAMECUBE-DISC-BUG-1a/1d/UX: a "disk"/"collision" conflict on a
        # platform that can have real multi-disc sets (PSX/PS2/Saturn/
        # Dreamcast/GameCube/Wii) is never auto-resolved by apply_ra_conflicts
        # (see ra_duplicates_service.py) — flag it here too so the UI can show
        # a "posible multi-disco" explanation instead of a plain conflict.
        if reasons & {"disk", "collision"} and plat.lower() in _MULTI_DISC_RISK_PLATFORMS:
            reasons.add("multi_disc_risk")
        if not reasons:
            # United by a coincidental title/sha1 match but nothing actually
            # duplicated (e.g. two unmatched files with the same filename stem
            # and no other signal) — don't invent a false positive.
            continue

        emit_group(idxs, reasons)

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
