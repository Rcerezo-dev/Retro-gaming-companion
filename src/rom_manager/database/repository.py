"""SQLite-backed library repository.

The implementation is split across per-aggregate mixins (see
:mod:`rom_manager.database.repositories`); ``LibraryRepository`` only assembles
them on top of ``_RepositoryBase``. The public API and the shared dataclasses
(re-exported below) are unchanged, so callers keep importing them from here.
"""

from __future__ import annotations

from rom_manager.database.repositories.assets import AssetsMixin
from rom_manager.database.repositories.base import _RepositoryBase
from rom_manager.database.repositories.duplicates import DuplicatesMixin
from rom_manager.database.repositories.games import GamesMixin
from rom_manager.database.repositories.metadata import MetadataMixin
from rom_manager.database.repositories.models import (
    DuplicateEntry,
    DuplicateGroup,
    MatchedGame,
    ScanSummary,
    UnresolvedGame,
)
from rom_manager.database.repositories.play_history import PlayHistoryMixin
from rom_manager.database.repositories.sync import SyncMixin

__all__ = [
    "DuplicateEntry",
    "DuplicateGroup",
    "LibraryRepository",
    "MatchedGame",
    "ScanSummary",
    "UnresolvedGame",
]


class LibraryRepository(
    GamesMixin,
    MetadataMixin,
    SyncMixin,
    AssetsMixin,
    DuplicatesMixin,
    PlayHistoryMixin,
    _RepositoryBase,
):
    """Assemble the per-aggregate mixins into the public repository class."""
