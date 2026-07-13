# Roadmap — Auditoría funcional 2026-07-12

Origen: auditoría de la app completa (132 módulos, backlog, fases 1–16) buscando
funciones útiles que **no** existen ya ni están en el backlog. Descartadas por
existir ya: watcher automático del Inbox (`web/daemons.py:141`), restore de
backups de saves (`backup/save_backup.py:111`), sync de savestates
(`state_extensions` en `sync/rclone_transport.py`).

Criterio de orden: pilares del proyecto (sync > Inbox > biblioteca) × riesgo de
pérdida de datos × esfuerzo. Cada tarea = una rama → PR a `develop`.

---

## AUD-1 — Sync Doctor: detectar desviación de reloj y saves anómalos (pilar 3)

**Problema.** Toda la resolución de conflictos del sync es "mtime gana"
(`sync/save_syncer.py`). Si el reloj de la Anbernic va atrasado/adelantado
(clásico en consolas sin RTC fiable o tras quedarse sin batería), el lado
equivocado gana **silenciosamente** en cada sync — es el modo de fallo más
probable de pérdida de progreso y hoy no hay ninguna defensa ni diagnóstico.

**Propuesta.** Panel "Sync Doctor" en la pestaña Sync:
- Desviación de reloj: `tools\adb.exe shell date +%s` vs `time.time()` del PC.
  Umbral configurable (default 120 s); si se supera, banner rojo y el sync por
  cable pide confirmación antes de resolver conflictos por mtime.
- Saves con mtime en el futuro (más recientes que "ahora" + margen) — síntoma
  directo de reloj mal puesto.
- Saves presentes solo en un lado (join de `list_local_saves` contra el listado
  remoto que ya hace `adb_transport.list_files`).
- Último sync por juego desde la tabla `save_sync_log` (ya existe, solo falta
  la vista).

**Archivos.** `sync/device_detector.py` o `sync/adb_transport.py` (comando
date), handler nuevo en `web/handlers/sync_cable.py`, sección en la pestaña
Sync. Solo stdlib.
**Esfuerzo.** M (1 sesión). **Hecho cuando** el panel muestra desviación real
con la consola conectada y el sync avisa si supera el umbral.

---

## AUD-2 — Verificación post-transferencia en el sync (pilar 3)

**Problema.** Tras un push/pull de un save no se verifica que el archivo llegó
íntegro: una transferencia ADB cortada o un fallo de escritura en la SD deja un
save corrupto que en el siguiente sync puede propagarse al otro lado (su mtime
es el más nuevo).

**Propuesta.** Tras cada transferencia, comparar hash origen/destino:
`adb shell md5sum <ruta>` vs `hashlib.md5` local (rclone ya tiene `check`).
Si no coincide: no tocar nada más, conservar el backup previo (ya se hace) y
reportar el archivo en el resultado del job. Marcar `verified` en
`save_sync_log`.

**Archivos.** `sync/adb_transport.py`, `sync/save_syncer.py`,
`sync/sync_log.py` (columna nueva → usar skill `/db-check` o agente
schema-migrator). **Esfuerzo.** S-M. **Hecho cuando** un save transferido
aparece como `verified` en el log y una corrupción simulada (truncar el archivo
remoto en test) se detecta y no se propaga.

---

## AUD-3 — Papelera unificada con purga automática (pilares 1 y 2)

**Problema.** INBOX-FIX-5 demostró el coste real: `Path.unlink()` en Windows no
pasa por la Papelera — 22 archivos irrecuperables. El patrón seguro ya existe
(`_discard_file()` → `_descartados/`, usado por RA duplicates y el organize del
Inbox) pero los demás borrados masivos siguen siendo destructivos: junk-delete,
bulk delete de duplicados, cleanup de ZIPs.

**Propuesta.** Todo borrado de archivo de la app pasa por el soft-discard a
`_descartados/` (reutilizar el helper existente, moverlo a `utils/` si hace
falta compartirlo). Purga automática de lo que lleve >N días (default 30,
configurable) en el health-check daemon que ya corre
(`web/daemons.py:_health_scheduler_loop`), y en Settings un contador
"Papelera: X archivos, Y GB" con botón "Vaciar ahora".

**Archivos.** `web/inbox_pipeline.py` (`_discard_file` → compartido),
`services/duplicates_service.py`, handler del junk-delete
(`web/handlers/esde/`), `web/daemons.py`, Settings.
**Esfuerzo.** M. **Hecho cuando** ningún call-site de la app llama
`unlink()`/`send2trash` directo sobre archivos de biblioteca y la purga corre
sola. Cumple de raíz la regla "nunca eliminar sin política de conflictos".

---

## AUD-4 — Identificar los `.md` ambiguos del Inbox por CRC (pilar 2)

**Problema.** ZIP-ROUTE-FIX-3 dejó 177 `.md` sueltos en la raíz del Inbox sin
carpeta que los desambigüe (¿Mega Drive o markdown?). Ya está anotado como
"posible ZIP-ROUTE-FIX-4" en el backlog pero sin tarea formal.

**Propuesta.** Para un `.md` suelto sin contexto de carpeta: calcular su CRC32
(o SHA1, ya se hashea en el scan) y consultarlo contra el índice que ya existe
(`CatalogMatcher.crc_index()` / índice SHA1). Hit en el DAT de Mega Drive →
es un ROM, procesar; miss → dejarlo quieto (posible markdown real).
Cero heurística nueva: es un lookup contra infraestructura ya construida.

**Archivos.** `web/inbox_pipeline.py` (detección de plataforma),
`detection/platform_detector.py`. **Esfuerzo.** S. **Hecho cuando** los 177
`.md` reales del Inbox quedan organizados (o listados como "sin match" con
razón explícita).

---

## AUD-5 — Informe de completitud de colección por plataforma / 1G1R (pilar 1)

**Problema.** La app sabe exactamente qué tienes (BD `games` con match) y qué
existe (DATs No-Intro/Redump cargados e indexados), pero nunca cruza ambos:
no hay forma de ver "SNES: 412/1.748 títulos (24 %) — te faltan estos".

**Propuesta.** Informe por plataforma: total de títulos del DAT (agrupando
región para modo 1G1R: contar por título base, no por dump), cuántos tienes,
% y lista de faltantes exportable a CSV (patrón ya usado en `/api/ra-check.csv`).
Solo lectura, cero riesgo. Pestaña nueva en el informe HTML existente
(`utils/library_report_html.py`) o sección en Tools.

**Archivos.** service nuevo pequeño (join `games.canonical_title` vs
`CatalogMatcher`), `utils/library_report_html.py`, handler + CSV.
**Esfuerzo.** M. **Hecho cuando** el informe muestra cifras por plataforma y
el CSV de faltantes se descarga.

---

## AUD-6 — `chdman verify` en el health check (pilar 1, opcional)

**Problema.** El health check compara SHA1 del archivo contra la BD, lo que
detecta corrupción *externa*, pero un CHD puede tener SHA1 estable y contenido
interno inválido desde su creación. `tools/chdman.exe verify` ya valida los
checksums internos.

**Propuesta.** Opción "verificación profunda de CHDs" en el health check
(checkbox, off por defecto — es lenta): correr `chdman verify` por CHD y
reportar fallos. **Esfuerzo.** S. Valor bajo — solo si sobra una sesión.

---

## Orden recomendado

| # | ID | Pilar | Esfuerzo | Por qué este orden |
|---|----|-------|----------|--------------------|
| 1 | AUD-1 | Sync | M | Único agujero real del pilar de más valor; riesgo silencioso de pérdida |
| 2 | AUD-2 | Sync | S-M | Cierra el segundo vector de corrupción del sync; comparte sesión con AUD-1 |
| 3 | AUD-3 | Seguridad | M | INBOX-FIX-5 ya costó 22 archivos; evita el siguiente susto |
| 4 | AUD-4 | Inbox | S | 177 archivos reales varados; lookup contra índice ya existente |
| 5 | AUD-5 | Biblioteca | M | Alto valor coleccionista, cero riesgo, pero no urge |
| 6 | AUD-6 | Biblioteca | S | Solo si sobra tiempo |

Interacción con el backlog existente: AUD-1/AUD-2 van **antes** que MEJ-4
(sync de cheats) — primero blindar el sync, luego ampliarlo. AUD-3 convierte
en obsoleta cualquier repetición de INBOX-FIX-5. AUD-4 sustituye a la nota
informal "ZIP-ROUTE-FIX-4" del backlog.
