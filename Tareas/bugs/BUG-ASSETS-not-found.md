# BUG: Tab "Assets" — shows "not found" instead of assets list

## Symptoms
- Tab "Assets" displays "not found" error
- No assets are listed

## Root Cause
**FIXED**: The `/api/assets` endpoint handler was missing from `collection.py`. The endpoint was defined in OpenAPI spec and had a response builder function but was never registered as an actual handler.

## Fix Applied
Added `/api/assets` GET endpoint handler to `src/rom_manager/web/handlers/collection.py`:
- Imported `_build_assets` from response_builders
- Added handler that accepts `root` query parameter
- Handler calls `_build_assets(assets_repo, source_root=src_root)` and returns JSON

## Status
✅ FIXED in this session
