from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class ExtractionResult:
    zip_path: Path
    extracted_files: list[Path]
    success: bool
    skipped_reason: str = ""
    error: str = ""


@dataclass(slots=True)
class ExtractionSummary:
    extracted: int = 0
    skipped: int = 0
    failed: int = 0
    deleted: int = 0
    results: list[ExtractionResult] = field(default_factory=list)


# Extensions of disc-based formats — these belong to the CHD workflow, not ZIP extraction
_DISC_EXTENSIONS = frozenset({".cue", ".bin", ".iso", ".img", ".mdf", ".mds", ".ccd"})


def find_zip_files(directory: Path) -> list[Path]:
    """Return all .zip files under directory, sorted."""
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
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            # Skip disc-based archives
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
        if result.skipped_reason:
            summary.skipped += 1
        elif result.error:
            summary.failed += 1
        else:
            summary.extracted += 1
            if delete_source and not dry_run:
                summary.deleted += 1
    return summary
