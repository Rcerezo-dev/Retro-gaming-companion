# BUG: Tab "Duplicados" — shows "sin duplicados" but likely has duplicates

## Symptoms
- Tab "Duplicados" shows "sin duplicados" (no duplicates)
- Was unreliable due to cascading errors from other tabs

## Root Cause
Cascading error from the _h function export issue affecting other tabs.

## Status
✅ FIXED: All related export issues have been fixed:
- Added _h function export to main.js
- Added _platBadge export to main.js
- Fixed RenamePlan.operations error in duplicates handler
- Fixed collision delete button selector

The Duplicados tab should now display correctly. If it still shows "sin duplicados", verify:
1. Run a scan first to ensure there's data
2. Check browser console for any remaining errors
