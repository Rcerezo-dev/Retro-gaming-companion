# BUG: Delete-all duplicates shows files deleted but they still exist on disk

## Symptoms
- Click "Eliminar todos los duplicados" button
- Response says "✓ 550 eliminados"
- After reload, the exact same list of ROMs appears
- Files actually still exist on disk (not deleted)

## Affected Files
- `src/rom_manager/web/handlers/duplicates.py::_delete_all_duplicates()`
- `src/rom_manager/web/static/js/tabs/duplicates.js::deleteAllDuplicates()`

## Root Cause
Investigating — likely one of:
1. Database entries are deleted but files aren't actually deleted from disk
2. `os.remove()` is failing silently but still being counted as success
3. Files are at different paths than what's in the database
4. Duplicate detection is using stale data

## Steps to Reproduce
1. Open app
2. Go to Duplicados tab
3. Click "Eliminar todos los duplicates"
4. Wait for completion
5. Observe file count reported (e.g., 550)
6. Reload duplicates list
7. Same files still appear

## Diagnostics Added
Enhanced both backend and frontend with detailed logging:

**Backend (`handlers/duplicates.py`):**
- Added verbose logging for each deletion attempt
- Tracking: file exists, file deleted, DB deleted
- Returns diagnostics array (first 10 items) in response

**Frontend (`tabs/duplicates.js`):**
- Logs diagnostics to browser console
- Warns if files still exist after delete-all

## Testing Steps
1. Click "Eliminar todos los duplicates"
2. Open browser console (F12)
3. Look for "Delete-all diagnostics" log entry
4. Check if files show `"deleted_file": true` and `"deleted_db": true`
5. If files are not being deleted, diagnostics will show `"deleted_file": false` with error details
6. Report the diagnostic output along with any error messages

## Status
⏳ INVESTIGATING: Added diagnostic logging to identify root cause
