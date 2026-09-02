from __future__ import annotations

import argparse
import csv
import io
import logging
from pathlib import Path

from rom_manager.catalog.matcher import CatalogMatcher
from rom_manager.config import load_config
from rom_manager.converters.chd_converter import convert_directory
from rom_manager.database import LibraryRepository
from rom_manager.logging_utils import configure_logging
from rom_manager.planner import build_plan
from rom_manager.reports import build_report, to_csv, to_json
from rom_manager.scanner import scan_library
from rom_manager.sync.rclone_transport import RcloneError, RcloneTransport
from rom_manager.sync.save_syncer import sync_saves

_logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rommgr",
        description="Retro Vault — gestor de biblioteca de ROMs y sincronización de saves.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan ROM and save files.")
    scan_parser.add_argument("source_path", type=Path, help="Folder to scan.")
    scan_parser.add_argument(
        "--quick",
        action="store_true",
        help="Skip hash calculation — index by name/size/mtime only. Much faster for large libraries.",
    )

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

    plan_parser = subparsers.add_parser(
        "plan",
        help="Preview renames for all matched ROMs (no files are changed).",
    )
    plan_parser.add_argument(
        "--keep-both",
        action="store_true",
        help="When two ROMs map to the same target name, add _1/_2 suffixes instead of marking as conflict.",
    )

    apply_parser = subparsers.add_parser(
        "apply",
        help="Execute the rename plan produced by 'rommgr plan'.",
    )
    apply_parser.add_argument(
        "--keep-both",
        action="store_true",
        help="Resolve plan-level name collisions with _1/_2 suffixes (same as 'plan --keep-both').",
    )

    inspect_assets_parser = subparsers.add_parser(
        "inspect-assets",
        help="Show asset coverage (images, videos, XML) per platform.",
    )
    inspect_assets_parser.add_argument(
        "--platform",
        metavar="SLUG",
        default=None,
        help="Filter by platform slug.",
    )
    inspect_assets_parser.add_argument(
        "--orphans",
        action="store_true",
        help="List only assets with no matching ROM platform.",
    )
    inspect_assets_parser.add_argument(
        "--missing",
        action="store_true",
        help="List only ROMs whose platform has no assets.",
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
        ("sync-saves", "Sync save files between ROM library and a remote (rclone)."),
        ("sync-status", "Show sync status for saves without transferring anything."),
    ):
        sp = subparsers.add_parser(cmd, help=hlp)
        sp.add_argument(
            "--library-dir",
            type=Path,
            default=None,
            metavar="PATH",
            help="Root of the ROM+saves library (overrides config.toml [library] library_root).",
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
        help="Convert PSX .cue+.bin sets AND bare .bin dumps to .chd, RA-hash verified (dry run by default).",
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
        "fix-platforms",
        help="Backfill missing platform data by inferring it from folder names (no re-hash needed).",
    )

    scrape_parser = subparsers.add_parser(
        "scrape",
        help="Fetch metadata (title, genre, box art) from ScreenScraper.fr for unscraped ROMs.",
    )
    scrape_parser.add_argument(
        "--platform",
        default=None,
        metavar="NAME",
        help="Only scrape ROMs for this platform.",
    )
    scrape_parser.add_argument(
        "--images",
        action="store_true",
        help="Also download box art images alongside the ROMs.",
    )
    scrape_parser.add_argument(
        "--limit",
        type=int,
        default=0,
        metavar="N",
        help="Stop after N ROMs (0 = no limit).",
    )

    export_gl_parser = subparsers.add_parser(
        "export-gamelists",
        help="Generate gamelist.xml files per platform for EmulationStation (Anbernic).",
    )
    export_gl_parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="Root output directory. Defaults to library_root from config.",
    )
    export_gl_parser.add_argument(
        "--platform",
        default=None,
        metavar="NAME",
        help="Only export for this platform.",
    )

    # ── Headless commands (S38-2) — suitable for Task Scheduler ─────────────

    sync_parser = subparsers.add_parser(
        "sync",
        help="Sync all cloud save sources defined in config.toml (headless, Task Scheduler-friendly).",
    )
    sync_parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually transfer files. Default is dry-run.",
    )
    sync_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only print summary line (no per-file output).",
    )
    sync_parser.add_argument(
        "--notify",
        action="store_true",
        help="Show a Windows desktop toast notification when done.",
    )

    health_parser = subparsers.add_parser(
        "health",
        help="Re-hash all ROMs and report corrupted/missing files. Exits 1 if issues found.",
    )
    health_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only print summary line (no per-ROM output).",
    )
    health_parser.add_argument(
        "--notify",
        action="store_true",
        help="Show a Windows desktop toast notification when done.",
    )

    organize_source_parser = subparsers.add_parser(
        "organize-source",
        help=(
            "Run the Inbox pipeline against an existing library folder (e.g. "
            "'Unknown/' or an orphan platform folder) to move already-identified "
            "files into ROMs/<platform>/. Dry run by default."
        ),
    )
    organize_source_parser.add_argument(
        "source_path", type=Path, help="Existing folder to organize (any path inside the library)."
    )
    organize_source_parser.add_argument(
        "--target-root",
        type=Path,
        default=None,
        metavar="PATH",
        help="Root to organize into (defaults to config.toml [library] library_root).",
    )
    organize_source_parser.add_argument(
        "--delete-source",
        action="store_true",
        help="Delete processed ZIPs instead of archiving them under _processed/ (requires --apply).",
    )
    organize_source_parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually organize the folder (default is dry run).",
    )
    organize_source_parser.add_argument(
        "--exclude-platform",
        action="append",
        default=[],
        metavar="PLATFORM",
        help=(
            "Leave files of this platform (as stored in the games table, e.g. "
            "'MAME', 'FBNeo') completely untouched by this run — repeat for "
            "more than one. They are set aside before the pipeline runs and "
            "restored to their exact original path afterwards, so a fresh "
            "'rommgr scan' is needed for them to reappear in the database."
        ),
    )

    decompress_parser = subparsers.add_parser(
        "decompress",
        help=(
            "Decompress console ZIPs already sitting inside organized platform "
            "folders (arcade/MAME ZIPs and disc sets are never touched). Dry run by default."
        ),
    )
    decompress_parser.add_argument("source_path", type=Path, help="Folder to scan for ZIPs.")
    decompress_parser.add_argument(
        "--delete-source",
        action="store_true",
        help="Delete each ZIP after a fully successful extraction (requires --apply).",
    )
    decompress_parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually decompress (default is dry run).",
    )

    resolve_dup_parser = subparsers.add_parser(
        "resolve-duplicates",
        help=(
            "Resolve console duplicate ROMs by keeping the RetroAchievements-"
            "supported copy (same logic as the 'Revisar copias' web tab). "
            "Arcade/MAME/FBNeo groups are excluded on purpose. Dry run by default."
        ),
    )
    resolve_dup_parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually discard the losing copies (default is dry run).",
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
    serve_parser.add_argument(
        "--tray",
        action="store_true",
        help="Show a system tray icon (Windows only). The server starts minimised in the background.",
    )
    serve_parser.add_argument(
        "--allow-insecure",
        action="store_true",
        help=(
            "Allow binding to a non-localhost host without a PIN configured. "
            "By default the server refuses to start in that case (anyone on the "
            "network could access your library). Use only on a trusted network."
        ),
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    import sys

    parser = build_parser()
    args = parser.parse_args(argv)

    # When running as a PyInstaller bundle, use the exe's directory as project root
    # so config.toml and .rommgr/ live next to RetroVault.exe.
    if getattr(sys, "frozen", False):
        _project_root = Path(sys.executable).parent
    else:
        _project_root = None  # defaults to cwd
    config = load_config(_project_root)
    logger = configure_logging(config.logs_dir)
    repository = LibraryRepository(config.database_path)
    repository_android = LibraryRepository(config.database_path_android)

    if args.command == "scan":
        source_path = args.source_path.resolve()
        if not source_path.exists() or not source_path.is_dir():
            parser.error(f"Source path does not exist or is not a directory: {source_path}")

        result = scan_library(source_path, config, repository, logger, quick=args.quick)
        if args.quick:
            print("Quick scan (no hashes — match and sync will not work until a full scan is run)")
        print(f"Scanned: {source_path}")
        print(f"Files seen:            {result.files_seen}")
        print(f"ROMs detected:         {result.roms_detected}")
        print(f"ROMs ya escaneados:    {result.roms_skipped}")
        print(f"Saves detected:        {result.saves_detected}")
        print(f"Assets detected:       {result.assets_detected}")
        print(f"System files skipped:  {result.system_files_detected}")
        print(f"Unknown files:         {result.unknown_files_detected}")
        print(f"Errors:                {result.errors}")
        if result.pruned:
            print(f"Orphaned records cleaned: {result.pruned}")  # DB-2: orphan cleanup
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

        print(
            f"\nSummary:  {len(plan.pending)} to rename  |  "
            f"{len(plan.conflicts)} conflicts  |  "
            f"{len(plan.already_correct)} already correct"
        )
        if plan.pending:
            print("Run 'rommgr apply' to execute the renames.")
        return 0

    if args.command == "apply":
        from rom_manager.renamer.file_renamer import central_save_dirs, rename_rom_with_saves
        from rom_manager.scanner.rom_scanner import utc_now

        plan = build_plan(repository)
        if not plan.pending:
            print("Nothing to apply.")
            if plan.conflicts:
                print(f"{len(plan.conflicts)} conflict(s) require manual resolution.")
            return 0

        repository.backup_database()

        save_exts = frozenset(config.save_extensions)
        extra_save_dirs = central_save_dirs(config)
        timestamp = utc_now()
        renamed = failed = saves_renamed = 0
        for op in plan.pending:
            outcome = rename_rom_with_saves(
                op.source_path, op.target_path, save_exts, extra_dirs=extra_save_dirs
            )
            if outcome.success:
                repository.apply_rename(
                    game_id=op.game.id,
                    old_source_path=str(op.source_path),
                    new_source_path=str(op.target_path),
                    new_filename=op.target_path.name,
                    timestamp=timestamp,
                )
                renamed += 1
                saves_renamed += outcome.saves_renamed
                if outcome.saves_renamed:
                    print(
                        f"  [OK]  {op.source_path.name}  →  {op.target_path.name}  (+{outcome.saves_renamed} save(s))"
                    )
                else:
                    print(f"  [OK]  {op.source_path.name}  →  {op.target_path.name}")
            else:
                print(f"  [FAIL] {op.source_path.name}: {outcome.error}")
                failed += 1

        print(f"\nRenamed: {renamed}  |  Saves renamed: {saves_renamed}  |  Failed: {failed}")
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
        library_dir_arg = args.library_dir or config.library_root
        if library_dir_arg is None:
            parser.error(
                "Library root not specified. "
                "Pass --library-dir or set [library] library_root in config.toml."
            )
        saves_dir = library_dir_arg.resolve()
        if not saves_dir.exists() or not saves_dir.is_dir():
            parser.error(f"Library directory does not exist: {saves_dir}")

        remote = args.remote or config.sync.rclone_remote
        if not remote:
            parser.error("Remote not specified. Pass --remote or set [sync] remote in config.toml.")

        dry_run = args.command == "sync-status" or not getattr(args, "apply", False)
        rclone_bin = args.rclone or config.rclone_binary
        transport = RcloneTransport(rclone=rclone_bin)

        if dry_run and args.command == "sync-saves":
            print("DRY RUN — no files will be transferred. Pass --apply to sync.\n")
        if args.command == "sync-status":
            print("Sync status (no files will be transferred).\n")

        try:
            from rom_manager.sync.delta_cache import DeltaCache

            _delta = DeltaCache(config.data_dir) if not dry_run else None
            # Use dual remotes if configured, otherwise fall back to single remote
            saves_remote_to_use = config.sync.saves_remote or remote
            states_remote_to_use = config.sync.states_remote or None
            result, decisions = sync_saves(
                saves_dir,
                saves_remote=saves_remote_to_use,
                transport=transport,
                repository=repository,
                save_extensions=config.save_extensions,
                state_extensions=config.state_extensions,
                states_remote=states_remote_to_use,
                dry_run=dry_run,
                delta_cache=_delta,
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
        delta_note = f"  |  Delta skipped: {result.delta_skipped}" if result.delta_skipped else ""
        print(
            f"\n{verb}Upload: {result.uploaded}  |  "
            f"{verb}Download: {result.downloaded}  |  "
            f"Up to date: {result.up_to_date}  |  "
            f"Conflicts: {result.conflicts}  |  "
            f"Errors: {result.errors}{delta_note}"
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
            print(
                f"Converted: {summary.converted}  |  Skipped: {summary.skipped}  |  Failed: {summary.failed}"
            )
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
        print(
            f"Matched (nombre): {matched_medium + matched_low}"
            + (f"  ({matched_low} ambiguos)" if matched_low else "")
        )
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

        print(
            f"Duplicate groups: {len(groups)}  ({total_files} files, ~{_fmt_size(total_wasted)} wasted)\n"
        )
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
                writer.writerow(
                    [
                        game.platform or "",
                        game.original_filename,
                        game.region or "",
                        game.sha1,
                        game.source_path,
                    ]
                )
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

    if args.command == "inspect-assets":
        platform_filter = getattr(args, "platform", None)

        if args.orphans:
            assets = repository.get_orphan_assets(platform=platform_filter)
            if not assets:
                print("No orphan assets found.")
                return 0
            print(f"Orphan assets ({len(assets)}):")
            for a in assets:
                plat = a["platform"] or "Unknown"
                print(f"  [{plat}]  {a['asset_type']}  {a['source_path']}")
            return 0

        if args.missing:
            roms = repository.get_roms_without_assets(platform=platform_filter)
            if not roms:
                print("All platforms have at least one asset.")
                return 0
            print(f"ROMs with no assets ({len(roms)}):")
            current_plat = None
            for r in roms:
                plat = r["platform"] or "Unknown"
                if plat != current_plat:
                    current_plat = plat
                    print(f"\n  {plat}")
                print(f"    {r['original_filename']}")
            return 0

        stats = repository.get_asset_platform_stats()
        if platform_filter:
            stats = [s for s in stats if s["platform"].lower() == platform_filter.lower()]
        if not stats:
            print("No asset data found. Run 'rommgr scan' first.")
            return 0

        header = (
            f"{'Platform':<20} {'ROMs':>6} {'Images':>8} {'Videos':>8} {'XML':>5} {'Orphans':>8}"
        )
        print(header)
        print("-" * len(header))
        for s in stats:
            print(
                f"{s['platform']:<20} {s['rom_count']:>6} {s['image_count']:>8} "
                f"{s['video_count']:>8} {s['xml_count']:>5} {s['orphan_assets']:>8}"
            )
        return 0

    if args.command == "fix-platforms":
        from rom_manager.detection.platform_detector import detect_platform

        print("Detecting platforms from folder names…")
        updated = repository.backfill_platforms(detect_platform)
        print(f"Updated: {updated} games")
        return 0

    if args.command == "scrape":
        from rom_manager.scanner.rom_scanner import utc_now
        from rom_manager.scraper.platform_ids import get_system_id
        from rom_manager.scraper.screenscraper import ScreenScraperClient, download_image

        if not config.credentials.screenscraper_user or not config.credentials.screenscraper_pass:
            parser.error(
                "ScreenScraper credentials not set. "
                "Add [screenscraper] user and pass to config.toml."
            )

        client = ScreenScraperClient(
            user=config.credentials.screenscraper_user,
            password=config.credentials.screenscraper_pass,
            dev_id=config.credentials.screenscraper_dev_id,
            dev_password=config.credentials.screenscraper_dev_pass,
        )

        games = repository.get_games_for_scraping(platform=args.platform)
        if not games:
            print("All games already scraped (or no games in library).")
            return 0

        limit = args.limit or len(games)
        print(f"Scraping {min(limit, len(games))} games from ScreenScraper…")
        found = skipped = errors = 0

        with repository.batch() as conn:
            for game in games[:limit]:
                system_id = get_system_id(game["platform"])
                result = client.search(
                    crc32=game["crc32"],
                    md5=game["md5"],
                    sha1=game["sha1"],
                    filename=game["original_filename"],
                    size_bytes=game["size_bytes"],
                    system_id=system_id,
                )
                if result is None:
                    print(f"  [—]   {game['original_filename']}")
                    repository.mark_metadata_scraped(game["id"], conn)  # DB-1: mark as checked
                    skipped += 1
                    continue

                box_art_path = ""
                if args.images and result.box_art_url:
                    img_dir = Path(game["source_path"]).parent / "media" / "images"
                    stem = Path(game["original_filename"]).stem
                    ext = ".png" if ".png" in result.box_art_url.lower() else ".jpg"
                    dest = img_dir / f"{stem}{ext}"
                    if download_image(result.box_art_url, dest):
                        box_art_path = str(dest)
                    else:
                        errors += 1
                        print(
                            f"  [!]   {game['original_filename']}: fallo al descargar la carátula"
                        )

                repository.upsert_metadata(
                    game_id=game["id"],
                    ss_game_id=result.ss_game_id,
                    title=result.title,
                    year=result.year,
                    genre=result.genre,
                    publisher=result.publisher,
                    developer=result.developer,
                    description=result.description,
                    rating=result.rating,
                    box_art_url=result.box_art_url,
                    box_art_path=box_art_path,
                    genres_list=result.genres_list,
                    players=result.players,
                    scraped_at=utc_now(),
                    connection=conn,
                )
                repository.mark_metadata_scraped(game["id"], conn)  # DB-1: mark as checked
                print(f"  [OK]  {game['original_filename']}  →  {result.title}")
                found += 1

        print(f"\nFound: {found}  |  Not found: {skipped}  |  Errors: {errors}")
        return 0

    if args.command == "export-gamelists":
        from rom_manager.scraper.gamelist_writer import write_gamelist

        output_root = args.output_dir or config.library_root
        if output_root is None:
            parser.error(
                "Output directory not specified. "
                "Pass --output-dir or set [library] library_root in config.toml."
            )
        output_root = Path(output_root).resolve()

        platforms = repository.get_scraped_platform_summary()
        if args.platform:
            platforms = [p for p in platforms if p["platform"] == args.platform]

        total_written = 0
        for plat in platforms:
            if plat["scraped"] == 0:
                continue
            entries = repository.get_metadata_for_platform(plat["platform"])
            if not entries:
                continue
            # Determine platform dir: output_root / <platform_slug>
            slug = plat["platform"].lower().replace(" ", "").replace("/", "_")
            platform_dir = output_root / slug
            platform_dir.mkdir(parents=True, exist_ok=True)
            out = write_gamelist(platform_dir, entries)
            print(f"  [{plat['platform']}]  {out}  ({len(entries)} entries)")
            total_written += 1

        if total_written == 0:
            print("No scraped metadata found. Run 'rommgr scrape' first.")
        else:
            print(f"\nExported {total_written} gamelist.xml file(s).")
        return 0

    if args.command == "sync":
        from rom_manager.config import build_cloud_sync_sources

        # REV43-52: previously only config.sync.sync_sources — this headless
        # command silently skipped the RA config/cheats/playtime sources that
        # the web UI's sync already includes (same helper, one behavior).
        sources = build_cloud_sync_sources(config)
        if not sources:
            print(
                "[ERROR] No hay fuentes de sync configuradas. Añade [[sync.sources]] en config.toml."
            )
            return 1

        dry_run = not args.apply
        if dry_run:
            print("DRY RUN — usa --apply para transferir archivos.\n")

        transport = RcloneTransport(rclone=config.rclone_binary)
        total_up = total_down = total_ok = total_err = 0
        any_error = False

        for source in sources:
            saves_dir = Path(source.local_dir)
            if not saves_dir.exists():
                print(f"  [ERROR] {source.name}: directorio no encontrado: {source.local_dir}")
                any_error = True
                continue

            exts = tuple() if source.sync_all else config.save_extensions
            try:
                from rom_manager.sync.delta_cache import DeltaCache

                _delta = DeltaCache(config.data_dir) if not dry_run else None
                result, decisions = sync_saves(
                    saves_dir,
                    saves_remote=source.remote,
                    transport=transport,
                    repository=repository,
                    save_extensions=exts,
                    state_extensions=config.state_extensions if not source.sync_all else tuple(),
                    states_remote=None,
                    dry_run=dry_run,
                    delta_cache=_delta,
                )
            except RcloneError as exc:
                print(f"  [ERROR] {source.name}: {exc}")
                any_error = True
                continue

            if not args.quiet:
                for d in decisions:
                    if d.action == "up_to_date":
                        continue
                    tag = {"upload": "↑", "download": "↓", "conflict": "⚠"}.get(d.action, d.action)
                    print(f"  [{tag}] {source.name} / {d.relative}")

            verb = "Haría " if dry_run else ""
            delta_note = f" Δ:{result.delta_skipped}" if result.delta_skipped else ""
            print(
                f"  {source.name}: {verb}↑{result.uploaded} ↓{result.downloaded} "
                f"= {result.up_to_date} conf:{result.conflicts} err:{result.errors}{delta_note}"
            )
            total_up += result.uploaded
            total_down += result.downloaded
            total_ok += result.up_to_date
            total_err += result.errors
            if result.errors:
                any_error = True

        print(
            f"\nTotal: ↑{total_up} subidos  ↓{total_down} descargados  "
            f"={total_ok} ya al día  err:{total_err}"
        )

        if args.notify:
            from rom_manager.utils.notifier import notify

            parts = []
            if total_up:
                parts.append(f"{total_up} subidos")
            if total_down:
                parts.append(f"{total_down} descargados")
            body = ", ".join(parts) if parts else "Todo al día"
            if total_err:
                body += f" ({total_err} errores)"
            notify("Retro Vault — Sync completado", body)

        return 1 if any_error else 0

    if args.command == "health":
        from rom_manager.utils.health_checker import check_library_health

        print("Verificando integridad de la biblioteca…")
        summary = check_library_health(repository)

        if not args.quiet:
            for r in summary.results:
                tag = "CORRUPTO" if r.status == "corrupted" else "FALTANTE"
                title = r.canonical_title or Path(r.source_path).name
                print(f"  [{tag}]  [{r.platform}]  {title}")
                print(f"          {r.source_path}")
                if r.status == "corrupted":
                    print(f"          SHA1 almacenado: {r.stored_sha1}…")
                    print(f"          SHA1 actual:     {r.computed_sha1}…")

        issues = summary.corrupted + summary.missing
        print(
            f"\nVerificados: {summary.ok}  |  Corruptos: {summary.corrupted}  |  Faltantes: {summary.missing}"
        )

        # Persist schedule so the daemon doesn't re-run immediately
        try:
            from rom_manager.web.server import _write_health_schedule

            _write_health_schedule(
                config, ok=summary.ok, corrupted=summary.corrupted, missing=summary.missing
            )
        except Exception:
            _logger.debug("Failed to persist health schedule", exc_info=True)

        if args.notify:
            from rom_manager.utils.notifier import notify

            if issues:
                notify(
                    "Retro Vault — Health Check",
                    f"⚠ {summary.corrupted} corruptos, {summary.missing} faltantes",
                )
            else:
                notify(
                    "Retro Vault — Health Check", f"✓ {summary.ok} ROMs verificados, sin problemas"
                )

        return 1 if issues else 0

    if args.command == "organize-source":
        from rom_manager.web.inbox_pipeline import _run_inbox_pipeline
        from rom_manager.web.jobs.manager import JobManager

        source_path = args.source_path.resolve()
        if not source_path.exists() or not source_path.is_dir():
            parser.error(f"Source path does not exist or is not a directory: {source_path}")
        target_root = args.target_root.resolve() if args.target_root else config.library_root

        exclude_platforms = set(args.exclude_platform)

        if not args.apply:
            from collections import Counter

            print("DRY RUN — no files will be changed. Pass --apply to organize.")
            # Same prefix match step 6 (organize) uses live — a recursive DB
            # query, not a filesystem walk, so it also counts nested folders
            # (_build_inbox_scan only looks at the top level — a much smaller,
            # misleading number for a folder like Unknown/ with subfolders).
            with repository.connect() as conn:
                rows = conn.execute(
                    "SELECT platform FROM games WHERE LOWER(source_path) LIKE ?",
                    (str(source_path).lower() + "%",),
                ).fetchall()
            if not rows:
                print(
                    f"No hay archivos ya escaneados bajo {source_path} "
                    "— ejecuta 'rommgr scan' primero."
                )
                return 0
            included = [r for r in rows if (r["platform"] or "") not in exclude_platforms]
            excluded = [r for r in rows if (r["platform"] or "") in exclude_platforms]
            by_platform = Counter(row["platform"] or "(sin identificar)" for row in included)
            print(f"Origen: {source_path}")
            print(f"Archivos que se organizarían: {len(included)}")
            for plat, n in by_platform.most_common():
                print(f"  {plat}: {n}")
            if excluded:
                print(f"Excluidos por --exclude-platform (quedan intactos): {len(excluded)}")
            print("\nRun with --apply to organize.")
            return 0

        # Files of an excluded platform must never reach the pipeline at all —
        # step 1 (extraction) already routes complete arcade ZIP sets straight
        # to the arcade folder by CRC content, independent of step 6's move,
        # so filtering only the final move would be too late. Set them aside
        # on disk first and restore them to their exact original path once the
        # pipeline is done, whether it succeeded or not.
        _shelved: list[tuple[Path, Path]] = []  # (temp_path, original_path)
        if exclude_platforms:
            import shutil as _shutil
            import tempfile as _tempfile

            with repository.connect() as conn:
                placeholders = ",".join("?" for _ in exclude_platforms)
                rows = conn.execute(
                    f"SELECT source_path FROM games WHERE LOWER(source_path) LIKE ? "
                    f"AND platform IN ({placeholders})",
                    (str(source_path).lower() + "%", *exclude_platforms),
                ).fetchall()
            if rows:
                holding_dir = Path(_tempfile.mkdtemp(prefix="rommgr_organize_source_excluded_"))
                for i, row in enumerate(rows):
                    original = Path(row["source_path"])
                    if not original.exists():
                        continue
                    temp_path = holding_dir / f"{i}_{original.name}"
                    _shutil.move(str(original), str(temp_path))
                    _shelved.append((temp_path, original))
                print(
                    f"{len(_shelved)} archivo(s) de {', '.join(sorted(exclude_platforms))} "
                    "apartados temporalmente, se restauran a su ruta exacta al terminar."
                )

        try:
            job_manager = JobManager()
            _run_inbox_pipeline(
                str(source_path),
                str(target_root) if target_root else "",
                args.delete_source,
                repository,
                config,
                job_manager,
            )
            result = job_manager.get_job("inbox")["result"] or {}
        finally:
            for temp_path, original in _shelved:
                original.parent.mkdir(parents=True, exist_ok=True)
                _shutil.move(str(temp_path), str(original))
            if _shelved:
                print(
                    f"{len(_shelved)} archivo(s) restaurados a su ruta original — "
                    "ejecuta 'rommgr scan' para que vuelvan a aparecer en la base de datos."
                )

        if result.get("error"):
            print(f"Error: {result['error']}")
            return 1
        print(f"Organizados:                    {result.get('organized', 0)}")
        print(f"Duplicados exactos descartados: {result.get('duplicates_removed', 0)}")
        print(f"Conflictos resueltos por RA:     {result.get('ra_resolved', 0)}")
        print(f"Conflictos sin resolver:         {result.get('conflicts_unresolved', 0)}")
        for err in result.get("organize_errors", []):
            print(f"  ! {err}")

        # ANBERNIC-ROMTREE-2: "mover... y borrar las vacías" — solo si de verdad
        # no queda ni un archivo dentro (nunca se fuerza el borrado).
        remaining_files = [p for p in source_path.rglob("*") if p.is_file()]
        if not remaining_files:
            for d in sorted((p for p in source_path.rglob("*") if p.is_dir()), reverse=True):
                try:
                    d.rmdir()
                except OSError:
                    pass
            try:
                source_path.rmdir()
                print(f"Carpeta de origen vacía eliminada: {source_path}")
            except OSError as exc:
                print(f"No se pudo eliminar la carpeta de origen ({source_path}): {exc}")
        else:
            print(
                f"Quedan {len(remaining_files)} archivo(s) en el origen "
                "(conflictos u otros no procesados) — no se borra la carpeta."
            )
        return 0

    if args.command == "decompress":
        from rom_manager.converters.zip_extractor import extract_directory

        source_path = args.source_path.resolve()
        if not source_path.exists() or not source_path.is_dir():
            parser.error(f"Source path does not exist or is not a directory: {source_path}")

        dry_run = not args.apply
        if dry_run:
            print("DRY RUN — no files will be changed. Pass --apply to decompress.")
        if args.delete_source and not args.apply:
            print("Note: --delete-source has no effect without --apply.")
        print()

        summary = extract_directory(source_path, delete_source=args.delete_source, dry_run=dry_run)

        for result in summary.results:
            if result.success:
                print(
                    f"  [OK]   {result.zip_path.name}  ->  {len(result.extracted_files)} archivo(s)"
                )
            elif result.skipped_reason:
                print(f"  [SKIP] {result.zip_path.name}  -  {result.skipped_reason}")
            elif result.error:
                print(f"  [FAIL] {result.zip_path.name}  -  {result.error}")

        print()
        if dry_run:
            print(f"Se descomprimirían: {summary.extracted}  |  Se saltarían: {summary.skipped}")
            if summary.extracted:
                print("Run with --apply to decompress.")
        else:
            print(
                f"Descomprimidos: {summary.extracted}  |  Saltados: {summary.skipped}  |  "
                f"Fallidos: {summary.failed}"
            )
            if summary.extracted:
                print("Re-run 'rommgr scan' to update the library database.")
        return 0

    if args.command == "resolve-duplicates":
        from rom_manager.services.ra_duplicates_service import apply_all_review_recommendations
        from rom_manager.web.builders.common import _repo_for_path
        from rom_manager.web.builders.duplicates import _build_review_queue

        # LIBRARY-AUDIT-4: MAME/FBNeo/Arcade share SHA1s with clones/parent sets
        # on purpose (docs/arcade-setup.md) — never auto-resolve those groups.
        _ARCADE_PLATFORMS = {"MAME", "FBNeo", "Arcade"}

        queue = _build_review_queue(repository, repository_android, config)
        arcade_groups = [g for g in queue["groups"] if g.get("platform") in _ARCADE_PLATFORMS]
        console_groups = [g for g in queue["groups"] if g.get("platform") not in _ARCADE_PLATFORMS]
        print(
            f"Grupos totales: {len(queue['groups'])}  "
            f"({len(arcade_groups)} arcade excluidos, {len(console_groups)} de consola)"
        )

        if not args.apply:
            print("DRY RUN - no files will be changed. Pass --apply to resolve.\n")
            # Mirror apply_all_review_recommendations' own branching exactly —
            # a group with a "disk"/"collision" reason never goes through
            # resolve_duplicate_ra (its "recommended" entry is not what
            # decides the outcome there), it's deferred to apply_ra_conflicts,
            # which itself never touches _MULTI_DISC_RISK_PLATFORMS (PSX/PS2/
            # Saturn/Dreamcast/GameCube/Wii) — showing a plain keep/discard
            # line for those would wrongly suggest a different disc of a
            # multi-disc game is "just a duplicate" about to be discarded.
            plain_groups = [
                g for g in console_groups if not (set(g.get("reasons", ())) & {"disk", "collision"})
            ]
            conflict_groups = [
                g for g in console_groups if set(g.get("reasons", ())) & {"disk", "collision"}
            ]
            multi_disc_risk = sum(
                1 for g in conflict_groups if "multi_disc_risk" in g.get("reasons", ())
            )

            for group in plain_groups:
                entries = group.get("entries", [])
                recommended = next((e for e in entries if e.get("recommended")), None)
                if not recommended:
                    continue
                discard = [e["filename"] for e in entries if e is not recommended]
                if not discard:
                    continue
                print(
                    f"  [{group.get('platform')}] conservar: {recommended['filename']}"
                    f"  ->  descartar: {', '.join(discard)}"
                )
            if conflict_groups:
                print(
                    f"\n{len(conflict_groups)} grupo(s) con conflicto de nombre (colision al "
                    "renombrar) se resuelven aparte via apply_ra_conflicts, no por esta lista:"
                )
                print(
                    f"  - {multi_disc_risk} en plataformas con riesgo de multi-disco "
                    "(PSX/PS2/Saturn/Dreamcast/GameCube/Wii) — nunca se tocan automaticamente"
                )
                print(
                    f"  - {len(conflict_groups) - multi_disc_risk} en el resto de plataformas "
                    "— se resuelven por logros RA si los hay, si no quedan sin resolver"
                )
            print("\nRun with --apply to resolve.")
            return 0

        for group in arcade_groups:
            repository.exclude_duplicate_group(group["group_key"], reason="arcade_intentional")
            if repository_android is not repository:
                repository_android.exclude_duplicate_group(
                    group["group_key"], reason="arcade_intentional"
                )

        # Re-read the queue now that arcade groups are permanently excluded.
        queue = _build_review_queue(repository, repository_android, config)

        def _get_repo(path_str: str):
            return _repo_for_path(path_str, repository, repository_android, config)

        result = apply_all_review_recommendations(
            _get_repo, [repository, repository_android], config, queue
        )
        print(f"Resueltos: {result.get('resolved', 0)}")
        for err in result.get("errors", []):
            print(f"  ! {err}")
        return 0

    if args.command == "init-config":
        from rom_manager.wizard import run_wizard

        return run_wizard(Path.cwd())

    if args.command == "serve":
        from rom_manager.web.server import InsecureExposureError, serve

        host = args.host or config.web_host
        port = args.port or config.web_port
        allow_insecure = config.web_allow_lan or getattr(args, "allow_insecure", False)
        lan_mode = host in ("0.0.0.0", "")
        local_url = f"http://127.0.0.1:{port}/" if lan_mode else f"http://{host}:{port}/"
        print(f"Retro Vault — {local_url}")
        if lan_mode:
            from rom_manager.web.lan import _check_firewall, lan_urls

            for url in lan_urls(port):
                print(f"           LAN — {url}")
            if not _check_firewall(port):
                print(
                    f"\n  AVISO: el puerto {port} puede estar bloqueado por el Firewall de Windows.\n"
                    f"  Si la Anbernic no conecta, ejecuta como Administrador:\n"
                    f"    .\\scripts\\open-firewall-port.ps1\n"
                )
        print("Press Ctrl+C to stop.")
        try:
            serve(
                host=host,
                port=port,
                repository=repository,
                config=config,
                repository_android=repository_android,
                tray=getattr(args, "tray", False),
                allow_insecure=allow_insecure,
            )
        except InsecureExposureError as exc:
            print(f"\n{exc}")
            return 2
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
