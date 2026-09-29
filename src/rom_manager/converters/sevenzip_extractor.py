from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from rom_manager.converters.zip_extractor import _ARCADE_FOLDER_NAMES, _DISC_RE
from rom_manager.utils.subprocess_flags import NO_WINDOW


@dataclass(slots=True)
class SevenZipExtractionResult:
    archive_path: Path
    extracted_files: list[Path]
    success: bool
    skipped_reason: str = ""
    error: str = ""
    skipped_existing: list[Path] = field(default_factory=list)


@dataclass(slots=True)
class SevenZipExtractionSummary:
    extracted: int = 0
    skipped: int = 0
    failed: int = 0
    deleted: int = 0
    results: list[SevenZipExtractionResult] = field(default_factory=list)


def find_7z_files(directory: Path) -> list[Path]:
    """Return all .7z files under directory (recursive), sorted."""
    return sorted(directory.rglob("*.7z"))


def list_7z_members(archive_path: Path, *, sevenzip: str = "7z") -> list[str] | None:
    """Return the relative path (as reported by 7z, may use '\\' or '/') of
    every real file inside *archive_path* (directories excluded), or None if
    7z couldn't list it (binary missing, archive corrupt/unreadable).

    Parses ``7z l -slt`` block output: the archive's own summary block (name,
    type, physical size...) comes before the first "----------" separator and
    is not an entry; after that, each entry is a run of "Key = Value" lines
    ended by a blank line, with ``Attributes`` starting with "D" for folders.
    """
    try:
        proc = subprocess.run(
            [sevenzip, "l", "-slt", str(archive_path)],
            capture_output=True,
            timeout=120,
            creationflags=NO_WINDOW,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None

    text = proc.stdout.decode("utf-8", errors="replace")
    _, sep, entries_text = text.partition("----------")
    if not sep:
        return None

    members: list[str] = []
    path: str | None = None
    is_dir = False
    for line in entries_text.splitlines():
        if not line.strip():
            if path is not None and not is_dir:
                members.append(path)
            path, is_dir = None, False
            continue
        if line.startswith("Path = "):
            path = line[len("Path = ") :]
        elif line.startswith("Attributes = "):
            is_dir = line[len("Attributes = ") :].strip().startswith("D")
    if path is not None and not is_dir:
        members.append(path)
    return members


def extract_7z(
    archive_path: Path,
    *,
    sevenzip: str = "7z",
    delete_source: bool = False,
    dry_run: bool = True,
) -> SevenZipExtractionResult:
    """Extract *archive_path* to its own parent directory, mirroring
    ``zip_extractor.extract_zip()``'s safety semantics: a member whose target
    already exists on disk is left alone (7z's own ``-aos``, "skip extracting
    of existing files"), and the source archive is only eligible for deletion
    once every member is confirmed on disk with no errors.
    """
    if _DISC_RE.match(archive_path.stem):
        return SevenZipExtractionResult(
            archive_path=archive_path,
            extracted_files=[],
            success=False,
            skipped_reason="Set multi-disco — convierte a CHD en vez de extraer",
        )

    if any(part.lower() in _ARCADE_FOLDER_NAMES for part in archive_path.parts[:-1]):
        return SevenZipExtractionResult(
            archive_path=archive_path,
            extracted_files=[],
            success=False,
            skipped_reason="ROM arcade/MAME — no extraer (el archivo es el ROM)",
        )

    members = list_7z_members(archive_path, sevenzip=sevenzip)
    if members is None:
        return SevenZipExtractionResult(
            archive_path=archive_path,
            extracted_files=[],
            success=False,
            error=f"No se pudo listar el .7z (¿{sevenzip!r} no encontrado o archivo corrupto?)",
        )

    dest_dir = archive_path.parent
    to_extract: list[Path] = []
    skipped_existing: list[Path] = []
    for name in members:
        target = dest_dir / name
        if target.exists():
            skipped_existing.append(target)
        else:
            to_extract.append(target)

    if dry_run:
        return SevenZipExtractionResult(
            archive_path=archive_path,
            extracted_files=to_extract,
            success=True,
            skipped_existing=skipped_existing,
        )

    if to_extract:
        try:
            subprocess.run(
                [sevenzip, "x", str(archive_path), f"-o{dest_dir}", "-aos", "-y"],
                check=True,
                capture_output=True,
                timeout=600,
                creationflags=NO_WINDOW,
            )
        except FileNotFoundError:
            return SevenZipExtractionResult(
                archive_path=archive_path,
                extracted_files=[],
                success=False,
                error=f"7z no encontrado: {sevenzip!r}",
            )
        except subprocess.TimeoutExpired:
            return SevenZipExtractionResult(
                archive_path=archive_path,
                extracted_files=[],
                success=False,
                error="Timeout extrayendo .7z (>600 s)",
            )
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode("utf-8", errors="replace").strip()
            return SevenZipExtractionResult(
                archive_path=archive_path,
                extracted_files=[],
                success=False,
                error=stderr or f"7z exited with code {exc.returncode}",
            )

    missing = [t for t in to_extract if not t.exists()]
    extracted_files = [t for t in to_extract if t.exists()]
    if missing:
        return SevenZipExtractionResult(
            archive_path=archive_path,
            extracted_files=extracted_files,
            success=False,
            error=f"{len(missing)} miembro(s) no extraídos",
            skipped_existing=skipped_existing,
        )

    # Every member is now present on disk (freshly extracted or pre-existing)
    # -- safe to drop the now-redundant source archive.
    if delete_source:
        try:
            from rom_manager.utils.trash import discard_to_trash

            discard_to_trash(archive_path)  # AUD-3: soft-discard
        except OSError:
            pass

    return SevenZipExtractionResult(
        archive_path=archive_path,
        extracted_files=extracted_files,
        success=True,
        skipped_existing=skipped_existing,
    )


def extract_7z_directory(
    directory: Path,
    *,
    sevenzip: str = "7z",
    delete_source: bool = False,
    dry_run: bool = True,
) -> SevenZipExtractionSummary:
    """Extract all .7z files under *directory*."""
    summary = SevenZipExtractionSummary()
    for archive_path in find_7z_files(directory):
        result = extract_7z(
            archive_path,
            sevenzip=sevenzip,
            delete_source=delete_source,
            dry_run=dry_run,
        )
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
