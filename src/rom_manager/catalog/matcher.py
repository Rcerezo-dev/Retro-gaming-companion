from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from rom_manager.catalog.catalog_loader import CatalogEntry, load_dat_file
from rom_manager.catalog.mame_loader import load_arcade_dir
from rom_manager.detection.filename_normalizer import normalize_for_match
from rom_manager.detection.platform_detector import PLATFORM_BY_EXTENSION, detect_platform
from rom_manager.retroachievements.ra_hash_psx import detect_psx_boot_serial
from rom_manager.utils.disc_tag import find_disc_number

_NON_ALNUM_RE = re.compile(r"[^A-Z0-9]")


def _normalize_serial(serial: str) -> str:
    return _NON_ALNUM_RE.sub("", serial.upper())

_logger = logging.getLogger(__name__)

# INBOX-FIX-2: No-Intro/Redump DAT filenames ("Nintendo - Super Nintendo
# Entertainment System (...).dat") don't match RetroArch folder-name tokens
# (platforms.toml's [folders] table), so a match never used to populate
# games.platform. Ordered most-specific-first so e.g. "game boy advance" is
# tried before the "game boy" substring it contains. Values are canonical
# names from web/handlers/system.py::_ES_PLATFORM_FOLDERS — only platforms
# this project actually routes to a folder are worth mapping here.
_DAT_PLATFORM_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("super nintendo entertainment system", "SNES"),
    ("nintendo entertainment system", "NES"),
    ("game boy advance", "Game Boy Advance"),
    ("game boy color", "Game Boy Color"),
    ("game boy", "Game Boy"),
    ("new nintendo 3ds", "Nintendo 3DS"),
    ("nintendo 3ds", "Nintendo 3DS"),
    ("nintendo 64", "Nintendo 64"),
    ("nintendo ds", "Nintendo DS"),
    ("family computer disk system", "Famicom Disk System"),
    ("gamecube", "GameCube"),
    ("nintendo - wii", "Wii"),
    ("playstation 2", "PlayStation 2"),
    ("playstation 3", "PlayStation 3"),
    ("playstation portable", "PSP"),
    ("playstation vita", "PS Vita"),
    ("playstation", "PlayStation"),
    ("mega drive", "Sega Mega Drive"),
    ("genesis", "Sega Mega Drive"),
    ("master system", "Master System"),
    ("game gear", "Game Gear"),
    ("32x", "Sega 32X"),
    ("dreamcast", "Dreamcast"),
    ("saturn", "Sega Saturn"),
    ("mega-cd", "Sega CD"),
    ("mega cd", "Sega CD"),
    ("sega cd", "Sega CD"),
    ("pc engine", "PC Engine"),
    ("turbografx", "PC Engine"),
    ("neo geo pocket", "Neo Geo Pocket Color"),
    ("neo geo", "Neo Geo"),
    ("wonderswan color", "WonderSwan Color"),
    ("wonderswan", "WonderSwan"),
    ("atari 2600", "Atari 2600"),
    ("atari 5200", "Atari 5200"),
    ("atari 7800", "Atari 7800"),
    ("atari lynx", "Atari Lynx"),
    ("atari jaguar", "Atari Jaguar"),
    ("atari st", "Atari ST"),
    ("amiga", "Amiga"),
    ("commodore 64", "Commodore 64"),
    ("zx spectrum", "ZX Spectrum"),
    ("msx", "MSX"),
    ("colecovision", "ColecoVision"),
    ("intellivision", "Intellivision"),
)


def _platform_from_dat_name(dat_filename: str) -> str | None:
    """Derive a canonical platform name from a No-Intro/Redump DAT filename."""
    lowered = dat_filename.lower()
    for keyword, platform in _DAT_PLATFORM_KEYWORDS:
        if keyword in lowered:
            return platform
    return None


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

    MATCH-FIX-1: for ``.zip`` filenames without a "(Region)" tag (MAME-style
    set names) pass 3 runs *before* pass 2 — the title fallback used to grab
    absurd cross-platform matches for those and the arcade pass never ran.

    Catalogs are loaded lazily on the first call to match().
    No-Intro is checked before Redump in both passes.
    """

    def __init__(
        self,
        nointro_dir: Path,
        redump_dir: Path,
        arcade_dir: Path | None = None,
        chdman_path: Path | None = None,
    ) -> None:
        self._nointro_dir = nointro_dir
        self._redump_dir = redump_dir
        self._arcade_dir = arcade_dir
        # CATALOG-MATCH-REGION-1: needed to extract a .chd's boot serial for
        # PSX region disambiguation in _match_by_title(). None just disables it.
        self._chdman_path = chdman_path
        # SHA1 → (CatalogEntry, dat_filename)
        self._nointro: dict[str, tuple[CatalogEntry, str]] = {}
        self._redump: dict[str, tuple[CatalogEntry, str]] = {}
        # normalized_title → [(CatalogEntry, dat_filename), …]
        self._title_index: dict[str, list[tuple[CatalogEntry, str]]] = {}
        # stem_lowercase → (title, year, manufacturer, source_filename)
        self._arcade: dict[str, tuple[str, str, str, str]] = {}
        # crc32_upper → (title, dat_source, platform) — construido bajo demanda
        self._crc: dict[str, tuple[str, str, str | None]] | None = None
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
                # CATALOG-MATCH-BUG-1: load_dat_file() auto-detecta XML vs
                # clrmamepro (texto plano) — load_nointro_dat() a secas solo
                # sabe XML y descartaba en silencio cualquier DAT clrmamepro
                # (21/271 nointro, 9/22 redump en la biblioteca real,
                # incluyendo Game Boy/GBA/NES/SNES/PS1/PS2/GameCube/Wii...),
                # degradando el match SHA1 exacto a un fallback por título
                # mucho menos fiable para esas plataformas.
                entries = load_dat_file(dat_file)
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

    def crc_index(self) -> dict[str, tuple[str, str, str | None]]:
        """CRC32 → (title, dat_source, platform) de No-Intro + Redump (ZIP-ROUTE-1).

        El header de un ZIP ya trae el CRC32 de cada entrada, así que este
        índice identifica ROMs comprimidos sin descomprimirlos. Un CRC
        reclamado por dos entradas con título distinto (p. ej. DATs
        recopilatorios como Evercade re-listando ROMs de Atari 2600) se
        descarta como ambiguo: nunca adivinar.
        """
        self._load()
        if self._crc is None:
            index: dict[str, tuple[str, str, str | None]] = {}
            ambiguous: set[str] = set()
            for catalog in (self._nointro, self._redump):
                for entry, source in catalog.values():
                    crc = entry.crc32.upper()
                    if not crc or crc in ambiguous:
                        continue
                    prev = index.get(crc)
                    if prev is None:
                        index[crc] = (entry.title, source, _platform_from_dat_name(source))
                    elif prev[0] != entry.title:
                        ambiguous.add(crc)
                        del index[crc]
            self._crc = index
        return self._crc

    # ------------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------------

    def match(
        self, sha1: str, filename: str | None = None, source_path: str | None = None
    ) -> MatchResult | None:
        """Return a MatchResult or None.

        Parameters
        ----------
        sha1:
            SHA1 hash of the ROM (case-insensitive).
        filename:
            Original filename (with or without extension). Used as fallback
            when the SHA1 is not found in any catalog.
        source_path:
            Full path of the file on disk (CATALOG-MATCH-BUG-1). Only used as
            a platform tiebreaker in `_match_by_title()` when the extension
            is ambiguous (`.zip`/`.chd`/`.iso`/...) — the caller's real folder
            (psx/, saturn/, dreamcast/...) is a reliable signal the filename
            alone can't provide.
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
                    platform=_platform_from_dat_name(source),
                )

        if filename is None:
            return None

        # MATCH-FIX-1: un .zip sin tag "(Región)" es un set arcade estilo MAME
        # casi seguro (los dumps No-Intro/Redump siempre llevan paréntesis).
        # El fallback por título los emparejaba con plataformas absurdas
        # (flicky.zip → "Fujitsu - FM-7", confianza low) y el pass arcade
        # nunca llegaba a probarse. Para esos nombres, arcade primero.
        mame_style = filename.lower().endswith(".zip") and "(" not in filename
        if mame_style:
            return self._match_arcade(filename) or self._match_by_title(filename, source_path)
        return self._match_by_title(filename, source_path) or self._match_arcade(filename)

    def _match_by_title(self, filename: str, source_path: str | None = None) -> MatchResult | None:
        """Pass 2 — Name-based fallback (No-Intro / Redump title index)."""
        key = normalize_for_match(filename)
        if not key:
            return None
        hits = self._title_index.get(key)
        if not hits:
            return None
        if len(hits) == 1:
            entry, source = hits[0]
            return MatchResult(
                title=entry.title,
                confidence="medium",
                catalog_source=source,
                platform=_platform_from_dat_name(source),
            )
        # MATCH-FIX-2: la misma clave de título normalizado puede venir de
        # varias plataformas (remakes, Virtual Console, romhacks...) — sin
        # esto se quedaba con hits[0], que solo depende del orden alfabético
        # de carga de los .dat (catalog/matcher.py:142), no de qué plataforma
        # es realmente el archivo. Preferir los hits cuya plataforma coincide
        # con la extensión real; si ninguno coincide (p.ej. .zip, ambiguo por
        # diseño), se queda con todos como antes.
        ext_platform = PLATFORM_BY_EXTENSION.get(Path(filename).suffix.lower())
        candidates = hits
        resolved_platform = ext_platform
        if ext_platform:
            platform_hits = [h for h in hits if _platform_from_dat_name(h[1]) == ext_platform]
            if platform_hits:
                candidates = platform_hits
        elif source_path:
            # CATALOG-MATCH-BUG-1: extensión ambigua (.zip/.chd/.iso/...) —
            # ext_platform no puede desambiguar por diseño (un .chd puede ser
            # PSX/Saturn/Dreamcast/Wii). detect_platform() sí sabe leer la
            # carpeta contenedora real (psx/, saturn/...), la misma señal ya
            # usada en el resto de la app — antes esto siempre caía a
            # hits[0], eligiendo la región/plataforma equivocada cuando el
            # SHA1 no calzaba exacto (típico de un .chd, que no es el hash
            # crudo del disco).
            folder_platform = detect_platform(Path(source_path))
            resolved_platform = folder_platform
            if folder_platform:
                platform_hits = [
                    h for h in hits if _platform_from_dat_name(h[1]) == folder_platform
                ]
                if platform_hits:
                    candidates = platform_hits

        # CATALOG-MATCH-REGION-1: la clave normalizada colapsa "Tekken (USA)"
        # y "Tekken (Europe)" en el mismo título — sin más señal, candidates[0]
        # solo depende del orden de carga del .dat, no de qué disco es
        # realmente. El serial de arranque real (SYSTEM.CNF, vía chdman para
        # un .chd) sí es contenido real del disco: comparado contra el
        # `serial` que trae cada entrada del DAT de Redump, desambigua sin
        # adivinar. Solo PSX por ahora (Saturn/Dreamcast necesitarían su
        # propio lector de disco).
        if resolved_platform == "PlayStation" and len(candidates) > 1 and source_path:
            real_serial = detect_psx_boot_serial(Path(source_path), chdman_path=self._chdman_path)
            if real_serial:
                real_norm = _normalize_serial(real_serial)
                serial_hits = [
                    h for h in candidates if h[0].serial and _normalize_serial(h[0].serial) == real_norm
                ]
                if len(serial_hits) == 1:
                    entry, source = serial_hits[0]
                    return MatchResult(
                        title=entry.title,
                        confidence="medium",
                        catalog_source=source,
                        platform=_platform_from_dat_name(source),
                    )
                if serial_hits:
                    candidates = serial_hits

        # GAMECUBE-DISC-BUG-1e: normalize_for_match() borra "(Disc N)" junto
        # con el resto de anotaciones, así que un set multi-disco colapsa a
        # una sola clave y `candidates` puede traer una entrada del DAT por
        # disco. Sin esto siempre ganaba la primera (casi siempre Disc 1),
        # asignando el mismo canonical_title a todos los discos del set.
        entry, source = candidates[0]
        file_disc = find_disc_number(filename)
        if file_disc is not None:
            for hit_entry, hit_source in candidates:
                if find_disc_number(hit_entry.title) == file_disc:
                    entry, source = hit_entry, hit_source
                    break
        return MatchResult(
            title=entry.title,
            confidence="low",
            catalog_source=source,
            ambiguous=True,
            platform=_platform_from_dat_name(source),
        )

    def _match_arcade(self, filename: str) -> MatchResult | None:
        """Pass 3 — Arcade stem lookup (MAME / FBNeo)."""
        if not self._arcade:
            return None
        arcade_hit = self._arcade.get(Path(filename).stem.lower())
        if not arcade_hit:
            return None
        title, _year, _mfr, source = arcade_hit
        # Derive platform from which catalog file it came from
        arcade_platform = "MAME" if source.lower().endswith(".xml") else "FBNeo"
        return MatchResult(
            title=title,
            confidence="medium",
            catalog_source=source,
            platform=arcade_platform,
        )

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
