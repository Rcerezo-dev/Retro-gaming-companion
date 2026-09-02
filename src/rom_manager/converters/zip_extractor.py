from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

# Matches "Game Title (Disc 1)" / "(Disk 2)" etc. — same pattern as m3u_generator
# The \s*$ anchor prevents false matches on track files like "Game (Disc 1) (Track 2)"
_DISC_RE = re.compile(r"^(.+?)\s*\(Dis[ck]\s*(\d+)\)\s*$", re.IGNORECASE)


@dataclass(slots=True)
class ExtractionResult:
    zip_path: Path
    extracted_files: list[Path]
    success: bool
    skipped_reason: str = ""
    error: str = ""
    is_disc_set: bool = False
    skipped_existing: list[Path] = field(default_factory=list)


@dataclass(slots=True)
class ExtractionSummary:
    extracted: int = 0
    skipped: int = 0
    failed: int = 0
    deleted: int = 0
    disc_sets: int = 0
    results: list[ExtractionResult] = field(default_factory=list)


# INBOX-FIX-6: only a multi-track descriptor means "this is a set, reconstruct
# via the CHD workflow instead of a raw unzip" — a lone .iso/.img/etc. (PS2,
# GameCube) is a single playable file and extracting it plain is correct.
_DISC_SET_EXTENSIONS = frozenset({".cue", ".gdi"})

# B7-5: Folder names that indicate arcade/MAME ROMs — ZIPs must NOT be extracted
# because the ZIP *is* the ROM (MAME loads directly from the archive).
_ARCADE_FOLDER_NAMES = frozenset(
    {
        "mame",
        "arcade",
        "fbneo",
        "fba",
        "neogeo",
        "mame2003",
        "mame2010",
        "mame2015",
        "mame2016",
        "mame_libretro",
    }
)


def find_zip_files(directory: Path) -> list[Path]:
    """Return all .zip files under directory (recursive), sorted."""
    return sorted(directory.rglob("*.zip"))


def is_arcade_zip_container(zip_path: Path, arcade_crc_index: dict) -> bool:
    """DECOMPRESS-ARCADE-GAP-3: True if every entry's CRC is a known arcade ROM.

    Detects an arcade/MAME set by content (CRC32 from the ZIP's own header,
    no need to extract) instead of trusting the ancestor folder name — a set
    sitting in an unaudited/misnamed folder still gets caught.
    """
    try:
        with zipfile.ZipFile(zip_path) as zf:
            infos = [i for i in zf.infolist() if not i.is_dir()]
            if not infos:
                return False
            return all(f"{info.CRC & 0xFFFFFFFF:08X}" in arcade_crc_index for info in infos)
    except (OSError, zipfile.BadZipFile):
        return False


def extract_zip(
    zip_path: Path,
    *,
    delete_source: bool = False,
    dry_run: bool = True,
    arcade_crc_index: dict | None = None,
) -> ExtractionResult:
    """Extract the contents of *zip_path* to the same directory, member by member.

    Skips the whole archive if:
    - The filename matches a multi-disc set pattern (e.g. "Game (Disc 1).zip")
    - It sits under an arcade/MAME folder (the ZIP itself is the ROM)
    - It contains a .cue/.gdi (multi-track set — use the CHD converter instead)

    Members whose target already exists on disk are left alone — a single
    collision no longer aborts the rest of the archive (INBOX-FIX-1). The
    source ZIP is only eligible for deletion once every member is confirmed
    on disk (freshly extracted or pre-existing) with no per-member errors.
    """
    # Skip ZIPs whose filename matches the disc-set pattern (e.g. "Game (Disc 1).zip")
    if _DISC_RE.match(zip_path.stem):
        return ExtractionResult(
            zip_path=zip_path,
            extracted_files=[],
            success=False,
            skipped_reason="Set multi-disco — convierte a CHD en vez de extraer",
            is_disc_set=True,
        )

    # B7-5: Skip arcade/MAME ZIPs — the ZIP is the ROM, extracting would break it.
    # Detect by parent folder name (any ancestor part that matches arcade names).
    if any(part.lower() in _ARCADE_FOLDER_NAMES for part in zip_path.parts[:-1]):
        return ExtractionResult(
            zip_path=zip_path,
            extracted_files=[],
            success=False,
            skipped_reason="ROM arcade/MAME — no extraer (el ZIP es el ROM)",
        )

    # DECOMPRESS-ARCADE-GAP-3: misma detección por contenido (CRC real) que ya
    # usa organize-source — cubre sets arcade sentados en carpetas mal
    # nombradas o no auditadas que el chequeo de nombre de arriba no ve.
    if arcade_crc_index and is_arcade_zip_container(zip_path, arcade_crc_index):
        return ExtractionResult(
            zip_path=zip_path,
            extracted_files=[],
            success=False,
            skipped_reason="ROM arcade/MAME (detectado por CRC) — no extraer (el ZIP es el ROM)",
        )

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = [n for n in zf.namelist() if not n.endswith("/")]
            # Skip multi-track disc sets (contents check) — a .cue/.gdi describes
            # sibling track files that need set-aware handling, not a plain unzip.
            if any(Path(n).suffix.lower() in _DISC_SET_EXTENSIONS for n in names):
                return ExtractionResult(
                    zip_path=zip_path,
                    extracted_files=[],
                    success=False,
                    skipped_reason="Set multi-disco (.cue/.gdi) — usa el conversor CHD",
                )

            dest_dir = zip_path.parent
            to_extract: list[str] = []
            skipped_existing: list[Path] = []
            for name in names:
                target = dest_dir / name
                if target.exists():
                    skipped_existing.append(target)
                else:
                    to_extract.append(name)

            if dry_run:
                return ExtractionResult(
                    zip_path=zip_path,
                    extracted_files=[dest_dir / n for n in to_extract],
                    success=True,
                    skipped_existing=skipped_existing,
                )

            extracted_files: list[Path] = []
            errors: list[str] = []
            for name in to_extract:
                try:
                    zf.extract(name, dest_dir)
                    extracted_files.append(dest_dir / name)
                except OSError as exc:
                    errors.append(f"{name}: {exc}")

    except zipfile.BadZipFile as exc:
        return ExtractionResult(
            zip_path=zip_path,
            extracted_files=[],
            success=False,
            error=f"ZIP inválido: {exc}",
        )
    except OSError as exc:
        return ExtractionResult(
            zip_path=zip_path,
            extracted_files=[],
            success=False,
            error=str(exc),
        )

    if errors:
        return ExtractionResult(
            zip_path=zip_path,
            extracted_files=extracted_files,
            success=False,
            error="; ".join(errors),
            skipped_existing=skipped_existing,
        )

    # Every member is now present on disk (freshly extracted or pre-existing) —
    # safe to drop the now-redundant source archive.
    if delete_source:
        try:
            from rom_manager.utils.trash import discard_to_trash

            discard_to_trash(zip_path)  # AUD-3: soft-discard
        except OSError:
            pass

    return ExtractionResult(
        zip_path=zip_path,
        extracted_files=extracted_files,
        success=True,
        skipped_existing=skipped_existing,
    )


def extract_directory(
    directory: Path,
    *,
    delete_source: bool = False,
    dry_run: bool = True,
    arcade_crc_index: dict | None = None,
) -> ExtractionSummary:
    """Extract all .zip files under *directory*."""
    summary = ExtractionSummary()
    for zip_path in find_zip_files(directory):
        result = extract_zip(
            zip_path,
            delete_source=delete_source,
            dry_run=dry_run,
            arcade_crc_index=arcade_crc_index,
        )
        summary.results.append(result)
        if result.is_disc_set:
            summary.disc_sets += 1
            summary.skipped += 1
        elif result.skipped_reason:
            summary.skipped += 1
        elif result.error:
            summary.failed += 1
        else:
            summary.extracted += 1
            if delete_source and not dry_run:
                summary.deleted += 1
    return summary
