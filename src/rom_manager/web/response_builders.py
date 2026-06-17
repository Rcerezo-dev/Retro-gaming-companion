"""Façade for the Retro Vault response builders.

The builder functions were split by domain into the ``web/builders/`` package
(SRP-1a). They are re-exported here so that existing imports
(``from rom_manager.web.response_builders import _build_X``) keep working without
touching any caller.
"""

from __future__ import annotations

from rom_manager.web.builders.common import (  # noqa: F401  (re-export)
    _json_response,
    _list_drives,
    _parse_format_opts,
    _repo_for_path,
    _test_path,
    _utc_now_str,
)
from rom_manager.web.builders.diff import (  # noqa: F401  (re-export)
    _build_library_diff,
)
from rom_manager.web.builders.duplicates import (  # noqa: F401  (re-export)
    _annotate_conflicts_with_ra,
    _annotate_duplicates_with_ra,
    _build_duplicates,
    _build_duplicates_two_repos,
    _build_ra_duplicates,
)
from rom_manager.web.builders.folders import (  # noqa: F401  (re-export)
    _build_folder_analysis,
    _build_junk_scan,
)
from rom_manager.web.builders.library import (  # noqa: F401  (re-export)
    _build_games,
    _build_library_report,
    _build_plan,
    _build_status,
    _count_companion_saves,
)
from rom_manager.web.builders.misc import (  # noqa: F401  (re-export)
    _build_assets,
    _build_cable_sync_preview,
    _build_config,
    _build_scrape_summary,
    _build_sync_log,
)
