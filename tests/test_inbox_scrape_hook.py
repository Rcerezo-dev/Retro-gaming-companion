"""INBOX-METADATA-INLINE-1: tests for _scrape_organized_games, the opt-in hook
that scrapes metadata for games the Inbox just organized. Isolated from the
full _run_inbox_pipeline (scan/match/rename), which needs a much heavier
fixture — this only covers the scrape-batch logic itself."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from rom_manager.web.inbox_pipeline import _scrape_organized_games


def _config(*, scrape_on_organize: bool, has_credentials: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        inbox=SimpleNamespace(scrape_on_organize=scrape_on_organize),
        credentials=SimpleNamespace(
            screenscraper_user="user" if has_credentials else "",
            screenscraper_pass="pass",
            screenscraper_dev_id="",
            screenscraper_dev_pass="",
        ),
    )


def test_noop_when_opt_in_disabled() -> None:
    with patch("rom_manager.services.scrape_service.scrape_game_metadata") as mocked:
        scraped, errors = _scrape_organized_games(
            [1, 2, 3], _config(scrape_on_organize=False), repository=None
        )

    assert (scraped, errors) == (0, [])
    mocked.assert_not_called()


def test_noop_when_no_games_organized() -> None:
    scraped, errors = _scrape_organized_games([], _config(scrape_on_organize=True), repository=None)

    assert (scraped, errors) == (0, [])


def test_noop_when_no_credentials() -> None:
    with patch("rom_manager.services.scrape_service.scrape_game_metadata") as mocked:
        scraped, errors = _scrape_organized_games(
            [1], _config(scrape_on_organize=True, has_credentials=False), repository=None
        )

    assert (scraped, errors) == (0, [])
    mocked.assert_not_called()


def test_reuses_one_client_across_the_batch() -> None:
    with (
        patch("rom_manager.services.scrape_service.scrape_game_metadata") as mocked,
        patch("rom_manager.scraper.screenscraper.ScreenScraperClient") as ctor,
    ):
        mocked.return_value = {"applied": True}
        _scrape_organized_games([1, 2, 3], _config(scrape_on_organize=True), repository="repo")

    ctor.assert_called_once()  # one client built, not one per game
    assert mocked.call_count == 3
    clients_passed = {call.kwargs["client"] for call in mocked.call_args_list}
    assert len(clients_passed) == 1  # same instance reused for every game


def test_a_failed_lookup_does_not_stop_the_rest_of_the_batch() -> None:
    def _side_effect(game_id, *_args, **_kwargs):
        if game_id == 2:
            return {"error": "network down"}
        return {"applied": True}

    with patch(
        "rom_manager.services.scrape_service.scrape_game_metadata", side_effect=_side_effect
    ):
        scraped, errors = _scrape_organized_games(
            [1, 2, 3], _config(scrape_on_organize=True), repository="repo"
        )

    assert scraped == 2
    assert errors == ["game_id=2: network down"]


def test_progress_callback_gets_index_and_total() -> None:
    calls: list[tuple[int, int]] = []
    with patch(
        "rom_manager.services.scrape_service.scrape_game_metadata", return_value={"applied": True}
    ):
        _scrape_organized_games(
            [10, 20],
            _config(scrape_on_organize=True),
            repository="repo",
            progress_cb=lambda idx, total: calls.append((idx, total)),
        )

    assert calls == [(1, 2), (2, 2)]
