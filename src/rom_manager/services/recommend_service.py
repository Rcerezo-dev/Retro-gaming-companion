"""MEJ-5: "¿A qué juego hoy?" — recommender v0 (weighted random pick).

No NLP model yet (that's Retro Sage's job — see SAGE-1/2 in the backlog,
still blocked on earlier phases). This is a simple heuristic: favor games
you haven't started, rate highly, or haven't touched in a while. Good enough
to break "which of my thousands of ROMs do I play" paralysis without any
real recommendation infrastructure.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime


def pick_game_for_today(candidates: list[dict], *, now: datetime | None = None) -> dict | None:
    """Weighted-random pick from *candidates* (rows shaped like
    ``LibraryRepository.get_recommendation_candidates()``). ``None`` if empty.

    Weight = pending_bonus * rating_bonus * recency_bonus:
      - pending_bonus: 3x when ``play_status`` is unset (never touched)
      - rating_bonus: ``1 + user_rating`` (0 if unrated) — a 5-star favorite
        gets 6x the weight of an unrated game
      - recency_bonus: 1x for a game played today, up to 3x for one untouched
        for 90+ days (or never played)
    """
    if not candidates:
        return None
    now = now or datetime.now(UTC)
    weights = [_weight(g, now) for g in candidates]
    return random.choices(candidates, weights=weights, k=1)[0]


def _weight(game: dict, now: datetime) -> float:
    pending_bonus = 3.0 if not game.get("play_status") else 1.0
    rating_bonus = 1.0 + (game.get("user_rating") or 0)
    recency_bonus = _recency_bonus(game.get("last_played_at"), now)
    return pending_bonus * rating_bonus * recency_bonus


def _recency_bonus(last_played_at: str | None, now: datetime) -> float:
    if not last_played_at:
        return 3.0  # never played — as "fresh" as it gets
    try:
        played = datetime.fromisoformat(last_played_at)
    except ValueError:
        return 1.0
    if played.tzinfo is None:
        played = played.replace(tzinfo=UTC)
    days = max(0.0, (now - played).total_seconds() / 86400)
    return min(3.0, 1.0 + days / 30.0)
