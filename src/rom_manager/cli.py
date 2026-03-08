from __future__ import annotations

import argparse
from pathlib import Path

from rom_manager.catalog.matcher import CatalogMatcher
from rom_manager.config import load_config
from rom_manager.converters.chd_converter import convert_directory
from rom_manager.database import LibraryRepository
from rom_manager.logging_utils import configure_logging
from rom_manager.planner import build_plan
from rom_manager.scanner import scan_library


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rommgr")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan ROM and save files.")
    scan_parser.add_argument("source_path", type=Path, help="Folder to scan.")

    subparsers.add_parser("status", help="Show library summary.")

    subparsers.add_parser(
        "unresolved",
        help="List ROMs not yet matched against a catalog.",
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
        default="chdman",
        metavar="PATH",
        help="Path to the chdman binary (default: 'chdman', assumes it is in PATH).",
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
            chdman=args.chdman,
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
        matched = 0
        unmatched = 0
        with repository.batch() as conn:
            for game in games:
                result = matcher.match(game.sha1)
                if result is not None:
                    repository.update_match(
                        game.source_path,
                        canonical_title=result.title,
                        match_confidence=result.confidence,
                        catalog_source=result.catalog_source,
                        connection=conn,
                    )
                    matched += 1
                else:
                    unmatched += 1

        print(f"\nMatched:   {matched}")
        print(f"Not found: {unmatched}")
        return 0

    if args.command == "unresolved":
        games = repository.get_unresolved_games()
        if not games:
            print("No unresolved games.")
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

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
