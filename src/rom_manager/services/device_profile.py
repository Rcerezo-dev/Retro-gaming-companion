"""DEVPROFILE-4a/4b: Tier A source detection + portable export/import.

Backend only (no UI yet — the Settings screen where the user confirms
detected sources before they sync is a separate, later piece, see
Tareas/Roadmap-DEVPROFILE-1-4.md §5).

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

from pathlib import Path

from rom_manager.config import SyncSource
from rom_manager.services.path_tokenizer import resolve, tokenize

# name → (subfolder under the RetroArch install dir, human label)
# ponytail: retroarch-core-options.cfg (a single file, not a folder) isn't
# covered here — SyncSource syncs directories. Add a single-file source kind
# if/when that file turns out to matter in practice.
_TIER_A_SUBDIRS = {
    "autoconfig": "RetroArch Autoconfig (mandos)",
    "shaders": "RetroArch Shaders",
    "system": "BIOS / System",
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
    return sources


def export_profile_sources(
    sources: list[SyncSource], roms_dir: Path, saves_dir: Path, system_dir: Path
) -> list[dict]:
    """Serialize *sources* with ``local_dir`` tokenized ({ROMS}/{SAVES}/
    {SYSTEM}) so the manifest is portable to another device (DEVPROFILE-4b).
    Sources outside all three roots (e.g. a standalone emulator's own config
    dir) keep their local_dir as-is — that pair syncs the same PC+Anbernic,
    the token substitution doesn't apply to them.
    """
    return [
        {
            "name": s.name,
            "local_dir": tokenize(Path(s.local_dir), roms_dir, saves_dir, system_dir),
            "remote": s.remote,
            "sync_all": s.sync_all,
        }
        for s in sources
    ]


def import_profile_sources(
    data: list[dict], roms_dir: Path, saves_dir: Path, system_dir: Path
) -> list[SyncSource]:
    """Reverse of ``export_profile_sources()``: resolve each entry's
    ``local_dir`` token against *this* device's own roots.
    """
    return [
        SyncSource(
            name=entry["name"],
            local_dir=str(resolve(entry["local_dir"], roms_dir, saves_dir, system_dir)),
            remote=entry["remote"],
            sync_all=entry.get("sync_all", True),
        )
        for entry in data
    ]
