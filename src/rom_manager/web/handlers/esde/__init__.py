"""ES-DE handler package — orchestrates the ES-DE / export / tools route groups.

``register()`` is a thin orchestrator: it delegates each domain to its
sub-registrar (system, reports, conversions, maintenance, doctor). The
``_handle_*`` helpers live in ``esde/system.py`` and are re-exported here
because ``server.py`` internals and ``handlers/system.py`` import them from the
``esde`` package.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from rom_manager.web.handlers.esde.system import (
    _handle_copy_assets_to_esde,
    _handle_disc_folders,
    _handle_esde_status,
    _handle_generate_es_systems,
)

if TYPE_CHECKING:
    import types
    from collections.abc import Callable

    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.jobs.manager import JobManager
    from rom_manager.web.router import Router


_logger = logging.getLogger(__name__)

__all__ = [
    "_handle_copy_assets_to_esde",
    "_handle_disc_folders",
    "_handle_esde_status",
    "_handle_generate_es_systems",
    "register",
]


# ── Public entry point ────────────────────────────────────────────────────────


def register(
    router: Router,
    *,
    config: AppConfig,
    repository: LibraryRepository,
    repo_android: LibraryRepository,
    get_repo_fn: Callable[[str], LibraryRepository],
    srv_mod: types.ModuleType,
    job_manager: JobManager,
) -> None:
    """Register ES-DE, export, report, utility and tool routes on *router*.

    Pure orchestrator: each call below registers one domain's routes.
    """

    from rom_manager.web.handlers.esde.conversions import register_conversions
    from rom_manager.web.handlers.esde.doctor import register_doctor
    from rom_manager.web.handlers.esde.maintenance import register_maintenance
    from rom_manager.web.handlers.esde.reports import register_reports
    from rom_manager.web.handlers.esde.system import register_system

    # ── ES-DE detection + status/system/misc utility routes ──────────────────
    register_system(
        router,
        config=config,
        repository=repository,
        repo_android=repo_android,
        get_repo_fn=get_repo_fn,
        job_manager=job_manager,
    )

    # ── Library report + export routes (html/json/csv/lpl) ───────────────────
    register_reports(
        router,
        config=config,
        repository=repository,
        get_repo_fn=get_repo_fn,
        job_manager=job_manager,
    )

    # ── Conversion / extraction routes (CHD, CSO, N64, ZIP, m3u, multidisc) ───
    register_conversions(router, config=config, repository=repository, job_manager=job_manager)

    # ── Maintenance routes (health check, zip/cue+bin cleanup, junk delete) ───
    register_maintenance(router, config=config, repository=repository, job_manager=job_manager)

    # ── Library doctor routes (orphaned saves, move/delete fixes, doctor report) ─
    register_doctor(router, config=config, repository=repository)
