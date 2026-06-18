"""Dataclasses returned by :class:`~rom_manager.database.repository.LibraryRepository`.

Kept in their own module so the per-aggregate mixins can share them without
importing the (assembled) repository class — which would create a cycle.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ScanSummary:
    total_games: int
    total_saves: int
    total_assets: int
    last_scan_at: str | None


@dataclass(slots=True)
class MatchedGame:
    id: int
    original_filename: str
    source_path: str
    platform: str | None
    extension: str
    canonical_title: str
    match_confidence: str
    sha1: str = ""


@dataclass(slots=True)
class DuplicateEntry:
    id: int
    original_filename: str
    source_path: str
    platform: str | None
    canonical_title: str | None
    size_bytes: int


@dataclass(slots=True)
class DuplicateGroup:
    sha1: str
    entries: list[DuplicateEntry]

    @property
    def wasted_bytes(self) -> int:
        """Bytes that could be freed by keeping only one copy."""
        if not self.entries:
            return 0
        return self.entries[0].size_bytes * (len(self.entries) - 1)


@dataclass(slots=True)
class UnresolvedGame:
    original_filename: str
    source_path: str
    platform: str | None
    region: str | None
    sha1: str
