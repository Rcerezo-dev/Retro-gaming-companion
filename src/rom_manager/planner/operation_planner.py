from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from rom_manager.database.repository import LibraryRepository, MatchedGame


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


def _canonical_filename(game: MatchedGame) -> str:
    """Build the target filename: canonical_title + original extension."""
    return game.canonical_title + game.extension


def build_plan(repository: LibraryRepository, *, keep_both: bool = False) -> RenamePlan:
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
        new_filename = _canonical_filename(game)
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

    # Detect plan-level collisions (two pending ops → same target path)
    resolved = resolve(plan.pending, keep_both=keep_both)
    plan.pending = [op for op in resolved if op.status == "pending"]
    plan.conflicts.extend(op for op in resolved if op.status == "conflict")

    return plan
