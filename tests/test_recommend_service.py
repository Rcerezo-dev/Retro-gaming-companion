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
