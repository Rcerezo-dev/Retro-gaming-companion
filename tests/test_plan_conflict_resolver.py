from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from rom_manager.database.repository import MatchedGame
from rom_manager.planner.operation_planner import RenameOperation, build_plan


def _make_game(
    *,
    id: int = 1,
    original_filename: str,
    source_path: str,
    canonical_title: str,
    extension: str = ".snes",
    platform: str | None = "SNES",
) -> MatchedGame:
    return MatchedGame(
        id=id,
        original_filename=original_filename,
        source_path=source_path,
        platform=platform,
        extension=extension,
        canonical_title=canonical_title,
        match_confidence="high",
    )


def _repo_with(games: list[MatchedGame]) -> MagicMock:
    repo = MagicMock()
    repo.get_matched_games.return_value = games
    return repo


# ---------------------------------------------------------------------------
# resolve() — direct unit tests
# ---------------------------------------------------------------------------


def test_no_collision_unchanged(tmp_path: Path) -> None:
    from rom_manager.planner.conflict_resolver import resolve

    g1 = tmp_path / "mario_hack.snes"
    g1.touch()
    g2 = tmp_path / "zelda_hack.snes"
    g2.touch()

    ops = [
        RenameOperation(
            game=MagicMock(), source_path=g1, target_path=tmp_path / "Mario.snes", status="pending"
        ),
        RenameOperation(
            game=MagicMock(), source_path=g2, target_path=tmp_path / "Zelda.snes", status="pending"
        ),
    ]
    result = resolve(ops)
    assert all(op.status == "pending" for op in result)
    assert result[0].target_path.name == "Mario.snes"
    assert result[1].target_path.name == "Zelda.snes"


def test_collision_marks_both_conflict(tmp_path: Path) -> None:
    from rom_manager.planner.conflict_resolver import resolve

    g1 = tmp_path / "tetris_a.snes"
    g1.touch()
    g2 = tmp_path / "tetris_b.snes"
    g2.touch()
    same_target = tmp_path / "Tetris (World).snes"

    ops = [
        RenameOperation(
            game=MagicMock(), source_path=g1, target_path=same_target, status="pending"
        ),
        RenameOperation(
            game=MagicMock(), source_path=g2, target_path=same_target, status="pending"
        ),
    ]
    result = resolve(ops)
    assert all(op.status == "conflict" for op in result)
    # Target paths remain unchanged in conflict mode
    assert all(op.target_path == same_target for op in result)


def test_keep_both_generates_unique_suffixes(tmp_path: Path) -> None:
    from rom_manager.planner.conflict_resolver import resolve

    g1 = tmp_path / "tetris_a.snes"
    g1.touch()
    g2 = tmp_path / "tetris_b.snes"
    g2.touch()
    same_target = tmp_path / "Tetris (World).snes"

    ops = [
        RenameOperation(
            game=MagicMock(), source_path=g1, target_path=same_target, status="pending"
        ),
        RenameOperation(
            game=MagicMock(), source_path=g2, target_path=same_target, status="pending"
        ),
    ]
    result = resolve(ops, keep_both=True)
    assert all(op.status == "pending" for op in result)
    names = {op.target_path.name for op in result}
    assert names == {"Tetris (World)_1.snes", "Tetris (World)_2.snes"}


def test_three_way_collision_keep_both(tmp_path: Path) -> None:
    from rom_manager.planner.conflict_resolver import resolve

    same_target = tmp_path / "Sonic.smd"
    ops = [
        RenameOperation(
            game=MagicMock(),
            source_path=tmp_path / f"s{i}.smd",
            target_path=same_target,
            status="pending",
        )
        for i in range(3)
    ]
    result = resolve(ops, keep_both=True)
    assert all(op.status == "pending" for op in result)
    names = {op.target_path.name for op in result}
    assert names == {"Sonic_1.smd", "Sonic_2.smd", "Sonic_3.smd"}


# ---------------------------------------------------------------------------
# build_plan() integration
# ---------------------------------------------------------------------------


def test_build_plan_detects_plan_level_conflict(tmp_path: Path) -> None:
    """Two games with the same canonical title → plan-level conflict."""
    g1 = tmp_path / "tetris_dump_a.gb"
    g1.touch()
    g2 = tmp_path / "tetris_dump_b.gb"
    g2.touch()

    games = [
        _make_game(
            id=1,
            original_filename="tetris_dump_a.gb",
            source_path=str(g1),
            canonical_title="Tetris (World)",
            extension=".gb",
            platform="Game Boy",
        ),
        _make_game(
            id=2,
            original_filename="tetris_dump_b.gb",
            source_path=str(g2),
            canonical_title="Tetris (World)",
            extension=".gb",
            platform="Game Boy",
        ),
    ]
    plan = build_plan(_repo_with(games))
    assert len(plan.conflicts) == 2
    assert len(plan.pending) == 0


def test_build_plan_keep_both_no_conflict(tmp_path: Path) -> None:
    """--keep-both resolves the collision without marking conflicts."""
    g1 = tmp_path / "tetris_a.gb"
    g1.touch()
    g2 = tmp_path / "tetris_b.gb"
    g2.touch()

    games = [
        _make_game(
            id=1,
            original_filename="tetris_a.gb",
            source_path=str(g1),
            canonical_title="Tetris (World)",
            extension=".gb",
            platform="Game Boy",
        ),
        _make_game(
            id=2,
            original_filename="tetris_b.gb",
            source_path=str(g2),
            canonical_title="Tetris (World)",
            extension=".gb",
            platform="Game Boy",
        ),
    ]
    plan = build_plan(_repo_with(games), keep_both=True)
    assert len(plan.conflicts) == 0
    assert len(plan.pending) == 2
    names = {op.target_path.name for op in plan.pending}
    assert names == {"Tetris (World)_1.gb", "Tetris (World)_2.gb"}


def test_build_plan_no_collision_unchanged(tmp_path: Path) -> None:
    """Games with distinct canonical titles are not affected by the resolver."""
    g1 = tmp_path / "mario.gb"
    g1.touch()
    g2 = tmp_path / "zelda.gb"
    g2.touch()

    games = [
        _make_game(
            id=1,
            original_filename="mario.gb",
            source_path=str(g1),
            canonical_title="Super Mario Land (World)",
            extension=".gb",
        ),
        _make_game(
            id=2,
            original_filename="zelda.gb",
            source_path=str(g2),
            canonical_title="The Legend of Zelda (USA)",
            extension=".gb",
        ),
    ]
    plan = build_plan(_repo_with(games))
    assert len(plan.pending) == 2
    assert len(plan.conflicts) == 0
