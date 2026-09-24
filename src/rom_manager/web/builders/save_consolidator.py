"""SAVE-CONSOLIDATOR-1 — web builder for the save-fragmentation report.

Thin JSON adapter over ``sync.save_consolidator.scan_save_groups``: scans the
local ``saves/`` and ``states/`` trees under ``library_root`` as two separate
roots (see that module's docstring for why mixing them produces false
positives) and returns only groups that need attention — a lone,
non-fragmented save is not reported.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rom_manager.sync.save_consolidator import scan_save_groups

if TYPE_CHECKING:
    from rom_manager.config import AppConfig

# blank/divergent first — that is the reading order the informe uses (real
# risk before "safe to dedupe")
_STATUS_ORDER = {"divergent": 0, "blank": 1, "identical": 2}


def _build_save_fragmentation_report(config: AppConfig) -> dict:
    if not config.library_root:
        return {"error": "library_root no configurado"}

    library_root = Path(config.library_root)
    roots = (
        ("saves", library_root / "saves", config.save_extensions),
        ("states", library_root / "states", config.state_extensions),
    )

    root_info = []
    groups_out = []
    summary = {"single": 0, "blank": 0, "identical": 0, "divergent": 0}

    for root_name, root_path, extensions in roots:
        exists = root_path.is_dir()
        root_info.append({"name": root_name, "path": str(root_path), "exists": exists})
        if not exists:
            continue

        for group in scan_save_groups(root_path, extensions):
            summary[group.status] += 1
            if group.status == "single":
                continue
            groups_out.append(
                {
                    "root": root_name,
                    "stem": group.stem,
                    "status": group.status,
                    "entries": [
                        {
                            "relative": f"{root_name}/{e.relative}",
                            "extension": e.extension,
                            "size": e.size,
                            "mtime": e.mtime.isoformat(),
                            "sha1": e.sha1,
                            "is_blank": e.is_blank,
                        }
                        for e in group.entries
                    ],
                }
            )

    groups_out.sort(key=lambda g: (_STATUS_ORDER[g["status"]], g["root"], g["stem"]))

    return {"roots": root_info, "summary": summary, "groups": groups_out}
