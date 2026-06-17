from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from rom_manager.catalog.catalog_loader import CatalogEntry, load_nointro_dat
from rom_manager.catalog.mame_loader import load_arcade_dir
from rom_manager.detection.filename_normalizer import normalize_for_match

_logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MatchResult:
    title: str
    confidence: str  # "high" | "medium" | "low"
    catalog_source: str  # DAT filename, e.g. "Nintendo - Game Boy (20240101).dat"
    ambiguous: bool = False
    platform: str | None = None  # set by arcade pass ("MAME" or "FBNeo")


class CatalogMatcher:
    """Matches ROM SHA1 hashes (and optionally filenames) against loaded catalogs.

    Strategy
    --------
    1. SHA1 exact lookup → confidence "high".
    2. Filename normalisation lookup (fallback when SHA1 misses):
       - Unique normalised title → confidence "medium".
       - Multiple titles share the same normalised key → confidence "low",
         ``ambiguous=True``, first hit returned.
    3. Arcade stem lookup (MAME/FBNeo): filename stem (without extension) matched
       against the arcade catalog → confidence "medium".

    Catalogs are loaded lazily on the first call to match().
    No-Intro is checked before Redump in both passes.
    """

    def __init__(self, nointro_dir: Path, redump_dir: Path, arcade_dir: Path | None = None) -> None:
        self._nointro_dir = nointro_dir
        self._redump_dir = redump_dir
        self._arcade_dir = arcade_dir
        # SHA1 → (CatalogEntry, dat_filename)
        self._nointro: dict[str, tuple[CatalogEntry, str]] = {}
        self._redump: dict[str, tuple[CatalogEntry, str]] = {}
        # normalized_title → [(CatalogEntry, dat_filename), …]
        self._title_index: dict[str, list[tuple[CatalogEntry, str]]] = {}
        # stem_lowercase → (title, year, manufacturer, source_filename)
        self._arcade: dict[str, tuple[str, str, str, str]] = {}
        self._loaded = False

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self._loaded:
            return
        self._nointro = self._load_dir(self._nointro_dir)
        self._redump = self._load_dir(self._redump_dir)
        self._build_title_index()
        if self._arcade_dir is not None:
            self._arcade = load_arcade_dir(self._arcade_dir)
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
                _logger.warning("Failed to load DAT %s, skipping", dat_file, exc_info=True)
                continue
            for sha1, entry in entries.items():
                result[sha1] = (entry, dat_file.name)
        return result

    def _build_title_index(self) -> None:
        """Build a normalised-title → entries index from both catalogs."""
        index: dict[str, list[tuple[CatalogEntry, str]]] = {}
        for catalog in (self._nointro, self._redump):
            for entry, source in catalog.values():
                key = normalize_for_match(entry.title)
                if not key:
                    continue
                index.setdefault(key, []).append((entry, source))
        self._title_index = index

    # ------------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------------

    def match(self, sha1: str, filename: str | None = None) -> MatchResult | None:
        """Return a MatchResult or None.

        Parameters
        ----------
        sha1:
            SHA1 hash of the ROM (case-insensitive).
        filename:
            Original filename (with or without extension). Used as fallback
            when the SHA1 is not found in any catalog.
        """
        self._load()
        sha1_upper = sha1.upper()

        # Pass 1 — SHA1 exact match (high confidence)
        for catalog in (self._nointro, self._redump):
            hit = catalog.get(sha1_upper)
            if hit:
                entry, source = hit
                return MatchResult(
                    title=entry.title,
                    confidence="high",
                    catalog_source=source,
                )

        if filename is None:
            return None

        # Pass 2 — Name-based fallback (No-Intro / Redump title index)
        key = normalize_for_match(filename)
        if key:
            hits = self._title_index.get(key)
            if hits:
                entry, source = hits[0]
                if len(hits) == 1:
                    return MatchResult(
                        title=entry.title,
                        confidence="medium",
                        catalog_source=source,
                    )
                return MatchResult(
                    title=entry.title,
                    confidence="low",
                    catalog_source=source,
                    ambiguous=True,
                )

        # Pass 3 — Arcade stem lookup (MAME / FBNeo)
        if self._arcade:
            stem = Path(filename).stem.lower()
            arcade_hit = self._arcade.get(stem)
            if arcade_hit:
                title, _year, _mfr, source = arcade_hit
                # Derive platform from which catalog file it came from
                arcade_platform = "MAME" if source.lower().endswith(".xml") else "FBNeo"
                return MatchResult(
                    title=title,
                    confidence="medium",
                    catalog_source=source,
                    platform=arcade_platform,
                )

        return None

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @property
    def nointro_entries(self) -> int:
        self._load()
        return len(self._nointro)

    @property
    def redump_entries(self) -> int:
        self._load()
        return len(self._redump)

    @property
    def arcade_entries(self) -> int:
        self._load()
        return len(self._arcade)
