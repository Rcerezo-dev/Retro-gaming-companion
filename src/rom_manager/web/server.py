from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from rom_manager.config import AppConfig
from rom_manager.database.repository import LibraryRepository
from rom_manager.planner import build_plan
from rom_manager.reports import build_report, to_csv, to_json
from rom_manager.web.frontend import HTML


def _json_response(data: object) -> bytes:
    return json.dumps(data, ensure_ascii=False).encode()


def _build_status(repository: LibraryRepository) -> dict:
    summary = repository.get_summary()
    dup_groups = repository.get_duplicate_groups()
    from rom_manager.reports.reporter import _get_all_games
    games = _get_all_games(repository)
    matched = sum(1 for g in games if g.canonical_title is not None)
    wasted = sum(g.wasted_bytes for g in dup_groups)
    return {
        "total_games": summary.total_games,
        "total_saves": summary.total_saves,
        "total_assets": summary.total_assets,
        "matched_games": matched,
        "unmatched_games": summary.total_games - matched,
        "duplicate_groups": len(dup_groups),
        "wasted_bytes": wasted,
        "last_scan_at": summary.last_scan_at,
    }


def _build_games(repository: LibraryRepository) -> dict:
    from rom_manager.reports.reporter import _get_all_games
    from dataclasses import asdict
    games = _get_all_games(repository)
    return {"games": [asdict(g) for g in games]}


def _build_plan(repository: LibraryRepository) -> dict:
    plan = build_plan(repository)
    return {
        "total": plan.total,
        "already_correct": len(plan.already_correct),
        "pending": [
            {
                "platform": op.game.platform,
                "source": str(op.source_path),
                "source_name": op.source_path.name,
                "target": str(op.target_path),
                "target_name": op.target_path.name,
            }
            for op in plan.pending
        ],
        "conflicts": [
            {
                "source_name": op.source_path.name,
                "target_name": op.target_path.name,
            }
            for op in plan.conflicts
        ],
    }


def _build_duplicates(repository: LibraryRepository) -> dict:
    groups = repository.get_duplicate_groups()
    total_files = sum(len(g.entries) for g in groups)
    total_wasted = sum(g.wasted_bytes for g in groups)
    return {
        "groups": [
            {
                "sha1": g.sha1,
                "canonical_title": g.entries[0].canonical_title,
                "platform": g.entries[0].platform,
                "wasted_bytes": g.wasted_bytes,
                "entries": [
                    {"source_path": e.source_path, "size_bytes": e.size_bytes}
                    for e in g.entries
                ],
            }
            for g in groups
        ],
        "total_files": total_files,
        "wasted_bytes": total_wasted,
    }


def make_handler(repository: LibraryRepository, config: AppConfig):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            pass  # suppress default request logging

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path

            try:
                if path == "/":
                    self._send(200, "text/html; charset=utf-8", HTML.encode())
                elif path == "/api/status":
                    self._send_json(_build_status(repository))
                elif path == "/api/games":
                    self._send_json(_build_games(repository))
                elif path == "/api/plan":
                    self._send_json(_build_plan(repository))
                elif path == "/api/duplicates":
                    self._send_json(_build_duplicates(repository))
                elif path == "/api/report.json":
                    report = build_report(repository)
                    body = to_json(report).encode()
                    self._send(200, "application/json; charset=utf-8", body,
                               extra_headers={"Content-Disposition": 'attachment; filename="report.json"'})
                elif path == "/api/report.csv":
                    report = build_report(repository)
                    body = to_csv(report).encode()
                    self._send(200, "text/csv; charset=utf-8", body,
                               extra_headers={"Content-Disposition": 'attachment; filename="report.csv"'})
                else:
                    self._send(404, "text/plain", b"Not found")
            except Exception as exc:
                body = json.dumps({"error": str(exc)}).encode()
                self._send(500, "application/json", body)

        def _send(
            self,
            code: int,
            content_type: str,
            body: bytes,
            extra_headers: dict[str, str] | None = None,
        ) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            for k, v in (extra_headers or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, data: object) -> None:
            body = _json_response(data)
            self._send(200, "application/json; charset=utf-8", body)

    return Handler


def serve(
    *,
    host: str,
    port: int,
    repository: LibraryRepository,
    config: AppConfig,
) -> None:
    handler = make_handler(repository, config)
    with ThreadingHTTPServer((host, port), handler) as httpd:
        httpd.serve_forever()
