# BUG: Asset images return 404 — Missing `/api/asset-image` endpoint

## Symptoms
- Game cover art images don't load (404 errors)
- Browser console shows: `GET /api/asset-image?game_id=XXXXX [404 Not Found]`
- Affects all tabs that display game covers (Games, Collection, Overview)

## Affected Files
- Frontend calls: `games.js`, `collection.js`, `overview.js`
- Missing handler in: `handlers/collection.py`

## Root Cause
The `/api/asset-image` endpoint was defined in OpenAPI spec but never implemented in handlers. The endpoint needs to:
1. Accept `game_id` parameter
2. Query game_metadata for box_art_path
3. Serve the image file with correct MIME type

## Fix Applied
Added `/api/asset-image` GET endpoint to `src/rom_manager/web/handlers/collection.py`:
- Validates game_id parameter (required, must be integer)
- Queries game_metadata table for box_art_path
- Returns 404 if no metadata or file doesn't exist
- Serves image file with correct MIME type
- Error handling for missing/unreadable files

## Status
✅ FIXED in this session
