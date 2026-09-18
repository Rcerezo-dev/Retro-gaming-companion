# Roadmap 10 — `i18n/translate-remaining-strings`

**Rama:** `i18n/translate-remaining-strings`
**Base:** `develop`
**Prioridad:** 🟡 P3
**Esfuerzo estimado:** ~1.5-2 h (mecánico pero disperso en muchos archivos —
más grande de lo que estimaba el plan original)
**Riesgo:** Muy bajo — solo cambia literales de string, ningún flujo de
control ni contrato de campo (`error` sigue siendo `error`, cambia el texto)

---

## Origen

`.claude/mejoras-por-rama.md` (sección 10) citaba 3 puntos concretos:
`esde.js` líneas 447/651/708/713 (TODOs en inglés), "mensajes de error en
Python que llegan al frontend en inglés" (sin ejemplos) y `main.js:655` (un
comentario en inglés). Verificado contra el código real (regla del proyecto
"investigar antes de arreglar", mismo patrón que 07/08/09):

- Los TODOs de `esde.js` ya no están en esas líneas — hay 2 hoy, en
  `esde.js:555` y `:746` (ver Fuera de alcance).
- `main.js:655` hoy es código en español (`'Descargando…'`) — ya no hay
  ningún comentario en inglés ahí.
- El punto sin ejemplos ("mensajes de error en Python...") **sí es real, y
  mucho más grande que 1-2 casos** — la mayoría del proyecto ya está en
  español (confirmado: `src/rom_manager/web/static/js/` no tiene ningún
  string de UI en inglés, `grep` amplio sin resultados), pero los
  `handlers/*.py` acumulan **~55 mensajes de error en inglés** que sí llegan
  al usuario.

**Confirmado que sí llegan al usuario, no es solo texto interno**: el
patrón `if (r.error) { showToast(r.error, 'error'); return; }` se repite en
`static/js/tabs/*.js` (ej. `games.js:233,273,310,413,1076,1086,1111`) — el
campo `error` de cualquier respuesta JSON se muestra tal cual en un toast.
No hay ninguna capa que traduzca o intercepte ese texto.

**Nota sobre `/localization-pass` (skill del proyecto)**: su descripción
dice "Audita `frontend.py`" — hoy `frontend.py` son 22 líneas (un ensamblador
de HTML, sin strings de UI), reliquia de antes del split del frontend a
`static/js/`. La skill apunta a un archivo que ya no es donde vive el
problema — este roadmap corrige directamente `web/handlers/*.py` y
`web/server.py`, no pasa por esa skill.

### Inventario real (por archivo, todos son `ctx._send_json({"error": ...})` o `ctx._send_error(...)` salvo que se indique otra cosa)

**Validaciones cortas de parámetro faltante — patrón mecánico, mismo fix en todos:**

| Archivo | Líneas | Texto actual |
|---|---|---|
| `handlers/games.py` | 264, 311, 340, 368, 429 | `"id required"` |
| `handlers/games.py` | 275, 662 | `"tag required"` |
| `handlers/games.py` | 419 | `"source_path required"` |
| `handlers/games.py` | 451 | `"not found"` |
| `handlers/games.py` | 488 | `"ra_game_id required"` |
| `handlers/games.py` | 493 | `"ra_game_id must be integer"` |
| `handlers/games.py` | 569, 606, 629, 718 | `"game_id required"` |
| `handlers/games.py` | 643 | `"game_id and tag required"` |
| `handlers/games.py` | 725 | `"game not found"` |
| `handlers/games.py` | 753 | `"backup_path and original_save required"` |
| `handlers/duplicates.py` | 208 | `"keep_path and discard_paths required"` |
| `handlers/esde/conversions.py` | 37, 216, 270, 381, 455, 484, 512 | `"source_path is required"` |
| `handlers/esde/conversions.py` | 566 | `"source_path required"` |
| `handlers/esde/doctor.py` | 40, 89 | `"paths list is required"` |
| `handlers/esde/doctor.py` | 61 | `"save_path and game_path are required"` |
| `handlers/esde/doctor.py` | 92 | `"library_root is required"` |
| `handlers/esde/maintenance.py` | 158, 178 | `"source_path is required"` |
| `handlers/esde/maintenance.py` | 252, 336 | `"path required"` |
| `handlers/esde/reports.py` | 45 | `"path parameter required (or set library_root in config)"` |
| `handlers/esde/reports.py` | 109 | `"library_root not configured"` |
| `handlers/inbox.py` | 52 | `"path parameter required (or set inbox.path in config.toml)"` |
| `handlers/inbox.py` | 133 | `"inbox_path not configured"` |
| `handlers/inbox.py` | 175 | `"path is required (or set inbox.path in config.toml)"` |
| `handlers/inbox.py` | 202 | `"library_root is required"` |
| `handlers/scraper.py` | 81, 496 | `"library_root not configured"` |
| `handlers/scraper.py` | 375 | `"game_id required"` |
| `handlers/sync.py` | 60 | `"RetroAchievements API key not configured"` |
| `handlers/sync_cable.py` | 305 | `"pc_path is required"` |
| `handlers/sync_cable.py` | 308 | `"anbernic_path is required"` |
| `handlers/config.py` | 329 | `"No recognised fields to update"` |

Nota de consistencia: `sync_cable.py:89` (`"serial requerido"`),
`play_history.py:99/104/304` (`"game_id (int) requerido"`, etc.) y
`esde/doctor.py:140/162` (`"path y expected_dir requeridos"`, `"path
requerido"`) **ya están en español** en el mismo archivo/patrón — usar esa
misma convención (`"<campo> requerido"`/`"<campo>s requeridos"`) para las de
la tabla de arriba, no inventar una nueva.

**Mensajes más largos, uno a uno (no mecánicos, requieren traducción propia):**

| Archivo:línea | Texto actual | Alcance real |
|---|---|---|
| `handlers/duplicates.py:195` | `"No RA check result available. Run RA check first."` | Se alcanza en uso normal (antes de correr el chequeo RA) |
| `handlers/esde/doctor.py:66` | `f"Save file not found: {save_path}"` | — |
| `handlers/esde/doctor.py:69` | `f"Game directory not found: {game_file.parent}"` | — |
| `handlers/esde/doctor.py:73` | `f"Target already exists: {target.name}"` | — |
| `handlers/esde/doctor.py:99` | `f"Could not create _huerfanos folder: {exc}"` | — |
| `handlers/esde/conversions.py:349` | `f"maxcso not found: {maxcso_path}"` | Se alcanza en uso normal si maxcso.exe falta |
| `handlers/collection.py:135` | `f"Invalid assets response: {result}"` (`_send_error(500, ...)`) | Solo en fallo genuino del servidor |
| `handlers/collection.py:182` | `"No asset found"` (`_send_error(404, ...)`) | Se alcanza si el juego no tiene carátula |
| `handlers/collection.py:197` | `f"Could not read asset: {e}"` (`_send_error(500, ...)`) | Solo en fallo genuino de disco |

### Confirmado que YA está en español (no tocar, evita falsos positivos de un grep amplio)

`cloud_auth.py`, `patches.py`, `organize.py`, `play_history.py` (salvo lo ya
anotado), `system.py`, `scan.py`, `server.py` (mensajes de auth/PIN),
`builders/common.py` — sus mensajes de error ya están en español, verificado
uno a uno, no aparecen en la lista de arriba.

---

## Objetivo

Traducir los ~55 mensajes de la tabla mecánica más los 9 mensajes largos —
64 en total — a español, siguiendo el estilo ya usado en el resto del mismo
archivo cuando exista (ver nota de consistencia arriba). No cambiar la
clave JSON (`error`), ni el código HTTP de `_send_error`, ni ninguna
condición de negocio — solo el texto del mensaje.

No tocar: los 2 TODOs de `esde.js` (555, 746) ni ningún comentario de
código (ver Fuera de alcance) — el criterio de éxito del plan original
(`grep -rn '"[A-Z][a-z]' src/rom_manager/web/static/js/`) ya pasa hoy sin
tocar nada ahí; esta rama es enteramente sobre `web/handlers/*.py`.

---

## Pasos

### Paso 1 — Traducir las validaciones mecánicas (patrón `"<campo> required"` → `"<campo> requerido"`)

Recorrer la tabla mecánica archivo por archivo. Ejemplo real
(`handlers/games.py:264`):

```python
# Antes:
            ctx._send_json({"error": "id required"})

# Después:
            ctx._send_json({"error": "id requerido"})
```

Para los compuestos (`"X and Y required"` → `"X y Y requeridos"`,
`"X must be integer"` → `"X debe ser un entero"`, `"X not configured"` →
`"X no configurado"`, `"X not found"` → `"X no encontrado"`): mismo criterio,
mantener el nombre técnico del campo tal cual (`game_id`, `source_path`,
etc. — son identificadores de API, no se traducen) y traducir solo la
gramática alrededor, igual que ya hacen los mensajes en español del mismo
archivo citados en la nota de consistencia.

### Paso 2 — Traducir los 9 mensajes largos uno a uno

Cada uno necesita su propia frase (no son mecánicos). Ejemplo
(`handlers/duplicates.py:195`):

```python
# Antes:
            ctx._send_json({"error": "No RA check result available. Run RA check first."})

# Después:
            ctx._send_json({"error": "No hay resultado de comprobación RA. Ejecuta la comprobación RA primero."})
```

(`handlers/esde/doctor.py:66`):

```python
# Antes:
            ctx._send_json({"error": f"Save file not found: {save_path}"})

# Después:
            ctx._send_json({"error": f"Save no encontrado: {save_path}"})
```

Aplicar el mismo criterio al resto de la tabla de "mensajes más largos".

### Paso 3 — Tests

Buscar tests existentes que hagan match exacto contra alguno de estos
textos en inglés (se romperían silenciosamente en verde-falso si el test
solo comprueba `"error" in resp` — pero si compara el texto exacto, hay que
actualizarlo):

```bash
grep -rn "id required\|required\"\|not configured\|not found\"\|is required" tests/ --include="*.py" | grep -v "\.pyc"
```

Actualizar cualquier aserción de texto exacto encontrada al nuevo string en
español. No añadir tests nuevos — esto es traducción de literales, no
lógica nueva.

### Paso 4 — Verificación

```bash
# Confirmar que no queda ningún mensaje de la tabla sin traducir:
grep -rn '"error": "[a-z_]* \(required\|is required\)"' src/rom_manager/web/handlers/ --include="*.py"
grep -rn '"error": f\?"[A-Z][a-z]* [a-z]' src/rom_manager/web/handlers/ --include="*.py"
# ambos deben devolver vacío tras el fix (o solo identificadores técnicos
# que no llevaban traducción, como nombres de campo — revisar caso a caso)

python -m pytest tests/ -q
ruff check src/rom_manager/web/handlers/
ruff format --check src/rom_manager/web/handlers/
```

---

## Fuera de alcance (documentado aparte, no entra en esta rama)

- **`esde.js:555` y `:746`** — comentarios `// TODO: Implement...` en
  código de producción. Son comentarios para desarrolladores, no strings de
  UI (no los ve ningún usuario) — el criterio de éxito del plan original ya
  pasa sin tocarlos. Traducirlos o no es una preferencia de estilo, no un
  gap de i18n real; se deja fuera para no mezclar dos tipos de cambio
  distintos en una rama que ya toca ~64 sitios.
- **`server.py`'s `self._send(404, "text/plain", b"Not found")`** (5
  ocurrencias, líneas 291/298/301/310/445) — es la respuesta HTTP genérica
  para un archivo estático no encontrado (JS/CSS/favicon), no un mensaje de
  aplicación; cambiar semántica HTTP estándar no aporta nada real al
  usuario y no es lo que el criterio de éxito pedía.
- Actualizar la skill `/localization-pass` para que apunte a los archivos
  reales en vez de `frontend.py` — es meta-trabajo sobre tooling del
  proyecto, no sobre el código; decidir aparte si vale la pena.

---

## Checklist

- [ ] Paso 1 — ~55 validaciones mecánicas traducidas (tabla completa)
- [ ] Paso 2 — 9 mensajes largos traducidos uno a uno
- [ ] Paso 3 — tests con aserciones de texto exacto actualizados (si los hay)
- [ ] Paso 4 — greps de verificación en vacío, suite + ruff + format limpios
- [ ] Commit en rama, PR a `develop`
