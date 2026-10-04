"""MEJ-5: "¿A qué juego hoy?" recommender v0 — weighted random pick.

No NLP model yet (that's Retro Sage's job); the weighting itself is the
thing worth protecting here, since randomness makes plain equality tests
useless. Statistical assertions over many draws instead.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from rom_manager.services.recommend_service import _recency_bonus, pick_game_for_today


def test_empty_candidates_returns_none() -> None:
    assert pick_game_for_today([]) is None


def test_single_candidate_always_picked() -> None:
    g = {"id": 1, "play_status": None, "user_rating": None, "last_played_at": None}
    assert pick_game_for_today([g]) == g


def test_pending_game_favored_over_recently_played() -> None:
    now = datetime(2026, 7, 23, tzinfo=UTC)
    recent = (now - timedelta(days=1)).isoformat()
    pending = {"id": 1, "play_status": None, "user_rating": None, "last_played_at": None}
    played_recently = {
        "id": 2,
        "play_status": "playing",
        "user_rating": None,
        "last_played_at": recent,
    }

    picks = [pick_game_for_today([pending, played_recently], now=now)["id"] for _ in range(500)]
    # pending: 3.0 (pending) * 1.0 (unrated) * 3.0 (never played) = 9.0
    # played_recently: 1.0 * 1.0 * ~1.03 (played yesterday) ≈ 1.03
    assert picks.count(1) > picks.count(2) * 3


def test_high_rating_increases_odds() -> None:
    now = datetime(2026, 7, 23, tzinfo=UTC)
    unrated = {
        "id": 1,
        "play_status": "playing",
        "user_rating": None,
        "last_played_at": now.isoformat(),
    }
    top_rated = {
        "id": 2,
        "play_status": "playing",
        "user_rating": 5,
        "last_played_at": now.isoformat(),
    }

    picks = [pick_game_for_today([unrated, top_rated], now=now)["id"] for _ in range(500)]
    assert picks.count(2) > picks.count(1) * 3


def test_recency_bonus_caps_at_90_days() -> None:
    now = datetime(2026, 7, 23, tzinfo=UTC)
    ninety_days = (now - timedelta(days=90)).isoformat()
    one_year = (now - timedelta(days=365)).isoformat()
    assert _recency_bonus(ninety_days, now) == 3.0
    assert _recency_bonus(one_year, now) == 3.0


def test_recency_bonus_never_played_is_max() -> None:
    now = datetime(2026, 7, 23, tzinfo=UTC)
    assert _recency_bonus(None, now) == 3.0


def test_recency_bonus_handles_malformed_timestamp() -> None:
    now = datetime(2026, 7, 23, tzinfo=UTC)
    assert _recency_bonus("not-a-date", now) == 1.0


# ── SAGE-4: smart_filter (propuesta A) ───────────────────────────────────────


def _game(i, genre=None, year=None, platform=None, **kw):
    return {
        "id": i,
        "genre": genre,
        "year": year,
        "platform": platform,
        "play_status": None,
        "user_rating": None,
        "last_played_at": None,
        **kw,
    }


def test_smart_filter_ordena_por_coincidencias_y_descarta_las_nulas() -> None:
    from rom_manager.services.recommend_service import smart_filter

    rpg_snes_90 = _game(1, "Role Playing Game", "1995", "SNES")  # 3+2+2
    rpg_gba_00 = _game(2, "Role Playing Game", "2003", "GBA")  # 3
    puzzle_snes_90 = _game(3, "Puzzle", "1994", "SNES")  # 2+2
    racing = _game(4, "Racing, Driving", "2001", "PSX")  # 0 -> fuera
    top = smart_filter(
        [racing, rpg_gba_00, puzzle_snes_90, rpg_snes_90],
        genres=("rpg", "role playing"),
        era="90s",
        platform="snes",
    )
    assert [g["id"] for g in top] == [1, 3, 2]
    assert top[0]["score"] == 7.0


def test_smart_filter_sin_filtros_devuelve_todos_hasta_limit_y_decada() -> None:
    from rom_manager.services.recommend_service import _decade, smart_filter

    assert len(smart_filter([_game(i) for i in range(10)], limit=5)) == 5
    assert (_decade("90s"), _decade("00s"), _decade("1994"), _decade("x")) == (
        1990,
        2000,
        1990,
        None,
    )
