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

## Próximos pasos para diagnosticar (no repetir sin datos reales)

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
