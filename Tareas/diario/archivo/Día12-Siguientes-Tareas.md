# Día 12 — Roadmap completo

> Fecha: 2026-03-17
> Estado al cierre de sesión: pipeline verde, BD optimizada, UI limpia, grid view y cable preview implementados.

---

## 📋 Carry-over del Día 11

| ID | Tarea | Estado |
|----|-------|--------|
| STRUCT-4 | Configurar RetroArch PC → Saving → Savefile Directory | ⏳ Acción de usuario |
| STRUCT-3 | Actualizar config.toml con ruta de saves centralizada | ⏳ Después de STRUCT-4 |
| STRUCT-5 | Verificar que gamelist.xml se exporta en subcarpeta de plataforma | ✅ Ya correcto en server.py (línea 2634) |

---

## Hecho en esta sesión

### `/test-pipeline` — PASS 6/6
- Scan, match, plan, prune stale: todos verdes
- **Bug encontrado y corregido**: `schema.py` intentaba crear `idx_games_last_played` antes de que la columna `last_played_at` existiera en BDs nuevas → añadidas `play_status` y `last_played_at` al `CREATE TABLE` original

### `/db-check` → aplicados todos los fixes
| ID | Fix | Estado |
|----|-----|--------|
| IDX-1 | `idx_games_canonical_title` añadido (64 refs en código) | ✅ |
| IDX-2 | `idx_games_play_status` e `idx_games_match_confidence` añadidos | ✅ |
| SQL-1 | `_alter_table_add_column()` con validación de whitelist — elimina f-string sin validar | ✅ |

### `/ui-audit` → aplicados los 3 fixes de mayor impacto
| ID | Fix | Estado |
|----|-----|--------|
| UI-EN | Strings residuales en inglés: `Loading…`, `Prev/Next`, `Page X of Y`, `/ page`, `Conflicts —`, `file(s)` | ✅ |
| UI-DEV | Todos los "Anbernic" visibles al usuario → `_devName` / "Consola Android" | ✅ |
| UI-ERR | 8 `alert()` sin guía de acción → añadida línea de acción contextual | ✅ |

### F5 — Vista de cuadrícula (grid view)
- Toggle `☰ / ⊞` en la barra de Games, persistido en `localStorage`
- Cards con thumbnail (`/api/asset-image`), título truncado y badge de plataforma
- `setGamesView()` + `_renderGamesGrid()` en `frontend.py`

### U3 — Preview antes del Cable Sync
- Nuevo endpoint `GET /api/cable-sync-preview`
- Botón "🔍 Ver resumen" en la pestaña Cable Sync
- Muestra: "PC: N saves · Consola: M saves · Se copiarán ≈ K archivos"
- Graceful cuando el dispositivo Android no es accesible (modo ADB)

---

## Pendiente (requiere hardware o acción del usuario)

| ID | Tarea | Tipo |
|----|-------|------|
| STRUCT-4 | Configurar RetroArch PC → saves centralizados | Usuario |
| STRUCT-3 | Actualizar config.toml tras STRUCT-4 | Usuario |
| V1 | Validar sync automático con SD card | Hardware |
| V2 | Validar migración a dos bases de datos | Hardware |
| V3 | Validar Inbox end-to-end | Hardware |
| V4 | RetroAchievements con API key real | Usuario |
| V5 | Guía Termux en la consola Android | Hardware |
| B1 | Renombrador en consola Android no reduce la cola | Hardware |

---

## Commits de esta sesión

```
49b476a  fix(db): add missing indexes + safe ALTER TABLE validation
de3cca4  fix(ui): translate residual EN strings, standardize device name, actionable errors
```
(F5 y U3 estaban ya en el árbol desde una sesión anterior — sin commit nuevo)

---

## Resumen de estado

| Bloque | Total | ✅ Hecho | ⏳ Pendiente |
|--------|-------|----------|-------------|
| Carry-over Día 11 | 3 | 1 (STRUCT-5) | 2 (usuario) |
| Pipeline / DB / UI | 3 skills | ✅ | — |
| F5 grid view | 1 | ✅ | — |
| U3 cable preview | 1 | ✅ | — |
| Validación hardware | 5 | 0 | 5 |
| Bugs (hardware) | 1 | 0 | 1 |
| **Total código** | **6** | **6** | **0** |
