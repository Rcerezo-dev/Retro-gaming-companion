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


@dataclass(slots=True)
class ExtractionSummary:
    extracted: int = 0
    skipped: int = 0
    failed: int = 0
    deleted: int = 0
    disc_sets: int = 0
    results: list[ExtractionResult] = field(default_factory=list)


# Extensions of disc-based formats — these belong to the CHD workflow, not ZIP extraction
_DISC_EXTENSIONS = frozenset({".cue", ".bin", ".iso", ".img", ".mdf", ".mds", ".ccd"})

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


def extract_zip(
    zip_path: Path,
    *,
    delete_source: bool = False,
    dry_run: bool = True,
) -> ExtractionResult:
    """Extract the contents of *zip_path* to the same directory.

    Skips if:
    - The archive contains .cue/.bin/.iso files (use CHD converter instead)
    - Any target file already exists on disk
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

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            # Skip disc-based archives (contents check)
            if any(Path(n).suffix.lower() in _DISC_EXTENSIONS for n in names):
                return ExtractionResult(
                    zip_path=zip_path,
                    extracted_files=[],
                    success=False,
                    skipped_reason="Contiene archivos de disco (.cue/.bin/.iso) — usa el conversor CHD",
                )

            dest_dir = zip_path.parent
            targets = [dest_dir / name for name in names if not name.endswith("/")]

            # Skip if any target already exists
            existing = [t for t in targets if t.exists()]
            if existing:
                return ExtractionResult(
                    zip_path=zip_path,
                    extracted_files=[],
                    success=False,
                    skipped_reason=f"Ya existe en destino: {existing[0].name}",
                )

            if dry_run:
                return ExtractionResult(
                    zip_path=zip_path,
                    extracted_files=targets,
                    success=True,
                )

            zf.extractall(dest_dir)

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

    if delete_source:
        try:
            zip_path.unlink()
        except OSError:
            pass

    return ExtractionResult(
        zip_path=zip_path,
        extracted_files=targets,
        success=True,
    )


def extract_directory(
    directory: Path,
    *,
    delete_source: bool = False,
    dry_run: bool = True,
) -> ExtractionSummary:
    """Extract all .zip files under *directory*."""
    summary = ExtractionSummary()
    for zip_path in find_zip_files(directory):
        result = extract_zip(zip_path, delete_source=delete_source, dry_run=dry_run)
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
