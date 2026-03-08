from __future__ import annotations

import argparse
from pathlib import Path

from rom_manager.config import load_config
from rom_manager.database import LibraryRepository
from rom_manager.logging_utils import configure_logging
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
