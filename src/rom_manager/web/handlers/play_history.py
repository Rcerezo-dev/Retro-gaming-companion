from __future__ import annotations

import json
import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.router import Router


# ── Public entry point ────────────────────────────────────────────────────────

# In-memory recommendations store (replaced on each POST from NLP model)
_recommendations: dict = {"items": [], "updated_at": None}


def register(
    router: "Router",
    *,
    repository: "LibraryRepository",
) -> None:
    """Register play-history CRUD routes on *router*."""

    # ── GET /api/play-history ─────────────────────────────────────────────────
    @router.get("/api/play-history")
    def get_play_history(ctx) -> None:
        """Return all games that have any play data or a user rating."""
        with repository.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    g.id,
                    g.canonical_title,
                    g.original_filename,
                    g.platform,
                    g.play_status,
                    g.play_count,
                    g.first_played_at,
                    g.last_played_at,
                    g.user_rating,
                    g.notes,
                    gm.genre,
                    gm.year,
                    gm.description
                FROM games g
                LEFT JOIN game_metadata gm ON gm.game_id = g.id
                WHERE g.play_count > 0
                   OR g.user_rating IS NOT NULL
                   OR g.play_status IS NOT NULL
                ORDER BY g.last_played_at DESC NULLS LAST
                """
            ).fetchall()

        games = []
        for row in rows:
            games.append({
                "id":              row["id"],
                "title":           row["canonical_title"] or row["original_filename"],
                "platform":        row["platform"],
                "play_status":     row["play_status"],
                "play_count":      row["play_count"] or 0,
                "first_played_at": row["first_played_at"],
                "last_played_at":  row["last_played_at"],
                "user_rating":     row["user_rating"],
                "notes":           row["notes"],
                "genre":           row["genre"],
                "year":            row["year"],
                "description":     row["description"],
            })

        ctx._send_json({"games": games, "total": len(games)})

    # ── POST /api/play-history ────────────────────────────────────────────────
    @router.post("/api/play-history")
    def update_play_history(ctx) -> None:
        """Update play metadata for a single game.

        Body (JSON):
            game_id    int   required
            rating     int   1-5 | null  (user_rating)
            status     str   played | completed | abandoned | null
            notes      str   free text | null
            tags       list  list of tag strings (replaces existing tags)
        """
        data: dict = getattr(ctx, "_post_data", {})

        game_id = data.get("game_id")
        if not isinstance(game_id, int):
            ctx._send_json({"error": "game_id (int) requerido"})
            return

        rating = data.get("rating")
        if rating is not None and rating not in (1, 2, 3, 4, 5):
            ctx._send_json({"error": "rating debe ser 1-5 o null"})
            return

        status = data.get("status")
        valid_statuses = {None, "played", "completed", "abandoned"}
        if status not in valid_statuses:
            ctx._send_json({"error": f"status debe ser uno de {sorted(s for s in valid_statuses if s)}"})
            return

        notes = data.get("notes")
        tags = data.get("tags")  # list[str] | None

        with repository.connect() as conn:
            # Verify game exists
            row = conn.execute("SELECT id FROM games WHERE id = ?", (game_id,)).fetchone()
            if row is None:
                ctx._send_json({"error": "Juego no encontrado"})
                return

            conn.execute(
                """
                UPDATE games
                SET user_rating = ?,
                    play_status = ?,
                    notes       = ?
                WHERE id = ?
                """,
                (rating, status, notes, game_id),
            )

            if tags is not None:
                # Replace all tags for this game
                conn.execute("DELETE FROM game_tags WHERE game_id = ?", (game_id,))
                for tag in tags:
                    tag = str(tag).strip()
                    if tag:
                        conn.execute(
                            "INSERT OR IGNORE INTO game_tags (game_id, tag) VALUES (?, ?)",
                            (game_id, tag),
                        )

            conn.commit()

        ctx._send_json({"ok": True})

    # ── GET /api/export-history ───────────────────────────────────────────────
    @router.get("/api/export-history")
    def export_history(ctx) -> None:
        """Export full game library + play/rating data as JSON for the NLP recommender.

        Includes ALL ROMs (played and unplayed) so the model can recommend
        from the unplayed set. Fields:
            id, title, platform, genre, year, developer, publisher, description,
            play_count, first_played_at, last_played_at, play_status,
            user_rating, tags, notes
        exported_at: ISO timestamp of export.
        """
        with repository.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    g.id,
                    COALESCE(g.canonical_title, g.original_filename) AS title,
                    g.platform,
                    g.play_status,
                    g.play_count,
                    g.first_played_at,
                    g.last_played_at,
                    g.user_rating,
                    g.notes,
                    gm.genre,
                    gm.year,
                    gm.developer,
                    gm.publisher,
                    gm.description
                FROM games g
                LEFT JOIN game_metadata gm ON gm.game_id = g.id
                WHERE g.file_type = 'rom'
                ORDER BY g.platform, title
                """
            ).fetchall()

            # Fetch all tags in one query — avoids N+1
            tag_rows = conn.execute(
                "SELECT game_id, tag FROM game_tags ORDER BY game_id, tag"
            ).fetchall()

        tags_by_game: dict[int, list[str]] = {}
        for tr in tag_rows:
            tags_by_game.setdefault(tr["game_id"], []).append(tr["tag"])

        games = []
        for row in rows:
            gid = row["id"]
            games.append({
                "id":              gid,
                "title":           row["title"],
                "platform":        row["platform"],
                "genre":           row["genre"],
                "year":            row["year"],
                "developer":       row["developer"],
                "publisher":       row["publisher"],
                "description":     row["description"],
                "play_count":      row["play_count"] or 0,
                "first_played_at": row["first_played_at"],
                "last_played_at":  row["last_played_at"],
                "play_status":     row["play_status"],
                "user_rating":     row["user_rating"],
                "tags":            tags_by_game.get(gid, []),
                "notes":           row["notes"],
            })

        payload = {
            "exported_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total": len(games),
            "games": games,
        }

        # Send as downloadable file
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        ctx._send(200, "application/json; charset=utf-8", body)

    # ── GET /api/recommendations ──────────────────────────────────────────────
    @router.get("/api/recommendations")
    def get_recommendations(ctx) -> None:
        """Return the current in-memory recommendation list with full game data."""
        items = _recommendations["items"]
        if not items:
            ctx._send_json({"items": [], "updated_at": None})
            return

        # Enrich with DB data for any items that only carry an id
        game_ids = [it["id"] for it in items if isinstance(it.get("id"), int)]
        games_by_id: dict[int, dict] = {}
        if game_ids:
            placeholders = ",".join("?" * len(game_ids))
            with repository.connect() as conn:
                rows = conn.execute(
                    f"""
                    SELECT g.id,
                           COALESCE(g.canonical_title, g.original_filename) AS title,
                           g.platform, gm.genre, gm.year, gm.box_art_path
                    FROM games g
                    LEFT JOIN game_metadata gm ON gm.game_id = g.id
                    WHERE g.id IN ({placeholders})
                    """,
                    game_ids,
                ).fetchall()
            games_by_id = {row["id"]: dict(row) for row in rows}

        enriched = []
        for it in items:
            gid = it.get("id")
            base = games_by_id.get(gid, {}) if isinstance(gid, int) else {}
            enriched.append({
                "id":       gid,
                "title":    it.get("title") or base.get("title"),
                "platform": it.get("platform") or base.get("platform"),
                "genre":    it.get("genre") or base.get("genre"),
                "year":     it.get("year") or base.get("year"),
                "score":    it.get("score"),
                "reason":   it.get("reason"),
            })

        ctx._send_json({"items": enriched, "updated_at": _recommendations["updated_at"]})

    # ── POST /api/recommendations ─────────────────────────────────────────────
    @router.post("/api/recommendations")
    def post_recommendations(ctx) -> None:
        """Receive recommendations from the NLP model and store in memory.

        Body (JSON):
            items  list  required — each item:
                id       int    game id in the local DB (optional if title given)
                title    str    game title (fallback if id unknown)
                platform str
                score    float  0-1 confidence score
                reason   str    human-readable explanation
        """
        data: dict = getattr(ctx, "_post_data", {})
        items = data.get("items")
        if not isinstance(items, list):
            ctx._send_json({"error": "items (list) requerido"})
            return

        _recommendations["items"] = items[:50]  # cap at 50
        _recommendations["updated_at"] = datetime.datetime.now(
            datetime.timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        ctx._send_json({"ok": True, "stored": len(_recommendations["items"])})
