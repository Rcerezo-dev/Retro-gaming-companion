# Roadmap 18 — `feature/game-blocklist`

**Rama:** `feature/game-blocklist`
**Base:** `develop`
**Prioridad:** 🟡 P3 — feature de conveniencia, no bloquea ningún pilar activo
**Esfuerzo estimado:** M (~4-5 h — diseño de marca persistente + 2-3 puntos de integración)
**Riesgo:** Bajo-medio — toca borrado en ambas bibliotecas (PC + Anbernic), debe seguir la regla del proyecto de nunca borrar sin política de conflictos documentada

---

## Origen

`GAME-BLOCKLIST` (`Tareas/backlog.md`, feedback usuario 2026-08-29,
`docs/Feedback/29/8.md`). Caso de uso explícito del usuario: "este juego (ej.
un Barbie) no me interesa, quiero borrarlo de PC y Anbernic a la vez, y que
ningún sync futuro me lo vuelva a colar". Distinto de `STORAGE-MGR`
(archivado: borrado en bloque puntual, sin bloqueo permanente) y de
`ANBERNIC-PICK` (el tag `"anbernic"` es opt-in por lo que SÍ debe estar en la
consola, no un "nunca más" global que también cubra el PC).

Necesita una marca persistente por **identidad de juego** (SHA1/
`canonical_title`, no por ruta — la ruta difiere entre PC y Anbernic y
cambia al renombrar) que el scan/inbox/match respeten.

Dos tareas, ambas 🔴 sin diseñar/implementar, la segunda depende de la
primera:

- **`GAME-BLOCKLIST-1`**: diseñar la marca de exclusión permanente (tabla o
  tag reservado tipo `game_tags`, keyed por SHA1) + acción "Eliminar de
  ambas bibliotecas" (PC → papelera `_descartados/`, Anbernic →
  `AdbTransport.remove`, mismo patrón de `STORAGE-MGR-3`/
  `services/storage_service.py`, pero marcando además de borrar).
- **`GAME-BLOCKLIST-2`**: hacer que scan/match/Inbox respeten la marca — un
  archivo con SHA1 bloqueado no se re-organiza ni se re-cuenta como
  pendiente si reaparece (p. ej. tras un sync `anbernic_to_pc` o un
  `adb pull` manual).

---

## Objetivo

1. Marca persistente por SHA1 que sobrevive a renombrados y aplica igual en
   ambas BDs.
2. Acción de UI "Eliminar de ambas bibliotecas" que marca y borra a la vez.
3. Que el resto del pipeline (scan/match/Inbox) respete la marca cuando el
   archivo reaparece.

---

## Pasos

### Paso 1 — Diseño de la marca persistente

Decisión de diseño (confirmar con el usuario antes de implementar): ¿tabla
nueva dedicada (`blocklist` con `sha1`, `canonical_title` de referencia,
fecha, motivo opcional) o reutilizar el patrón `game_tags` ya existente con
un tag reservado (p. ej. `"blocklisted"`)? Reutilizar `game_tags` es más
consistente con el patrón ya establecido en el proyecto (`ANBERNIC-PICK` usa
el mismo mecanismo para el tag `"anbernic"`), pero `game_tags` está keyed por
`game_id`, no por SHA1 — y un `game_id` no sobrevive a que el archivo se
borre y reaparezca después (fila nueva, id nuevo). Si se reutiliza
`game_tags`, hace falta una tabla auxiliar separada `sha1 → blocked` que no
dependa de que exista una fila `games` viva. Documentar la decisión final en
el propio código (docstring corto) antes de implementar.

### Paso 2 — Acción "Eliminar de ambas bibliotecas"

`services/storage_service.py` (mismo patrón que `STORAGE-MGR-3`): al marcar
un juego como bloqueado, borrar también el archivo activo —
PC → `_discard_file()`/papelera `_descartados/` (nunca borrado directo,
regla del proyecto), Anbernic → `AdbTransport.remove()` si hay dispositivo
conectado (avisar y continuar si no lo hay, no bloquear la marca por falta
de cable). Confirmar que la operación marca ANTES de borrar (si el borrado
falla a medias, el juego queda marcado igual y no puede colarse de vuelta
sin revisión).

### Paso 3 — UI

Botón/acción en la pestaña Juegos (o el panel de detalle de un juego) —
"Eliminar de ambas bibliotecas" con confirmación explícita (es una acción
destructiva, mismo patrón de confirmación que ya usan otras acciones de
borrado del proyecto).

### Paso 4 — Respetar la marca en scan/match/Inbox

`scanner/rom_scanner.py` o `web/inbox_pipeline.py` (punto de entrada exacto
por confirmar durante la implementación — ver cuál de los dos procesa
primero un archivo que reaparece). Cuando un archivo con SHA1 bloqueado
reaparece (tras un sync `anbernic_to_pc` o un `adb pull` manual), decidir:
¿se auto-descarta en silencio, o se avisa una vez y se deja para revisión?
(Confirmar con el usuario — auto-descartar en silencio es más cómodo pero
más arriesgado si el bloqueo fue un error; avisar una vez es más seguro pero
menos automático). Sea cual sea la decisión, el archivo bloqueado no debe
re-organizarse ni contarse como "pendiente" en ningún informe.

### Paso 5 — Tests

- Marca + borrado: juego marcado → desaparece de ambas bibliotecas, la marca
  persiste en BD.
- Reaparición: archivo con SHA1 bloqueado vuelve a aparecer en un scan →
  comportamiento según lo decidido en el Paso 4 (auto-descarte o aviso), en
  ningún caso se re-organiza como si fuera nuevo.
- Renombrado: el mismo archivo (mismo SHA1) con nombre distinto sigue
  reconociéndose como bloqueado.

### Paso 6 — Verificación

```bash
python -m pytest tests/ -q
ruff check src/rom_manager/services/storage_service.py src/rom_manager/database/repositories/metadata.py
```

---

## Fuera de alcance

- Bloqueo masivo/por lote (bloquear varios juegos a la vez) — esta rama
  cubre el caso de uso base (un juego a la vez), un bloqueo masivo puede
  añadirse después reutilizando el mismo mecanismo.
- Desbloqueo/reversión de la marca — no mencionado en el pedido original del
  usuario; si hace falta, es una extensión pequeña sobre el mismo diseño.

---

## Checklist

- [x] Paso 1 — diseño de la marca persistente confirmado (tabla dedicada `blocklist`, decisión usuario 2026-09-24)
- [x] Paso 2 — acción "Eliminar de ambas bibliotecas" implementada (`block_and_delete_game`)
- [x] Paso 3 — UI (botón en el panel de juego + confirmación explícita)
- [x] Paso 4 — scan/match/Inbox respetan la marca (avisa una vez, decisión usuario 2026-09-24)
- [x] Paso 5 — tests nuevos (`tests/test_blocklist.py`, 8 tests: marca+borrado, reaparición, renombrado)
- [x] Paso 6 — suite completa (1451 tests) + ruff check/format limpios
- [ ] Commit en rama, PR a `develop` — pendiente, requiere confirmación explícita del usuario
