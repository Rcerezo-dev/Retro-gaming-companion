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

## CABLE-UX-3 — Autoseleccionar modo SD/ADB (pilar 3)

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

---

## CABLE-UX-4 — Quitar el select "Conflictos" de la tarjeta auto-sync

**Problema.** `conflict_policy` solo lo consume `save_syncer.py:270` (sync
cloud); el daemon de cable lo ignora y resuelve siempre por mtime. Además
"Dirección: Más reciente gana" y "Conflictos: Más reciente gana" lado a lado
(`tab-cable.html:23-39`) es una duplicación que confunde.

**Propuesta.** Quitar el select de la tarjeta de cable; su sitio es la config
de sync cloud (Settings). `saveAutoSyncSettings` deja de enviarlo
(`sync.js:1163-1173`).

**Archivos.** `tab-cable.html`, `sync.js`. **Esfuerzo.** S. **Hecho cuando**
la tarjeta solo muestra opciones que el sync por cable usa de verdad.

---

## CABLE-UX-5 — Unificar campos de ruta duplicados

**Problema.** Dos inputs "Ruta del PC" (`cable-pc-path` y `cable-adb-pc-path`,
rellenados idénticos en `loadCableSync`, `sync.js:792-793`) y dos "Ruta
Android" (tarjeta auto-sync `auto-sync-android-path` y sección ADB
`cable-android-path`, con defaults distintos).

**Propuesta.** Un solo input de PC fuera del bloque de modo; un solo input
Android compartido con la config de auto-sync.

**Archivos.** `tab-cable.html`, `sync.js`. **Esfuerzo.** S. **Hecho cuando**
cada ruta se escribe una sola vez y ambos modos/la tarjeta la comparten.

---

## CABLE-UX-6 — Defaults coherentes (dirección y aviso de dry-run)

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

---

## CABLE-UX-7 — Colapsar las instrucciones A/B/C/D

**Problema.** ~80 líneas de instrucciones (`tab-cable.html:52-136`) con la
opción A expandida siempre, encima del formulario, en cada visita — también
para quien ya sincroniza a diario.

**Propuesta.** Un único `<details>` "¿Cómo conecto la consola?"; abierto solo
si nunca hubo un sync exitoso (dato disponible en
`/api/auto-sync-status.last_sync_at`).

**Archivos.** `tab-cable.html`, `sync.js`. **Esfuerzo.** S. **Hecho cuando**
un usuario con syncs previos ve el formulario arriba y la ayuda plegada.

---

## CABLE-UX-8 — Sync Doctor sin ritual previo

**Problema.** `runSyncDoctor` falla con "Activa el Modo ADB y detecta un
dispositivo primero" (`sync.js:759-762`) si el select no se pobló a mano.

**Propuesta.** Si no hay serial, llamar `/api/adb-devices` y usar el primer
device ready antes de rendirse.

**Archivos.** `sync.js`. **Esfuerzo.** S. **Hecho cuando** "Ejecutar
diagnóstico" funciona a un clic con la consola conectada.

---

## CABLE-UX-9 — Unificar los tres bucles de copia (causa raíz)

**Problema.** Manual (`handlers/sync_cable.py:_do_cable_sync`), ADB auto
(`cable_sync_daemon.py:_run_auto_sync`) y SD auto (`_run_sd_auto_sync`)
reimplementan walk+compare+copy con garantías distintas: verify MD5
solo-saves / siempre / nunca; safe_mode solo en manual; el SD auto sobrescribe
sin backup en `pc_to_anbernic` (`cable_sync_daemon.py:409-429`), rozando la
regla "ante duda, no sobreescribir". Es la causa raíz de CABLE-UX-1 y de
futuras divergencias.

**Propuesta.** Extraer un módulo compartido de sync (walk, filtro por
extensiones, compare por mtime, copy con verify/safe/log) que consuman los
tres. Las políticas (safe_mode, verify, skew-check) se definen una vez.

**Archivos.** módulo nuevo en `sync/` (p. ej. `sync/cable_engine.py`),
`web/handlers/sync_cable.py`, `web/cable_sync_daemon.py`.
**Esfuerzo.** M-L. **Hecho cuando** los tres caminos comparten el mismo motor
y los tests cubren las políticas en un solo sitio.

---

## CABLE-UX-10 — Config como única fuente de verdad para rutas

**Problema.** Cascada `ovPc || cfg.library_root || localStorage` en
`loadCableSync` (`sync.js:787-796`) mezclando inputs de Overview, config y
`localStorage` (`anbernic_path`, `cable_pc_path` — escritos en
`doCableSync:878-879`). Cuatro fuentes de verdad que pueden divergir.

**Propuesta.** Config (`library_root`/`anbernic_root`) como única fuente;
eliminar el localStorage y la lectura de inputs de otra pestaña.

**Archivos.** `sync.js`. **Esfuerzo.** S. **Hecho cuando** cambiar la ruta en
Settings se refleja en Cable Sync sin estados fantasma.

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
| 10 | CABLE-UX-9 | Sync | M-L | Refactor de fondo; mejor tras estabilizar 1-3 |

Interacción con el backlog: CABLE-UX-3 resuelve VAL-FIX-6; VAL-FIX-5 (preview
en modo ADB) encaja naturalmente dentro de CABLE-UX-2 si el resumen pasa a
mostrarse en el flujo del botón primario.
