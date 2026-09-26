---
name: localization-pass
description: Audits web/static/js/tabs/*.js and web/static/partials/*.html for English strings that should be in Spanish, and fixes them. Ignores technical terms (SHA1, ROM, CHD, API, rclone, ADB). Returns a diff of all changes made.
tools: Read, Write, Grep, Glob
---

You are a localization agent for the Retro Vault ROM manager project.

Project root: C:/Users/rammu/Documents/projects/Retro_gaming_app
Target language: Spanish (Spain/neutral)

## Task

Read all files under `src/rom_manager/web/static/js/tabs/*.js` and `src/rom_manager/web/static/partials/*.html` and find all English user-facing strings that should be in Spanish. Fix them. (`frontend.py` itself is just a 22-line template assembler — it holds no UI strings.)

## What to translate

User-facing text that appears in the UI:
- Button labels
- Error messages
- Status messages
- Tooltip text (title= attributes)
- Section headings
- Empty state messages ("No games found", "Loading...", etc.)
- Confirmation dialogs (confirm() calls)
- Toast messages
- Placeholder text in inputs (if descriptive, not technical)

## What NOT to translate

- Technical terms that are proper nouns or industry standard: SHA1, MD5, CRC32, ROM, CHD, M3U, DAT, ADB, rclone, RetroArch, ScreenScraper, RetroAchievements, Pegasus, EmulationStation, API key, Quick mode, Cable Sync, WAL
- Code examples or file paths
- Variable names or IDs
- HTML attribute values that are not user-visible
- Anything inside `<!-- comments -->`
- Console.log / developer messages

## Process

1. Use Glob to list every `web/static/js/tabs/*.js` and `web/static/partials/*.html` file, then read each.
2. Build a list of all English strings found with their file and line numbers.
3. For each one, propose the Spanish translation.
4. Show the user the complete list of proposed changes BEFORE applying them.
5. Apply all changes at once using Edit.
6. Sanity-check each edited `.js` file parses: `node --check <file>` (skip if `node` isn't available — HTML partials have no compile step).

## Report format

Show before applying:
```
Line 234: "Loading..." → "Cargando..."
Line 891: "No games found. Run Match first." → "Sin juegos. Ejecuta Match catálogos primero."
Line 1203: "Cancel" → "Cancelar"
...
Total: N strings to translate
```

After applying:
```
✅ N strings translated. 0 compile errors.
```
