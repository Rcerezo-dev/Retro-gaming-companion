"""Publish scraped media into RetroArch's ``thumbnails/`` convention.

RetroArch uses a completely different layout than ES-DE: fixed folders per
platform (``<db_name>/Named_Boxarts|Named_Snaps/``), files named by playlist
``label`` (== ``canonical_title``) instead of ROM filename, and it only
accepts PNG. ES-DE and Retro Vault's own web UI already read the scraped file
directly from ``media/images|screenshots/`` next to the ROM (single source,
zero duplication) — this module bridges that single source into RetroArch's
tree without duplicating bytes when possible:

- Source already PNG: hardlinked into place (same inode — zero extra disk
  usage, and a rescrape that overwrites the source in place stays in sync
  since the hardlink still points at the same data).
- Source is JPG (RetroArch rejects JPG outright): converted once via
  PowerShell + ``System.Drawing`` (stdlib-only, same trick as
  ``utils/notifier.py``) into a cache keyed by the source's mtime, then that
  cached PNG is hardlinked/copied in — re-runs skip already-converted covers.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from rom_manager.utils.lpl_generator import platform_db_name
from rom_manager.utils.subprocess_flags import NO_WINDOW

if TYPE_CHECKING:
    from collections.abc import Callable

    from rom_manager.database.repository import LibraryRepository

_logger = logging.getLogger(__name__)

# DB column -> RetroArch thumbnail subfolder
_KINDS = (
    ("box_art_path", "Named_Boxarts"),
    ("screenshot_path", "Named_Snaps"),
)

_INVALID_LABEL_CHARS = '<>:"/\\|?*'


def _safe_label(canonical_title: str) -> str:
    """Strip filesystem-invalid characters from a title used as a filename."""
    return "".join(c for c in canonical_title if c not in _INVALID_LABEL_CHARS).strip()


def _convert_to_png(src: Path, dest_png: Path) -> bool:
    """Convert *src* to PNG at *dest_png* via PowerShell + System.Drawing."""
    dest_png.parent.mkdir(parents=True, exist_ok=True)
    script = (
        "Add-Type -AssemblyName System.Drawing;"
        f"$img = [System.Drawing.Image]::FromFile('{src}');"
        f"$img.Save('{dest_png}', [System.Drawing.Imaging.ImageFormat]::Png);"
        "$img.Dispose()"
    )
    try:
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            check=True,
            capture_output=True,
            creationflags=NO_WINDOW,
            timeout=30,
        )
        return dest_png.exists()
    except Exception:
        _logger.warning("Conversión JPG→PNG falló: %s", src, exc_info=True)
        return False


def _link_or_copy(src: Path, dest: Path) -> None:
    """Hardlink *src* into *dest* (same volume) or copy as a cross-volume fallback."""
    if dest.exists():
        dest.unlink()
    try:
        os.link(src, dest)
    except OSError:
        shutil.copy2(src, dest)


def publish_retroarch_thumbnails(
    library_root: Path,
    repository: LibraryRepository,
    retroarch_root: Path,
    *,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict:
    """Publish box art + screenshots to ``<retroarch_root>/thumbnails/``.

    *on_progress*, if given, is called as ``on_progress(current, total)`` once
    per game processed — lets the web layer report progress on a job that can
    take minutes at library scale (each JPG conversion shells out).

    Returns
    -------
    dict with ``published``, ``converted`` (JPG→PNG conversions actually
    performed), ``skipped_no_title`` (no ``canonical_title`` to name the
    file), ``missing_source`` (DB row points at a file no longer on disk)
    and ``errors`` (list of str).
    """
    cache_dir = library_root / ".rommgr" / "retroarch_thumbnails_cache"
    thumbs_root = retroarch_root / "thumbnails"

    with repository.connect() as conn:
        rows = conn.execute(
            """
            SELECT g.platform, g.canonical_title,
                   m.box_art_path, m.screenshot_path
            FROM games g
            JOIN game_metadata m ON m.game_id = g.id
            WHERE g.file_type = 'rom'
              AND g.platform IS NOT NULL
              AND (
                (m.box_art_path IS NOT NULL AND m.box_art_path != '')
                OR (m.screenshot_path IS NOT NULL AND m.screenshot_path != '')
              )
            """
        ).fetchall()

    published = 0
    converted = 0
    skipped_no_title = 0
    missing_source = 0
    errors: list[str] = []

    total = len(rows)
    for index, row in enumerate(rows, start=1):
        if on_progress is not None:
            on_progress(index, total)
        label = _safe_label(row["canonical_title"] or "")
        if not label:
            skipped_no_title += 1
            continue
        db_name = platform_db_name(row["platform"])

        for column, subdir in _KINDS:
            src_str = row[column]
            if not src_str:
                continue
            src = Path(src_str)
            if not src.exists():
                missing_source += 1
                continue

            if src.suffix.lower() == ".png":
                real_src = src
            else:
                cached = cache_dir / subdir / f"{src.stem}.png"
                if not cached.exists() or cached.stat().st_mtime < src.stat().st_mtime:
                    if not _convert_to_png(src, cached):
                        errors.append(f"{src}: conversión JPG→PNG falló")
                        continue
                    converted += 1
                real_src = cached

            dest_dir = thumbs_root / db_name / subdir
            dest = dest_dir / f"{label}.png"
            if dest.exists():
                try:
                    if dest.samefile(real_src):
                        published += 1
                        continue
                except OSError:
                    pass
            try:
                dest_dir.mkdir(parents=True, exist_ok=True)
                _link_or_copy(real_src, dest)
                published += 1
            except OSError as exc:
                errors.append(f"{dest}: {exc}")

    return {
        "published": published,
        "converted": converted,
        "skipped_no_title": skipped_no_title,
        "missing_source": missing_source,
        "errors": errors,
    }
