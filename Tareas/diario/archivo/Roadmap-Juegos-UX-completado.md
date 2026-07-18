# Roadmap — Pestaña Juegos: logros por juego + playtime automático (2026-07-13)

Roadmap de dos features nuevas para la pestaña **Juegos** (`tab-games.html` +
panel de detalle en `_foot.html` + `js/tabs/games.js` + backend
`web/handlers/games.py`, `retroachievements/ra_client.py`,
`database/repositories/play_history.py`): (1) vista de logros
adquiridos/faltantes por juego, (2) tiempo jugado automático desde PC y
Anbernic, sumado. A diferencia de los roadmaps anteriores (auditorías de UX
sobre funcionalidad existente), este es un roadmap de **feature nueva** —
pero arranca investigando qué ya existe para no reinventar nada. Cada ítem
tiene ID `JUEGOS-UX-n`.

Relacionado: `MEJ-1` en `Tareas/backlog.md` (playtime real vía `.lrtl`) — este
roadmap detalla el diseño concreto que faltaba; los ítems de playtime de
abajo sustituyen/desarrollan MEJ-1, no lo duplican.

---

## Estado (2026-07-18, rama `feature/juegos-ux`)

- ✅ **JUEGOS-UX-1** — `/api/ra-user-progress` devuelve el array `achievements`.
- ✅ **JUEGOS-UX-2** — sección de logros en el panel (`gp-ra-achievements`),
  desbloqueados/pendientes con "ver todos".
- ✅ **JUEGOS-UX-3** — `loading="lazy"` en los badges (el cache TTL de URLs no
  hizo falta: el JSON ya se cachea 1h en `_ra_progress_cache`).
- ✅ **JUEGOS-UX-4** — control manual eliminado (`gpLogPlaytime` fuera).
- ✅ **JUEGOS-UX-5** — columnas `playtime_minutes_pc` / `_android` + migración.
- ✅ **JUEGOS-UX-6** — `utils/lrtl_scanner.py` + upsert MAX
  (`set_playtime_minutes`) + job `playtime_scan`.
- ✅ **JUEGOS-UX-7** — ambas patas. **Cable**: `/api/playtime-scan` hace pull
  adb de `playlists/logs` y acumula en `_android`. **Cloud** (rama
  `feature/juegos-ux-7-cloud`): `sync.playtime_remote` en config → el cloud
  sync añade dos SyncSource (`<remote>/pc` ↔ logs de RetroArch del PC,
  `<remote>/android` ↔ `.rommgr/android_lrtl/`) e ingesta los `.lrtl` en la BD
  tras cada sync real; el script Termux de la consola sube sus logs a
  `<remote>/android` (solo subida — nunca toca `/pc`); `/api/playtime-scan`
  escanea `.rommgr/android_lrtl/` aunque no haya cable.
- ✅ **JUEGOS-UX-8** — total automático "Xh Ym totales · PC / Consola" + botón
  ↻ Actualizar.
- ✅ **JUEGOS-UX-9** — cada origen sin datos se muestra como "sin datos".

## Estado actual (lo que ya existe, verificado en código)

- **Logros**: el panel de juego ya muestra un resumen agregado —
  `X/Y logros (Z%)`, puntos, hardcore — vía `/api/ra-user-progress`
  (`games.py:461-516`), que llama a
  `API_GetGameInfoAndUserProgress.php` de RetroAchievements
  (`games.py:496-502`). Esa respuesta de RA **ya incluye** el array completo
  `Achievements` (id, título, descripción, puntos, icono, fecha de
  desbloqueo) — pero el handler lo descarta y solo se queda con 5 números
  agregados (`games.py:507-514`). No hay ni un solo punto en el código
  (`retroachievements/*`, `games.py`) que parsee o guarde logros
  individuales — confirmado por búsqueda de `Achievements`/`BadgeName`/
  `DateEarned` en todo `retroachievements/`.
- **Playtime**: el bloque "⏱ Tiempo jugado" del panel de juego
  (`_foot.html:163-175`, `gp-playtime-wrap`) es **enteramente manual y no
  persiste nada**. `gpLogPlaytime()` (`games.js:531-542`) valida los campos,
  muestra `alert('Sesión registrada: Xh Ym...')` y limpia los inputs — sin
  ninguna llamada a `apiPost`. El usuario cree que está guardando su tiempo y
  no se guarda absolutamente nada.
  La base de datos tampoco tiene dónde guardarlo: `play_history.py:36-45`
  (`record_play_session`) solo incrementa `play_count` (nº de sesiones) y
  `last_played_at` — no existe ninguna columna de minutos/duración.

---

## A. Logros adquiridos y faltantes por juego

**JUEGOS-UX-1 — Backend: exponer la lista de logros individual, no solo el agregado**
Extender `/api/ra-user-progress` (`games.py:461-516`) para incluir un array
`achievements` con, por cada entrada del diccionario `Achievements` que RA ya
devuelve: `id`, `title`, `description`, `points`, `badge_url`
(`https://media.retroachievements.org/Badge/{BadgeName}.png`), `earned`
(bool), `earned_hardcore` (bool), `earned_at`. Mantener el cache en memoria
de 1h ya existente (`_ra_progress_cache`, línea 486-490) — el payload crece
pero sigue siendo pequeño (JSON, no imágenes).

**JUEGOS-UX-2 — Frontend: sección de logros en el panel de juego**
Nuevo bloque debajo de `gp-ra-user-progress` (`_foot.html:138`) que renderiza
la lista devuelta por JUEGOS-UX-1: icono + título + descripción + puntos,
separados en "Desbloqueados (X)" / "Pendientes (Y)" o con un check/candado
visual. Reutilizar el patrón de lista colapsable ya usado en
`tools.js:444` (`_faCollapsibleList`) en vez de crear un componente nuevo —
mismo problema (listas largas, ver 10 + expandir el resto).

**JUEGOS-UX-3 — Perf: lazy-load de iconos de logros**
Un juego puede tener 50+ logros; usar `loading="lazy"` en los `<img>` de
badge y considerar cachear las URLs de icono con el mismo patrón TTL que ya
usa `.rommgr/ra_cache/ra_hashes_{console_id}.json` (memoria del proyecto,
sección RetroAchievements) en vez de inventar un cache nuevo.

## B. Tiempo jugado automático (PC + Anbernic, sumado)

**JUEGOS-UX-4 — 🔴 Eliminar el control manual actual: no guarda nada**
`gpLogPlaytime()` (`games.js:531-542`) es pura apariencia — ningún
`apiPost`, ningún dato persistido. Esto contradice el pilar 3 del proyecto
("sin miedo, sin intervención manual"). Quitar los inputs manuales
(`_foot.html:167-174`) en cuanto exista el tracking automático de
JUEGOS-UX-6/7; mientras tanto, si se necesita un fix inmediato de mínimo
esfuerzo, ocultar el botón "Registrar" o marcarlo claramente como
"simulado/no persiste" para no engañar al usuario.

**JUEGOS-UX-5 — Esquema de datos: separar minutos por origen para poder sumar sin duplicar**
Añadir `playtime_minutes_pc` y `playtime_minutes_android` (columnas nuevas o
tabla `play_history` extendida) en vez de un único `playtime_minutes` — si
el `.lrtl` de Android se sincroniza al PC (o viceversa), sumar un total
único sin separar por origen duplicaría o sobrescribiría minutos ya
contados. Regla del proyecto ("en sync: ante duda, no sobreescribir")
aplica igual aquí: cada origen es dueño de su propio contador; el total
mostrado es la suma de los dos, nunca un merge destructivo.

**JUEGOS-UX-6 — Scanner de logs `.lrtl` de RetroArch (PC)**
Los logs de tiempo de juego de RetroArch viven en
`playlists/logs/<Core>/<rom>.lrtl` (JSON con claves `runtime` "hh:mm:ss" y
`last_played`). Nuevo módulo stdlib-json (sin dependencias externas, regla
del proyecto) que recorre esa carpeta, matchea cada `.lrtl` con un juego
usando el mismo criterio que `record_play_session`
(`play_history.py:26-27`: título canónico o stem de archivo, case-insensitive),
y hace upsert de `playtime_minutes_pc` + `last_played_at`. Correr como job de
background con el patrón ya existente (`_job_lock`/`_jobs`/polling 2s,
`jobs.js`) porque recorrer todos los cores puede tardar en bibliotecas
grandes.

**JUEGOS-UX-7 — Sync de `.lrtl` desde Anbernic (mismo pipeline que los saves)**
Añadir `.lrtl` como un `SyncSource` más del cable/cloud sync — mismo patrón
que MEJ-4 propone para `.cht` (~10 líneas en `config.py` +
`sync/sync_cloud.py`). Los `.lrtl` sincronizados desde Android se procesan
con el mismo scanner de JUEGOS-UX-6 pero acumulando en
`playtime_minutes_android`, nunca sobrescribiendo `_pc`. Sin esta separación,
sincronizar el `.lrtl` de Android pisaría el de PC en vez de sumarse —
es el riesgo real y el motivo de JUEGOS-UX-5.

**JUEGOS-UX-8 — UI: total automático en vez de entrada manual**
Sustituir el bloque `gp-playtime-wrap` (`_foot.html:163-175`) por un total
recalculado solo: "X h Y m totales · PC: A h · Anbernic: B h" + última
sesión (reutilizar el formato relativo ya existente en `gpShowPlaytimeInfo`,
`games.js:504-529`, "Hace X días/horas"). Sin inputs, sin botón — se
actualiza tras cada sync o escaneo, igual que el resto de datos automáticos
de la pestaña.

**JUEGOS-UX-9 — 🟢 Mientras no exista el scanner, no aparentar precisión**
Si JUEGOS-UX-6/7 se implementan en fases, dejar claro en la UI que el dato
mostrado es parcial (p.ej. solo PC, o "sin datos de Anbernic aún") en vez de
un número que parece total pero no lo es.

---

## Top 3 por impacto

1. **JUEGOS-UX-4** — el control de tiempo jugado actual literalmente no
   guarda nada; es el hallazgo más grave porque el usuario cree que sí.
2. **JUEGOS-UX-6 + JUEGOS-UX-7** — el motor real de tracking automático
   (scanner `.lrtl` + sync Android) es la feature que se ha pedido; sin esto
   las demás piezas (UI, suma) no tienen datos que mostrar.
3. **JUEGOS-UX-1 + JUEGOS-UX-2** — los logros por juego son el fruto más
   bajo: el dato ya se descarga de RA en cada carga del panel, solo falta
   dejar de descartarlo y pintarlo.

## Fases sugeridas

- **Fase 1 (logros, 1 rama):** JUEGOS-UX-1, JUEGOS-UX-2, JUEGOS-UX-3 — el
  dato ya existe, es la fase más rápida de entregar valor visible.
- **Fase 2 (freno de daño):** JUEGOS-UX-4 — ocultar o marcar el control
  manual actual mientras se construye el resto, para dejar de engañar al
  usuario ya.
- **Fase 3 (motor de playtime):** JUEGOS-UX-5 (esquema), JUEGOS-UX-6
  (scanner PC).
- **Fase 4 (unificación PC+Anbernic):** JUEGOS-UX-7 (sync `.lrtl` Android),
  JUEGOS-UX-8 (UI del total), JUEGOS-UX-9 (honestidad mientras se completa).
