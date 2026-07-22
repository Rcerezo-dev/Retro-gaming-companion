from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from rom_manager.database.repository import LibraryRepository, MatchedGame
from rom_manager.detection.filename_normalizer import sanitize_filename
from rom_manager.utils.paths import same_file as _same_file

# Disc-based platforms where each game gets its own subfolder (e.g. psx/Game/Game.cue).
# Also used as the heuristic to detect whether source is flat (parent.name in this set)
# or already in a subfolder (parent.name not in this set).
_DISC_SUBFOLDER_PLATFORMS: frozenset[str] = frozenset(
    {
        "psx",
        "saturn",
        "ps2",
        "dreamcast",
        "gamecube",
        "wii",
    }
)

# Annotations de región al estilo No-Intro: (USA), (Europe), (World), etc.
_REGION_RE = re.compile(
    r"\s*\((?:USA|Europe|World|Japan|Germany|France|Spain|Italy|Australia|"
    r"Brazil|Korea|China|Netherlands|Sweden|Russia|Canada|Taiwan|"
    r"Asia|Unknown|En|En,Fr|En,Es|En,Fr,De|En,Fr,De,Es)\)",
    re.IGNORECASE,
)

# Annotations de revisión: (Rev 1), (Rev A), (v1.0), (v1.1), etc.
_REVISION_RE = re.compile(r"\s*\((Rev [A-Z0-9]+|v\d[\d.]*)\)", re.IGNORECASE)

# TABS-FIX-6-DISC: tag de disco al estilo No-Intro/Redump, p.ej. "(Disc 2)".
_DISC_TAG_RE = re.compile(r"\(disc\s*\d+\)", re.IGNORECASE)


@dataclass(slots=True)
class FormatOptions:
    include_region: bool = True
    include_revision: bool = True
    include_platform: bool = False
    include_sha: bool = False
    sha_length: int = 8  # chars of SHA1 to append (4–40)


@dataclass(slots=True)
class RenameOperation:
    game: MatchedGame
    source_path: Path
    target_path: Path
    # "pending" | "already_correct" | "conflict"
    status: str
    # "disk" — target file already exists on disk (different file)
    # "collision" — two pending ops share the same target path
    # "" — not a conflict
    conflict_reason: str = ""


@dataclass(slots=True)
class RenamePlan:
    pending: list[RenameOperation] = field(default_factory=list)
    already_correct: list[RenameOperation] = field(default_factory=list)
    conflicts: list[RenameOperation] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.pending) + len(self.already_correct) + len(self.conflicts)


def _canonical_filename(
    game: MatchedGame, opts: FormatOptions | None = None, *, include_disc_tag: bool = True
) -> str:
    """Build the target filename applying optional format options.

    Component order: [platform - ]title[ (Disc N)][ (region)][ (revision)][ [sha]]

    TABS-FIX-6-DISC: No-Intro/Redump often share one canonical_title across
    every disc of a multi-disc set (no disc number in the DAT) — without the
    real "(Disc N)" tag from the source filename, every disc computes the
    same target filename, collides, and "Resolver con RA" can discard Disc
    2/3 thinking they're alternate copies. *include_disc_tag=False* derives
    the shared game *folder* name, which must stay disc-agnostic.
    """
    title = game.canonical_title

    if include_disc_tag and not _DISC_TAG_RE.search(title):
        disc_match = _DISC_TAG_RE.search(game.original_filename)
        if disc_match:
            title = f"{title} {disc_match.group(0)}"

    if opts is not None:
        if not opts.include_region:
            title = _REGION_RE.sub("", title)
        if not opts.include_revision:
            title = _REVISION_RE.sub("", title)
        title = sanitize_filename(title.strip())

        sha_part = f" [{game.sha1[: max(4, min(40, opts.sha_length))]}]" if opts.include_sha else ""
        if opts.include_platform and game.platform:
            title = f"{game.platform} - {title}"

        return title + sha_part + game.extension

    return title + game.extension


def build_plan(
    repository: LibraryRepository,
    opts: FormatOptions | None = None,
    keep_both: bool = False,
) -> RenamePlan:
    """Generate a rename plan for all matched games.

    A game is 'already_correct' if its filename already matches the canonical title.
    A game is 'conflict' if the target path already exists on disk (and differs from
    source) **or** if two pending operations would write to the same target path.
    Otherwise it is 'pending'.

    With *keep_both=True* plan-level collisions are resolved by appending numeric
    suffixes (``_1``, ``_2``, …) instead of marking them as conflicts.
    """
    from rom_manager.planner.collision_resolver import resolve

    plan = RenamePlan()

    for game in repository.get_matched_games():
        source = Path(game.source_path)
        new_filename = _canonical_filename(game, opts)

        # Disc platforms: each game lives in its own subfolder (psx/Game/Game.cue).
        # TABS-FIX-6-DISC: the folder is shared by every disc of a set, so it must
        # be derived disc-agnostic even though new_filename now carries the tag.
        if game.platform and game.platform.lower() in _DISC_SUBFOLDER_PLATFORMS:
            folder_name = Path(_canonical_filename(game, opts, include_disc_tag=False)).stem
            target = (
                source.parent.parent / folder_name / new_filename
                if source.parent.name.lower() not in _DISC_SUBFOLDER_PLATFORMS
                else source.parent / folder_name / new_filename
            )
        else:
            target = source.parent / new_filename

        if source == target:
            plan.already_correct.append(
                RenameOperation(
                    game=game, source_path=source, target_path=target, status="already_correct"
                )
            )
        elif target.exists() and not _same_file(source, target):
            # Target exists and is a *different* file — genuine disk conflict
            plan.conflicts.append(
                RenameOperation(
                    game=game,
                    source_path=source,
                    target_path=target,
                    status="conflict",
                    conflict_reason="disk",
                )
            )
        else:
            # Either target doesn't exist, or it's the same file (case-only rename on Windows)
            plan.pending.append(
                RenameOperation(game=game, source_path=source, target_path=target, status="pending")
            )

    # Detect plan-level collisions (two pending ops → same target path)
    resolved = resolve(plan.pending, keep_both=keep_both)
    plan.pending = [op for op in resolved if op.status == "pending"]
    plan.conflicts.extend(op for op in resolved if op.status == "conflict")

    return plan
