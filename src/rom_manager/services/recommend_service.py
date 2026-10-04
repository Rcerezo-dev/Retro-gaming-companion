"""MEJ-5: "¿A qué juego hoy?" — recommender v0 (weighted random pick).

No NLP model yet (that's Retro Sage's job — see SAGE-1/2 in the backlog,
still blocked on earlier phases). This is a simple heuristic: favor games
you haven't started, rate highly, or haven't touched in a while. Good enough
to break "which of my thousands of ROMs do I play" paralysis without any
real recommendation infrastructure.
"""

from __future__ import annotations

import random
import re
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


# SAGE-4 (propuesta A, sin ML): "¿qué quiero jugar hoy?" por preferencias marcadas.
# ponytail: sin filtro de nº de jugadores -- game_metadata.players casi vacío
# (solo se rellena al re-scrapear, SAGE-2); añadirlo cuando haya datos. Sin
# propuesta C (perfil desde favoritos): hoy 0 favoritos/valoraciones en la BD.
_W_GENRE, _W_ERA, _W_PLATFORM = 3.0, 2.0, 2.0


def smart_filter(
    games: list[dict],
    *,
    genres: tuple[str, ...] = (),
    era: str | None = None,
    platform: str | None = None,
    limit: int = 5,
    now: datetime | None = None,
) -> list[dict]:
    """Top *limit* de *games* por coincidencia con las preferencias.

    score = suma de pesos de lo que coincide (género 3, década 2, plataforma 2).
    Un juego sin ninguna coincidencia se descarta si hay algún filtro; el
    empate se rompe con el ``_weight`` de MEJ-5 (pendiente/valoración/recencia).
    ``era``: "80s", "90s"... o "1990s"; ``genres`` por subcadena sin mayúsculas.
    """
    now = now or datetime.now(UTC)
    wanted = tuple(g.lower() for g in genres if g)
    decade = _decade(era)
    scored: list[tuple[float, float, dict]] = []
    for g in games:
        score = 0.0
        genre = (g.get("genre") or "").lower()
        if wanted and any(w in genre for w in wanted):
            score += _W_GENRE
        if decade is not None and _decade(g.get("year")) == decade:
            score += _W_ERA
        if platform and (g.get("platform") or "").lower() == platform.lower():
            score += _W_PLATFORM
        if score == 0 and (wanted or decade is not None or platform):
            continue
        scored.append((score, _weight(g, now), g))
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [dict(g, score=score) for score, _, g in scored[:limit]]


def _decade(value: str | None) -> int | None:
    """ "90s"/"1990s"/"1994" -> 1990; ``None`` si no se entiende."""
    m = re.match(r"\s*(\d{2,4})", value or "")
    if not m:
        return None
    n = int(m.group(1))
    if n < 100:  # "90s" -> 1990, "00s" -> 2000
        n += 1900 if n >= 50 else 2000
    return n // 10 * 10
