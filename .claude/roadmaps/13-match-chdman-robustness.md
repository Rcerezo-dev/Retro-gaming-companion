# Roadmap 13 — `fix/match-chdman-robustness`

**Rama:** `fix/match-chdman-robustness`
**Base:** `develop`
**Prioridad:** 🟠 P2 — no pierde datos (la transacción por `batch()` protege la BD), pero puede dejar el job `match` colgado decenas de minutos sin forma de diagnosticarlo ni cancelarlo, obligando a matar el proceso del servidor
**Esfuerzo estimado:** S-M (~3-4 h)
**Riesgo:** Bajo — toca timeout/progreso/cancelación de una llamada ya existente, no cambia la lógica de desambiguación en sí

---

## Origen

`MATCH-HANG-CHDMAN-1` (`Tareas/backlog.md`, hallazgo 2026-09-15). Al re-lanzar
`POST /api/match` sobre 7.738 filas sin resolver, el job se quedó
`running=true` más de 30 minutos sin avance visible. `Get-Process python`
mostró CPU casi plano — el proceso Python estaba bloqueado esperando un
`subprocess.run()`; el trabajo real ocurre en un `chdman.exe` hijo cuyo tiempo
de CPU no aparece en el proceso padre. `POST /api/stop-job`
(`job_manager.cancel_event`) no lo paró — el bucle de `match()` solo comprueba
`_cancel.is_set()` entre filas, nunca dentro de una llamada bloqueante.

Mecanismo confirmado leyendo el código: `catalog/matcher.py::_match_by_title`
dispara `detect_psx_boot_serial()` (`retroachievements/ra_hash_psx.py:181-184`,
rama `.chd`) para desambiguar región PSX cuando hay varios candidatos del
mismo título — y eso llama a `_extract_chd()`
(`retroachievements/ra_cd_image.py:207`), que tiene un timeout de **300s por
llamada individual**, no por job completo. Si la cola de `match` tiene varias
filas PSX ambiguas seguidas, cada una puede consumir hasta 5 minutos sin que
el job progrese ni pueda cancelarse antes de que termine la fila actual en
curso. `web/handlers/scan.py::_do_match` (el bucle del job) solo comprueba
`_cancel` entre filas, nunca dentro de la llamada a `matcher.match()`.

Recuperado la vez que pasó matando el proceso del servidor y reiniciándolo —
sin pérdida de datos porque `update_match` corre dentro de un único
`batch()`/transacción por el run completo, así que nada se comiteó a medias.

---

## Objetivo

No cambiar el resultado de la desambiguación (eso es `CATALOG-MATCH-REGION-1`/
`-2`, ya resuelto) — solo hacer que un cuelgue sea diagnosticable y cancelable
sin matar el proceso:

1. Timeout más corto en `_extract_chd()` para este uso concreto
   (desambiguación PSX, no conversión completa — no hace falta esperar 300s
   solo para leer el `SYSTEM.CNF`/boot serial).
2. El job `match` reporta progreso (fila actual / total) como ya hacen
   `download_dats`/`convert_chd`, para poder diagnosticar un cuelgue real sin
   adivinar mirando `Get-Process`.
3. Cancelación real: que `_cancel.is_set()` se pueda comprobar (o el
   subprocess se pueda matar) dentro de una llamada bloqueante, no solo entre
   filas.

---

## Pasos

### Paso 1 — Timeout dedicado para desambiguación

`_extract_chd()` (`retroachievements/ra_cd_image.py:207`) hoy usa un timeout
fijo de 300s pensado para conversión completa. Añadir un parámetro
`timeout: int` (o una constante separada, p. ej. `_BOOT_SERIAL_TIMEOUT`) que
`detect_psx_boot_serial()` pase con un valor mucho menor (candidato: 30-60s —
leer el boot serial es mucho más barato que convertir el CHD completo,
confirmar con una medición real antes de fijar el número). No tocar el
timeout de 300s del camino de conversión real (`convert_to_chd`/
`convert_bin_to_chd`), solo el de desambiguación.

### Paso 2 — Progreso por fila en el job `match`

`web/handlers/scan.py::_do_match` — mismo patrón ya usado en
`download_dats`/`convert_chd` (`_xxx_progress` dict, actualizado por fila,
expuesto vía `/api/job-status`). Añadir algo como `_match_progress = {"current":
i, "total": n, "row": <nombre de archivo actual>}` para que un cuelgue real
señale exactamente qué fila lo está causando, en vez de tener que investigar
a ciegas como pasó hoy.

### Paso 3 — Cancelación dentro de una llamada bloqueante

Investigar si `subprocess.run(..., timeout=X)` ya es suficiente tras el Paso 1
(un timeout de 30-60s por fila hace que la cola nunca se quede bloqueada más
de ese margen, aunque `_cancel` no se compruebe dentro de la llamada) o si
hace falta además matar el subprocess activo cuando llega una cancelación
real (`_cancel.is_set()`) — mismo patrón que ya podría existir en otro job de
subprocess largo del proyecto, revisar antes de implementar algo nuevo desde
cero.

### Paso 4 — Localizar el `.chd` concreto que disparó el cuelgue de hoy

Con el progreso del Paso 2 ya en su sitio, la próxima vez que se re-lance
`match` sobre las filas PSX pendientes, identificar si hay un archivo
concreto de la biblioteca que dispara sistemáticamente el timeout (disco
dañado, formato no estándar) — no bloqueante para el resto del roadmap, pero
vale la pena verificar una vez implementado el resto.

### Paso 5 — Tests

- `detect_psx_boot_serial()`/`_extract_chd()` con timeout corto: mock de
  `subprocess.run` que tarda más que el timeout → excepción/`None` manejado
  sin colgar el test.
- Progreso del job: `_do_match` con varias filas → `_match_progress` avanza
  fila a fila.

### Paso 6 — Verificación

```bash
python -m pytest tests/ -q
ruff check src/rom_manager/retroachievements/ src/rom_manager/web/handlers/scan.py
```

Verificación real (no solo tests): re-lanzar `match` sobre una cola con
varias filas PSX ambiguas y confirmar que el job termina o se puede cancelar
en minutos, no en "más de 30 minutos sin avance" como hoy.

---

## Checklist

- [x] Paso 1 — timeout dedicado para desambiguación (`_extract_chd`) — `_BOOT_SERIAL_TIMEOUT = 60`, medido contra la biblioteca real (~22s peor caso observado)
- [x] Paso 2 — progreso por fila en `_do_match` — `match_progress` en `/api/job-status` + barra en Overview
- [x] Paso 3 — cancelación real dentro de la llamada bloqueante — resuelto sin tocar el subprocess: el timeout de 60s ya acota la espera máxima por fila
- [ ] Paso 4 — localizar el `.chd` disparador — no reproducible (la cola original de 7.738 filas ya no existe), no bloqueante según lo previsto
- [x] Paso 5 — tests nuevos (5, en `test_ra_hash_psx.py`/`test_jobs_manager.py`/`test_handlers_scan.py`)
- [x] Paso 6 — suite completa (1330 tests) + ruff/format limpios + verificación real (`rommgr match` sobre 6.518 filas, 13.4s, sin cuelgue)
- [ ] Commit en rama, PR a `develop` — pendiente, requiere confirmación explícita del usuario
