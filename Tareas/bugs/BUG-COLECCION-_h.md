# BUG: Tab "Coleccion" — window._h is not a function

## Symptoms
- Tab "Coleccion" shows error: `window._h is not a function`
- Collection data doesn't render

## Root Cause
The function `_h` (HTML escape helper) was not being exported on the window object.

## Status
✅ FIXED: Added _h function definition to main.js and exported on window object

## Related Issues
- BUG-ORG-1: Organizar tab had same _h error (also fixed)
- BUG-PLATBADGE: window._platBadge export (fixed)
