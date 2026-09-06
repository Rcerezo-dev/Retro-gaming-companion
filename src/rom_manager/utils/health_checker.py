from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from rom_manager.hashing.hash_calculator import calculate_hashes


@dataclass(slots=True)
class DiscHealthResult:
    cue_path: str
    rescue_candidates: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DiscHealthSummary:
    broken: int = 0
    results: list[DiscHealthResult] = field(default_factory=list)


def check_disc_set_health(directory: Path) -> DiscHealthSummary:
    """DISC-HEALTH-1: recorre *directory* buscando sets ``.cue`` rotos
    (referencian un ``.bin`` que no existe) y, para cada uno, si ya hay un
    ``.chd``/``.pbp`` jugable del mismo juego en cualquier otra parte del
    árbol -- región/edición distinta cuenta (título normalizado).

    Repite el método 100% manual usado en
    ``Tareas/psx-cue-rotos-2026-08-30.md`` (22 ``.cue`` rotos, 21
    recuperables sin pérdida real solo comprobando esto a mano) como función
    reutilizable, mismo espíritu que :func:`check_library_health` pero para
    integridad de sets multi-archivo en vez de "existe la ruta".
    """
    from rom_manager.converters.chd_converter import find_cue_files, is_broken_cue_set
    from rom_manager.retroachievements.ra_checker import _normalize_title

    summary = DiscHealthSummary()
    broken_cues = [cue for cue in find_cue_files(directory) if is_broken_cue_set(cue)]
    if not broken_cues:
        return summary

    _PLAYABLE_EXTS = {".chd", ".pbp"}
    candidates_by_title: dict[str, list[Path]] = {}
    for f in directory.rglob("*"):
        if f.is_file() and f.suffix.lower() in _PLAYABLE_EXTS:
            candidates_by_title.setdefault(_normalize_title(f.stem), []).append(f)

    for cue in broken_cues:
        rescues = sorted(str(p) for p in candidates_by_title.get(_normalize_title(cue.stem), []))
        summary.broken += 1
        summary.results.append(DiscHealthResult(cue_path=str(cue), rescue_candidates=rescues))
    return summary


@dataclass(slots=True)
class MisplacedExtensionResult:
    path: str
    folder_platform: str
    detected_platform: str


@dataclass(slots=True)
class MisplacedExtensionsSummary:
    misplaced: int = 0
    results: list[MisplacedExtensionResult] = field(default_factory=list)


def check_misplaced_extensions_health(directory: Path) -> MisplacedExtensionsSummary:
    """LIB-MISPLACED-1: recorre las carpetas de plataforma ya organizadas bajo
    *directory* (``psx/``, ``gba/``, etc. -- nombres de ``PLATFORM_BY_FOLDER``)
    buscando archivos cuya extensión pertenece a otra plataforma distinta a la
    de su carpeta (reutiliza ``detect_platform()``/``PLATFORM_BY_EXTENSION``,
    ya fiables en el Inbox). El Inbox solo audita lo que entra nuevo; esto
    cubre lo que ya lleva tiempo mal colocado dentro de una carpeta organizada
    (encontrado a mano: chips MAME y ROMs ``.md``/``.nes`` sueltos en ``gba/``).

    Limitación conocida: las extensiones ambiguas (``.zip``, ``.bin``,
    ``.cue``...) se resuelven por contexto de carpeta en ``detect_platform()``,
    así que un ``.zip`` de arcade dentro de ``psx/`` nunca choca -- para eso
    hace falta inspección de contenido (ver ``zip_router.py``), fuera del
    alcance de este chequeo.
    """
    from rom_manager.detection.platform_detector import PLATFORM_BY_FOLDER, detect_platform

    summary = MisplacedExtensionsSummary()
    for folder in sorted(p for p in directory.iterdir() if p.is_dir()):
        expected = PLATFORM_BY_FOLDER.get(folder.name.lower())
        if expected is None:
            continue
        for f in folder.rglob("*"):
            if not f.is_file():
                continue
            actual = detect_platform(f)
            if actual is not None and actual != expected:
                summary.misplaced += 1
                summary.results.append(
                    MisplacedExtensionResult(
                        path=str(f), folder_platform=expected, detected_platform=actual
                    )
                )
    return summary


@dataclass(slots=True)
class HealthResult:
    source_path: str
    stored_sha1: str
    computed_sha1: str
    status: str  # "ok" | "corrupted" | "missing" | "chd_invalid"
    platform: str = ""
    canonical_title: str = ""


@dataclass(slots=True)
class HealthSummary:
    ok: int = 0
    corrupted: int = 0
    missing: int = 0
    chd_invalid: int = 0  # AUD-6: checksums internos del CHD inválidos
    results: list[HealthResult] = field(default_factory=list)


def _chd_verify_ok(path: Path, chdman_path: str) -> bool:
    """AUD-6: run ``chdman verify`` — validates the CHD's internal checksums.

    A CHD can have a stable file-level SHA1 and still be internally invalid
    since creation; only chdman can see that. Returns True on success or when
    chdman itself can't run (missing binary must not flag healthy files).
    """
    import subprocess

    try:
        r = subprocess.run(
            [chdman_path, "verify", "-i", str(path)],
            capture_output=True,
            timeout=600,
        )
        return r.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return True


def check_library_health(
    repository,  # LibraryRepository
    *,
    progress_cb: Callable[[int, int, str], None] | None = None,
    cancel_event: threading.Event | None = None,
    chd_verify: bool = False,
    chdman_path: str = "chdman",
) -> HealthSummary:
    """Re-hash every ROM in the library and compare against the stored SHA1.

    *progress_cb* is called as ``progress_cb(current, total, filename)``
    for each file processed.  If *cancel_event* is set the loop stops early.
    With *chd_verify* (AUD-6, slow) each hash-OK ``.chd`` also runs
    ``chdman verify`` to validate its internal checksums.
    """
    summary = HealthSummary()

    # Fetch all games that have a stored SHA1
    with repository.connect() as conn:
        rows = conn.execute(
            "SELECT source_path, sha1, original_filename, platform, canonical_title FROM games WHERE sha1 != '' AND sha1 IS NOT NULL"
        ).fetchall()

    total = len(rows)
    for idx, row in enumerate(rows, 1):
        if cancel_event is not None and cancel_event.is_set():
            break
        path = Path(row["source_path"])
        stored = row["sha1"]
        filename = row["original_filename"] or path.name

        if progress_cb:
            progress_cb(idx, total, filename)

        if not path.exists():
            summary.missing += 1
            summary.results.append(
                HealthResult(
                    source_path=row["source_path"],
                    stored_sha1=stored,
                    computed_sha1="",
                    status="missing",
                    platform=row["platform"] or "",
                    canonical_title=row["canonical_title"] or "",
                )
            )
            continue

        try:
            hashes = calculate_hashes(path)
            computed = hashes.sha1
        except OSError:
            computed = ""

        if computed == stored:
            # AUD-6: deep CHD verification — only on hash-OK files (a hash
            # mismatch is already reported as corrupted)
            if chd_verify and path.suffix.lower() == ".chd":
                if progress_cb:
                    progress_cb(idx, total, f"[chdman verify] {filename}")
                if not _chd_verify_ok(path, chdman_path):
                    summary.chd_invalid += 1
                    summary.results.append(
                        HealthResult(
                            source_path=row["source_path"],
                            stored_sha1=stored,
                            computed_sha1=computed,
                            status="chd_invalid",
                            platform=row["platform"] or "",
                            canonical_title=row["canonical_title"] or "",
                        )
                    )
                    continue
            summary.ok += 1
            # Only store non-OK results to keep memory usage low
        else:
            summary.corrupted += 1
            summary.results.append(
                HealthResult(
                    source_path=row["source_path"],
                    stored_sha1=stored,
                    computed_sha1=computed,
                    status="corrupted" if computed else "missing",
                    platform=row["platform"] or "",
                    canonical_title=row["canonical_title"] or "",
                )
            )

    return summary
