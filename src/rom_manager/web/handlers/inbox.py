from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import rom_manager.web.state as _state

if TYPE_CHECKING:
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
    job_manager: JobManager,
) -> None:
    """Register inbox / setup routes on *router*."""

    # ── GET /api/inbox-count ─────────────────────────────────────────────────
    @router.get("/api/inbox-count")
    def get_inbox_count(ctx) -> None:
        inbox_p = config.inbox.path
        count = 0
        if inbox_p:
            _ib = Path(inbox_p)
            if _ib.exists():
                count = sum(1 for f in _ib.iterdir() if f.is_file())
        ctx._send_json({"count": count})

    # ── GET /api/inbox-scan ──────────────────────────────────────────────────
    @router.get("/api/inbox-scan")
    def get_inbox_scan(ctx) -> None:
        from rom_manager.web.inbox_pipeline import _build_inbox_scan

        qs = getattr(ctx, "_qs", {})
        inbox_path_str = qs.get("path", [""])[0].strip() or config.inbox.path
        if not inbox_path_str:
            ctx._send_json({"error": "path parameter required (or set inbox.path in config.toml)"})
        else:
            ctx._send_json(_build_inbox_scan(inbox_path_str))

    # ── GET /api/inbox-status ────────────────────────────────────────────────
    @router.get("/api/inbox-status")
    def get_inbox_status(ctx) -> None:
        status = job_manager.get_status()
        ctx._send_json(
            {
                "running": status["inbox_running"],
                "progress": status.get("inbox_progress"),
                "result": status.get("inbox_result"),
            }
        )

    # ── GET /api/inbox-watcher-status ────────────────────────────────────────
    @router.get("/api/inbox-watcher-status")
    def get_inbox_watcher_status(ctx) -> None:
        ctx._send_json(dict(_state._inbox_watcher_status))

    # ── POST /api/inbox-run ──────────────────────────────────────────────────
    @router.post("/api/inbox-run")
    def post_inbox_run(ctx) -> None:
        _do_inbox_run(ctx, ctx._post_data, config, repository, job_manager)

    # ── POST /api/setup-run ──────────────────────────────────────────────────
    @router.post("/api/setup-run")
    def post_setup_run(ctx) -> None:
        _do_setup_run(ctx, ctx._post_data, config, repository, job_manager)


# ── Multipart upload — called directly from do_POST (pre-router) ─────────────


def handle_inbox_upload(config: AppConfig, content_type: str, body: bytes, ctx) -> None:
    """Save multipart file-upload(s) directly to inbox_path."""
    import re as _re

    bm = _re.search(r"boundary=([^\s;]+)", content_type)
    if not bm:
        ctx._send_error(400, "Missing multipart boundary")
        return
    inbox_path = config.inbox.path
    if not inbox_path:
        ctx._send_json({"error": "inbox_path not configured"})
        return
    inbox_dir = Path(inbox_path)
    inbox_dir.mkdir(parents=True, exist_ok=True)
    boundary = ("--" + bm.group(1)).encode()
    saved: list[str] = []
    errors: list[str] = []
    for part in body.split(boundary)[1:]:
        if part[:2] == b"--":
            break
        if part.startswith(b"\r\n"):
            part = part[2:]
        if b"\r\n\r\n" not in part:
            continue
        hdr_bytes, file_data = part.split(b"\r\n\r\n", 1)
        if file_data.endswith(b"\r\n"):
            file_data = file_data[:-2]
        hdr_text = hdr_bytes.decode("utf-8", errors="replace")
        fm = _re.search(r'filename="([^"]+)"', hdr_text)
        if not fm:
            continue
        fname = Path(fm.group(1)).name
        if not fname:
            continue
        try:
            (inbox_dir / fname).write_bytes(file_data)
            saved.append(fname)
        except OSError as exc:
            errors.append(f"{fname}: {exc}")
    ctx._send_json({"saved": saved, "errors": errors, "count": len(saved)})


# ── Handler logic ─────────────────────────────────────────────────────────────


def _do_inbox_run(
    ctx, data: dict, config: AppConfig, repository: LibraryRepository, job_manager
) -> None:
    from rom_manager.web.inbox_pipeline import _run_inbox_pipeline

    inbox_path_str = data.get("path", "").strip() or config.inbox.path
    if not inbox_path_str:
        ctx._send_json({"error": "path is required (or set inbox.path in config.toml)"})
        return
    target_root_str = (
        data.get("target_root", "").strip()
        or config.inbox.target_root
        or (str(config.library_root) if config.library_root else "")
    )
    delete_source = bool(data.get("delete_source", config.inbox.delete_source))

    def run() -> None:
        _run_inbox_pipeline(
            inbox_path_str, target_root_str, delete_source, repository, config, job_manager
        )

    ctx._send_json(job_manager.start("inbox", run))


def _do_setup_run(
    ctx, data: dict, config: AppConfig, repository: LibraryRepository, job_manager
) -> None:
    """Launch the first-time setup wizard pipeline as a background job."""
    from rom_manager.web.inbox_pipeline import _run_setup_pipeline

    lib_root = data.get("library_root", "").strip() or (
        str(config.library_root) if config.library_root else ""
    )
    if not lib_root:
        ctx._send_json({"error": "library_root is required"})
        return

    from rom_manager.config import load_config, write_config_toml

    updates: dict = {}
    if not config.library_root or str(config.library_root) != lib_root:
        updates["library.library_root"] = lib_root
    android_root = data.get("android_root", "").strip()
    if android_root and (not config.anbernic_root or str(config.anbernic_root) != android_root):
        updates["library.anbernic_root"] = android_root
    if updates:
        write_config_toml(config.project_root, updates)
        new_cfg = load_config(config.project_root)
        config.library_root = new_cfg.library_root
        if android_root:
            config.anbernic_root = new_cfg.anbernic_root
        config.device_name = new_cfg.device_name

    options = {
        "clean_junk": bool(data.get("clean_junk", False)),
        "extract_zips": bool(data.get("extract_zips", True)),
        "scan": bool(data.get("scan", True)),
        "match": bool(data.get("match", True)),
    }

    def run() -> None:
        _run_setup_pipeline(lib_root, options, repository, config, job_manager)

    ctx._send_json(job_manager.start("setup", run))
