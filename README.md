# ROM Manager Local

A local CLI tool for scanning, identifying, and organizing retro game ROM libraries.

Designed for a shared setup: one ROM collection that works both on a Windows PC (desktop emulators) and an Anbernic RG 556 (RetroArch on Android), with save sync via cloud storage coming in a later phase.

---

## Features

- Recursive scan of any folder — classifies every file as ROM, save, frontend asset, system support, or unknown
- SHA1 + MD5 + CRC32 hashing for every ROM
- Platform detection by file extension
- Region detection from filename (No-Intro parentheses style, GoodTools bracket codes, plain-text fallbacks)
- Catalog matching against local No-Intro and Redump DAT files (SHA1 lookup → canonical title)
- SQLite inventory at `.rommgr/library.sqlite` — survives re-scans via upsert
- No runtime dependencies — pure Python stdlib

---

## Installation

Requires **Python 3.11+**.

```bash
# Clone the repo
git clone https://github.com/your-username/Retro_gaming_app.git
cd Retro_gaming_app

# Install (editable)
pip install -e .

# Install with dev tools (pytest)
pip install -e .[dev]
```

> If you use Conda, create an environment first:
> ```bash
> conda create -n rom_manager python=3.12
> conda activate rom_manager
> pip install -e .[dev]
> ```

On Windows, a convenience launcher is included so you do not need to modify PATH:

```bat
scripts\rommgr.cmd <command>
```

---

## Usage

```bash
# Scan a folder and hash all ROMs
rommgr scan <path-to-roms>

# Show library summary
rommgr status

# Match unresolved ROMs against No-Intro / Redump catalogs
rommgr match

# List ROMs that have not been matched yet
rommgr unresolved
```

### Example session

```
> rommgr scan D:\ROMs
Scanned: D:\ROMs
Files seen:            4 821
ROMs detected:         4 203
Saves detected:        312
Assets detected:       180
Unknown files:         126

> rommgr match
Loading catalogs…
  No-Intro: 98 432 entries
  Redump:   45 678 entries

Matching 4 203 unresolved ROMs…
Matched:   4 101
Not found: 102
```

---

## Catalog DAT files

The matcher reads `.dat` files in Logiqx XML format (the standard used by No-Intro and Redump).

Place them in:

```
.rommgr/
  catalogs/
    nointro/   ← cartridge DATs (GB, GBC, GBA, NES, SNES, N64, DS, …)
    redump/    ← disc DATs (PSX, PS2, PSP, GameCube, Wii, Dreamcast, …)
```

Download DATs from [No-Intro](https://www.no-intro.org/) and [Redump](http://redump.org/).

---

## Project structure

```
src/rom_manager/
  cli.py                      # Commands: scan, status, match, unresolved
  config.py                   # AppConfig (paths, extensions)
  logging_utils.py
  catalog/
    catalog_loader.py         # Parse Logiqx XML DATs → sha1→CatalogEntry
    matcher.py                # CatalogMatcher: SHA1 lookup across all DATs
  database/
    schema.py                 # SQLite schema + automatic migrations
    repository.py             # LibraryRepository (upsert, batch, match updates)
  detection/
    file_classifier.py        # ROM / save / asset / system / unknown
    platform_detector.py      # Platform from extension
    region_parser.py          # Region from filename
    filename_normalizer.py
    set_detector.py
  hashing/
    hash_calculator.py        # SHA1 + MD5 + CRC32, 1 MB chunks
  scanner/
    rom_scanner.py            # Main scan loop
    asset_scanner.py
    save_scanner.py
tests/
  test_catalog_matcher.py
  test_file_classifier.py
  test_filename_normalizer.py
  test_region_parser.py
```

---

## Roadmap

| Phase | Description | Status |
|---|---|---|
| 1 | Scan, hash, SQLite inventory, basic CLI | Done |
| 2 | Catalog matching via SHA1 (No-Intro + Redump) | Done |
| 3 | Plan + Apply: safe rename and move operations | Pending |
| 4 | Duplicate detection, incremental scans, reports | Pending |
| 5 | Save sync (PC ↔ Anbernic RG 556) via rclone + Dropbox | Pending |
| 6 | Local web frontend | Pending |

---

## Running tests

```bash
pytest
```

96 tests, no external dependencies required.

---

## License

MIT
