from __future__ import annotations

from typing import TYPE_CHECKING

from rom_manager.services.duplicates_service import (
    delete_all_duplicates,
    delete_all_duplicates_multi,
    delete_duplicate,
)
from rom_manager.services.ra_duplicates_service import (
    apply_ra_conflicts,
    discard_all_ra_duplicates,
    discard_no_support,
    discard_ra_duplicate,
    resolve_duplicate_ra,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from rom_manager.config import AppConfig
    from rom_manager.database.repository import LibraryRepository
    from rom_manager.web.jobs.manager import JobManager
    from rom_manager.web.router import Router


# ── Public entry point ────────────────────────────────────────────────────────


def register(
    router: Router,
    *,
    config: AppConfig,
    repository: LibraryRepository,
    repo_android: LibraryRepository,
    get_repo_fn: Callable[[str], LibraryRepository],
    job_manager: JobManager,
) -> None:
    """Register duplicate-management routes on *router*.

    Routes are thin: they parse the request and delegate the business logic to
    ``services.duplicates_service`` / ``services.ra_duplicates_service``.
    """
    from rom_manager.sync.adb_transport import resolve_single_device_transport
    from rom_manager.web.builders.duplicates import (
        _build_duplicates_two_repos,
        _build_ra_duplicates,
    )

    def _adb_transport():
        # TABS-FIX-1a: resuelto por request (no cacheado) — el dispositivo
        # puede conectarse/desconectarse entre una carga de la lista y el clic
        # en "Eliminar".
        return resolve_single_device_transport(config.adb)

    # ── GET /api/duplicates ───────────────────────────────────────────────────
    @router.get("/api/duplicates")
    def get_duplicates(ctx) -> None:
        qs = getattr(ctx, "_qs", {})
        source_root = qs.get("source_root", [None])[0] or None
        pc_root = qs.get("pc_root", [None])[0] or None
        ab_root = qs.get("ab_root", [None])[0] or None
        ctx._send_json(
            _build_duplicates_two_repos(
                repository,
                repo_android,
                config,
                source_root=source_root,
                pc_root=pc_root,
                ab_root=ab_root,
            )
        )

    # ── GET /api/ra-duplicates ────────────────────────────────────────────────
    @router.get("/api/ra-duplicates")
    def get_ra_duplicates(ctx) -> None:
        ctx._send_json(_build_ra_duplicates(repository, config))

    # ── POST /api/duplicates/delete ───────────────────────────────────────────
    @router.post("/api/duplicates/delete")
    def post_delete_duplicate(ctx) -> None:
        data = ctx._post_data
        source_path = data.get("source_path", "")
        ctx._send_json(
            delete_duplicate(
                get_repo_fn(source_path),
                game_id=data.get("game_id"),
                source_path=source_path,
                adb_transport=_adb_transport(),
            )
        )

    # ── POST /api/duplicates/delete-all ──────────────────────────────────────
    @router.post("/api/duplicates/delete-all")
    def post_delete_all_duplicates(ctx) -> None:
        # source_root = device selector root; empty = "Sistema completo" → both DBs
        source_root = (ctx._post_data.get("source_root") or "").strip()
        # DUPLICADOS-UX-1: el filtro de plataforma de la UI restringe también el borrado
        platform = (ctx._post_data.get("platform") or "").strip()
        adb_transport = _adb_transport()
        if source_root:
            ctx._send_json(
                delete_all_duplicates(
                    get_repo_fn(source_root), platform=platform, adb_transport=adb_transport
                )
            )
        else:
            ctx._send_json(
                delete_all_duplicates_multi(
                    [repository, repo_android], platform=platform, adb_transport=adb_transport
                )
            )

    # ── POST /api/duplicates/exclude ──────────────────────────────────────────
    @router.post("/api/duplicates/exclude")
    def post_exclude_duplicate(ctx) -> None:
        sha1 = ctx._post_data.get("sha1", "")
        if sha1:
            source_root = (ctx._post_data.get("source_root") or "").strip()
            if source_root:
                repos = [get_repo_fn(source_root)]
            else:
                # "Sistema completo": el grupo puede vivir en cualquiera de las
                # dos BDs — INSERT OR IGNORE hace que excluir en ambas sea seguro
                repos = [repository, repo_android]
            for repo in repos:
                repo.exclude_duplicate_sha1(sha1)
            ctx._send_json({"ok": True})
        else:
            ctx._send_error(400, "sha1 required")

    # ── GET /api/duplicates/exclusions ────────────────────────────────────────
    @router.get("/api/duplicates/exclusions")
    def get_duplicate_exclusions(ctx) -> None:
        # DUPLICADOS-UX-5: lista revisable de grupos marcados como copia intencional.
        # Se mergean ambas BDs dedupeando por sha1 (exclude escribe en las dos).
        seen: dict[str, dict] = {}
        for repo in (repository, repo_android):
            for row in repo.get_excluded_duplicates():
                if row["sha1"] not in seen:
                    seen[row["sha1"]] = row
        ctx._send_json({"exclusions": list(seen.values())})

    # ── POST /api/duplicates/exclusions/remove ────────────────────────────────
    @router.post("/api/duplicates/exclusions/remove")
    def post_remove_duplicate_exclusion(ctx) -> None:
        sha1 = ctx._post_data.get("sha1", "")
        if not sha1:
            ctx._send_error(400, "sha1 required")
            return
        for repo in (repository, repo_android):
            repo.remove_excluded_duplicate(sha1)
        ctx._send_json({"ok": True})

    # ── POST /api/apply-ra-conflicts ──────────────────────────────────────────
    @router.post("/api/apply-ra-conflicts")
    def post_apply_ra_conflicts(ctx) -> None:
        ctx._send_json(apply_ra_conflicts(repository, config, adb_transport=_adb_transport()))

    # ── POST /api/ra-duplicates/discard ───────────────────────────────────────
    @router.post("/api/ra-duplicates/discard")
    def post_ra_duplicate_discard(ctx) -> None:
        source_path = ctx._post_data.get("path", "").strip()
        if not source_path:
            ctx._send_error(400, "path required")
            return
        ctx._send_json(
            discard_ra_duplicate(get_repo_fn(source_path), source_path, _adb_transport())
        )

    # ── POST /api/ra-duplicates/discard-all ──────────────────────────────────
    @router.post("/api/ra-duplicates/discard-all")
    def post_ra_duplicate_discard_all(ctx) -> None:
        ra_dups = _build_ra_duplicates(repository, config)
        ctx._send_json(discard_all_ra_duplicates(repository, ra_dups, _adb_transport()))

    # ── POST /api/ra-check/discard-no-support ────────────────────────────────
    @router.post("/api/ra-check/discard-no-support")
    def post_ra_discard_no_support(ctx) -> None:
        result = job_manager.get_status()["ra_check_result"]
        if not result:
            ctx._send_json({"error": "No RA check result available. Run RA check first."})
            return
        ctx._send_json(
            discard_no_support(repository, result.get("no_support_entries", []), _adb_transport())
        )

    # ── POST /api/resolve-duplicate-ra ───────────────────────────────────────
    @router.post("/api/resolve-duplicate-ra")
    def post_resolve_duplicate_ra(ctx) -> None:
        data = ctx._post_data
        keep_path = data.get("keep_path", "").strip()
        discard_paths = data.get("discard_paths", [])
        if not keep_path or not discard_paths:
            ctx._send_json({"error": "keep_path and discard_paths required"})
            return
        # El grupo entero vive en un mismo dispositivo → enrutar por keep_path
        ctx._send_json(
            resolve_duplicate_ra(get_repo_fn(keep_path), keep_path, discard_paths, _adb_transport())
        )
