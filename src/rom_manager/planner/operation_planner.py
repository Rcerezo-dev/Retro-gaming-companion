from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from rom_manager.database.repository import LibraryRepository, MatchedGame
from rom_manager.detection.filename_normalizer import sanitize_filename

def _same_file(a: Path, b: Path) -> bool:
    """Return True if *a* and *b* refer to the same file on disk.

    On Windows (case-insensitive FS) ``Path("game.gba").exists()`` returns
    True even when ``Path("Game.gba")`` is the only file, so we must
    distinguish a *case-only* rename from a true conflict.
    """
    try:
        return a.samefile(b)
    except OSError:
        return False


# Annotations de región al estilo No-Intro: (USA), (Europe), (World), etc.
_REGION_RE = re.compile(
    r"\s*\((?:USA|Europe|World|Japan|Germany|France|Spain|Italy|Australia|"
    r"Brazil|Korea|China|Netherlands|Sweden|Russia|Canada|Taiwan|"
    r"Asia|Unknown|En|En,Fr|En,Es|En,Fr,De|En,Fr,De,Es)\)",
    re.IGNORECASE,
)

# Annotations de revisión: (Rev 1), (Rev A), (v1.0), (v1.1), etc.
_REVISION_RE = re.compile(r"\s*\((Rev [A-Z0-9]+|v\d[\d.]*)\)", re.IGNORECASE)


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


def _canonical_filename(game: MatchedGame, opts: FormatOptions | None = None) -> str:
    """Build the target filename applying optional format options.

    Component order: [platform - ]title[ (region)][ (revision)][ [sha]]
    """
    title = game.canonical_title

    if opts is not None:
        if not opts.include_region:
            title = _REGION_RE.sub("", title)
        if not opts.include_revision:
            title = _REVISION_RE.sub("", title)
        title = sanitize_filename(title.strip())

        sha_part = f" [{game.sha1[:max(4, min(40, opts.sha_length))]}]" if opts.include_sha else ""
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
    from rom_manager.planner.conflict_resolver import resolve

    plan = RenamePlan()

    for game in repository.get_matched_games():
        source = Path(game.source_path)
        new_filename = _canonical_filename(game, opts)
        target = source.parent / new_filename

        if source.name == new_filename:
            plan.already_correct.append(
                RenameOperation(game=game, source_path=source, target_path=target, status="already_correct")
            )
        elif target.exists() and not _same_file(source, target):
            # Target exists and is a *different* file — genuine disk conflict
            plan.conflicts.append(
                RenameOperation(game=game, source_path=source, target_path=target, status="conflict", conflict_reason="disk")
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
