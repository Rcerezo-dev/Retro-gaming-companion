from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from rom_manager.hashing.hash_calculator import calculate_hashes


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
