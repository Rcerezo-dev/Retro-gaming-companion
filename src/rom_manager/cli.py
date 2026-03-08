from __future__ import annotations

import argparse
import csv
import io
from pathlib import Path

from rom_manager.catalog.matcher import CatalogMatcher
from rom_manager.config import _CONFIG_TOML_TEMPLATE, load_config
from rom_manager.converters.chd_converter import convert_directory
from rom_manager.database import LibraryRepository
from rom_manager.logging_utils import configure_logging
from rom_manager.planner import build_plan
from rom_manager.reports import build_report, to_csv, to_json
from rom_manager.scanner import scan_library
from rom_manager.sync.rclone_transport import RcloneError, RcloneTransport
from rom_manager.sync.save_syncer import sync_saves


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rommgr")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan ROM and save files.")
    scan_parser.add_argument("source_path", type=Path, help="Folder to scan.")

    subparsers.add_parser("status", help="Show library summary.")

    unresolved_parser = subparsers.add_parser(
        "unresolved",
        help="List ROMs not yet matched against a catalog.",
    )
    unresolved_parser.add_argument(
        "--export",
        metavar="FILE",
        default=None,
        help="Export the list to a CSV file instead of printing to stdout.",
    )

    subparsers.add_parser(
        "match",
        help="Match unresolved ROMs against No-Intro and Redump catalogs.",
    )

    subparsers.add_parser(
        "plan",
        help="Preview renames for all matched ROMs (no files are changed).",
    )

    subparsers.add_parser(
        "apply",
        help="Execute the rename plan produced by 'rommgr plan'.",
    )

    subparsers.add_parser(
        "duplicates",
        help="List ROM files that share the same SHA1 hash (exact duplicates).",
    )

    report_parser = subparsers.add_parser(
        "report",
        help="Export a library report as JSON or CSV.",
    )
    report_parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        dest="report_format",
        help="Output format (default: json).",
    )
    report_parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write output to FILE instead of stdout.",
    )

    for cmd, hlp in (
        ("sync-saves", "Sync save files between local saves dir and a remote (rclone)."),
        ("sync-status", "Show sync status for saves without transferring anything."),
    ):
        sp = subparsers.add_parser(cmd, help=hlp)
        sp.add_argument(
            "--saves-dir",
            type=Path,
            default=None,
            metavar="PATH",
            help="Local saves folder (overrides config.toml [library] saves_dir).",
        )
        sp.add_argument(
            "--remote",
            default=None,
            metavar="REMOTE",
            help="rclone remote path (overrides config.toml [sync] remote).",
        )
        sp.add_argument(
            "--rclone",
            default=None,
            metavar="PATH",
            help="Path to rclone binary (overrides config.toml [sync] rclone).",
        )
        if cmd == "sync-saves":
            sp.add_argument(
                "--apply",
                action="store_true",
                help="Actually transfer files (default is dry run).",
            )

    chd_parser = subparsers.add_parser(
        "convert-chd",
        help="Convert PSX .cue+.bin sets to .chd (dry run by default).",
    )
    chd_parser.add_argument("source_path", type=Path, help="Folder to scan for .cue files.")
    chd_parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually perform the conversion (default is dry run).",
    )
    chd_parser.add_argument(
        "--delete-source",
        action="store_true",
        help="Delete .cue and .bin files after successful conversion (requires --apply).",
    )
    chd_parser.add_argument(
        "--chdman",
        default=None,
        metavar="PATH",
        help="Path to the chdman binary (overrides config.toml [tools] chdman).",
    )

    subparsers.add_parser(
        "init-config",
        help="Generate a sample config.toml in the current directory.",
    )

    serve_parser = subparsers.add_parser(
        "serve",
        help="Start the local web interface.",
    )
    serve_parser.add_argument(
        "--host",
        default=None,
        help="Host to bind (overrides config.toml [web] host, default 127.0.0.1).",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind (overrides config.toml [web] port, default 7777).",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = load_config()
    logger = configure_logging(config.logs_dir)
    repository = LibraryRepository(config.database_path)

    if args.command == "scan":
        source_path = args.source_path.resolve()
        if not source_path.exists() or not source_path.is_dir():
            parser.error(f"Source path does not exist or is not a directory: {source_path}")

        result = scan_library(source_path, config, repository, logger)
        print(f"Scanned: {source_path}")
        print(f"Files seen:            {result.files_seen}")
        print(f"ROMs detected:         {result.roms_detected}")
        print(f"ROMs skipped (cached): {result.roms_skipped}")
        print(f"Saves detected:        {result.saves_detected}")
        print(f"Assets detected:       {result.assets_detected}")
        print(f"System files skipped:  {result.system_files_detected}")
        print(f"Unknown files:         {result.unknown_files_detected}")
        print(f"Errors:                {result.errors}")
        return 0

    if args.command == "status":
        summary = repository.get_summary()
        print(f"Database:   {config.database_path}")
        print(f"Games:      {summary.total_games}")
        print(f"Saves:      {summary.total_saves}")
        print(f"Assets:     {summary.total_assets}")
        print(f"Last scan:  {summary.last_scan_at or 'never'}")
        return 0

    if args.command == "plan":
        plan = build_plan(repository)
        if plan.total == 0:
            print("No matched games found. Run 'rommgr match' first.")
            return 0

        if plan.pending:
            print(f"Pending renames ({len(plan.pending)}):")
            current_platform = None
            for op in plan.pending:
                platform = op.game.platform or "Unknown"
                if platform != current_platform:
                    current_platform = platform
                    print(f"\n  {platform}")
                print(f"    {op.source_path.name}")
                print(f"    → {op.target_path.name}")

        if plan.conflicts:
            print(f"\nConflicts — target already exists ({len(plan.conflicts)}):")
            for op in plan.conflicts:
                print(f"  [CONFLICT] {op.source_path.name}  →  {op.target_path.name}")

        print(f"\nSummary:  {len(plan.pending)} to rename  |  "
              f"{len(plan.conflicts)} conflicts  |  "
              f"{len(plan.already_correct)} already correct")
        if plan.pending:
            print("Run 'rommgr apply' to execute the renames.")
        return 0

    if args.command == "apply":
        import os
        from rom_manager.scanner.rom_scanner import utc_now

        plan = build_plan(repository)
        if not plan.pending:
            print("Nothing to apply.")
            if plan.conflicts:
                print(f"{len(plan.conflicts)} conflict(s) require manual resolution.")
            return 0

        timestamp = utc_now()
        renamed = 0
        failed = 0
        for op in plan.pending:
            try:
                os.rename(op.source_path, op.target_path)
                repository.apply_rename(
                    game_id=op.game.id,
                    old_source_path=str(op.source_path),
                    new_source_path=str(op.target_path),
                    new_filename=op.target_path.name,
                    timestamp=timestamp,
                )
                renamed += 1
            except OSError as exc:
                print(f"  [FAIL] {op.source_path.name}: {exc}")
                failed += 1

        print(f"Renamed: {renamed}  |  Failed: {failed}")
        if plan.conflicts:
            print(f"{len(plan.conflicts)} conflict(s) were skipped — resolve manually.")
        return 0

    if args.command == "report":
        report = build_report(repository)
        if args.report_format == "json":
            output = to_json(report)
        else:
            output = to_csv(report)

        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            print(f"Report written to {args.output}  ({report.total_games} games)")
        else:
            print(output)
        return 0

    if args.command in ("sync-saves", "sync-status"):
        saves_dir_arg = args.saves_dir or config.saves_dir
        if saves_dir_arg is None:
            parser.error(
                "Saves directory not specified. "
                "Pass --saves-dir or set [library] saves_dir in config.toml."
            )
        saves_dir = saves_dir_arg.resolve()
        if not saves_dir.exists() or not saves_dir.is_dir():
            parser.error(f"Saves directory does not exist: {saves_dir}")

        remote = args.remote or config.rclone_remote
        if not remote:
            parser.error(
                "Remote not specified. "
                "Pass --remote or set [sync] remote in config.toml."
            )

        dry_run = args.command == "sync-status" or not getattr(args, "apply", False)
        rclone_bin = args.rclone or config.rclone_binary
        transport = RcloneTransport(rclone=rclone_bin)

        if dry_run and args.command == "sync-saves":
            print("DRY RUN — no files will be transferred. Pass --apply to sync.\n")
        if args.command == "sync-status":
            print("Sync status (no files will be transferred).\n")

        try:
            result, decisions = sync_saves(
                saves_dir,
                remote,
                transport=transport,
                repository=repository,
                save_extensions=config.save_extensions,
                dry_run=dry_run,
            )
        except RcloneError as exc:
            print(f"[ERROR] {exc}")
            return 1

        for d in decisions:
            if d.action == "up_to_date":
                continue
            tag = {"upload": "↑ UPLOAD", "download": "↓ DOWNLOAD", "conflict": "⚠ CONFLICT"}.get(
                d.action, d.action.upper()
            )
            print(f"  [{tag}]  {d.relative}")

        verb = "Would " if dry_run else ""
        print(
            f"\n{verb}Upload: {result.uploaded}  |  "
            f"{verb}Download: {result.downloaded}  |  "
            f"Up to date: {result.up_to_date}  |  "
            f"Conflicts: {result.conflicts}  |  "
            f"Errors: {result.errors}"
        )
        if not dry_run and result.errors == 0 and (result.uploaded + result.downloaded) > 0:
            print("Sync complete.")
        return 0

    if args.command == "convert-chd":
        source_path = args.source_path.resolve()
        if not source_path.exists() or not source_path.is_dir():
            parser.error(f"Source path does not exist or is not a directory: {source_path}")

        dry_run = not args.apply
        if dry_run:
            print("DRY RUN — no files will be changed. Pass --apply to convert.")
        if args.delete_source and not args.apply:
            print("Note: --delete-source has no effect without --apply.")
        print()

        summary = convert_directory(
            source_path,
            chdman=args.chdman or config.chdman,
            delete_source=args.delete_source,
            dry_run=dry_run,
        )

        for result in summary.results:
            bins = ", ".join(p.name for p in result.bin_paths)
            if result.success:
                action = "would convert" if dry_run else "converted"
                print(f"  [OK]  {result.cue_path.name}  →  {result.chd_path.name}")
                if bins:
                    print(f"        bins: {bins}")
            else:
                tag = "SKIP" if result.error and "already exists" in result.error else "FAIL"
                print(f"  [{tag}] {result.cue_path.name}  —  {result.error}")

        print()
        if dry_run:
            print(f"Would convert: {summary.converted}  |  Would skip: {summary.skipped}")
            if summary.converted:
                print("Run with --apply to perform the conversion.")
        else:
            print(f"Converted: {summary.converted}  |  Skipped: {summary.skipped}  |  Failed: {summary.failed}")
            if summary.converted:
                print("Re-run 'rommgr scan' to update the library database.")
        return 0

    if args.command == "match":
        matcher = CatalogMatcher(
            nointro_dir=config.catalogs_nointro_dir,
            redump_dir=config.catalogs_redump_dir,
        )
        print("Loading catalogs…", flush=True)
        # Trigger lazy load and report catalog sizes
        nointro_count = matcher.nointro_entries
        redump_count = matcher.redump_entries
        print(f"  No-Intro: {nointro_count:,} entries")
        print(f"  Redump:   {redump_count:,} entries")

        games = repository.get_unresolved_games()
        if not games:
            print("No unresolved games to match.")
            return 0

        print(f"\nMatching {len(games)} unresolved ROMs…")
        matched_high = 0
        matched_medium = 0
        matched_low = 0
        unmatched = 0
        with repository.batch() as conn:
            for game in games:
                result = matcher.match(game.sha1, game.original_filename)
                if result is not None:
                    repository.update_match(
                        game.source_path,
                        canonical_title=result.title,
                        match_confidence=result.confidence,
                        catalog_source=result.catalog_source,
                        connection=conn,
                    )
                    if result.confidence == "high":
                        matched_high += 1
                    elif result.confidence == "medium":
                        matched_medium += 1
                    else:
                        matched_low += 1
                else:
                    unmatched += 1

        print(f"\nMatched (SHA1):   {matched_high}")
        print(f"Matched (nombre): {matched_medium + matched_low}"
              + (f"  ({matched_low} ambiguos)" if matched_low else ""))
        print(f"Sin match:        {unmatched}")
        return 0

    if args.command == "duplicates":
        groups = repository.get_duplicate_groups()
        if not groups:
            print("No duplicates found.")
            return 0

        total_files = sum(len(g.entries) for g in groups)
        total_wasted = sum(g.wasted_bytes for g in groups)

        def _fmt_size(n: int) -> str:
            for unit in ("B", "KB", "MB", "GB"):
                if n < 1024:
                    return f"{n:.1f} {unit}"
                n /= 1024
            return f"{n:.1f} TB"

        print(f"Duplicate groups: {len(groups)}  ({total_files} files, ~{_fmt_size(total_wasted)} wasted)\n")
        for group in groups:
            title = group.entries[0].canonical_title or "(unmatched)"
            platform = group.entries[0].platform or "Unknown"
            print(f"[SHA1: {group.sha1[:12]}…]  {platform}  ·  {title}")
            for entry in group.entries:
                print(f"  {entry.source_path}  ({_fmt_size(entry.size_bytes)})")
            print()
        return 0

    if args.command == "unresolved":
        games = repository.get_unresolved_games()
        if not games:
            print("No unresolved games.")
            return 0

        if args.export:
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["platform", "original_filename", "region", "sha1", "source_path"])
            for game in games:
                writer.writerow([
                    game.platform or "",
                    game.original_filename,
                    game.region or "",
                    game.sha1,
                    game.source_path,
                ])
            Path(args.export).write_text(buf.getvalue(), encoding="utf-8")
            print(f"Exported {len(games)} unresolved ROMs to {args.export}")
            return 0

        current_platform = None
        for game in games:
            platform = game.platform or "Unknown platform"
            if platform != current_platform:
                current_platform = platform
                print(f"\n{platform}")
                print("-" * len(platform))
            region = f"[{game.region}]" if game.region and game.region != "UNK" else ""
            print(f"  {game.original_filename}  {region}")

        print(f"\nTotal: {len(games)} unresolved")
        return 0

    if args.command == "init-config":
        toml_path = Path.cwd() / "config.toml"
        if toml_path.exists():
            print(f"config.toml already exists at {toml_path} — not overwriting.")
            return 1
        toml_path.write_text(_CONFIG_TOML_TEMPLATE, encoding="utf-8")
        print(f"Created {toml_path}")
        print("Edit it to set your saves_dir, remote, and tool paths.")
        return 0

    if args.command == "serve":
        from rom_manager.web.server import serve

        host = args.host or config.web_host
        port = args.port or config.web_port
        print(f"Starting ROM Manager at http://{host}:{port}/")
        print("Press Ctrl+C to stop.")
        serve(host=host, port=port, repository=repository, config=config)
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
