# BUG: Organizar tab — window._platBadge is not a function

## Symptoms
- In Organizar tab, when trying to display games with naming problems
- Error: `window._platBadge is not a function`
- List of games doesn't render

## Root Cause
The function `_platBadge` was defined in games.js but not exported, and thus not available on the window object.

## Fix Applied
1. Added `export` to `_platBadge` function definition in games.js (line 199)
2. Added `_platBadge` to import statement in main.js
3. Added `_platBadge` to Object.assign window exports in main.js

## Status
✅ FIXED in this session
