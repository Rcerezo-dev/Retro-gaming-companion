from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from rom_manager.database.repository import LibraryRepository, MatchedGame
from rom_manager.detection.filename_normalizer import sanitize_filename

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


@dataclass(slots=True)
class RenameOperation:
    game: MatchedGame
    source_path: Path
    target_path: Path
    # "pending" | "already_correct" | "conflict"
    status: str


@dataclass(slots=True)
class RenamePlan:
    pending: list[RenameOperation] = field(default_factory=list)
    already_correct: list[RenameOperation] = field(default_factory=list)
    conflicts: list[RenameOperation] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.pending) + len(self.already_correct) + len(self.conflicts)


def _canonical_filename(game: MatchedGame, opts: FormatOptions | None = None) -> str:
    """Build the target filename applying optional format options."""
    title = game.canonical_title

    if opts is not None:
        if not opts.include_region:
            title = _REGION_RE.sub("", title)
        if not opts.include_revision:
            title = _REVISION_RE.sub("", title)
        title = sanitize_filename(title.strip())

    return title + game.extension


def build_plan(
    repository: LibraryRepository,
    opts: FormatOptions | None = None,
) -> RenamePlan:
    """Generate a rename plan for all matched games.

    A game is 'already_correct' if its filename already matches the canonical title.
    A game is 'conflict' if the target path already exists on disk (and differs from source).
    Otherwise it is 'pending'.
    """
    plan = RenamePlan()

    for game in repository.get_matched_games():
        source = Path(game.source_path)
        new_filename = _canonical_filename(game, opts)
        target = source.parent / new_filename

        if source.name == new_filename:
            plan.already_correct.append(
                RenameOperation(game=game, source_path=source, target_path=target, status="already_correct")
            )
        elif target.exists():
            plan.conflicts.append(
                RenameOperation(game=game, source_path=source, target_path=target, status="conflict")
            )
        else:
            plan.pending.append(
                RenameOperation(game=game, source_path=source, target_path=target, status="pending")
            )

    return plan
