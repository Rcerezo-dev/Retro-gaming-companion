from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from rom_manager.database.repository import MatchedGame
from rom_manager.planner.operation_planner import build_plan


def _make_game(
    *,
    id: int = 1,
    original_filename: str,
    source_path: str,
    canonical_title: str,
    extension: str = ".gb",
    platform: str | None = "Game Boy",
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


def test_pending_rename(tmp_path: Path) -> None:
    rom = tmp_path / "tetris.gb"
    rom.touch()
    game = _make_game(
        original_filename="tetris.gb",
        source_path=str(rom),
        canonical_title="Tetris (World)",
    )
    plan = build_plan(_repo_with([game]))

    assert len(plan.pending) == 1
    assert plan.pending[0].target_path.name == "Tetris (World).gb"
    assert len(plan.already_correct) == 0
    assert len(plan.conflicts) == 0


def test_already_correct(tmp_path: Path) -> None:
    rom = tmp_path / "Tetris (World).gb"
    rom.touch()
    game = _make_game(
        original_filename="Tetris (World).gb",
        source_path=str(rom),
        canonical_title="Tetris (World)",
    )
    plan = build_plan(_repo_with([game]))

    assert len(plan.already_correct) == 1
    assert len(plan.pending) == 0


def test_conflict_target_exists(tmp_path: Path) -> None:
    rom = tmp_path / "tetris_hack.gb"
    rom.touch()
    (tmp_path / "Tetris (World).gb").touch()  # target already occupied
    game = _make_game(
        original_filename="tetris_hack.gb",
        source_path=str(rom),
        canonical_title="Tetris (World)",
    )
    plan = build_plan(_repo_with([game]))

    assert len(plan.conflicts) == 1
    assert len(plan.pending) == 0


def test_empty_when_no_games() -> None:
    plan = build_plan(_repo_with([]))
    assert plan.total == 0


def test_multidisc_set_does_not_collide(tmp_path: Path) -> None:
    """TABS-FIX-6-DISC: canonical_title identical across discs (DAT has no disc
    number) must not collide — each disc keeps its "(Disc N)" tag from the
    original filename, and the shared game folder stays disc-agnostic."""
    psx_dir = tmp_path / "psx"
    psx_dir.mkdir()
    games = []
    for n in (1, 2, 3):
        src = psx_dir / f"Final Fantasy VII (Disc {n})" / f"Final Fantasy VII (Disc {n}).cue"
        src.parent.mkdir(parents=True)
        src.touch()
        games.append(
            _make_game(
                id=n,
                original_filename=f"Final Fantasy VII (Disc {n}).cue",
                source_path=str(src),
                canonical_title="Final Fantasy VII (Europe)",  # same for all discs, no disc tag
                extension=".cue",
                platform="psx",
            )
        )
    plan = build_plan(_repo_with(games))

    assert len(plan.conflicts) == 0
    assert len(plan.pending) == 3
    filenames = {op.target_path.name for op in plan.pending}
    assert filenames == {
        "Final Fantasy VII (Europe) (Disc 1).cue",
        "Final Fantasy VII (Europe) (Disc 2).cue",
        "Final Fantasy VII (Europe) (Disc 3).cue",
    }
    # All three discs share the same game folder
    folders = {op.target_path.parent.name for op in plan.pending}
    assert folders == {"Final Fantasy VII (Europe)"}


def test_multidisc_set_messy_tags_do_not_collide(tmp_path: Path) -> None:
    """DUP-RA-COLLISION-1: real-world dumps often skip the strict "(Disc N)"
    form No-Intro/Redump uses. ``find_disc_tag`` also recognizes "Disc1"
    (no parens/space) and "cd2" so these don't collide either — the same
    guarantee as the strict-form case in ``test_multidisc_set_does_not_collide``."""
    psx_dir = tmp_path / "psx"
    psx_dir.mkdir()
    names = {1: "Final Fantasy VII Disc1.cue", 2: "Final Fantasy VII-cd2.cue"}
    games = []
    for n, filename in names.items():
        src = psx_dir / filename
        src.touch()
        games.append(
            _make_game(
                id=n,
                original_filename=filename,
                source_path=str(src),
                canonical_title="Final Fantasy VII (Europe)",
                extension=".cue",
                platform="psx",
            )
        )
    plan = build_plan(_repo_with(games))

    assert len(plan.conflicts) == 0
    assert len(plan.pending) == 2
    filenames = {op.target_path.name for op in plan.pending}
    assert filenames == {
        "Final Fantasy VII (Europe) (Disc 1).cue",
        "Final Fantasy VII (Europe) (Disc 2).cue",
    }


def test_mixed_statuses(tmp_path: Path) -> None:
    # pending
    g1_path = tmp_path / "mario.gb"
    g1_path.touch()
    # already correct
    g2_path = tmp_path / "Kirby (USA).gb"
    g2_path.touch()
    # conflict
    g3_path = tmp_path / "zelda_old.gb"
    g3_path.touch()
    (tmp_path / "Zelda (USA).gb").touch()

    games = [
        _make_game(
            id=1,
            original_filename="mario.gb",
            source_path=str(g1_path),
            canonical_title="Super Mario Land (World)",
        ),
        _make_game(
            id=2,
            original_filename="Kirby (USA).gb",
            source_path=str(g2_path),
            canonical_title="Kirby (USA)",
        ),
        _make_game(
            id=3,
            original_filename="zelda_old.gb",
            source_path=str(g3_path),
            canonical_title="Zelda (USA)",
        ),
    ]
    plan = build_plan(_repo_with(games))

    assert len(plan.pending) == 1
    assert len(plan.already_correct) == 1
    assert len(plan.conflicts) == 1
    assert plan.total == 3
