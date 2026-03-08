from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rom_manager.catalog.catalog_loader import CatalogEntry, load_nointro_dat


@dataclass(slots=True)
class MatchResult:
    title: str
    confidence: str  # "high" for SHA1 match
    catalog_source: str  # DAT filename, e.g. "Nintendo - Game Boy (20240101).dat"


class CatalogMatcher:
    """Matches ROM SHA1 hashes against loaded No-Intro and Redump catalogs.

    Catalogs are loaded lazily on the first call to match().
    No-Intro is checked first (cartridges); Redump second (optical discs).
    """

    def __init__(self, nointro_dir: Path, redump_dir: Path) -> None:
        self._nointro_dir = nointro_dir
        self._redump_dir = redump_dir
        self._nointro: dict[str, tuple[CatalogEntry, str]] = {}
        self._redump: dict[str, tuple[CatalogEntry, str]] = {}
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        self._nointro = self._load_dir(self._nointro_dir)
        self._redump = self._load_dir(self._redump_dir)
        self._loaded = True

    @staticmethod
    def _load_dir(directory: Path) -> dict[str, tuple[CatalogEntry, str]]:
        result: dict[str, tuple[CatalogEntry, str]] = {}
        if not directory.exists():
            return result
        for dat_file in sorted(directory.glob("*.dat")):
            try:
                entries = load_nointro_dat(dat_file)
            except Exception:
                continue
            for sha1, entry in entries.items():
                result[sha1] = (entry, dat_file.name)
        return result

    def match(self, sha1: str) -> MatchResult | None:
        """Return a MatchResult for the given SHA1 or None if not found."""
        self._load()
        sha1_upper = sha1.upper()
        for catalog in (self._nointro, self._redump):
            hit = catalog.get(sha1_upper)
            if hit:
                entry, source = hit
                return MatchResult(
                    title=entry.title,
                    confidence="high",
                    catalog_source=source,
                )
        return None

    @property
    def nointro_entries(self) -> int:
        self._load()
        return len(self._nointro)

    @property
    def redump_entries(self) -> int:
        self._load()
        return len(self._redump)
