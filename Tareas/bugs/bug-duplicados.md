# Diario de bugs: pestaña Duplicados

---

## BUG-DUP-1 — "Eliminar todo" falla: 286 grupos mostrados, 100 no se pueden eliminar

**Funciones implicadas:**
- `GET /api/duplicates` → `response_builders._build_duplicates_two_repos`
- `POST /api/duplicates/delete-all` → `handlers/duplicates._delete_all_duplicates`

### Síntoma

La UI muestra 286 grupos de duplicados. Al pulsar "Eliminar todos", el resultado dice
que ~100 no se han podido eliminar (`failed`). No es un error de permisos aleatorio:
el número de failed es consistente.

### Causa raíz identificada (2026-03-31)

Hay un **desajuste estructural** entre lo que muestra la UI y lo que procesa el backend:

**GET /api/duplicates** usa `_build_duplicates_two_repos` que combina tres tipos de grupos:
1. Grupos con ≥2 copias dentro del PC
2. Grupos con ≥2 copias dentro de Android
3. **Grupos donde el mismo SHA1 aparece en PC Y Android** (mismo juego en ambos dispositivos)

El tipo 3 se añade explícitamente en `response_builders.py:896-897`:
```python
for sha1 in set(pc_sha1_map) & set(android_sha1_map):
    combined.append(DuplicateGroup(sha1=sha1, entries=pc_sha1_map[sha1] + android_sha1_map[sha1]))
```

Estos son **copias intencionales PC↔Android** — el mismo juego en ambos dispositivos.
La UI incluso lo dice en la barra de contexto: *"las copias PC↔Anbernic se excluyen"*,
pero el backend las incluye. Contradicción directa.

**POST /api/duplicates/delete-all** llama a `repository.get_duplicate_groups()` —
solo la BD de PC, sin saber nada de Android. Cuando intenta borrar los archivos de
los grupos tipo 3, la ruta de Android no está montada en Windows → `os.remove()` falla
→ `failed += 1`.

### Diagrama del problema

```
UI muestra 286 grupos:
  ├── ~186 grupos con ≥2 copias en PC         → delete-all los procesa (éxito)
  ├── ~X grupos con ≥2 copias en Android      → delete-all NO los procesa (usa solo repo PC)
  └── ~100 grupos PC↔Android (intencionales)  → delete-all intenta borrar ruta Android
                                                  → os.remove() falla → 100 failed
```

### Fix aplicado (2026-03-31)

Eliminadas las líneas 896-897 de `response_builders._build_duplicates_two_repos`
y las variables `pc_sha1_map`/`android_sha1_map` que ya no se usan.

Los grupos PC↔Android ya no se incluyen en la detección. El conteo debería bajar
y el "Eliminar todos" no debería tener más `failed` por rutas de Android no montadas.

**Pendiente verificar:** ejecutar con datos reales y confirmar que `failed` = 0.

### Intentos anteriores

- Intento 1 (Día X): se intentó eliminar duplicados, falló. No quedó documentado qué
  error específico se produjo.

---

## BUG-DUP-2 — `_apply_ra_conflicts` — ganador RA sin renombrar

**Función:** `src/rom_manager/web/handlers/duplicates.py::_apply_ra_conflicts`
**Endpoint:** `POST /api/apply-ra-conflicts`
**Bug-ID:** B-test (pendiente desde Día 22)
**Síntoma declarado:** al pulsar "Resolver por RA", no está verificado que el ganador
quede renombrado al nombre canónico y el perdedor acabe en `_descartados/`.

---

## Historial de intentos

### Intento 1 — Día 8 (primera implementación)

**Qué se hizo:**
- Endpoint `POST /api/apply-ra-conflicts` creado en `server.py`.
- Lógica: iterar `plan.conflicts`, buscar MD5 en caché RA local, mover perdedor a
  `_descartados/`, borrarlo de BD. Devuelve `{resolved, skipped_no_ra, errors}`.
- Solo contemplaba conflictos de tipo "disk" (un `source` quiere renombrar a un
  `target_path` ya ocupado).

**Problema detectado (Día 9):**
- Si el caché RA no existe, la función devuelve `resolved: 0, skipped_no_ra: N` sin
  explicar por qué. No se muestra mensaje claro en UI.
- El test real nunca se ejecutó.

---

### Intento 2 — Día 22 (commit `7e89632` — `fix(BUG-K)`)

**Qué se hizo:**
- Reescritura completa de `_apply_ra_conflicts`.
- Ahora distingue dos tipos de conflicto:
  - `"disk"`: un source quiere renombrar a un target ya ocupado → compara RA de
    ambos → descarta el de menos logros.
  - `"collision"`: varios sources quieren renombrar al mismo target → agrupa por
    `target_path` → descarta todos salvo el de más logros.
- Se añade `no_cache: true` en la respuesta cuando no hay caché.
- Se añade el botón RA también para conflictos de tipo "collision".

**Problema pendiente (B-test):**
- El test real nunca se ejecutó con datos reales.
- El ganador **no se renombra dentro de esta función** — solo se elimina el perdedor.
  El rename del ganador requeriría una llamada separada a Apply.

---

## Estado actual del código (2026-03-31)

### Flujo real de `_apply_ra_conflicts`:

```
plan = build_plan(repository, opts)
  ↓
Para cada conflicto "disk":
  → _ra_for_path(source_path)   → busca MD5 en BD, luego en caché RA
  → _ra_for_path(target_path)
  → _discard(loser_path)        → mueve a _descartados/, borra de BD

Para cada grupo de conflictos "collision" (mismo target_path):
  → _ra_for_path(source_path) para cada candidato
  → scored.sort(by RA desc)
  → _discard(loser.source_path) para todos menos el primero
```

### Lo que NO hace:
- **No renombra el ganador.** El ganador sigue en `source_path` con su nombre original.
  Para que quede en `target_path` (nombre canónico), el usuario debe pulsar Apply
  después.
- **No actualiza el plan en memoria.** Después de descartar, la UI muestra el plan
  anterior hasta que el usuario lo recarga.

### Hipótesis de por qué `resolved` puede ser siempre 0:

**H1 — MD5 no almacenado en BD:**
`_ra_for_path` hace:
```python
SELECT md5 FROM games WHERE source_path = ?
```
Si la columna `md5` está vacía (la app no siempre calcula MD5 al escanear — el MD5
para RA se calcula aparte con el RA check), `_ra_for_path` devuelve -1 para todos los
archivos → todos se saltan como `skipped_no_ra`.

**H2 — Ruta en BD no coincide con `op.source_path`:**
`source_path` en la BD puede estar en formato Windows (`C:\roms\...`) mientras
`op.source_path` (construido por `build_plan`) puede variar. Si no coinciden
exactamente, el `SELECT` no encuentra la fila → MD5 = None → RA = -1.

**H3 — Caché RA vacío o formato incorrecto:**
`_hash_lib_for(plat)` lee `ra_hashes_{console_id}.json` y lo parsea con `_pgl`
(`ra_client._parse_game_list`). Si el JSON tiene formato distinto al esperado o
la plataforma no tiene `console_id` mapeado en `ra_platform_ids.py`, devuelve `{}`.

**H4 — La función sí funciona, pero el usuario no sabe que necesita Apply después:**
El perdedor se mueve a `_descartados/` correctamente, pero el ganador sigue sin
renombrar porque eso es responsabilidad del Apply. Si el usuario no hace Apply después,
ve el ganador con el nombre original y cree que no funcionó.

---

## ROOT CAUSE ANALYSIS — Confirmed (2026-04-02)

**The Problem:** `resolved` is always 0 because MD5s are never populated in the games table.

**Why?** The dependency chain is broken:
1. RA Check (do_ra_check) calculates MD5 and stores in DB
2. Build plan (build_plan) lists conflicts
3. Apply RA (apply_ra_conflicts) queries MD5 from DB to score by RA

If user runs step 3 without step 1, all MD5 queries return NULL → all scores = -1 → all skipped.

**Evidence:**
- Code at line 220: `md5 = (row["md5"] or "").lower()` — returns empty string if MD5 is NULL
- Line 223-224: `if not md5: return -1` — confirms MD5 absence returns -1
- Line 249-250: `if src_ra <= 0 and tgt_ra <= 0: skipped_no_ra += 1` — both return -1 when MD5 missing
- Diagnostic at lines 298-309: Returns `debug_samples` showing if MD5 exists in DB

**The Hidden Second Problem:** Even if MD5s exist and losers are discarded correctly, **the winner is NOT renamed**:
- Line 256-257: Only calls `_discard(loser_path)` — moves loser to _descartados/
- Winner stays in `op.source_path` with original filename
- To reach `op.target_path` (canonical name), user must press Apply after
- User sees winner with wrong name → thinks "Resolver por RA" didn't work → tries again

---

## SOLUTION — Three-Part Fix (to avoid repeating failures)

### Part 1: Enforce Prerequisite (User-facing)
Before allowing "Resolver por RA" button, the UI should verify RA Check ran:
- Show hint: "⚠️ Antes de resolver, ejecuta primero 'Check RA' en la pestaña ES-DE para calcular MD5s"
- Button remains disabled until `no_cache = false` in RA Check result

**Implementation location:** `static/js/tabs/duplicates.js` — when loading conflicts, check if `ra_cache` dir exists and warn if empty.

### Part 2: Auto-Rename Winner (Backend Logic)
Modify `_apply_ra_conflicts` to rename winner after discarding loser:

```python
# After discarding losers (line 291-296), rename the winner:
if op.source_path != op.target_path and op.source_path.exists():
    try:
        op.target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(op.source_path), str(op.target_path))
        # Update DB: source_path → target_path
        with repository.connect() as _c:
            _c.execute(
                "UPDATE games SET source_path = ? WHERE source_path = ?",
                (str(op.target_path), str(op.source_path))
            )
            _c.commit()
    except Exception as exc:
        errors.append(f"Rename winner {op.source_path.name} → {op.target_path.name}: {exc}")
```

**Benefit:** User sees the winner renamed immediately after "Resolver por RA", not after a separate Apply step.

### Part 3: Improve Diagnostic Output
Current diagnostics at line 316-317 are good but add context:

```python
ctx._send_json({
    "resolved":      resolved,
    "skipped_no_ra": skipped_no_ra,
    "errors":        errors[:10],
    "no_cache":      not cache_files_exist,
    "debug_samples": debug_samples,
    "hint":          (
        "Si resolved=0 y skipped_no_ra>0:\n"
        "  1. Ejecuta primero RA Check (ES-DE tab) para calcular MD5s\n"
        "  2. Si debug_samples muestra 'not_found', la ruta en BD no coincide\n"
        f"  3. Cache status: {'❌ No RA cache' if not cache_files_exist else '✓ RA cache found'}"
    ),
    "next_step":     "Ahora pulsa Apply para confirmar cambios" if resolved > 0 else "Ejecuta RA Check primero"
})
```

---

## Why Previous Attempts Failed (Post-Mortem)

### Attempt 1 (Día 8 — "first implementation")
- **What went wrong:** No documentation of what the test revealed. Code created but never actually tested.
- **Why it failed:** Without running the test and seeing `resolved=0, skipped_no_ra=N`, the dependency on RA Check was never discovered.

### Attempt 2 (Día 22 — Rewrite with collision handling)
- **What went wrong:** Added collision handling and diagnostic output, but still never ran with real data to verify diagnostics.
- **Why it failed:**
  - Diagnostics were added but output was never inspected
  - The "winner not renamed" issue was identified in code review but assumed acceptable (user would run Apply after)
  - Still no test run to confirm the dependency chain was broken

### Why Both Failed
**The root cause is PROCEDURAL, not technical:**
1. **No test execution loop** — Code was written, merged, but never actually tested with real conflicts
2. **Broken assumption** — "Diagnost when issues arise" instead of "test the three code paths (disk/collision/no-cache) with data"
3. **No dependency documentation** — RA Check must run BEFORE Resolver; this was never enforced in UI

**The Solution Path That Should Have Been Followed:**
1. Write function + test it immediately with real data
2. If `resolved=0`, inspect `debug_samples` output
3. Document the dependency ("RA Check first")
4. Enforce at UI level (disable button or show hint)
5. Only then mark as verified

---

## Implementation Checklist

- [ ] **Part 1 — UI prerequisite check** (duplicates.js)
  - [ ] Check if RA cache exists when loading conflicts tab
  - [ ] Show warning if `ra_hashes_*.json` files don't exist
  - [ ] Disable "Resolver por RA" button with hint
  - [ ] Enable button only after RA Check runs

- [ ] **Part 2 — Auto-rename winner** (duplicates.py::_apply_ra_conflicts)
  - [ ] After discarding loser, rename winner source → target
  - [ ] Update DB path reference
  - [ ] Handle conflicts if target already exists
  - [ ] Add errors if rename fails

- [ ] **Part 3 — Better diagnostics** (duplicates.py)
  - [ ] Improve hint text with clear steps
  - [ ] Add `next_step` field to guide user
  - [ ] Show cache status emoji (❌ or ✓)

- [ ] **Test with Real Data**
  - [ ] Create test scenario: multiple duplicates with RA cache populated
  - [ ] Run RA Check first
  - [ ] Run Resolver
  - [ ] Verify winners are renamed AND moved to correct location
  - [ ] Verify losers are in _descartados/
  - [ ] Verify DB is updated
  - [ ] Inspect debug_samples output

---

1. **Verificar H1 primero** — añadir log o respuesta extra con:
   ```python
   # en _apply_ra_conflicts, antes de iterar:
   sample_md5s = []
   for op in plan.conflicts[:3]:
       with repository.connect() as c:
           row = c.execute("SELECT md5, source_path FROM games WHERE source_path = ?",
                           (str(op.source_path),)).fetchone()
           sample_md5s.append(dict(row) if row else {"not_found": str(op.source_path)})
   # devolver sample_md5s en la respuesta para diagnóstico
   ```

2. **Si H1 confirmado** — el MD5 para RA se calcula durante el RA Check
   (`/api/ra-check`). El B-test solo puede funcionar si el RA Check se ha ejecutado
   primero. Documentar esto como prerequisito en la UI.

3. **Si H2** — normalizar rutas con `Path(source_path).resolve()` tanto al insertar
   en BD como al comparar en `_ra_for_path`.

4. **Si H4** — añadir en la respuesta del botón: "N conflictos resueltos. Pulsa
   Aplicar para renombrar los ganadores."

---

## Qué NO intentar (ya probado o descartado)

- Reescribir la lógica de selección de ganador — ya es correcta conceptualmente.
- Añadir el botón RA para conflictos de tipo "collision" — ya está desde Día 22.
- Manejar el caso `no_cache` — ya está desde Día 22.
- **No intentar manejar duplicados PC↔Android en el mismo endpoint** — Las rutas de Android no están montadas en Windows; `os.remove()` falla. Si la UI incluye estos "duplicados intencionales", el backend `delete-all` fallará en ~100 casos. Solución: excluir estos grupos de la UI desde el principio (ya hecho en fix 2026-03-31).

---

## User feedback & Design issues (2026-03-31)

Extracted from testing session. Documented here to avoid design regressions.

### DUP-3: Rename "Colisión de plan" resolution
**User feedback:** "Si 2 archivos tienen el mismo nombre canónico, eso implica que están duplicados, por lo que yo los eliminaría desde esta misma pestaña."

**Current state:** Duplicates tab shows conflicts with option to rename some variants to different canonical names (Region/Revision). This confuses users — duplicates should be deleted, not renamed to preserve both.

**Recommendation:** For duplicates with identical canonical name, offer delete-from-duplicates option instead of rename. Track in backlog as **UX-3**.

### UX-1 & UX-2: Device connectivity indicators
**User feedback:** "no me gusta que aparezca como que está conectada la SD cuando no es así. Podríamos marcar de alguna manera en las cards de inicio que no lo está? también habría que evitar que se puedan 'ejecutar cambios' en dispositivo activo 'consola android' cuando no está enchufada"

**Current state:** App shows Android DB in startup cards even when SD card is not plugged in. No visual distinction. UI allows applying changes to disconnected device.

**Issues:**
- Users may accidentally run operations against wrong device
- No feedback that Android SD is offline

**Recommendation:**
1. Add connectivity status indicator in startup cards — clearly show "Android (DISCONNECTED)" when SD unmounted
2. Disable "Ejecutar cambios" button when target device is offline
3. Track in backlog as **UX-1** and **UX-2**.

### DB-1: Metadata cache flag
**User feedback:** "También necesito saber si hay alguna manera de comprobar cuáles tienen metadatos ANTES DE SCRAPEAR, o incluso, si es posible asignar un valor a un archivo (un booleano) en nuestra base de datos para saber que, ya ha sido escaneado sin encontrar datos, por lo que no hay que volver a pasarlo por el scraper"

**Current state:** No way to mark files as "already scraped without result" — they get re-scraped repeatedly.

**Recommendation:** Add `metadata_checked: BOOLEAN` column to games table. Set `true` after scraper runs (regardless of result). Allows UI to:
- Show which files are cacheable before scraping
- Skip already-failed files in batch operations
- Track in backlog as **DB-1**.

### DB-2: Orphaned record cleanup
**User feedback:** "crees que es buena cosa usar este formato de SQLite para nuestra colección? me da la sensación de que los archivos no se eliminan de la base de datos cuando ya los he borrado de la normal"

**Current state:** Unclear if `os.remove()` + `repository.delete_game()` are always called together. May leave DB orphans.

**Recommendation:**
1. Audit all delete workflows — verify both file removal and DB cleanup happen
2. Consider auto-cleanup on library scan (detect files in DB but not on disk)
3. Track in backlog as **DB-2**.

### DUP-4: Clarify delete-all counts
**User feedback (data from test):** "224 grupos — 484 archivos — ~313.7 MB. Al pulsar 'eliminar todos', devuelve 99 no eliminados. Es desconcertante ver cómo dice que hay 224 grupos, 484 archivos, pero 100 no han podido ser eliminados (que pasa con los otros 124?)"

**Current state:** Response shows only `{resolved, failed, skipped}` without breakdown by source (PC duplicates, Android duplicates, mixed).

**Recommendation:** Expand `POST /api/duplicates/delete-all` response to show:
```python
{
  "total": 224,
  "resolved": 186,     # PC-only duplicates deleted
  "skipped_android": 38,  # Android-only (not mounted)
  "skipped_mixed": 100,   # PC↔Android intencionales (now excluded from GET)
  "failed": 0
}
```
Track in backlog as **DUP-4**.