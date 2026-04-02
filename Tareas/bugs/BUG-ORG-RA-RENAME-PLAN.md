# BUG: Organizar tab "Resolver por RA" — RenamePlan missing operations attribute

## Symptoms
- Click "Resolver por RA" button in Organizar tab
- Error response: `{"error": "'RenamePlan' object has no attribute 'operations'"}`
- RA conflict resolution doesn't work

## Root Cause
In `handlers/duplicates.py::_apply_ra_conflicts()` at line 343, code was trying to access `plan.operations` which doesn't exist. The RenamePlan class only has `pending`, `already_correct`, and `conflicts` attributes.

## Fix Applied
Changed line 343 in `src/rom_manager/web/handlers/duplicates.py`:
- **Before**: `for op in (list(plan.conflicts) + list(plan.operations))[:3]:`
- **After**: `for op in (list(plan.conflicts) + list(plan.pending))[:3]:`

This allows the diagnostic sampling code to collect samples from both conflicts and pending operations.

## Status
✅ FIXED in this session
