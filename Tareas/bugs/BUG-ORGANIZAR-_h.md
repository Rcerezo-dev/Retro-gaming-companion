# BUG: Tab "Organizar" — window._h is not a function

## Symptoms
- Tab "Organizar" shows error: `window._h is not a function`
- Table that was previously visible doesn't render
- Page doesn't display the plan/organization interface

## Affected Files
- `src/rom_manager/web/static/js/tabs/organize.js`
- Possibly: `src/rom_manager/web/static/js/main.js` (exports)

## Root Cause
The function `_h` (HTML escape helper) is not being exported on the window object. It's used for HTML sanitization in the organize tab but hasn't been set on window.

## Steps to Reproduce
1. Open app
2. Click "Organizar" in left sidebar
3. See error message and blank table

## Status
✅ FIXED: Added _h function definition to main.js and exported on window object

## Related Issues
- BUG-COL-1: Coleccion tab had same _h error (also fixed)
- BUG-ORG-RA-RENAME-PLAN: RenamePlan missing operations attribute
- BUG-PLATBADGE: window._platBadge is not a function


