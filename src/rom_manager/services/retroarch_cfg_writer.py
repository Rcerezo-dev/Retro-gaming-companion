"""Writes known keys into RetroArch's retroarch.cfg without touching the rest
of the file (DEVPROFILE-2).

PC-only: Android's retroarch.cfg isn't reachable without root (DEVPROFILE-0,
see Tareas/Roadmap-DEVPROFILE-1-4.md §3). Enabling the *_by_content sort
flags matters beyond convenience — it's what makes RemoteRouter's per-core
subfolder assumption (``saves/<core>/<rom>.srm``) true by construction
instead of by luck, so today's sync stops guessing the layout.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

_MANAGED_BOOL_KEYS = (
    "sort_savefiles_by_content_enable",
    "sort_savestates_by_content_enable",
)


def read_key(text: str, key: str) -> str | None:
    """Current value of *key* in a RetroArch-style cfg, or None if absent/empty/"default"."""
    m = re.search(rf'^{re.escape(key)}\s*=\s*"(.*)"', text, re.MULTILINE)
    if not m:
        return None
    val = m.group(1).strip()
    return val if val not in ("", "default") else None


def _set_key(text: str, key: str, value: str) -> str:
    line = f'{key} = "{value}"'
    pattern = re.compile(rf'^{re.escape(key)}\s*=\s*".*"\s*$', re.MULTILINE)
    if pattern.search(text):
        return pattern.sub(line, text, count=1)
    sep = "" if text == "" or text.endswith("\n") else "\n"
    return f"{text}{sep}{line}\n"


@dataclass(slots=True)
class SavefileLayout:
    savefile_dir: str
    savestate_dir: str


def read_savefile_layout(text: str) -> SavefileLayout:
    """Read the current savefile_directory/savestate_directory (empty if unset/default)."""
    return SavefileLayout(
        savefile_dir=read_key(text, "savefile_directory") or "",
        savestate_dir=read_key(text, "savestate_directory") or "",
    )


def default_savefile_layout(library_root: Path) -> SavefileLayout:
    """DEVPROFILE-2d: default target dirs for the manual "apply layout" button.

    Matches the ``library_root/saves`` + ``library_root/states`` convention
    the D2 implicit cloud sync already assumes (see ``server.py``'s
    ``_implicit_tray`` for ``sync.saves_remote``/``sync.states_remote``) —
    reusing it here is what makes the two sides agree by construction.
    """
    return SavefileLayout(
        savefile_dir=str(library_root / "saves"),
        savestate_dir=str(library_root / "states"),
    )


@dataclass(slots=True)
class ApplyResult:
    applied: bool = False
    backup_path: str = ""
    changed_keys: dict[str, str] = field(default_factory=dict)
    error: str = ""


def apply_savefile_layout(cfg_path: Path, savefile_dir: str, savestate_dir: str) -> ApplyResult:
    """Write savefile_directory/savestate_directory and enable both
    sort-by-content flags in *cfg_path*.

    Backs up the file first (``.bak``, overwritten on each apply — this is a
    rare manual action, not the versioned save-backup path, ponytail: no
    history needed here, add it if that changes) — "en sync: ante duda, no
    sobreescribir; guardar backup primero" (CLAUDE.md). No-ops (no backup, no
    write) if every managed key already has the requested value.
    """
    result = ApplyResult()
    try:
        text = cfg_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        result.error = f"No se pudo leer {cfg_path}: {exc}"
        return result

    updates = {
        "savefile_directory": savefile_dir,
        "savestate_directory": savestate_dir,
        **{key: "true" for key in _MANAGED_BOOL_KEYS},
    }

    new_text = text
    changed: dict[str, str] = {}
    for key, value in updates.items():
        if read_key(text, key) == value:
            continue
        new_text = _set_key(new_text, key, value)
        changed[key] = value

    if not changed:
        result.applied = True
        return result

    backup_path = cfg_path.with_suffix(cfg_path.suffix + ".bak")
    try:
        shutil.copy2(cfg_path, backup_path)
    except OSError as exc:
        result.error = f"No se pudo crear el backup {backup_path}: {exc}"
        return result

    try:
        cfg_path.write_text(new_text, encoding="utf-8")
    except OSError as exc:
        result.error = f"No se pudo escribir {cfg_path}: {exc}"
        return result

    result.applied = True
    result.backup_path = str(backup_path)
    result.changed_keys = changed
    return result
