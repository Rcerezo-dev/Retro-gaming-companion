# BUG: Organizar tab "Eliminar duplicados" button in collision section — doesn't work

## Symptoms
- In Organizar tab, when viewing a "Colisión de plan" section
- Click "Eliminar duplicados" button
- Nothing happens, button appears to be non-functional

## Affected Files
- `src/rom_manager/web/static/js/tabs/organize.js` (deleteCollisionDuplicates function at line 315)

## Root Cause
The DOM selector used to find collision rows was broken:
```javascript
'#plan-content table:has(thead:contains("ROM")) tbody tr td[data-game-id]'
```

Issues:
1. `:contains()` is a jQuery pseudo-selector, not standard CSS
2. `:has()` pseudo-selector was not being used correctly
3. The selector couldn't find the collision rows, resulting in empty collisionRows array
4. The function would return early at line 321 with "No hay duplicados en colisión" message

## Fix Applied
Changed the selector to use standard DOM API:
```javascript
const collisionHeader = Array.from(document.querySelectorAll('#plan-content h3'))
  .find(h => h.textContent.includes('Colisión de plan'));

const collisionRows = collisionHeader
  ? collisionHeader.parentElement.querySelectorAll('td[data-game-id]')
  : document.querySelectorAll('#plan-content td[data-game-id]');
```

This approach:
1. Finds the "Colisión de plan" header
2. Gets its parent div (the collision section)
3. Selects all `td[data-game-id]` elements within that section
4. Falls back to finding all collision rows if header not found

## Status
✅ FIXED in this session
