# Roadmap — Cable Sync UX: simplificar la experiencia (auditoría 2026-07-13)

Origen: auditoría del flujo completo de Cable Sync (`tab-cable.html`, `sync.js`,
`handlers/sync_cable.py`, `cable_sync_daemon.py`). El caso de uso del pilar 3
("conecto la consola y los saves aparecen solos") exige hoy ~10 decisiones:
qué sincronizar (4 checkboxes), dirección (3 radios), modo SD/ADB, 2-4 campos
de ruta, detección manual de dispositivo y 4 checkboxes de opciones — con un
bloque de instrucciones de ~80 líneas encima del formulario.

Tareas registradas en `Tareas/backlog.md` §CABLE-UX. Relacionado: VAL-FIX-5/6
(ya registrados en el backlog, no se duplican aquí). Cada tarea = una rama → PR.

---

## CABLE-UX-1 — Pre-flight de reloj en el backend (seguridad, pilar 3) ✅

**Problema.** El check de desviación de reloj de AUD-1 solo existe en el
frontend: `doCableSync` llama `/api/sync-doctor?quick=1` antes de un sync
"newest" manual (`sync.js:863-871`), pero el daemon de auto-sync dispara syncs
"newest" por mtime en cada conexión **sin comprobar skew**
(`cable_sync_daemon.py:_auto_sync_loop` — cero referencias a
skew/`device_epoch`). Es justo el escenario de pérdida silenciosa que AUD-1
quería proteger: reloj mal puesto → el lado equivocado gana en cada conexión
automática.

**Propuesta.** Mover el check al backend, al inicio del job `cable_sync`
cuando `direction == "newest"` (cubre manual y auto con un solo guard). Si
`skew_exceeded`: abortar con error claro en el resultado del job ("Reloj de la
consola desviado X min — ajusta la hora antes de sincronizar por fecha").
De paso se elimina el `confirm()` del frontend.

**Archivos.** `web/handlers/sync_cable.py` (`_do_cable_sync`),
`web/cable_sync_daemon.py` (`_run_auto_sync`), reutilizar
`_build_sync_doctor(..., quick=True)`. Quitar el pre-flight de `sync.js:863-871`.
**Esfuerzo.** S. **Hecho cuando** un skew simulado (> umbral) aborta tanto el
sync manual como el auto-sync con mensaje visible, y con skew normal ambos
funcionan igual que hoy.

**Hecho.** Guard síncrono en `_do_cable_sync` (antes de `def run()`) cuando
`use_adb and direction == "newest" and not dry_run`: llama a
`_build_sync_doctor(..., quick=True)` y devuelve `{"error": ...}` sin arrancar
el job si `skew_exceeded`. Mismo guard en `_auto_sync_loop` justo antes de
`_jm.start(...)`, con `continue` (vuelve a esperar sin sincronizar) y
`last_error` visible en la tarjeta de auto-sync. El `confirm()` del frontend
se quitó de `doCableSync` (ya no hace falta un pre-flight que solo avisaba:
el backend rechaza). Tests nuevos: `tests/test_cable_sync_clock_guard.py`
(guard bloquea con skew, deja pasar con reloj OK, no llama a `device_epoch`
si `direction != "newest"`).

---

## CABLE-UX-2 — Botón primario "Sincronizar saves ahora" (pilar 3) ✅

**Problema.** La acción del día a día está enterrada al final de un formulario
con ~10 decisiones. Un usuario nuevo no sabe qué marcar; el usuario habitual
repite el mismo ritual cada vez.

**Propuesta.** Botón primario arriba de la pestaña que sincroniza saves con la
config de auto-sync (device detectado + saves + dirección configurada +
verify). El plumbing existe: `promptSyncNow()` (`sync.js:1016`) ya postea
`/api/cable-sync` y el daemon ya sabe hacer el sync completo con la config
guardada. Todo el formulario manual actual pasa a un `<details>`
"Sincronización avanzada" — no se toca por dentro, solo se colapsa.

**Archivos.** `web/static/partials/tab-cable.html`,
`web/static/js/tabs/sync.js`. Backend sin cambios (o endpoint fino que ejecute
el mismo camino que el auto-sync bajo demanda).
**Esfuerzo.** M. **Hecho cuando** con la consola conectada, un clic sincroniza
saves y muestra el resultado, sin tocar ningún otro control.

**Hecho.** Botón `#btn-quick-sync` arriba de la pestaña → `doQuickSync()`
(`sync.js`): lee `library_root`/`anbernic_root` de `/api/config`, dirección de
`/api/auto-sync-status`, y el primer dispositivo ADB listo de
`/api/adb-devices` (fallback a modo SD si no hay ADB); postea a
`/api/cable-sync` con `what:['saves']` — mismo endpoint y motor que el
formulario manual, cero duplicación. `jobs.js` extendido para reflejar el
estado del job también en este botón (antes solo mutaba `#btn-cable-sync`).
El formulario completo (`<h3>Sincronización por cable</h3>` en adelante,
antes del panel de Sync Doctor) quedó envuelto en
`<details>⚙ Sincronización avanzada</details>`, cerrado por defecto.

---

## CABLE-UX-3 — Autoseleccionar modo SD/ADB (pilar 3) ✅

**Problema.** El radio `cable-ab-mode` (`tab-cable.html:198-210`) pregunta al
usuario algo que la app ya sabe: el daemon ADB sondea dispositivos cada 10 s y
el daemon SD detecta la unidad montada cada 8 s.

**Propuesta.** Al cargar la pestaña: preseleccionar ADB si `/api/adb-devices`
devuelve un device ready (y autorellenar el select de dispositivo), o SD si
`anbernic_root` existe como ruta. El radio queda como override manual.
Resuelve de rebote VAL-FIX-6 (no se validaría la ruta SD en modo ADB).

**Archivos.** `web/static/js/tabs/sync.js` (`loadCableSync`).
**Esfuerzo.** S. **Hecho cuando** abrir la pestaña con la consola por USB deja
el modo ADB activo con el dispositivo seleccionado, sin clics.

**Hecho.** `loadCableSync()` consulta `/api/adb-devices` una vez por sesión de
pestaña (flag `_cableModeAutoSelected`, para no pelear con un cambio manual
del usuario en visitas posteriores): si hay un device `ready`, marca el radio
ADB, llama `_onCableModeChange()` y `detectAdbDevices()`; si no y
`anbernic_root` está configurado, marca el radio SD. El radio sigue editable
a mano en cualquier momento.

---

## CABLE-UX-4 — Quitar el select "Conflictos" de la tarjeta auto-sync ✅

**Problema.** `conflict_policy` solo lo consume `save_syncer.py:270` (sync
cloud); el daemon de cable lo ignora y resuelve siempre por mtime. Además
"Dirección: Más reciente gana" y "Conflictos: Más reciente gana" lado a lado
(`tab-cable.html:23-39`) es una duplicación que confunde.

**Propuesta.** Quitar el select de la tarjeta de cable; su sitio es la config
de sync cloud (Settings). `saveAutoSyncSettings` deja de enviarlo
(`sync.js:1163-1173`).

**Archivos.** `tab-cable.html`, `sync.js`. **Esfuerzo.** S. **Hecho cuando**
la tarjeta solo muestra opciones que el sync por cable usa de verdad.

**Hecho (con ajuste de alcance).** Al implementarlo se verificó que este
select era el **único** control de UI para `sync.conflict_policy` en toda la
app — Cloud Sync no tenía ninguno propio. Borrarlo sin más habría dejado el
ajuste solo editable a mano en `config.toml`. Se movió (no se borró) a
`tab-sync.html`, dentro del panel "Sincronización de saves": nuevo
`saveConflictPolicy()` en `sync.js` que postea a `/api/config`
(`sync.conflict_policy` ya estaba en el `allowed` set de
`handlers/config.py:261`, sin cambios de backend). `saveAutoSyncSettings()`
deja de leer/enviar ese campo; `_pollAutoSync()` precarga el nuevo select
igual que antes precargaba el viejo.

---

## CABLE-UX-5 — Unificar campos de ruta duplicados ✅

**Problema.** Dos inputs "Ruta del PC" (`cable-pc-path` y `cable-adb-pc-path`,
rellenados idénticos en `loadCableSync`, `sync.js:792-793`) y dos "Ruta
Android" (tarjeta auto-sync `auto-sync-android-path` y sección ADB
`cable-android-path`, con defaults distintos).

**Propuesta.** Un solo input de PC fuera del bloque de modo; un solo input
Android compartido con la config de auto-sync.

**Archivos.** `tab-cable.html`, `sync.js`. **Esfuerzo.** S. **Hecho cuando**
cada ruta se escribe una sola vez y ambos modos/la tarjeta la comparten.

**Hecho.** `cable-adb-pc-path` eliminado; `cable-pc-path` es ahora un único
input fuera del bloque de modo (usado por FS y ADB por igual — `doCableSync`,
`loadCableSyncPreview`, `runSyncDoctor`, `testCablePath`). `cable-android-path`
eliminado; la sección ADB del formulario reutiliza `auto-sync-android-path`
(la tarjeta de arriba) con una nota explicando de dónde sale el valor —
`doCableSync`, `testAdbPath` y `runSyncDoctor` leen ese mismo id.

---

## CABLE-UX-6 — Defaults coherentes (dirección y aviso de dry-run) ✅

**Problema.** Dirección por defecto "PC → Consola: *Sobrescribe los archivos
de la consola*" (`tab-cable.html:170-173`) con "Modo seguro (*no
sobreescribir*)" marcado (`:288-291`) → el resultado típico es "0 copiados /
N omitidos" sin explicación. Y el checkbox dry-run empieza desmarcado pero su
aviso "se copiarán realmente" empieza oculto (`:282,298` — solo aparece tras
tocar el checkbox).

**Propuesta.** Default `direction=newest` (el caso saves) y sincronizar el
aviso de dry-run con el estado inicial del checkbox al cargar.

**Archivos.** `tab-cable.html`, `sync.js`. **Esfuerzo.** S. **Hecho cuando**
los defaults no se contradicen y el aviso refleja el estado real al abrir.

**Hecho.** El radio `checked` por defecto pasó de `pc_to_anbernic` a `newest`.
`loadCableSync()` llama `_onCableDryRunChange()` y `_onCableDirectionChange()`
al cargar la pestaña (antes solo corrían en el `onchange` manual), así el
aviso "se copiarán realmente" y las filas condicionales (SHA1/espejo)
reflejan el estado inicial real de los controles, no una foto fija del HTML.

---

## CABLE-UX-7 — Colapsar las instrucciones A/B/C/D ✅

**Problema.** ~80 líneas de instrucciones (`tab-cable.html:52-136`) con la
opción A expandida siempre, encima del formulario, en cada visita — también
para quien ya sincroniza a diario.

**Propuesta.** Un único `<details>` "¿Cómo conecto la consola?"; abierto solo
si nunca hubo un sync exitoso (dato disponible en
`/api/auto-sync-status.last_sync_at`).

**Archivos.** `tab-cable.html`, `sync.js`. **Esfuerzo.** S. **Hecho cuando**
un usuario con syncs previos ve el formulario arriba y la ayuda plegada.

**Hecho.** Las 4 opciones (A/B/C/D) + aviso MTP quedaron dentro de un único
`<details id="cable-howto">` con resumen "¿Cómo conecto la consola?".
`_pollAutoSync()` (ya corre globalmente desde el arranque de la app) decide
`howto.open` una vez por sesión según `d.status.last_sync_at` de
`/api/auto-sync-status` — igual patrón de "una vez, no pelear con el usuario"
que CABLE-UX-3.

---

## CABLE-UX-8 — Sync Doctor sin ritual previo ✅

**Problema.** `runSyncDoctor` falla con "Activa el Modo ADB y detecta un
dispositivo primero" (`sync.js:759-762`) si el select no se pobló a mano.

**Propuesta.** Si no hay serial, llamar `/api/adb-devices` y usar el primer
device ready antes de rendirse.

**Archivos.** `sync.js`. **Esfuerzo.** S. **Hecho cuando** "Ejecutar
diagnóstico" funciona a un clic con la consola conectada.

**Hecho.** `runSyncDoctor()` ya no exige el select poblado a mano: si está
vacío, llama a `/api/adb-devices` y usa el primer device `ready`; solo si
tampoco hay ninguno muestra el aviso (ahora accionable: "conecta la consola y
activa la depuración USB").

---

## CABLE-UX-9 — Unificar los tres bucles de copia (causa raíz)

**Problema.** Manual (`handlers/sync_cable.py:_do_cable_sync`), ADB auto
(`cable_sync_daemon.py:_run_auto_sync`) y SD auto (`_run_sd_auto_sync`)
reimplementan walk+compare+copy con garantías distintas: verify MD5
solo-saves / siempre / nunca; safe_mode solo en manual; el SD auto sobrescribe
sin backup en `pc_to_anbernic` (`cable_sync_daemon.py:409-429`), rozando la
regla "ante duda, no sobreescribir". Es la causa raíz de CABLE-UX-1 y de
futuras divergencias.

Dividido en subtareas más pequeñas (2026-07-14) — los tres consumidores no
son simétricos (ADB manual usa `AdbTransport`, filesystem manual usa
`shutil`, SD-auto no tiene safe_mode), así que el motor compartido se
construye incrementalmente en vez de en un solo refactor M-L.

### CABLE-UX-9a — Backup antes de overwrite en SD auto ✅

**Problema.** `_run_sd_auto_sync`, rama `pc_to_anbernic`
(`cable_sync_daemon.py:449-450`), sobrescribe sin backup ni safe_mode. Es el
hueco de seguridad más urgente y no depende del motor compartido.
**Archivos.** `web/cable_sync_daemon.py`. **Esfuerzo.** S.

**Hecho.** Backup a `.rommgr/cable_sync_backups/<AAAA-MM-DD>/` antes de
sobrescribir en ambas ramas (`pc_to_anbernic` y `anbernic_to_pc`) cuando el
destino ya existe. Se registra `BACKUP <ruta>` en el log antes del `COPY`.

### CABLE-UX-9b — Extraer el motor de filesystem ✅

**Propuesta.** Generalizar walk + filtro por extensión + compare por mtime +
copy (safe_mode/verify/dry_run) de la rama no-ADB de `_do_cable_sync` en
`sync/cable_engine.py`, sin cambiar el comportamiento de manual todavía.
**Archivos.** módulo nuevo `sync/cable_engine.py`. **Esfuerzo.** S.

**Hecho.** `sync/cable_engine.py`: `iter_files` (walk saltando dotfiles),
`plan_direction` (resuelve `pc_to_anbernic`/`anbernic_to_pc`/`newest` a una
lista de `CopyPlanItem` sin tocar disco) y `copy_item` (aplica
`CopyPolicy(dry_run, safe_mode, skip_existing)` con callback `on_event` para
logging/progreso, desacoplado de logger/job_manager concretos). No cubre
ADB (CABLE-UX-9e) ni `delete_extra`/dedup SHA1 — siguen del lado del
caller. Módulo aún no enchufado a ningún consumidor (eso es 9c/9d);
`tests/test_cable_engine.py` cubre el camino feliz de cada función.

### CABLE-UX-9c — Migrar SD auto al motor ✅

**Propuesta.** `_run_sd_auto_sync` enchufa `cable_engine` y elimina su
`_iter_files`/`_copy`/`_mtime` propios (incluye el backup de 9a como
política del motor). **Archivos.** `web/cable_sync_daemon.py`.
**Esfuerzo.** S. **Depende de** 9b.

**Hecho.** `_run_sd_auto_sync` usa `cable_engine.plan_direction` +
`copy_item`; el backup de 9a se hace por `item` antes de llamar
`copy_item` (no dentro del motor, para no acoplar el motor a la política
de backups). Simplificación de rebote: el motor unifica en un único plan
lo que antes eran dos walks redundantes (uno por dirección) en modo
`newest` — mismo resultado, menos trabajo. El contador "Omitidos" para
empates de mtime se recalcula con un recorrido extra marcado
`ponytail:` (árboles de saves son pequeños). Tests existentes
(`test_cable_sync_daemon.py`) siguen en verde sin cambios.

### CABLE-UX-9d — Migrar manual (rama filesystem) al motor ✅

**Propuesta.** `_do_cable_sync` (rama no-ADB) pasa a ser un caller fino del
motor. **Archivos.** `web/handlers/sync_cable.py`. **Esfuerzo.** S.
**Depende de** 9b.

**Hecho.** Los tres bucles por dirección (`pc_to_anbernic`,
`anbernic_to_pc`, `newest`) usan `cable_engine.plan_direction` +
`copy_item`; `_copy` local se sustituyó por `_apply_copy`, que traduce los
eventos del motor (SAFE/SKIP/ERROR/COPY/DRYRUN) a los mismos
contadores/log/`details` de siempre — comportamiento observable sin
cambios. El dedup por SHA1 (`anbernic_to_pc`) y el espejo `delete_extra`
siguen del lado del caller, como estaba previsto en 9b. El conteo de
"Omitidos" en modo `newest` usa el mismo recorrido extra `ponytail:` que
9c (empates de mtime no generan `CopyPlanItem`). El modo ADB no se tocó
(CABLE-UX-9e). Nuevo `tests/test_sync_cable_filesystem.py` cubre
pc→anbernic, safe_mode por defecto y el conteo de empates en `newest`
disparando `_do_cable_sync` vía el router real, en vez de solo lo
sintético; los 40 tests de `cable`/`sync` en verde.

### CABLE-UX-9e — Unificar la política ADB ✅

**Problema.** `_adb_copy_to_pc/device` (manual) y `_run_auto_sync` (daemon)
reimplementan el mismo criterio "verify MD5 solo en saves" por separado.
**Propuesta.** Wrapper compartido sobre `AdbTransport.pull/push` con esa
política en un solo sitio (no entra en `cable_engine.py`: la primitiva de
copia es `AdbTransport`, no `shutil`). **Archivos.**
`web/handlers/sync_cable.py`, `web/cable_sync_daemon.py`, módulo nuevo o
`sync/adb_transport.py`. **Esfuerzo.** S.

**Hecho.** `should_verify(name, verify_exts)` en `sync/adb_transport.py` —
única fuente de la política. Manual (`sync_cable.py`) la llama con
`save_exts` (allí conviven ROMs y saves, así que solo verifica saves).
Daemon (`cable_sync_daemon.py`) la llama con `effective_exts` (el filtro de
extensión ya aplicado por fuente saves/states), preservando su
comportamiento previo de verificar siempre — solo ve archivos que ya
matchean esa extensión. `tests/test_adb_transport_policy.py` cubre la
política; los 43 tests de `cable`/`sync` en verde.

### CABLE-UX-9f — Tests del motor

**Propuesta.** `test_cable_engine.py` cubriendo safe_mode/verify/skew en un
solo sitio — el "hecho cuando" original de CABLE-UX-9. **Esfuerzo.** S.
**Depende de** 9b.

**Hecho cuando (conjunto).** Los tres caminos comparten el mismo motor de
filesystem, la política ADB está unificada, y los tests cubren las
políticas en un solo sitio.

---

## CABLE-UX-10 — Config como única fuente de verdad para rutas ✅

**Problema.** Cascada `ovPc || cfg.library_root || localStorage` en
`loadCableSync` (`sync.js:787-796`) mezclando inputs de Overview, config y
`localStorage` (`anbernic_path`, `cable_pc_path` — escritos en
`doCableSync:878-879`). Cuatro fuentes de verdad que pueden divergir.

**Propuesta.** Config (`library_root`/`anbernic_root`) como única fuente;
eliminar el localStorage y la lectura de inputs de otra pestaña.

**Archivos.** `sync.js`. **Esfuerzo.** S. **Hecho cuando** cambiar la ruta en
Settings se refleja en Cable Sync sin estados fantasma.

**Hecho.** `localStorage.getItem/setItem('cable_pc_path'|'anbernic_path')`
eliminado de `loadCableSync()` y `doCableSync()`. Se mantiene el override de
Overview (`ov-pc-path`/`ov-ab-path`) — es la misma convención puntual que ya
usan Assets/Colección/Organizar/Juegos (bug de esa convención ya cubierto
por ASSETS-UX-1, fuera de alcance aquí). Sin escritura automática a config
desde Cable Sync: si el usuario quiere que la ruta persista, la fija en
Ajustes explícitamente — evita sobreescribir `library_root`/`anbernic_root`
como efecto secundario silencioso de escribir en un campo de esta pestaña.

---

## Orden recomendado

| # | ID | Pilar | Esfuerzo | Por qué este orden |
|---|----|-------|----------|--------------------|
| 1 | CABLE-UX-1 | Sync/Seguridad | S | Agujero real de pérdida silenciosa en el camino automático |
| 2 | CABLE-UX-2 | UX | M | El 80 % de la mejora percibida; convierte el pilar 3 en un clic |
| 3 | CABLE-UX-3 | UX | S | Elimina la decisión SD/ADB; resuelve VAL-FIX-6 de rebote |
| 4 | CABLE-UX-6 | UX | S | Defaults que no se contradicen — barato y visible |
| 5 | CABLE-UX-4 | UX | S | Quita un control muerto que confunde |
| 6 | CABLE-UX-7 | UX | S | Devuelve la zona noble al formulario |
| 7 | CABLE-UX-5 | UX | S | Menos campos duplicados |
| 8 | CABLE-UX-8 | UX | S | Sync Doctor a un clic |
| 9 | CABLE-UX-10 | UX | S | Una sola fuente de verdad de rutas |
| 10 | CABLE-UX-9a | Sync/Seguridad | S | Cierra el hueco de overwrite sin backup en SD auto |
| 11 | CABLE-UX-9b | Sync | S | Motor compartido de filesystem (sin cambiar comportamiento) |
| 12 | CABLE-UX-9c | Sync | S | SD auto usa el motor |
| 13 | CABLE-UX-9d | Sync | S | Manual (filesystem) usa el motor |
| 14 | CABLE-UX-9e | Sync | S | Política ADB unificada entre manual y daemon |
| 15 | CABLE-UX-9f | Sync | S | Tests del motor |

Interacción con el backlog: CABLE-UX-3 resuelve VAL-FIX-6; VAL-FIX-5 (preview
en modo ADB) encaja naturalmente dentro de CABLE-UX-2 si el resumen pasa a
mostrarse en el flujo del botón primario.
