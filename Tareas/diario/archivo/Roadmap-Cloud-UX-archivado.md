> **ARCHIVADO 2026-07-17** — las 12 tareas completadas (CLOUD-UX-6 y 7 en
> feature/anbernic-ux; el resto en la rama fix/cloud-ux, un commit por tarea).
> Estado por tarea en Tareas/backlog.md §CLOUD-UX.

# Roadmap — Cloud: auditoría UX/UI y lógica (2026-07-13)

Origen: auditoría de la pestaña Cloud (`tab-sync.html`, `js/tabs/sync.js`,
`js/main.js`, `js/jobs.js`, `handlers/sync_cloud.py`, `handlers/cloud_auth.py`).
Hallazgo central: **el camino recomendado está roto de punta a punta** — el
botón "Usar para saves + states (recomendado)" lanza ReferenceError; si
existiera, guardaría un remote sin `:` (inválido); y si guardara bien,
"Sincronizar" fallaría igualmente porque el backend exige `[[sync.sources]]`
antes de mirar los remotes implícitos. Además, el estado de conexión cloud
nunca carga al abrir la pestaña por otro ReferenceError en `showTab`.

Tareas registradas en `Tareas/backlog.md` §CLOUD-UX. Cada tarea = una rama → PR.
Todo es pilar 3 (sync de saves = valor diferencial).

---

## CLOUD-UX-1 — Tres funciones inexistentes: backup muerto y estado de conexión que no carga

**Problema.** Tres identificadores usados por la pestaña no existen en ningún
módulo ni en `window`:

- `applyRcloneSavesStates()` — el botón primario "Usar para saves + states
  (recomendado)" (`tab-sync.html:165`). La función existe en `sync.js:556`
  pero **no está en el export** (`sync.js:1578-1644`) ni en el
  `Object.assign(window, …)` de `main.js` (sí está `applyRcloneRemote`,
  `main.js:154`). Clic → ReferenceError.
- `backupNow()` — botón "Hacer backup ahora" (`tab-sync.html:42`). Solo existe
  `API.backupNow` en `api.js:142`; no hay función global. Clic → ReferenceError.
- `loadManualBackups` — no existe en ninguna parte. Consecuencias en cadena:
  `main.js:479` ejecuta `loadSync(); loadManualBackups?.(); loadCloudAuthStatus();`
  — el optional chaining **no** protege identificadores no declarados, así que
  lanza ReferenceError y **`loadCloudAuthStatus()` nunca se ejecuta al abrir
  la pestaña**: la tarjeta "Conexión cloud" se queda en "Comprobando…" hasta
  pulsar ↻ a mano. Y `jobs.js:439` llama `window.loadManualBackups()` tras
  completar un backup → TypeError que corta el resto de `_applyJobStatus` en
  ese tick. La lista "ZIPs manuales guardados" (`manual-backups-list`) no se
  rellena nunca (el endpoint `/api/manual-backups` existe, `games.py:360`).

**Propuesta.** Escribir `backupNow()` (POST `/api/backup-now` + `startPolling()`)
y `loadManualBackups()` (GET `/api/manual-backups` → lista) en `sync.js`;
exportar las tres junto con `applyRcloneSavesStates` y añadirlas al
`Object.assign(window, …)`.

**Archivos.** `sync.js`, `main.js`. **Esfuerzo.** S. **Hecho cuando** abrir la
pestaña muestra el estado de conexión sin clics, "Hacer backup ahora" crea el
ZIP y aparece en la lista, y el botón "recomendado" ejecuta su función.

---

## CLOUD-UX-2 — Los botones "Guardar" del panel rclone escriben remotes sin `:`

**Problema.** `/api/rclone-status` devuelve los remotes **sin** dos puntos
(`sync_cloud.py:143`, `rstrip(":")`) y el select se puebla con esos valores
(`sync.js:485`). Pero `applyRcloneRemote` y `applyRcloneSavesStates` concatenan
`remote + path` (`sync.js:543, 562-563`) → guardan `dropboxRetroSync/saves` en
vez de `dropbox:RetroSync/saves`. Es especialmente traicionero porque
"Verificar conexión" sí funciona (el backend re-añade el `:`,
`sync_cloud.py:196`): test OK → guardado inválido. Evidencia del desajuste: la
preselección compara `opt.value === currentRemote` con `currentRemote`
terminando en `:` (`sync.js:489-491`) y no coincide nunca.

**Propuesta.** Normalizar en un solo sitio: que el select conserve el `:` (o
añadirlo al construir el remote final) y arreglar la preselección de paso.

**Archivos.** `sync.js` (`loadRcloneStatus`, `applyRcloneRemote`,
`applyRcloneSavesStates`). **Esfuerzo.** XS. **Hecho cuando** guardar escribe
`dropbox:RetroSync/saves` y reabrir el panel preselecciona el remote actual.

---

## CLOUD-UX-3 — "Sincronizar" falla con la configuración recomendada (saves+states sin sources)

**Problema.** `_do_sync` corta con "No hay fuentes de sync configuradas.
Añade [[sync.sources]] en config.toml" si `sync_sources` está vacío
(`sync_cloud.py:246-251`) — **antes** de llegar al bloque D2 que sincroniza
los remotes implícitos `saves_remote`/`states_remote` (`sync_cloud.py:346-366`).
Quien configure solo el camino recomendado no puede sincronizar. El aviso del
frontend tiene el mismo punto ciego: `sync-context-bar` mira solo
`cfg.sync_sources` (`sync.js:34-43`).

**Propuesta.** Error solo si no hay ni sources ni remotes implícitos
(`saves_remote`/`states_remote`/`remote`); el context bar del frontend, igual.

**Archivos.** `handlers/sync_cloud.py` (`_do_sync`), `sync.js` (`loadSync`).
**Esfuerzo.** S. **Hecho cuando** con `saves_remote`/`states_remote`
configurados y cero `[[sync.sources]]`, "Estado (dry run)" reporta las dos
fuentes implícitas.

---

## CLOUD-UX-4 — El wizard OAuth puede escribir el token en el provider equivocado

**Problema.** Al terminar la autorización, `_pollCloudAuth` finaliza contra
"el primer provider no configurado" (`sync.js:1532-1543`). Con Dropbox y
Google Drive ambos sin configurar, conectar **Google Drive** escribe el token
bajo el remote `dropbox` (tipo dropbox) — `_PROVIDERS` lista dropbox primero
(`cloud_auth.py:23-26`). El provider era conocido en `startCloudAuth`.

**Propuesta.** Guardar `providerId` al iniciar el flujo (variable de módulo en
`sync.js`), o mejor: que `/api/cloud-auth/poll` devuelva `provider` y
`remote_name` (el backend los recibe en `/start` y puede retenerlos junto al
token). De paso: rechazar `/start` si ya hay un flujo vivo, y que
`cancelCloudAuth` avise al backend (hoy el subprocess `rclone authorize` sigue
vivo hasta 5 min tras cancelar, `cloud_auth.py:49-54`).

**Archivos.** `sync.js`, `handlers/cloud_auth.py`. **Esfuerzo.** S. **Hecho
cuando** conectar Google Drive con Dropbox sin configurar crea el remote
`gdrive` tipo `drive`.

---

## CLOUD-UX-5 — Resultado de sync sin guard `result_ts`: notificaciones repetidas

**Problema.** `jobs.js:104-105` llama `_renderSyncResult(s.sync_result)` en
**cada tick** de polling — scan, match y backup usan el guard `_shownResultTs`
(`jobs.js:88-103, 429-432`), sync no. La notificación de escritorio "Sync
completado" (`sync.js:1452-1462`) se re-dispara cada 2 s mientras el polling
siga vivo por cualquier otro job (p. ej. un scan tras el sync). Es exactamente
el patrón `result_ts` documentado en CLAUDE.md, sin aplicar aquí.

**Propuesta.** Mismo guard que los demás jobs. De paso, refrescar el log de la
pestaña (`loadSync()`) al consumir un resultado nuevo no-dry-run, que hoy queda
obsoleto hasta reabrir la pestaña.

**Archivos.** `jobs.js`. **Esfuerzo.** XS. **Hecho cuando** un sync seguido de
un scan produce exactamente una notificación.

---

## CLOUD-UX-6 — Modo TV: el botón de sync llama a un endpoint que no existe

**Problema.** `tvStartSync` postea a `/api/do-sync` (`sync.js:334`); el
endpoint real es `/api/sync` (`sync_cloud.py:90`). El flujo táctil guiado para
la consola (ANBERNIC-TV) muere con error siempre.

**Propuesta.** Corregir la URL. **Archivos.** `sync.js`. **Esfuerzo.** XS.
**Hecho cuando** el paso 2 del flujo TV lanza el sync y muestra el resultado.

---

## CLOUD-UX-7 — El script bootstrap de Termux hardcodea `dropbox:/RetroSync/saves`

**Problema.** `_build_bootstrap_script` genera `~/sync-saves.sh` con
`REMOTE="dropbox:/RetroSync/saves"` fijo (`sync_cloud.py:666`), ignorando
`config.sync.saves_remote`. Si el usuario usa gdrive u otra carpeta, la
consola sincroniza contra un remote inexistente. Además usa `rclone bisync`
mientras el PC usa `SaveSyncer` (conflict_policy, backups, log) — dos motores
con políticas distintas sobre los mismos archivos; el bisync no respeta "ante
duda, no sobreescribir".

**Propuesta.** Mínimo: inyectar `config.sync.saves_remote` (y las extensiones
de `config.save_extensions`, hoy también hardcodeadas) en el script. Evaluar
aparte si bisync es aceptable como motor del lado consola o si necesita
`--conflict-resolve newest` + backup-dir para alinearse con la política del PC.

**Archivos.** `handlers/sync_cloud.py`. **Esfuerzo.** S (la parte de config).
**Hecho cuando** el script generado refleja el remote y extensiones reales.

---

## CLOUD-UX-8 — Reordenar la pestaña: setup arriba como checklist, comparadores fuera

**Problema.** Orden actual: conexión → botones de sync → backup → estado de
saves → comparador de bibliotecas → auditoría de árbol → **config de rclone al
fondo**, escondida tras "⚙ Verificar rclone" (`tab-sync.html:106-178`). La
configuración imprescindible (elegir remote + carpeta) es lo último y lo menos
visible; hay 4 superficies de configuración (wizard OAuth, "Detectar carpeta
local", panel rclone manual, instrucciones de terminal Dropbox/GDrive) que se
solapan. Y los dos comparadores PC-vs-consola (SHA1 por BD y árbol por rutas,
`tab-sync.html:62-104`) son herramientas de dispositivo, no de cloud — no
tocan rclone.

**Propuesta.** (1) Un bloque de setup tipo checklist arriba: "1. Conectar
(wizard OAuth) → 2. Elegir carpeta → 3. Probar", que se colapsa cuando todo
está en verde. Las instrucciones de terminal quedan como `<details>` de
fallback dentro. (2) Después, la acción del día a día (Sincronizar + resultado
+ estado de saves). (3) Backup al final. (4) Comparador de bibliotecas y
auditoría de árbol → mover a Cable Sync o Herramientas (o un `<details>`
"Herramientas de comparación" al fondo).

**Archivos.** `tab-sync.html`, `sync.js` (solo reordenar/colapsar; la lógica
no cambia). **Esfuerzo.** M. **Hecho cuando** un usuario nuevo ve primero qué
configurar y el habitual ve primero "Sincronizar".

---

## CLOUD-UX-9 — Cerrar el hueco entre "Conectado" y "sync configurado"

**Problema.** El wizard OAuth acaba en "✓ Conectado" pero nadie configura
`saves_remote` — con solo el wizard, "Sincronizar" da error de fuentes. El
estado "Conectado" (remote existe en rclone) y el destino de sync
(`saves_remote` en config) viven desconectados; `_rcloneActiveTargetHtml`
(`sync.js:447-459`) ya calcula el destino activo pero solo se ve dentro del
panel avanzado.

**Propuesta.** Tras `finalize` exitoso, ofrecer en la misma tarjeta: "Usar
`<remote>:RetroSync` para saves + states" (un clic — reutiliza
`applyRcloneSavesStates` ya arreglada por CLOUD-UX-1/2). Y mostrar el destino
activo (o su ausencia) en la tarjeta "Conexión cloud", no solo dentro del
panel avanzado.

**Archivos.** `sync.js`, `tab-sync.html`. **Esfuerzo.** S. **Hecho cuando**
conectar Dropbox desde cero deja el sync funcional sin visitar el panel rclone.

---

## CLOUD-UX-10 — Mensajes que mandan a editar config.toml o a Settings

**Problema.** El context bar y el estado vacío dicen "configura
`[[sync.sources]]` en config.toml" (`sync.js:38,43`) y el error de `loadSync`
enlaza a "Settings → Configuración de rclone" (`sync.js:65`) — cuando el panel
de rclone está en **esta misma pestaña** y la UI ya puede configurar los
remotes recomendados sin tocar TOML. El banner offline (`tab-sync.html:17-19`)
también manda a Settings.

**Propuesta.** Tras CLOUD-UX-3, los mensajes apuntan al bloque de setup de la
propia pestaña (scroll/anchor), y solo mencionan config.toml para el caso
avanzado de `[[sync.sources]]` múltiples.

**Archivos.** `sync.js`, `tab-sync.html`. **Esfuerzo.** XS. **Hecho cuando**
ningún mensaje de esta pestaña exige editar TOML para el caso básico.

---

## CLOUD-UX-11 — "Estado de saves" y backups: cargar solos al abrir

**Problema.** "⏱ Estado de saves" exige clic en "↻ Cargar" (`tab-sync.html:56`)
siendo una lectura local barata (`/api/save-comparison` lee la BD,
`games.py:367`). La lista de backups ídem (una vez exista `loadManualBackups`,
CLOUD-UX-1).

**Propuesta.** Auto-cargar ambos en `showTab('sync')`; el botón ↻ se queda
para refrescar.

**Archivos.** `main.js:479`, `sync.js`. **Esfuerzo.** XS. **Hecho cuando**
abrir la pestaña muestra la tabla de saves sin clics.

---

## CLOUD-UX-12 — Mostrar las decisiones por archivo (`sync-decisions` está muerto)

**Problema.** El backend calcula y envía la lista de decisiones por archivo
(qué se sube/baja/conflicto — `sync_cloud.py:323-327, 417-421`) y el div
`sync-decisions` existe (`tab-sync.html:33`), pero **nadie lo rellena**:
`_renderSyncResult` solo pinta totales "↑ 2 ↓ 1 ✓ 40" (`sync.js:1440-1466`).
Para el pilar 3, saber *qué* save se movió y en qué dirección es la diferencia
entre confiar y no confiar en el sync — especialmente en dry run.

**Propuesta.** Renderizar en `_renderSyncResult` una lista por fuente:
acción (↑/↓/⚠) + ruta relativa, con los conflictos destacados. En dry run es
el "plan" que el usuario revisa antes de pulsar Sincronizar (mismo patrón
plan→apply del resto de la app).

**Archivos.** `sync.js`. **Esfuerzo.** S. **Hecho cuando** un dry run lista
los archivos que se moverían y un sync real lista los movidos.

---

## Orden recomendado

| # | ID | Tipo | Esfuerzo | Por qué este orden |
|---|----|------|----------|--------------------|
| 1 | CLOUD-UX-1 | Bug | S | Tres ReferenceError: backup muerto y estado de conexión que no carga |
| 2 | CLOUD-UX-2 | Bug | XS | El guardado "recomendado" escribe remotes inválidos |
| 3 | CLOUD-UX-3 | Bug | S | Sin esto, la config recomendada no sincroniza nada |
| 4 | CLOUD-UX-4 | Bug | S | Token OAuth en el provider equivocado — corrupción de config |
| 5 | CLOUD-UX-5 | Bug | XS | Notificaciones repetidas; patrón result_ts pendiente |
| 6 | CLOUD-UX-6 | Bug | XS | Endpoint inexistente en modo TV |
| 7 | CLOUD-UX-9 | UX | S | Cierra el hueco conectado→configurado (necesita 1 y 2) |
| 8 | CLOUD-UX-12 | UX | S | Confianza en el sync: ver qué se mueve |
| 9 | CLOUD-UX-8 | UX | M | Reordenar la pestaña; mejor tras estabilizar el setup |
| 10 | CLOUD-UX-10 | UX | XS | Mensajes coherentes con la nueva estructura |
| 11 | CLOUD-UX-11 | UX | XS | Auto-carga de estado de saves y backups |
| 12 | CLOUD-UX-7 | Sync | S | Script Termux alineado con la config real |

Menores anotados sin tarea propia (van de acompañamiento): toasts con tipo
`'success'` sin CSS (app.css solo define `.ok/.err/.info`; `sync.js:1544,1564`),
y el texto del panel de backup menciona Dropbox hardcodeado (`tab-sync.html:40`).
