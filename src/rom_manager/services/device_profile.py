"""DEVPROFILE-4a/4b: Tier A source detection + portable export/import.
DEVPROFILE-5a adds the missing piece: actually uploading that export as a
manifest, see ``save_profile_manifest()``.

Tier A = config/<core>/*.cfg, retroarch-core-options.cfg, config/remaps/,
autoconfig/, shaders/, .opt in bulk, BIOS/system/ — everything the D2 cloud
sync can already move as a whole folder via ``SyncSource(sync_all=True)``.
``config/`` (which already covers ``config/<core>/*.opt`` AND
``config/remaps/``, since remaps live *inside* config/) and ``cheats/`` are
already wired via ``config.sync.ra_config_dir``/``cheats_dir`` +
``build_cloud_sync_sources()`` — nothing new needed there. This module only
covers the Tier A folders that mechanism doesn't reach yet.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from rom_manager.config import SyncSource
from rom_manager.services.path_tokenizer import resolve, tokenize

if TYPE_CHECKING:
    from rom_manager.sync.rclone_transport import RcloneTransport

# name → (subfolder under the RetroArch install dir, human label)
_TIER_A_SUBDIRS = {
    "autoconfig": "RetroArch Autoconfig (mandos)",
    "shaders": "RetroArch Shaders",
    "system": "BIOS / System",
}

# DEVPROFILE-9: RetroArch's own recent/favorites playlists -- single files
# under <RetroArch dir>/playlists, restored via SyncSource(single_file=True)
# (see sync_single_file()). Playtime (.lrtl) already syncs on its own via
# build_cloud_sync_sources() (JUEGOS-UX-7) -- not repeated here. RA
# credentials (cheevos_*) stay out of scope: their accessibility without
# root on Android is unconfirmed (roadmap 19 "Fuera de alcance").
_TIER_A_SINGLE_FILES = {
    "playlists/content_history.lpl": "RetroArch Recientes",
    "playlists/content_favorites.lpl": "RetroArch Favoritos",
}

# DEVPROFILE-8: tool-owned data under project_root/.rommgr worth restoring on
# a new PC.
_DATA_SUBDIRS = {
    "catalogs": "Catálogos No-Intro/Redump/Arcade (DATs)",
}

# DEVPROFILE-8b: the SQLite DBs are single files, not directories -- restored
# via SyncSource(single_file=True) the same way as _TIER_A_SINGLE_FILES.
_DATA_SINGLE_FILES = {
    "library_pc.db": "Base de datos PC (library_pc.db)",
    "library_android.db": "Base de datos Android (library_android.db)",
}


def detect_tier_a_sources(ra_dir: Path, remote_base: str) -> list[SyncSource]:
    """Candidate Tier A ``SyncSource`` entries found under *ra_dir* (the
    RetroArch install folder, parent of retroarch.exe). Only folders that
    actually exist are returned — nothing is created. *remote_base* (e.g.
    ``"dropbox:RetroSync"``) is used to suggest a remote path per source;
    the confirmation screen lets the user change it before saving.
    """
    sources = []
    remote_base = remote_base.rstrip("/")
    for subdir, label in _TIER_A_SUBDIRS.items():
        local_dir = Path(ra_dir) / subdir
        if not local_dir.is_dir():
            continue
        sources.append(
            SyncSource(
                name=label,
                local_dir=str(local_dir),
                remote=f"{remote_base}/{subdir}",
                sync_all=True,
            )
        )
    for relative, label in _TIER_A_SINGLE_FILES.items():
        local_file = Path(ra_dir) / relative
        if not local_file.is_file():
            continue
        sources.append(
            SyncSource(
                name=label,
                local_dir=str(local_file),
                remote=f"{remote_base}/{Path(relative).name}",
                single_file=True,
            )
        )
    return sources


def detect_data_sources(project_root: Path, remote_base: str) -> list[SyncSource]:
    """DEVPROFILE-8: candidate ``SyncSource`` entries for tool-owned data
    under *project_root*/.rommgr (the No-Intro/Redump/Arcade DAT catalogs
    today) -- avoids re-downloading and re-matching catalogs by hand on a new
    PC. Independent of RetroArch being configured at all, unlike
    ``detect_tier_a_sources()``."""
    sources = []
    remote_base = remote_base.rstrip("/")
    data_dir = Path(project_root) / ".rommgr"
    for subdir, label in _DATA_SUBDIRS.items():
        local_dir = data_dir / subdir
        if not local_dir.is_dir():
            continue
        sources.append(
            SyncSource(
                name=label,
                local_dir=str(local_dir),
                remote=f"{remote_base}/{subdir}",
                sync_all=True,
            )
        )
    for filename, label in _DATA_SINGLE_FILES.items():
        local_file = data_dir / filename
        if not local_file.is_file():
            continue
        sources.append(
            SyncSource(
                name=label,
                local_dir=str(local_file),
                remote=f"{remote_base}/{filename}",
                single_file=True,
            )
        )
    return sources


def export_profile_sources(
    sources: list[SyncSource],
    roms_dir: Path,
    saves_dir: Path,
    system_dir: Path,
    project_root: Path | None = None,
) -> list[dict]:
    """Serialize *sources* with ``local_dir`` tokenized ({ROMS}/{SAVES}/
    {SYSTEM}/{PROJECT_ROOT}) so the manifest is portable to another device
    (DEVPROFILE-4b). Sources outside all watched roots (e.g. a standalone
    emulator's own config dir) keep their local_dir as-is — that pair syncs
    the same PC+Anbernic, the token substitution doesn't apply to them.
    """
    return [
        {
            "name": s.name,
            "local_dir": tokenize(Path(s.local_dir), roms_dir, saves_dir, system_dir, project_root),
            "remote": s.remote,
            "sync_all": s.sync_all,
            "single_file": s.single_file,
        }
        for s in sources
    ]


_MANIFEST_FILENAME = "device-profile.json"


def save_profile_manifest(
    sources: list[SyncSource],
    roms_dir: Path,
    saves_dir: Path,
    system_dir: Path,
    transport: RcloneTransport,
    remote_base: str,
    project_root: Path | None = None,
) -> str:
    """DEVPROFILE-5a: upload the tokenized ``export_profile_sources()`` output
    as ``<remote_base>/device-profile.json`` — the manifest ``rommgr restore``
    (DEVPROFILE-5b+) reads to bootstrap a new device. Closes the gap where
    export/import existed as pure functions with no production caller (see
    Tareas/Roadmap-DEVPROFILE-5-6.md §1).

    Reuses ``RcloneTransport.upload()``'s existing fallback-remote routing
    (empty extension tuples → always routes to *fallback_remote*, already
    exercised by ``test_upload_unknown_ext_falls_back_to_fallback_remote``)
    instead of adding a new single-file upload method.

    Returns the full remote path written.
    """
    manifest = export_profile_sources(sources, roms_dir, saves_dir, system_dir, project_root)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
        tmp_path = Path(fh.name)
    try:
        transport.upload(tmp_path, _MANIFEST_FILENAME, fallback_remote=remote_base.rstrip("/"))
    finally:
        tmp_path.unlink(missing_ok=True)
    return f"{remote_base.rstrip('/')}/{_MANIFEST_FILENAME}"


def import_profile_sources(
    data: list[dict],
    roms_dir: Path,
    saves_dir: Path,
    system_dir: Path,
    project_root: Path | None = None,
) -> list[SyncSource]:
    """Reverse of ``export_profile_sources()``: resolve each entry's
    ``local_dir`` token against *this* device's own roots.
    """
    return [
        SyncSource(
            name=entry["name"],
            local_dir=str(
                resolve(entry["local_dir"], roms_dir, saves_dir, system_dir, project_root)
            ),
            remote=entry["remote"],
            sync_all=entry.get("sync_all", True),
            single_file=entry.get("single_file", False),
        )
        for entry in data
    ]
