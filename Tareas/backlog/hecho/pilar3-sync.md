# Hecho — Pilar 3 — Sync de saves PC ↔ Anbernic — → #204

> Secciones ✅ de `Tareas/backlog/pilar3-sync.md` (todas sus tareas cerradas). Referencia.

### CABLE-UX — Auditoría de Cable Sync: simplificar la experiencia (2026-07-13)

Auditoría del flujo completo de Cable Sync (`tab-cable.html`, `sync.js`,
`handlers/sync_cable.py`, `cable_sync_daemon.py`). El caso de uso del pilar 3
("conecto la consola y los saves aparecen solos") exige hoy ~10 decisiones:
qué sincronizar (4 checkboxes), dirección (3 radios), modo SD/ADB, 2-4 campos
de ruta, detección manual de dispositivo y 4 checkboxes de opciones — con un
bloque de instrucciones de ~80 líneas encima del formulario. Detalle, archivos
y criterios de "hecho" en `Tareas/Roadmap-Cable-UX.md`. Relacionado:
VAL-FIX-5/6 (ya registrados, no se duplican aquí). Orden: 1 es seguridad,
2-3 son el grueso de la simplificación, el resto elimina fricción menor.

| ID | Task | Pilar | Esfuerzo | Estado |
|----|------|-------|----------|--------|
| CABLE-UX-1 | **El pre-flight de reloj (AUD-1) solo existe en el frontend** — `doCableSync` hace el check quick antes de "newest" (`sync.js:863-871`), pero el daemon de auto-sync dispara sync "newest" por mtime en cada conexión SIN comprobar skew (`cable_sync_daemon.py:_auto_sync_loop` — cero referencias a skew/`device_epoch`), que es justo el escenario que AUD-1 quería proteger. Fix raíz: mover el check al backend — al inicio del job `cable_sync` con `direction=newest` (manual y auto); si `skew_exceeded`, abortar con error claro en vez de sincronizar. De paso se elimina el `confirm()` del frontend | Sync/Seguridad | S | ✅ (feature/cable-ux) |
| CABLE-UX-2 | **Un botón "Sincronizar saves ahora" como acción primaria** — la acción del día a día está enterrada al final del formulario. Nota: `promptSyncNow()` no era plumbing reutilizable — posteaba `/api/cable-sync` con body vacío, que siempre falla la validación de `pc_path` (bug latente sin usuarios afectados porque el resultado se tragaba en silencio). Fix real: nuevo `doQuickSync()` que arma el body con `library_root`/`anbernic_root` de config + dirección de la tarjeta auto-sync + primer dispositivo ADB listo, reutilizando `/api/cable-sync` (mismo motor, no uno nuevo); botón primario arriba de la pestaña; el formulario manual completo pasa a un `<details>` "Sincronización avanzada" | UX | M | ✅ (feature/cable-ux) |
| CABLE-UX-3 | **El modo SD/ADB se pregunta al usuario cuando la app ya lo sabe** — hay que elegir el radio `cable-ab-mode` a mano (`tab-cable.html:198-210`), pero el daemon ADB ya sondea dispositivos cada 10 s y el daemon SD ya detecta la unidad montada. Fix: al cargar la pestaña, preseleccionar ADB si `/api/adb-devices` devuelve un device ready (y autorellenar el select), o SD si `anbernic_root` existe como ruta; el radio queda como override manual. Resuelve de rebote VAL-FIX-6 (no se validaría la ruta SD en modo ADB) | UX | S | ✅ (feature/cable-ux) |
| CABLE-UX-4 | **El select "Conflictos" de la tarjeta auto-sync no hace nada en cable sync** — `conflict_policy` solo lo consume `save_syncer.py:270` (sync cloud); el daemon de cable ignora ese valor y resuelve siempre por mtime. Además "Dirección: Más reciente gana" y "Conflictos: Más reciente gana" lado a lado (`tab-cable.html:23-39`) es una duplicación que confunde. Fix: quitar el select de la tarjeta de cable (su sitio es la config de sync cloud). Verificado en vivo: era el único control de UI para `conflict_policy` en toda la app — se movió (no se borró) a `tab-sync.html`, nuevo `saveConflictPolicy()` vía `/api/config` (ya en el `allowed` set de `handlers/config.py:261`) | UX | S | ✅ (feature/cable-ux) |
| CABLE-UX-5 | **Campos duplicados para la misma ruta** — dos inputs "Ruta del PC" (`cable-pc-path` y `cable-adb-pc-path`, rellenados idénticos en `loadCableSync`, `sync.js:792-793`) y dos "Ruta Android" (tarjeta auto-sync `auto-sync-android-path` y sección ADB `cable-android-path`, defaults distintos). Fix: un solo input de PC fuera del bloque de modo; un solo input Android compartido con la config de auto-sync | UX | S | ✅ (feature/cable-ux) |
| CABLE-UX-6 | **Defaults contradictorios** — dirección por defecto "PC → Consola: *Sobrescribe los archivos de la consola*" (`tab-cable.html:170-173`) con "Modo seguro (*no sobreescribir*)" marcado (`:288-291`) → el resultado típico es "0 copiados / N omitidos" sin explicación. Y el checkbox dry-run empieza desmarcado pero su aviso "se copiarán realmente" empieza oculto (`:282,298` — solo aparece tras tocar el checkbox). Fix: default `direction=newest` (el caso saves), y sincronizar el aviso de dry-run con el estado inicial | UX | S | ✅ (feature/cable-ux) |
| CABLE-UX-7 | **Las instrucciones A/B/C/D ocupan la zona noble en cada visita** — ~80 líneas (`tab-cable.html:52-136`) con la opción A expandida siempre, encima del formulario. Fix: colapsar todo en un único `<details>` "¿Cómo conecto la consola?"; abrirlo solo si nunca hubo un sync exitoso (dato ya disponible en `/api/auto-sync-status.last_sync_at`) | UX | S | ✅ (feature/cable-ux) |
| CABLE-UX-8 | **Sync Doctor exige ritual previo** — `runSyncDoctor` falla con "Activa el Modo ADB y detecta un dispositivo primero" (`sync.js:759-762`) si no se pobló el select a mano. Fix: si no hay serial, llamar `/api/adb-devices` y usar el primer device ready antes de rendirse | UX | S | ✅ (feature/cable-ux) |
| CABLE-UX-9 | **Tres implementaciones divergentes del bucle de copia** — manual (`handlers/sync_cable.py:_do_cable_sync`), ADB auto (`cable_sync_daemon.py:_run_auto_sync`) y SD auto (`_run_sd_auto_sync`) reimplementan el walk+compare+copy con garantías distintas. Causa raíz de CABLE-UX-1. Dividido en subtareas (ver `Roadmap-Cable-UX.md`) | Sync | M-L | ✅ (feature/cable-ux) |
| CABLE-UX-9a | **SD auto sobrescribe sin backup** en `pc_to_anbernic`/`anbernic_to_pc` (`cable_sync_daemon.py:409-429`), rozando "ante duda, no sobreescribir". Fix: backup a `.rommgr/cable_sync_backups/<fecha>/` antes de overwrite | Sync | S | ✅ (feature/cable-ux) |
| CABLE-UX-9b | Extraer motor compartido de filesystem (walk, filtro, compare por mtime, copy con verify/safe/log) en `sync/cable_engine.py`, generalizando la rama no-ADB de `_do_cable_sync` sin cambiar comportamiento | Sync | S | ✅ (feature/cable-ux) |
| CABLE-UX-9c | Migrar `_run_sd_auto_sync` al motor de 9b | Sync | S | ✅ (feature/cable-ux) |
| CABLE-UX-9d | Migrar rama filesystem de `_do_cable_sync` al motor de 9b | Sync | S | ✅ (feature/cable-ux) |
| CABLE-UX-9e | Unificar política ADB (verify MD5 solo-saves) entre manual (`_adb_copy_to_pc/device`) y daemon (`_run_auto_sync`) | Sync | S | ✅ (feature/cable-ux) |
| CABLE-UX-9f | Tests del motor compartido (`test_cable_engine.py`): safe_mode/verify/skew en un solo sitio | Sync | S | ✅ (feature/cable-ux) |
| CABLE-UX-10 | **Cuatro fuentes de verdad para las rutas** — cascada `ovPc \|\| cfg.library_root \|\| localStorage` en `loadCableSync` (`sync.js:787-796`) mezclando inputs de Overview, config y `localStorage` (`anbernic_path`, `cable_pc_path` — escritos en `doCableSync:878-879`). Fix: config (`library_root`/`anbernic_root`) como única fuente; eliminar el localStorage | UX | S | ✅ (feature/cable-ux) |
| CABLE-UX-11 | **CABLE-UX-10 huérfano `localStorage['anbernic_path']`** — quitó el único `setItem` (era en `doCableSync`), pero 6 sitios seguían leyéndolo como fallback cuando `ov-ab-path` está vacío (normal en cualquier sesión hasta que se visita Inicio, porque `loadOverview()` no corre en el arranque): `config.js:318,322` (`doBatchRun`, Herramientas — bloqueaba con alert aunque `anbernic_root` estuviera configurado), `duplicates.js:25` (`loadDuplicates`), `duplicates.js:358` (`setToolsContext`), `scan.js:129` (`quickScanAndroid`), `main.js:587` (`openHtmlReportAndroid`), `sync.js:98` (barra de contexto de Assets). Conecta con ASSETS-UX-1 (`Roadmap-Assets-UX.md`), que documentaba este mismo fallback como si funcionara. Fix: los 6 sitios ahora consultan `cfg.anbernic_root` (fetch a `/api/config`, ya disponible en todos salvo `main.js`/`scan.js` donde se añadió) antes de caer a `localStorage`/`(no configurado)` — mismo patrón que ya usaba `overview.js:403` correctamente. No se resucita el `setItem`: sigue la filosofía de CABLE-UX-10 (config como única fuente de verdad) | Sync/UX | S | ✅ (feature/cable-ux) |

---

> ✅ Archivado en `Tareas/diario/archivo/archivo.md`: CLOUD-UX-1..3 (wizard, auditoría 2026-07-12) y CLOUD-UX-1..12 (auditoría de la pestaña Cloud, 2026-07-13) — ambas secciones completas.

---

### ANBERNIC-UX — Auditoría de la pestaña Anbernic: UX/UI, lógica y seguridad (2026-07-13)

Auditoría de la pestaña Anbernic (`tab-anbernic.html`, `js/tabs/sync.js`,
`_banners.html`, `handlers/sync_cloud.py`, `handlers/system.py`, `web/lan.py`).
Hallazgo central: **dos generadores de script de setup que se contradicen en
la misma pantalla, uno de ellos sin endpoint (404)**; y la instalación por
defecto sirve el rclone.conf con tokens OAuth a toda la LAN sin PIN.
Detalle, archivos y criterios de "hecho" en `Tareas/Roadmap-Anbernic-UX.md`.
Relacionadas (no duplicar): CLOUD-UX-6 (panel TV roto), CLOUD-UX-7 (remote
hardcodeado en `/s`). Todo pilar 3.

| ID | Task | Tipo | Esfuerzo | Estado |
|----|------|------|----------|--------|
| ANBERNIC-UX-1 | **Dos generadores de setup contradictorios** — el comando del paso 5 usa `/s` (`sync.js:402`, crea `~/sync-saves.sh`, bisync, remote hardcodeado = CLOUD-UX-7); el botón "Descargar .sh" y el panel de Settings usan `/api/anbernic-setup.sh` (`_build_anbernic_setup_sh`, `system.py:218`, crea `~/retrovault-sync.sh`, `rclone copy --update`, lee config); la caja "Después del setup" (`tab-anbernic.html:156`) documenta el script que el comando recomendado NO crea. Fix: un solo generador canónico en `/s` con lo bueno de system.py (config + copy --update); borrar el otro | Bug | M | ✅ (feature/anbernic-ux) |
| ANBERNIC-UX-2 | **"Descargar .sh" y panel Settings → 404** — `/api/anbernic-setup.sh` no está registrado en ningún handler (solo `openapi.json:4597`; el builder de `system.py:218` es código muerto). Afecta al botón del paso 5 (`sync.js:415`) y a todo el Android setup panel de Settings (QR+curl, `sync.js:238-253`). Fix (tras -1): apuntar todo a `/s` y evaluar eliminar el panel de Settings (superficie duplicada) | Bug | S | ✅ (feature/anbernic-ux) |
| ANBERNIC-UX-3 | **Seguridad: rclone.conf (tokens OAuth) servido a toda la LAN sin auth** — el guard (`sync_cloud.py:27-34`) solo exige PIN si `web_allow_lan=false`, pero los defaults son `web_host="0.0.0.0"` + `web_allow_lan=true` (`config.py:430,432`): cualquier dispositivo de la red descarga los tokens por HTTP plano. Fix: token efímero de un uso embebido en el script `/s`, o PIN obligatorio para este endpoint en binding no-loopback | Seguridad | M | ✅ (feature/anbernic-ux) |
| ANBERNIC-UX-4 | **IP personal hardcodeada como fallback** — `get_bootstrap_script` usa `"192.168.1.160"` si `get_lan_ip()` falla (`sync_cloud.py:48`). Fix: usar el header `Host` de la request como fallback | Bug | XS | ✅ (feature/anbernic-ux) |
| ANBERNIC-UX-5 | **La promesa del paso 1 es falsa** — dice que al abrir la URL en la consola "aparecerá una guía de instalación con botones de descarga" (`tab-anbernic.html:30-32`); lo que aparece es `android-detected-panel` (`_banners.html:21-52`): panel de sync sin botones de instalación, "PC conectado" hardcodeado y botón roto (CLOUD-UX-6). Fix: estado "primera vez" con vista táctil de instalación + comprobación real del servidor | UX | M | ✅ (feature/anbernic-ux) |
| ANBERNIC-UX-6 | **QR en el paso 1** — teclear `http://ip:7777` en la consola es el paso más doloroso; `renderQR` ya existe (`config.js:499`) y no se usa aquí. Además "Copiar URL" copia al portapapeles del PC y el tip del paso 5 alude a un portapapeles-por-ADB que no existe (`tab-anbernic.html:147`). Fix: QR junto a `anb-ip-display`, quitar textos de funciones inexistentes | UX | XS | ✅ (feature/anbernic-ux) |
| ANBERNIC-UX-7 | **Sin check de prerequisitos** — la pestaña no consulta `/api/rclone-status` (sin remotes, el script descarga un rclone.conf vacío y la consola queda a medias) ni avisa de binding loopback / firewall Windows (`_check_firewall` existe en `lan.py:52` pero solo se usa en CLI, `cli.py:969`). Fix: banner arriba con ① cloud configurado ② servidor accesible por LAN | UX | S | ✅ (feature/anbernic-ux) |
| ANBERNIC-UX-8 | **Errores silenciosos y enlaces engañosos** — si `/api/local-url` falla, "Detectando…"/"Cargando…" quedan para siempre (`sync.js:418-420`); "Descargar Termux APK" abre la página de releases, no un APK (`tab-anbernic.html:82`). Fix: error visible con reintento + etiquetas honestas | UX | XS | ✅ (feature/anbernic-ux) |
| ANBERNIC-UX-9 | **`/api/local-url` gasta un `subprocess` en cada llamada** — `_check_firewall` (`web/lan.py:52`, invocado desde `handlers/esde/system.py:59,66`) lanza `netsh advfirewall firewall show rule` (spawn de proceso, decenas de ms en Windows) en cada `GET /api/local-url`; tras ANBERNIC-UX-7 ese endpoint se llama también desde `loadAnbernicTab()` y `tvToggleSetup()` (`sync.js:410,283`), no solo desde Settings. Fix: cachear el resultado unos segundos/minutos en memoria (el estado del firewall no cambia entre refrescos de pestaña) o solo comprobarlo si `lan_bound=true` y ha pasado un TTL desde la última comprobación | Rendimiento | XS | ✅ caché en memoria `_firewall_cache` (`web/lan.py`), TTL 60s por puerto — evita el `subprocess` en refrescos consecutivos de pestaña. 2 tests nuevos (`test_lan_firewall_cache.py`) |
| ANBERNIC-UX-10 | **Token de setup: un solo slot global, no por sesión** — `_mint_setup_token` (`handlers/sync_cloud.py:141`) sobreescribe `_state._anbernic_setup_token` (`web/state.py:40`) en cada llamada a `GET /api/anbernic-setup-token`; si se abre la pestaña Anbernic en dos pestañas del navegador a la vez, el segundo mint invalida el comando ya copiado del primero (403 al ejecutarlo). Bajo impacto (app de un solo usuario/escritorio) pero fix barato: token efímero por request en vez de global, o lista de tokens válidos con TTL en vez de un único slot | Bug | XS | ✅ `_state._anbernic_setup_tokens` pasa de dict único a lista de tokens vivos (`web/state.py`, `sync_cloud.py`); mintear uno nuevo poda los caducados pero conserva los que aún no expiraron — dos pestañas ya no se invalidan entre sí, cada token sigue caducando a los 10 min. Test nuevo `test_minting_new_token_does_not_invalidate_still_valid_ones` |

Validación en hardware pendiente: comprobar en la RG556 si Termux limpio trae
`curl` (el one-liner `curl -s …/s \| bash` falla si no; la guía manual
`docs/sync/Guia-Termux-Anbernic.md` no lo usa).

---

### CABLE-ROM-FIX — El sync de ROMs por cable no compara con el destino (hallazgo 2026-08-13)

Plan de implementación para los pendientes `-5`/`-6` en
`.claude/roadmaps/16-cable-sync-format-gaps.md`.

Origen: el usuario pidió sincronizar biblioteca PC↔consola vía Cable Sync
(`what: ["roms"]`). Investigación con dry-run real contra la RG556
(serial `RG556006101273`, SD en `/storage/521D-04EA`, 49 GB libres de 466 GB):
pidió copiar **47.191 archivos / 516 GB** — la biblioteca del PC entera,
sin importar que la SD ya tenga casi todo (misma estructura de carpetas que
el PC). Repetido con `skip_existing: true` + `skip_sha1_dups: true`: **resultado
idéntico**, byte a byte.

Causa raíz: `web/handlers/sync_cable.py:597-605` (rama `direction ==
"pc_to_anbernic"`) itera todos los archivos del PC y llama a
`_adb_copy_to_device` para cada uno **sin comprobar nunca** el listado del
dispositivo (`ab_adb_files`, calculado en la línea 569 pero solo usado para
`delete_extra` y estadísticas de progreso — nunca para decidir qué copiar).
El parámetro `skip_existing` que acepta el endpoint no se referencia en
ningún punto de esta rama. `sync/adb_transport.py:278`
(`AdbTransport.push`) tampoco compara contenido/mtime antes de subir — en
`dry_run` ni siquiera llega a intentarlo, solo devuelve el tamaño local.
Contraste: la rama `anbernic_to_pc` (línea 636) sí usa `use_sha1`/hash para
saltar duplicados — la asimetría sugiere que `pc_to_anbernic` quedó a medias.

| ID | Task | Notas |
|----|------|-------|
| CABLE-ROM-FIX-1 | Implementar comparación real contra `ab_adb_files`/`pc_root` antes de copiar en ambas ramas ADB (`pc_to_anbernic` y `anbernic_to_pc`) — mismo criterio que ya usa `cable_engine.copy_item` en el modo sistema de archivos (tamaño) | `web/handlers/sync_cable.py:597-605,672-729` | ✅ rama `fix/cable-sync-rom-skip-existing` → PR #161 |
| CABLE-ROM-FIX-2 | Guard de espacio libre en destino antes de empezar (ya existe un patrón idéntico en `zip_router.py:_extract_collection` — `shutil.disk_usage(dest_dir).free`) — evita rellenar la SD a medias | `web/handlers/sync_cable.py` (rama ADB de `_do_cable_sync`) | ✅ `AdbTransport.free_bytes()` (`sync/adb_transport.py`, vía `df -k`) + guard antes de escribir en corridas reales (`dry_run=False`) |
| CABLE-ROM-FIX-3 | Sync por plataformas — con el fix, la SD (78 GB libres) sigue sin caber la biblioteca completa (305,9 GB). No hace falta código nuevo: el endpoint ya soporta `pc_path`/`android_path` apuntando a una subcarpeta. Desglose real por plataforma: `psx` 61,1 GB, `gamecube` 34,3 GB, `ps2` 29,9 GB, `Unknown` 25,2 GB (basura), `arcade` 17,6 GB no caben; el resto (~66 GB tras `skip_existing`) sí | — | ✅ ejecutado de verdad 2026-08-13/14: 50 carpetas, confirmado en `.rommgr/cable_sync_ops.log` — terminó sin errores reales (`errors=0` en todas las corridas de esa sesión salvo un reintento transitorio de daemon adb sobre un `.jpg` de wheel, sin relación con ROMs/saves ni con PSX). `psx`/`gamecube`/`ps2`/`Unknown`/`arcade` siguen sin sincronizar — pendientes de espacio en la SD |
| CABLE-ROM-FIX-5 | Sync real de `arcade` a la RG556 (2026-08-27): **ya terminó solo**, no hizo falta pausarlo — `copied=3192 skipped=49 errors=2`. Los 2 errores son el mismo hipo transitorio de daemon adb ya visto en Día49 (`daemon still not running`), no relacionado con los archivos en sí: `lresort.zip` y `Ring of Destruction_ Slammasters II (Europe 940902).zip` probablemente no llegaron. `arcade/_descartados` (1,13 GB de sets incompletos) se apartó temporalmente antes del sync para no llenar la SD de basura, y se restauró después — no se sincronizó. `gamecube` (34,3 GB) quedó sin lanzar, pendiente para la próxima sesión | `.rommgr/cable_sync_ops.log` (línea `Fin 2026-08-26T23:47:45Z`) | ✅ arcade hecho (verificar los 2 archivos concretos en el próximo sync); 🔴 gamecube pendiente |
| CABLE-ROM-FIX-4 | La allowlist de carpetas por plataforma usada en CABLE-ROM-FIX-3 fue manual/ad-hoc (script de orquestación de esa sesión, no persistido). Añadir selector de plataformas incluir/excluir en la UI de Cable Sync (o config), reutilizando `PLATFORM_BY_FOLDER`/`_ES_PLATFORM_FOLDERS` ya existentes, para no tener que rehacerla a mano cada vez que la SD no tenga espacio para todo | `web/handlers/sync_cable.py`, frontend Cable Sync | ✅ nuevo campo `exclude_platform_folders` (lista de carpetas en minúscula, p.ej. `["arcade"]`) en `POST /api/cable-sync` — aplica en `_wanted()` (lado PC/SD, ambos roots) y en el nuevo `_wanted_info()` (lado Android/ADB, junto a `_wanted_name`), cubriendo las 3 direcciones y el espejo (`delete_extra`: una plataforma excluida nunca cuenta como "extra"). `GET /api/platform-folders` nuevo expone `_STANDARD_PLATFORM_FOLDERS` para poblar el `<select multiple>` "Excluir plataformas" en `tab-cable.html`, cargado una vez por sesión de pestaña (`_loadCablePlatformFolders()`, mismo patrón que `_cableModeAutoSelected`). 6 tests nuevos (`tests/test_sync_cable_exclude_platforms.py`); verificado además con smoke test HTTP real contra el servidor (`pc_to_anbernic`, excluyendo `arcade`: solo copió `psx/`). Suite completa 1220/1220 |
| CABLE-ROM-FIX-6 | **Alcance medido 2026-09-11** — el Día59 (2026-09-10) bloqueó Cable Sync en espejo de `ps2`/`psx`/`gamecube` por un desajuste `.chd` vs `.bin`/`.cue` sin cuantificar. Medido por título (extensión aparte) cruzando PC (`E:\Carpetas anbernic\`) contra el dispositivo (ADB, `ROMs/`): **el problema es exclusivo de PSX** — PC tiene `ps2/`/`gamecube/` en `.iso`/`.rvz` en ambos lados (mismo formato), sin ningún `.chd` en ninguno de los dos para esas 2 plataformas salvo un único caso en `ps2/` (`Crash Bandicoot - The Wrath of Cortex.chd`, solo en el dispositivo, sin ninguna versión equivalente en el PC en ningún formato — no es un mismatch de formato, es contenido exclusivo del dispositivo, categoría de riesgo distinta e inherente a cualquier espejo). En PSX sí es real y grande: de los **129 títulos que el dispositivo tiene como `.cue`/`.bin`**, **70 (54%) ya están convertidos a `.chd` en el PC** — esos 70 (**127 archivos `.bin`/`.cue`, 32,75 GB**) son exactamente el patrón que causó el incidente de `TRASH-FIX-5` (`Castlevania - Symphony of the Night`, `Crash Bandicoot`, etc., están en esta lista) y que un espejo `delete_extra=true` seguiría interpretando como "extra" a borrar por comparar solo ruta/nombre exacto, no contenido. Conclusión: `gamecube`/`ps2` **no tienen el bloqueante de formato** — solo espacio (`CABLE-ROM-FIX-3`); **solo `psx` sigue bloqueado** hasta que el espejo (o una conversión previa a `.chd` en el dispositivo) reconozca `.chd`≡`.cue`/`.bin` del mismo juego.

**Implementado (2026-09-22, Día69, roadmap 16)**: opción (b) elegida por el
usuario — comparación cross-formato en el espejo, sin mover ni convertir
nada. `normalize_title_cross_format()` (antes `_normalize_title_cross_format`,
privada de `web/builders/duplicates.py`, movida a `utils/disc_tag.py` para
poder compartirla con `sync_cable.py` sin acoplar el módulo de sync al de
duplicados) normaliza el stem quitando el tag de disco; nuevo
`_DISC_IMAGE_EXTENSIONS` (`.chd`/`.cue`/`.gdi`/`.ccd`/`.iso`) acota el guard
solo a formatos de imagen de disco — un cartucho (`.gb`/`.gba`/...) con el
mismo título tras quitar el tag nunca debe suprimir su propio borrado, ahí sí
importa el nombre exacto. Antes de marcar cualquier archivo como "extra" en
los 4 sitios de `web/handlers/sync_cable.py` (`delete_extra`, modo ADB y modo
filesystem/SD, ambas direcciones), se comprueba si el otro lado ya tiene un
archivo de imagen de disco con el mismo título normalizado, en cualquier
formato — si lo tiene, no se borra. Fallo asimétrico a propósito: en el peor
caso dos discos distintos con el mismo título salvo el número de disco (un
set multi-disco real) coinciden por error y uno se queda sin sincronizar
silenciosamente — nunca se borra nada real, mismo criterio que "ante duda, no
sobreescribir" del proyecto. 2 tests nuevos (`tests/test_sync_cable_cross_format.py`,
modo filesystem, ambas direcciones): confirmados en rojo contra el código
anterior (`git stash`) y en verde tras el fix. Suite completa: 1430 tests, 0
regresiones. Paso 1 del roadmap (sync real de `gamecube`) sigue pendiente —
es solo ejecución, no código, fuera de esta sesión (requiere ADB conectado). | `utils/disc_tag.py` (`normalize_title_cross_format`, movida), `web/builders/duplicates.py` (import actualizado), `web/handlers/sync_cable.py` (`_DISC_IMAGE_EXTENSIONS`, `_cross_format_stems`, `_is_cross_format_equivalent`, aplicado en los 4 sitios `delete_extra`), `tests/test_sync_cable_cross_format.py` | ✅ hecho 2026-09-22 (Paso 2-3 del roadmap 16) — desbloquea el espejo completo de `psx`; Paso 1 (ejecutar el sync de `gamecube` pendiente) sigue por hacer, requiere hardware |

### ANBERNIC-PICK — Selección manual de qué se lleva a la Anbernic — → #246

Origen: sesión 2026-08-28, tras organizar un bestset de FBNeo (636 juegos) y
encontrar 295 conflictos de versión de romset. `CABLE-ROM-FIX-4` (arriba)
ya cubre incluir/excluir por **plataforma entera**; esto es más fino —
juego a juego o colección a colección — reutilizando lo que ya existe en
vez de construir un selector nuevo. Decisión del usuario: manual explícito,
no automático por espacio libre/prioridad.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| ANBERNIC-PICK-1 | **Marcar juegos para la Anbernic reutilizando `game_tags`** — sin esquema nuevo: tag reservado `"anbernic"` vía `add_tag_bulk`/`remove_tag_bulk` (`database/repositories/metadata.py`). `POST /api/tag-bulk` (`web/handlers/games.py`) reutiliza `get_games_paginated` con los mismos filtros que `/api/games` para aplicar el tag a todo lo que cumple el filtro actual | `database/repositories/metadata.py`, `web/handlers/games.py`, `web/static/js/tabs/games.js` | ✅ PR #248 — botones "Marcar para Anbernic"/"Desmarcar" en la pestaña Juegos, con confirmación mostrando el total. 5 tests nuevos (`tests/web/test_tag_bulk.py`). Verificado en vivo contra la biblioteca real |
| ANBERNIC-PICK-2 | **Cable Sync filtra por la marca en la rama de ROMs** — `_do_cable_sync` (`web/handlers/sync_cable.py:395`, `os.walk(root)`) no cruza contra ninguna marca hoy; añadir checkbox opt-in "solo juegos marcados" que, activo, salta cualquier archivo cuyo `games.source_path` no tenga el tag `"anbernic"` antes de copiarlo. Por defecto desactivado (comportamiento actual sin cambios) | `web/handlers/sync_cable.py:395`, frontend Cable Sync | ✅ `only_tagged` en `_do_cable_sync`: precalcula el set de `source_path` con tag `anbernic` una vez (join `games`+`game_tags`) y `_wanted()` lo consulta solo para archivos ROM del lado PC (no afecta a saves ni a `anbernic_to_pc`, que no tiene marcas que consultar). Checkbox "Solo ROMs marcados para la Anbernic" en `tab-cable.html`, visible solo con "ROMs" marcado. 4 tests nuevos (`tests/test_sync_cable_only_tagged.py`), 1047 pass |
| ANBERNIC-PICK-3 | **Informe de la corrida** — agregar en una vista legible los contadores que el pipeline ya calcula por corrida (organizados, duplicados exactos descartados, resueltos por RA, conflictos sin resolver) en vez de solo el log de texto — insumo directo para "qué se movió, qué no, qué se reemplazó, qué se renombró" que pidió el usuario. Base de datos real de la sesión 2026-08-28 ya disponible como caso de prueba: 13.211 organizados, 1.005 renombrados, 152 duplicados, 0 resueltos por RA, 295 conflictos (176 arcade) | `web/inbox_pipeline.py`, `web/static/js/tabs/inbox.js` | ✅ el paso "organize" no contaba duplicados exactos descartados ni conflictos sin resolver por separado (solo iban mezclados como texto en `organize_errors`) — dos contadores nuevos (`duplicates_removed`, `conflicts_unresolved`) en `_run_inbox_pipeline`, incrementados en las ramas ya existentes de `_same_content`/`_resolve_organize_conflict`. `_renderInboxResult()` (`inbox.js`) los añade a la línea de resumen junto a "Resueltos por RA" (ya se calculaba pero no se mostraba) |
| ANBERNIC-PICK-4 | **El sync también debe quitar de la consola lo que ya no está marcado** — petición del usuario 2026-08-29: al sincronizar, lo no marcado debería desaparecer de la Anbernic, no solo dejar de copiarse, para poder liberar espacio con el mismo flujo. Ya existía el checkbox "Espejo completo" (`delete_extra`) independiente de `only_tagged`; combinados, la rama ADB (cable) ya funcionaba bien (`_arel not in _pc_rels`, `_pc_rels` calculado con `_wanted()` que sí respeta el tag), pero la rama sistema de archivos (SD montada) no — su bucle de "extra en destino" llamaba a `_wanted(_f)` sobre archivos del lado Anbernic, que **siempre** devuelve `True` para ese lado (rama `except ValueError` de `_wanted`, necesaria para no romper `anbernic_to_pc`/`newest`, que sí deben ignorar el tag por diseño de ANBERNIC-PICK-2) | `web/handlers/sync_cable.py` (bucle `delete_extra` de `pc_to_anbernic`, modo sistema de archivos) | ✅ ese bucle ahora filtra por categoría (`_wanted_name`, igual que ya hacía la rama ADB) en vez de por `_wanted()` completo — "extra" sale de comparar contra `_pc_rels`, que ya respeta el tag; sin tocar `anbernic_to_pc`/`newest`. Tooltip de "Espejo completo" actualizado explicando la combinación. 1 test nuevo (`test_only_tagged_with_mirror_removes_untagged_from_device`), 1034 pass |

**Validado con dry-run real contra la RG556 (2026-08-29)**: 1 juego real
(`'96 Flag Rally.zip`, arcade) marcado `anbernic` vía `/api/tag`, sync
`pc_to_anbernic` por ADB, `what=roms`, `only_tagged=true`,
`delete_extra=true`, `dry_run=true` contra `/storage/521D-04EA/ROMs/arcade`.
Resultado: el marcado se detecta correctamente como ya presente (`SKIP —
mismo tamaño`, nunca entra en la lista de borrado) y **3.461 archivos sin
marcar** se listan como "se borrarían" (`.rommgr/cable_sync_ops.log`) — el
combo funciona tal como se diseñó. El tag de prueba se quitó al terminar
(sin residuo). Nota: el servidor llevaba corriendo desde antes del fix de
ANBERNIC-PICK-4 (Python no recarga módulos en caliente) — hubo que
reiniciarlo para probar la versión real del código; se esperó primero a que
terminara un job de Inbox en curso (15.105 ROMs) antes de reiniciar.

> **ANBERNIC-PICK-5 — hallazgo durante la validación anterior, bug real
> preexistente (no introducido por ANBERNIC-PICK-4)**: de los 3.461
> "extra" candidatos a borrar, **204 eran `.jpg` de `media/wheels/` (carátulas),
> más 2 `.txt`, 1 `.xml`, 1 `.ini`** — ninguno es un ROM, y el sync estaba
> acotado a `what=["roms"]` (sin "assets"/"media" marcado). Causa: `_cat_name()`
> (`web/handlers/sync_cable.py:372`) clasifica cualquier archivo que no sea
> una extensión de save como `"rom"` — no comprueba una lista real de
> extensiones de ROM, así que `_wanted_name()` (`:378`) acepta cualquier cosa
> que no sea un save cuando `"roms"` está en `what`. Con "Espejo completo"
> activo, esto borraría carátulas y metadatos junto con los ROMs de verdad.
> No afecta a copiar (solo se copian archivos que ya pasaron por el scan como
> ROM/save en la BD), pero si el "extra" del lado Anbernic no está en la BD
> —caso típico de `media/`, que nunca se escanea como juego— nada lo protege
> de aparecer como "extra". Pendiente: `_cat_name()` debería devolver una
> tercera categoría (`"other"`) para lo que no sea ni save ni ROM reconocido,
> y `_wanted_name()` debería excluirla salvo que `"assets"`/`"media"` esté en
> `what` explícitamente | `web/handlers/sync_cable.py:372-382` | ✅ `_cat_name()` ahora
> resuelve contra `ROM_EXTENSIONS` (`detection/platform_detector.py`, la misma
> tabla ya fiable del Inbox y de `LIB-MISPLACED-1`) en vez de asumir "rom" por
> descarte: extensión de save → `"save"`, extensión de ROM reconocida →
> `"rom"`, cualquier otra cosa → `"other"`. `_wanted_name()` solo considera
> `"other"` deseado si `"assets"` está explícitamente en `what` — con
> `what=["roms"]` (el caso real del incidente), carátulas/metadatos ya no
> cuentan como "extra" ni se copian ni se borran. `_category()` (usado solo
> para gating de backup de saves) no se tocó — sigue siendo binario
> save/rom, sin riesgo porque solo protege la rama "save". 3 tests nuevos
> (`tests/test_sync_cable_other_category.py`): reproduce el incidente exacto
> (espejo con `what=["roms"]` no borra `.jpg`/`.txt`/`.xml`/`.ini` huérfanos),
> confirma que el espejo real de ROMs sigue funcionando, y que pedir
> `"assets"` explícitamente sí permite espejar "other" |
| ANBERNIC-PICK-8 | **Enviar/eliminar en bloque desde la pestaña Juegos, sin pasar por el tag `anbernic`** (renumerado desde una colision de ID con ANBERNIC-PICK-4 -- ambas ramas reclamaron el mismo numero en paralelo) — complementa ANBERNIC-PICK-1/2 (que exigen marcar antes): dos botones nuevos que actúan directo sobre **el filtro actual** de la pestaña (mismo criterio que "Marcar para Anbernic"), por ADB. `direction="send_selected"` resuelve los juegos del filtro (`get_games_paginated`), dedupea duplicados del mismo juego quedándose con el que tiene más logros RA (`filter_duplicate_winners`, reutilizado de Duplicados de ROM) y hace skip-existing por tamaño antes de empujar. `direction="remove_selected"` copia el save de cada juego al PC (verificado por MD5) **antes** de borrar el ROM — un save nunca se borra ni se pierde si falla la copia — y solo entonces elimina por ADB | `web/handlers/sync_cable.py` (`_do_cable_sync`, ramas `send_selected`/`remove_selected`), `services/ra_duplicates_service.py` (`filter_duplicate_winners` reutilizado), frontend `tabs/games.js` (`sendFilteredToAnbernic`/`removeFilteredFromAnbernic`) + `tab-games.html` | ✅ 6 tests nuevos (`test_cable_sync_send_selected.py`, `test_cable_sync_remove_selected.py`, `test_ra_bulk_send_dedup.py`) |

| ANBERNIC-PICK-6 | **Discoverabilidad (feedback usuario 2026-08-29)**: el usuario no encontró cómo copiar en bulk PC→Anbernic ni cómo marcar juegos para que se retiren de la consola — ambos ya existen (Cable Sync con "solo ROMs marcados" + "Espejo completo" quita de la Anbernic lo no marcado, ANBERNIC-PICK-2/4) pero no están enlazados/explicados desde donde el usuario los buscó (Herramientas). Falta UX de descubrimiento, no código nuevo | `web/static/partials/tab-tools.html`, `tab-cable.html` | ✅ panel nuevo "Enviar archivos a la Anbernic" al principio de Herramientas, con el resumen del flujo (marcar en Juegos → Cable Sync "solo marcados"/"Espejo completo") y dos botones: uno a Juegos (`showTab('games')`) y otro a Cable Sync que además abre y hace scroll a "Sincronización avanzada" (`goToCableSyncAdvanced()`, `tabs/sync.js` — nuevo `id="cable-advanced-details"` en el `<details>`). Sin endpoints nuevos, solo navegación. Verificado sirviendo la página real (`curl` contra `rommgr serve`); no probado clic a clic en navegador (extensión Chrome no disponible en esta sesión) |
| ANBERNIC-PICK-7 | **Ampliación de ANBERNIC-PICK-6 (aclarado 2026-08-29): sync guiado de primer uso** — el usuario quiere empezar a usar la Anbernic llevando plataformas pequeñas enteras (NDS, arcade) sin tocar nada más, y eligiendo juego a juego en plataformas grandes (PS2) por espacio. El mecanismo ya existe (`ANBERNIC-PICK-1`: `POST /api/tag-bulk` con los mismos filtros que `/api/games`, incluye `platform` → marcar "toda una plataforma" es 1 filtro + 1 botón; `ANBERNIC-PICK-2`: Cable Sync "solo ROMs marcados") — falta un asistente/wizard en Juegos o Cable Sync que lo guíe explícitamente ("¿Qué te llevas a la Anbernic?" → plataformas pequeñas con checkbox "todo", grandes con enlace a la selección juego a juego) en vez de que el usuario tenga que descubrir la combinación de filtro+tag+sync por su cuenta | `web/static/js/tabs/games.js`, `tab-cable.html` | ✅ botón "🧭 Asistente guiado" en Herramientas (`openAnbernicWizard()`, `games.js`) — modal con plataformas separadas en pequeñas (≤2 GiB, botón "Marcar toda" de un clic vía `/api/tag-bulk`) y grandes (botón "Elegir juego a juego →" que navega a Juegos filtrado por esa plataforma, orden "Fecha de añadido"). `/api/platform-stats` (ya existente) ampliado con `total_size`/`tagged_count` por plataforma, sin endpoint nuevo. Además, selector individual nuevo en Juegos: botón 📦 por fila (`toggleRowAnbernic()`, mismo patrón que la ★ de favorito, vía `/api/tag` ya existente) y orden nuevo "Fecha de añadido" (`sort_by=added`, `created_at` expuesto en `/api/games`). 1038 pass. Verificado en vivo: `/api/platform-stats` con tamaños reales (MAME 37,7 GB, Arcade 27,5 GB, FBNeo 8,1 GB...), toggle 📦 ida y vuelta sobre un juego real sin dejar residuo |

---

### FTP-PICK — Elegir ROMs desde el navegador de la Anbernic (petición usuario 2026-08-29)

Origen: `docs/Feedback/29/8.md` + petición directa del usuario en sesión — quiere
poder, desde la Anbernic, elegir qué ROMs traerse del PC mientras `rommgr serve`
está corriendo, sin pasar por Cable Sync/ADB. **Rediseñado a mitad de sesión**:
el plan original (servidor FTP a mano + app Android nativa en Kotlin) se
descartó por sugerencia del propio usuario — la Anbernic **ya abre un
navegador** para llegar al servidor (mismo flujo que la pestaña Anbernic de
setup guiado), así que un botón de descarga en la propia pestaña Juegos
reutiliza servidor, auth, buscador y filtros ya existentes, sin protocolo
nuevo ni código Kotlin sin compilar. La implementación FTP + app nativa
(`ftp/ftp_server.py`, `PcFtpClient.kt`, `PickScreen.kt`) se hizo, se verificó
contra la biblioteca real y **se borró entera** al cambiar de enfoque — nada
de eso queda en el repo.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| FTP-PICK-1 | **Endpoint de descarga por HTTP, reutilizable desde donde sea** — nuevo `GET /api/download-rom?path=<source_path>`: solo sirve rutas que ya están en la BD como ROM (`file_type='rom'`, nunca un archivo arbitrario del disco aunque exista físicamente) y que además resuelvan dentro de `library_root`/`anbernic_root` (`Path.resolve()` + `is_relative_to()`, mismo patrón de path traversal que REV43-16). Streaming real vía `shutil.copyfileobj` (nuevo `ctx._send_file()` en `web/server.py`) — nunca carga el archivo entero en memoria, a diferencia de `_send()`/`/api/asset-image` (pensados para JSON/imágenes pequeñas); necesario porque un ISO de PS2/GameCube puede pesar varios GB. `Content-Disposition: attachment` con el nombre real del juego. Enlace ⬇ en la tabla de Juegos (`games.js`) para uso directo desde el navegador | `web/handlers/games.py` (`get_download_rom`), `web/server.py` (`_send_file`), `web/static/js/tabs/games.js` | ✅ 5 tests nuevos (`tests/web/test_download_rom.py`: descarga normal, sin parámetro, archivo no trackeado en BD aunque exista en disco, traversal fuera de `library_root`, archivo borrado tras el scan) + **probado contra la biblioteca real**: descargado un `.nes` real por HTTP y comparado SHA1 byte a byte contra el original (coinciden); confirmado 404 para una ruta arbitraria del sistema no trackeada y 400 sin parámetro `path`, ambos contra el servidor real corriendo. 1042 pass |
| FTP-PICK-2 | **Pantalla "Elegir ROMs" en la app Android (ANDROID-SYNC)** — decisión final del usuario: quería el flujo dentro de la app nativa que ya se está construyendo, no solo un enlace en el navegador. En vez de repetir el error del primer intento (protocolo FTP a mano + cliente Kotlin a medida, descartado), la app llama por HTTP normal a los mismos dos endpoints ya probados en el lado Python (`GET /api/games` para buscar/filtrar, `GET /api/download-rom` para bajar) — cero protocolo nuevo, cero librería nueva (`HttpURLConnection`/`org.json` son parte de la plataforma Android, igual que el SDK de Dropbox ya en uso). `PcApiClient.kt` nuevo: `listPlatforms()`/`listGames()` parsean el JSON ya devuelto por el PC, `downloadRom()` guarda en `<romsDestPath>/<carpeta-de-plataforma-real-del-PC>/<nombre>` — la carpeta se deduce del propio `source_path` que ya devuelve `/api/games` (segmento inmediatamente anterior al nombre de archivo), sin necesitar conocer `library_root` del PC. Pantalla `ui/pick/PickScreen.kt` (formulario IP:puerto → lista de plataformas + buscador + lista de juegos con descarga y progreso), tercera pestaña en `MainActivity.kt`. Ajustes nuevos en `SettingsRepository.kt` (`pcHost`, `romsDestPath`). `usesCleartextTraffic="true"` en el manifest (HTTP plano, no HTTPS — mismo modelo de confianza de LAN doméstica que `allow_lan` en el PC; sin login, asume el PC sin PIN activo, limitación conocida documentada en el propio código) | `android/app/src/main/java/com/retrovault/android/sync/PcApiClient.kt` (nuevo), `ui/pick/PickScreen.kt` (nuevo), `data/prefs/SettingsRepository.kt`, `ui/MainActivity.kt`, `AndroidManifest.xml` | ✅ **compilado y verificado 2026-08-29** con toolchain portable (`JAVA_HOME`=jdk17, `./gradlew test assembleDebug`, ambos en verde). Encontrado y arreglado un bug real de compilación: `PickScreen.kt:9` importaba `androidx.compose.foundation.layout.weight` como función de paquete — `weight` es en realidad un método miembro de las interfaces `RowScope`/`ColumnScope` (no una función top-level importable), así que el import resolvía a un símbolo interno no relacionado y rompía `compileDebugKotlin`/`compileReleaseKotlin`. Fix: eliminar el import — los dos usos de `.weight(1f)` ya están dentro de lambdas `Row{}`/`Column{}`, se resuelven solos por receiver implícito sin necesitar import. `./gradlew test` (incluye `PcApiClientTest.kt`, 3 tests) en verde. **2026-09-08 — instalación real confirmada, interacción manual bloqueada**: `app-debug.apk` del 2026-08-30 (coincide byte a byte con el HEAD actual, working tree limpio en `android/`) instalado con `adb install -r` en la RG556 real — éxito. `rommgr serve` real levantado en `192.168.1.160:7777` (misma red que el WiFi de la RG556, `192.168.1.165`), API respondiendo (`GET /api/games` → 200). `am start -n com.retrovault.android/.ui.MainActivity` confirma que la Activity ya está en primer plano sin crash ("Warning: Activity not started, its current task has been brought to the front" = ya estaba arriba). **No se pudo completar la prueba interactiva** (introducir IP, listar juegos, descargar): la pantalla de la RG556 vuelve a dormirse casi al instante pese a `KEYCODE_WAKEUP`/`wm dismiss-keyguard` (settings dice `screen_off_timeout=1800000`, no explica el comportamiento) — 3 de 4 capturas salieron en negro (10.608 bytes, tamaño idéntico = mismo frame vacío), sin margen para tocar la UI a ciegas por ADB. Sin cambios de código; validación de tap-through sigue pendiente de hacerse a mano por el usuario frente al dispositivo |

---

### GAME-BLOCKLIST — Eliminar un juego de ambas bibliotecas y evitar que un sync lo recupere (feedback usuario 2026-08-29)

Plan de implementación en `.claude/roadmaps/18-game-blocklist.md`.

Origen: `docs/Feedback/29/8.md`, aclarado por el usuario — caso de uso: "este juego
(ej. un Barbie) no me interesa, quiero borrarlo de PC y Anbernic a la vez, y que
ningún sync futuro me lo vuelva a colar". Distinto de `STORAGE-MGR` (archivado:
borrado en bloque puntual, sin bloqueo permanente) y de `ANBERNIC-PICK`
(el tag `"anbernic"` es opt-in por lo que SÍ debe estar en la consola, no un
"nunca más" global que también cubra el PC). Necesita una marca persistente
por identidad de juego (SHA1/`canonical_title`, no por ruta — la ruta difiere
entre PC y Anbernic y cambia al renombrar) que el scan/inbox/match respete.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| GAME-BLOCKLIST-1 | Diseñar la marca de exclusión permanente (tabla dedicada `blocklist`: sha1, canonical_title, reason, created_at — decisión confirmada con el usuario 2026-09-24, no el patrón `game_tags`) + acción "Eliminar de ambas bibliotecas" (PC → papelera `_descartados/`, Anbernic → `AdbTransport.remove`, mismo patrón de `STORAGE-MGR-3`/`services/storage_service.py`, marcando ANTES de borrar) | `database/schema.py`, `database/repositories/blocklist.py` (nuevo), `services/storage_service.py` (`block_and_delete_game`), `web/handlers/collection.py` (`POST /api/blocklist/block`), UI: `web/static/partials/_foot.html` + `web/static/js/tabs/games.js` (`gpBlockAndDelete`) | ✅ hecho (2026-09-24) |
| GAME-BLOCKLIST-2 | Hacer que el scan/match/Inbox respeten la marca — un archivo con SHA1 bloqueado no se re-organiza ni se re-cuenta como pendiente si reaparece (p. ej. tras un sync `anbernic_to_pc` o un `adb pull` manual); decisión confirmada con el usuario 2026-09-24: se avisa una vez y se deja para revisión manual (nunca auto-descarte silencioso) | `database/repositories/games.py` (`get_unresolved_games`/`get_matched_games` excluyen sha1 bloqueados), `web/inbox_pipeline.py` (paso "organizar" salta bloqueados + `blocked_found` en el resultado), `web/handlers/collection.py` (`/api/sync-roms` rechaza sha1 bloqueado en ambas direcciones), `web/static/js/tabs/inbox.js` (aviso en el resultado del job) | ✅ hecho (2026-09-24) |

---

### SYNC-WII-SCOPE-1 — `SyncSource` no puede acotar solo los saves reales de Dolphin (Wii) (hallazgo rammu, 2026-09-21)

Al reestructurar `sync.sources` en rammu siguiendo `Tareas/Estructura-Estandarizada-Sync.md`
(convenio `dropbox:/RetroSync/saves/<emulador>/<tipo>` de PC2, `dolphin/gc` +
`dolphin/wii`), la fuente `Dolphin (Wii)` con `local_dir` apuntando a la
carpeta `Wii/` completa (`sync_all=true`) empezó a subir el NAND emulado
entero (`title/<tipo>/<id>/content/` = IOS, System Menu, apps de canales
instalados — `.app`, certificados `.pem`, `fst.bin`), no solo los saves.
Medido en rammu: **96 MB en `Wii/` total, de los que solo 0.29 MB son saves
reales** (`title/*/*/data/`, el equivalente NAND del save real por juego —
`title/00010000/<gameid-hex>/data/`). `SyncSource` solo soporta un
`local_dir` plano (sin include/exclude), así que no hay forma de acotar hoy
a "todas las subcarpetas `data/` bajo `title/*/*`" sin sincronizar también
`content/` (las apps instaladas). Parado a mitad de sync real (`--apply`)
antes de subir más basura; fuente `Dolphin (Wii)` desactivada en
`config.toml` (comentada, con la medición) hasta que se diseñe bien.
**GC no tiene este problema** — su carpeta ya es 100% saves (`.gci` +
`.raw`), se dejó activa. **Limpieza pendiente**: revisar
`dropbox:/RetroSync/saves/dolphin/wii` — puede tener algunos `.app`/`.pem`
subidos antes de parar el proceso (no es sensible ni gran volumen, pero es
basura que no debería estar ahí).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| SYNC-WII-SCOPE-1 | Sincronizar solo `title/*/*/data/` de Dolphin (Wii) | `config.py` (`SyncSource.include_glob`), `sync/save_syncer.py` (`list_local_saves`, `sync_saves`), `cli.py` (x2), `web/handlers/sync_cloud.py` | ✅ hecho 2026-09-21 — opción (a): campo `include_glob: str = "**/*"` en `SyncSource` (compatible hacia atrás, resto de fuentes sin cambio de comportamiento), usado en `saves_dir.glob(include_glob)` en vez del `rglob("*")` fijo. `config.toml` reactivado con `include_glob = "title/*/*/data/**/*"`. Test `test_list_local_saves_include_glob_scopes_dolphin_wii_nand` en `tests/test_save_syncer.py`. Verificado en dry-run real contra el NAND de rammu: 10 archivos detectados (todos bajo `data/`), `content/`/`shared1/`/etc. excluidos — antes eran 96 MB, ahora ~0.29 MB reales. Pendiente aplicar en PC2 y reactivar allí también |
| SYNC-WII-SCOPE-2 | Limpiar `dropbox:/RetroSync/saves/dolphin/wii` de archivos de sistema subidos por error antes de detectar SYNC-WII-SCOPE-1 (`.app`, `.pem`, `fst.bin` — no saves) | — (limpieza manual en Dropbox o vía `rclone delete`) | ✅ hecho 2026-09-21 — `tools/rclone.exe purge` sobre la carpeta entera, confirmado vacía (53 archivos, 17.4 MB, 0 saves reales entre ellos) |

---

### CABLE-SYNC-DUP-PATHS-1 — investigación cable-sync ADB con la Anbernic real (rammu, 2026-09-21) — cerrada, no era un bug

Con la Anbernic conectada por USB (autorizada, `adb devices` → `device`), se
probó `POST /api/cable-sync` (`direction=pc_to_anbernic`, `use_adb=true`,
`dry_run=true`). Primer intento con `pc_path=E:\Carpetas anbernic` (raíz de
la biblioteca): **528/528 marcados para copiar, 0 ya coincidentes** —
sospecha inicial de bug real de matching, **descartada tras seguir la
cadena hasta la causa raíz** (regla "Investigar antes de arreglar",
CLAUDE.md):

1. **Error de test #1 — `pc_path` incorrecto**: se pasó la raíz de la
   biblioteca (`E:\Carpetas anbernic`) en vez de la carpeta de saves
   (`E:\Carpetas anbernic\saves`). En Android, RetroArch guarda los saves
   planos junto a la plataforma (`RetroArch/mame/fixeight.nv`), sin
   subcarpeta `saves/` — con `pc_path` mal puesto, TODAS las rutas
   relativas quedaban desalineadas por ese segmento de más. Repetido con
   `pc_path=.../saves`: bajó a 229/229 copiar, seguía en 0 skipped.
2. **Error de test #2 — falta `skip_existing: true`**: `_skip_existing_device()`
   (`web/handlers/sync_cable.py:729`) devuelve `False` sin comprobar nada
   si `skip_existing` no viene en el payload — **por defecto es `false`**,
   así que cualquier dry-run sin ese flag marca todo como "a copiar" aunque
   ya exista igual en el dispositivo. No es un bug, es un parámetro opt-in
   de la propia API (ver `openapi.json` — no aparece en el ejemplo de
   payload, por eso se me pasó la primera vez). Con
   `pc_path=.../saves` + `skip_existing=true`: **123 ya coinciden (mismo
   tamaño), 106 realmente faltan, 0 errores** — número coherente, cierra
   la investigación.

**Hallazgo secundario real, menor**: 8 nombres de save duplicados en 2-3
rutas distintas del dispositivo (19 de 288 archivos totales) — restos de un
`savefile_directory` mal configurado en el pasado en la Anbernic (mismo
patrón de drift que `retroarch_cfg_writer.py` en PC, ver commit `ac9e905`
de hoy), ejemplo verificado con `adb shell find ... -iname 'punisher.nv'`:
`RetroArch/saves/cps1/punisher.nv` (convenio nuevo) +
`RetroArch/cps1/punisher.nv` + `RetroArch/cps1/fbneo/punisher.nv`
(legado). Solo 19 archivos, no bloquea nada — separado en su propia tarea.

**No se ejecutó ningún `--apply` real** en esta sesión (quedó todo en
dry-run) — 106 archivos / ~230 MB reales pendientes de subir a la
Anbernic, listos para aplicar en la próxima sesión con los parámetros ya
correctos (`pc_path=.../saves`, `android_path=/storage/emulated/0/RetroArch`,
`skip_existing=true`).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
**Mapeo completo + backup hechos 2026-09-21** (rammu, con la Anbernic real
por ADB) — **no se borró nada del dispositivo**, decisión del usuario
("informe + backup, sin borrar todavía"). 823 archivos de save/state en el
dispositivo, **289 nombres duplicados en rutas legado (706 archivos
implicados)** — mucho mayor que la estimación original de 8. Clasificados
en `.rommgr/legacy_dups_report_2026-09-21.csv` (gitignored, local):

| Clasificación | Grupos | Criterio |
|---|---|---|
| `junk_zero_bytes` | 14 | Todas las copias son 0 bytes — basura, sin riesgo de pérdida |
| `safe_same_copy_event` | 145 | Mismo tamaño, mtimes a ≤60s entre sí — típico de una migración puntual (mismo patrón que `CABLE-SYNC-SAVES-PREFIX-1`: "Advance Wars 2 [E].sav", 2s de diferencia) |
| `review_time_gap` | 123 | Mismo tamaño pero mtimes separados >60s — mismo tamaño no garantiza mismo contenido, revisar caso a caso antes de decidir |
| `CONFLICT_diff_size` | 7 | Tamaño distinto entre copias — divergencia real de contenido, **nunca borrar automáticamente** |

**Por qué no se automatizó el borrado ni con criterio "más reciente":**
uno de los 7 grupos conflictivos (`Pokemon - Edicion Plata SoulSilver
(Spain).sav`) tiene 3 copias — dos idénticas de 512KB (`nds/` y
`saves/nds/`, duplicado real y seguro) y una tercera de **0 bytes** en
`emulator_saves/me.magnum.melonds/saves/` con el mtime más reciente
(2026-08-28). Un criterio ciego de "quedarse con la copia más nueva por
fecha" habría elegido el archivo vacío y descartado la partida real de
512KB — la razón por la que esta tarea sigue sin automatizar el borrado
(Pilar 3: "cualquier bug aquí es prioridad absoluta, pérdida de progreso").
Los otros 6 grupos conflictivos son el mismo patrón: saves antiguos del
core `VBA Next` (abandonado) junto a saves mucho más recientes del core
`gba` actual — casi seguro seguros de borrar, pero no decidido
automáticamente sin revisión humana.

**Backup completo**: los 706 archivos de los 289 grupos (TODAS las
copias, no solo las "candidatas a borrar") están en
`.rommgr/legacy_dups_backup_2026-09-21/` (gitignored, local, misma
estructura relativa que el dispositivo) — 706/706 ok, 0 errores.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CABLE-SYNC-LEGACY-DUPS-1 | Limpiar en la Anbernic los saves duplicados en rutas legado — no bloquea el cable-sync normal (`CABLE-SYNC-SAVES-PREFIX-2` ya lo hace robusto a esto), solo deja basura residual | — (limpieza manual en el dispositivo, sin tocar código) | ✅ **completo 2026-09-21**. Primera pasada (bajo riesgo, tamaño/fecha): 159 grupos/240 archivos (`junk_zero_bytes` + `safe_same_copy_event`) borrados, backup previo intacto, 0 errores — ver detalle abajo. **Segunda pasada (los 130 grupos restantes, `review_time_gap` + `CONFLICT_diff_size`) resuelta por contenido real**: en vez de decidir por tamaño/fecha (arriesgado — el `size_bytes` de un save GBA de tamaño fijo no dice nada del contenido), se calculó el SHA1 real de cada copia contra el backup local ya hecho (sin tocar el dispositivo, que estaba ocupado con el rescan `ps2` de `ANDROID-DUP-2`). Resultado: de 321 archivos en esos 130 grupos, **174 eran copias byte-idénticas de verdad** (mismo contenido exacto, solo cambiaba la ruta/fecha) — borradas vía `adb shell rm`, 0 errores, verificado post-borrado que las 147 rutas canónicas conservadas (una por cada contenido realmente distinto) siguen intactas. **Ningún archivo de contenido único se tocó** — incluye casos con saves reales de un core distinto (p. ej. `Metroid - Zero Mission [E].srm` tiene un save propio bajo `saves/mGBA/` además del de `VBA Next`/`gba`), que quedan sin resolver a propósito, decisión del usuario si alguna vez hace falta. **Hallazgo colateral nuevo, sin implementar**: 2 grupos tenían copias bajo `saves/.stversions/<core>/` — carpeta de versionado de Syncthing (herramienta de terceros en el dispositivo, no creada por este proyecto), debería excluirse del escaneo/legacy-dup igual que `_descartados/`/`emulator_saves/`, no se ha tocado. Backup completo de las 3 pasadas sigue en `.rommgr/legacy_dups_backup_2026-09-21/` |
| CABLE-SYNC-APPLY-1 | Ejecutar el `--apply` real de `pc_to_anbernic` con los parámetros ya validados (`pc_path=E:\Carpetas anbernic\saves`, `android_path=/storage/emulated/0/RetroArch`, `skip_existing=true`, `safe_mode=true`) — 106 archivos / ~230 MB pendientes de subir | — | ✅ hecho 2026-09-21 — 106 subidos, 123 ya coincidían, 0 errores, 232 MB, coincide exacto con el dry-run |

---

### CABLE-SYNC-SAVES-PREFIX-1 — cable-sync ADB no reconoce el convenio D2 `saves/` del PC — afecta a la UI real, no solo al test de arriba (rammu, 2026-09-21)

Al ejecutar `CABLE-SYNC-APPLY-1` con `pc_path` apuntando **directamente** a
`E:\Carpetas anbernic\saves` (no a la raíz de la biblioteca) tuvo que
usarse a propósito para que el matching funcionara. Pero **la UI real
(`sync.js:940`, `_setIfEmpty('cable-pc-path', ... cfg.library_root ...)`)
por defecto pone `pc_path = library_root`** (la raíz completa, no
`.../saves`) — necesario porque el mismo campo también sirve para
sincronizar ROMs, no solo saves. Con ese valor por defecto, cualquier
usuario que haya centralizado sus saves con el convenio D2
(`savefile_directory = library_root/saves`, el mismo botón "Aplicar
layout de saves" arreglado hoy en `ac9e905`) sufriría el mismo problema
que el primer intento de `CABLE-SYNC-DUP-PATHS-1`: **todos los saves se
marcarían como "nuevos"** en vez de detectarse como ya sincronizados,
porque la ruta relativa del lado PC lleva el prefijo `saves/` y la del
lado Android no.

**Causa raíz confirmada en código**: `canonical_rel_posix()`
(`sync/android_paths.py`) traduce el primer segmento (carpeta de
plataforma) usando `PLATFORM_BY_FOLDER`/`_ES_PLATFORM_FOLDERS`, pero por
diseño explícito (su propio docstring) **no toca segmentos que no
reconoce como plataforma — y `saves` es uno de ellos**: `"no inventa una
carpeta nueva para algo que no reconoce (p. ej. carpetas de sistema como
BIOS/ o saves/)"`.

**No es un fix trivial de una línea** — verificado en el dispositivo real
(`adb shell find`/`ls_recursive` sin filtro) que **el propio Android
mezcla convenios según el core**: algunos escriben el save plano junto a
la plataforma (`RetroArch/mame/fixeight.nv`), otros ya usan su propia
subcarpeta `saves/<core>/` (`RetroArch/saves/mame2003/nvram/mk3.nv`,
`RetroArch/saves/bsnes2014/Earthbound (1).srm`) — quitar sin más el
prefijo `saves/` del lado PC rompería el matching para los cores que sí
lo tienen en Android. Necesita diseño, no un parche a ciegas, en el pilar
de mayor riesgo del proyecto ("cualquier bug aquí es prioridad absoluta",
CLAUDE.md).

**Mapeo real completado (rammu, 2026-09-21, `adb shell find`/`stat` sobre la
Anbernic conectada)** — el problema es mucho más grande que los "8
duplicados" estimados en `CABLE-SYNC-LEGACY-DUPS-1`: hay carpeta plana
(`RetroArch/<plataforma>/`) Y carpeta `saves/` para prácticamente todas las
plataformas probadas, con solapamiento de nombre de archivo casi total y
**ambas copias con actividad reciente** (no es basura histórica de una
migración puntual — algunos juegos escriben en un lado, otros en el otro,
en la misma sesión de uso):

| Plataforma | Archivos en plano | Archivos en `saves/` | Mismo nombre en ambos |
|---|---|---|---|
| mame | 25 | 24 | 24 |
| gba | 47 | 115 | 46 |
| psx | 7 | 9 | 6 |
| snes | 4 | 3 | 3 |
| nes | 2 | 3 | 1 |
| cps1 | 3 | 2 | 2 |
| cps2 | 2 | 1 | 1 |

Verificado con `stat` en `Advance Wars 2 [E].sav` (gba): mismo tamaño
(65536 B) en plano y en `saves/`, mtimes a 2 segundos de diferencia
(2025-03-09) — copia puntual antigua, no reescritura activa de ese archivo
concreto. Pero `ls -t` muestra archivos con mtime reciente en **ambas**
ubicaciones (`Pokémon Rojo fuego [E].sav` en plano, `Pokemon WaterBlue.srm`
y `Final Fantasy Tactics [E].srm` en `saves/gba`) — confirma que hoy en
día se sigue escribiendo en los dos sitios según qué core/config se use
por partida, no es solo arrastre histórico.

**El nombre de la subcarpeta bajo `saves/` no es consistente**: a veces es
el nombre canónico de plataforma ya reconocido por `PLATFORM_BY_FOLDER`
(`saves/gba`, `saves/psx`, `saves/snes`, `saves/mame`, y por coincidencia
`saves/cps1`/`saves/cps2`/`saves/fbneo`, que están en `platforms.toml`
como alias de "Arcade"), y a veces es el nombre del core de RetroArch tal
cual, que **no** está en `PLATFORM_BY_FOLDER` (`saves/mame2003`,
`saves/bsnes2014`, `saves/Snes9x`, `saves/Snes9x 2005 Plus`,
`saves/VBA Next`, `saves/FCEUmm`, `saves/mGBA`, `saves/PPSSPP`,
`saves/Citra`, `saves/LRPS2`, `saves/Beetle PSX`). No hay mapeo core→plataforma
completo hoy en el código — haría falta construirlo y mantenerlo para
poder confiar en el segundo segmento de la ruta.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CABLE-SYNC-SAVES-PREFIX-1 | Mapear en el dispositivo real qué cores usan `saves/<core>/` vs plano junto a la plataforma | — (investigación en el dispositivo real, sin tocar código) | ✅ hecho 2026-09-21 — ver tabla y hallazgos arriba |

**Hallazgos relacionados, fuera de alcance de este fix** (revisado el código
alrededor de `_skip_existing_device`/`_skip_existing_pc` al implementar,
sin tocarlos — CLAUDE.md "Investigar antes de arreglar"):

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CABLE-SYNC-DOWNLOAD-DEST-1 | Canonicalizar el destino de descarga (`anbernic_to_pc`/`newest`), que escribía en `pc_root / rel_posix` usando la ruta cruda del dispositivo sin canonicalizar | `sync/android_paths.py` (`canonical_download_rel_posix`, nueva), `web/handlers/sync_cable.py` (`_adb_copy_to_pc`, delete_extra ×2), `sync/cable_engine.py` (`plan_direction`, ramas `anbernic_to_pc`/`newest`), `web/cable_sync_daemon.py` (`_adb_copy_to_pc` legacy) | ✅ hecho 2026-09-21 — decisión de diseño confirmada con el usuario: (1) con carpeta intermedia reconocible (`saves/psx/foo.sav`, "psx" SÍ es plataforma conocida) → aterriza en la ruta canónica sin `saves/` (`psx/foo.sav`), igual criterio que ya usa la subida; (2) con carpeta intermedia ambigua (`saves/mame2003/...`, core sin mapear) → se mantiene la ruta cruda, no se arriesga a adivinar mal. Nueva función `canonical_download_rel_posix()` en `android_paths.py`, usada en los 3 sitios que escriben destino de descarga — incluye actualizar los 2 bloques `delete_extra`/espejo que comparaban por ruta cruda (si no, un archivo recién bajado a su ruta canónica se leía como "extra" y se borraba). 8 tests unitarios nuevos (4 en `test_android_paths.py`, 2 en `test_cable_engine.py`, más los de `canonical_download_rel_posix` en sí) cubriendo exactamente el caso `saves/gba/mario.sav → gba/mario.sav` y el caso ambiguo sin tocar. Suite completa (1417 tests) sin regresiones nuevas. **Validado en real 2026-09-22** (Día68 continuación): `--apply` real de `newest` con `pc_path=library_root`, `android_path=/storage/emulated/0/RetroArch`, 96/96 copiados, 0 errores. Verificado con mtimes tras la operación: `ps2/Mcd001.ps2` (carpeta reconocible en origen) bajó 1:1 sin pasar por `saves/`, confirmando el caso (1). Casos con carpeta intermedia `Unknown/` en origen (`sailormn_europe.nv`, `Kid Dracula (World)...sav`) se preservaron tal cual en destino (`Unknown/...`) — no es un fallo de nuestra canonicalización, es RetroArch en el propio dispositivo el que ya guarda esos saves bajo `Unknown/` (core sin mapear a contenido), confirmando el caso (2) también funciona en real |
| CABLE-SYNC-NEWEST-CANON-1 | Corregir la dirección `newest` en modo ADB, que comparaba `pc_index`/`ab_index` por ruta relativa cruda de ambos lados | `web/handlers/sync_cable.py` (bloque `elif direction == "newest":`) | ✅ hecho 2026-09-21 — reescrito para reusar el `ab_index`/`ab_by_name` ya construidos arriba (eliminada la reconstrucción redundante) con el mismo fallback por nombre de `CABLE-SYNC-SAVES-PREFIX-2`: solo hace match por nombre si hay un único candidato del lado Android (ambiguo con >1 candidato → se trata como archivo distinto, comportamiento anterior conservado como fallback seguro). Test nuevo `test_newest_direction_skips_file_under_different_device_prefix_same_mtime`. **Validado en real** con `pc_path=library_root`, `direction=newest`: 405/597 reconocidos como ya sincronizados; los 192 restantes son casos legítimos (BIOS/defaults solo en un lado, diferencias reales de mtime), sin ruido del problema de prefijos |
| CABLE-SYNC-NEWEST-CANON-2 | Mismo problema de fondo en las otras 2 reimplementaciones independientes de "newest": (a) `sync/cable_engine.py:plan_direction()` — compartido por el sync manual en modo filesystem/SD montada y el daemon SD-auto; (b) el fallback "RetroArch (legacy)" del daemon auto-sync ADB (activo cuando `get_adb_sync_sources()` no devuelve fuentes — usuarios sin `emulator_paths` configurado) | `sync/cable_engine.py` (`plan_direction`, rama `newest`), `web/cable_sync_daemon.py` (fallback "RetroArch (legacy)") | ✅ hecho 2026-09-21 — en vez de parchear cada reimplementación por separado, se extrajo la lógica de matching (ya escrita 3 veces con el mismo bug) a una función única y testeada: `reconcile_newest_by_name()` en `sync/android_paths.py` — empareja por clave exacta, con fallback por nombre solo si hay un único candidato del lado Android (ambiguo → sin emparejar, comportamiento seguro). Las 3 implementaciones (`sync_cable.py`, `cable_engine.py`, `cable_sync_daemon.py`) ahora son consumidores delgados de la misma función — evita que el mismo bug reaparezca una cuarta vez. 4 tests unitarios nuevos en `tests/test_android_paths.py` + 2 tests nuevos en `test_cable_engine.py`. Suite completa (1414 tests) sin regresiones (los 3 fallos que aparecen son ambientales — dispositivo ADB real conectado, no relacionados). **Revalidado en real tras el refactor**: mismo resultado exacto que antes (405/597 reconocidos, 192 candidatos legítimos, 0 errores) — el refactor no cambió comportamiento. El fallback per-emulador ADB del daemon (`adb_sources` con `local_saves`/`android_saves` dedicados) no tiene este problema — son carpetas 1:1 sin ambigüedad de plataforma, no se tocó |

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CABLE-SYNC-SAVES-PREFIX-2 | Matching correcto ignorando el prefijo/carpeta intermedia del lado Android | `web/handlers/sync_cable.py` (`_skip_existing_device`, `_skip_existing_pc`) | ✅ hecho 2026-09-21 — implementada la opción de "matchear por nombre de archivo, ignorando segmentos intermedios", con tamaño como criterio de colisión (mismo patrón ya usado en todo el archivo para "ya existe"). Índice secundario `ab_by_name`/`_pc_by_name()` construido a partir de los índices existentes (`ab_index`, `_iter_files(pc_root)`) — sin mapeo core→plataforma, sin tocar `android_paths.py`. Tests nuevos en `tests/test_cable_sync_rom_skip_existing.py` (prefijo `saves/` en ambas direcciones). **Validado en real** contra la Anbernic con `pc_path=library_root` (el caso que antes fallaba, `CABLE-SYNC-DUP-PATHS-1`): antes 0/528 reconocidos, ahora **522/528 saltados como ya sincronizados, solo 6 genuinamente nuevos** (dry-run, `pc_to_anbernic`, `skip_existing=true`) |

---

### CABLE-SYNC-EMULATOR-SAVES-LEAK-1 — `emulator_saves/` (carpeta interna del PC) se filtra al dispositivo (rammu, 2026-09-21)

Investigando por qué `Pokemon - Edicion Plata SoulSilver (Spain).sav`
aparecía como conflicto en `CABLE-SYNC-LEGACY-DUPS-1` (una copia de 0
bytes con el mtime más reciente de las 3): **no es un conflicto real de
partidas**. El save de verdad está en `nds/Pokemon - Edicion Plata
SoulSilver (Spain).sav` (512KB, el que usa el core normal de RetroArch).
La copia sospechosa vive en
`/storage/emulated/0/RetroArch/emulator_saves/me.magnum.melonds/saves/...`
— y `emulator_saves/<package>/` es una carpeta que `get_adb_sync_sources()`
(`config.py`) usa **solo en el PC** para bajar saves por-emulador vía
ADB; nunca debería existir tal cual dentro del árbol `RetroArch/` del
dispositivo.

**Confirmado que no es un caso aislado**: hay **54 archivos** bajo
`/storage/emulated/0/RetroArch/emulator_saves/` en el dispositivo real
(toda la carpeta de estados de DuckStation incluida), todos con mtime a
pocos segundos entre sí — una única subida masiva, no uso real de la app.

**Causa raíz**: cuando `get_adb_sync_sources()` devuelve una lista vacía
(`adb_sources`), el daemon de auto-sync (`web/cable_sync_daemon.py`,
`_run_auto_sync`) cae al fallback `"RetroArch (legacy)"` con
`local_saves = config.library_root` (la biblioteca **entera**) contra
`android_saves = config.sync.auto_sync_android_path` — sin excluir
`emulator_saves/`, que es puramente contabilidad interna del propio
proyecto, no algo que ningún core de RetroArch en Android reconozca. El
mismo problema aplica al endpoint manual `/api/cable-sync`
(`web/handlers/sync_cable.py`) cuando `pc_path=library_root`: `_iter_files`
solo excluye dotfiles y `_descartados/`, no `emulator_saves/`. El archivo
de origen en el PC ya estaba a 0 bytes (melonDS nunca llegó a guardar esa
partida concreta — se jugó con otro core), así que la copia subida
también salió vacía; sin pérdida de progreso real, pero explica varios de
los 289 grupos de `CABLE-SYNC-LEGACY-DUPS-1` (al menos los 54 confirmados
+ los que generaron por round-trip de vuelta al PC, como el `saves/saves/`
doblemente anidado visto en `Castlevania - Dawn of Sorrow`).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| CABLE-SYNC-EMULATOR-SAVES-LEAK-1 | Excluir `emulator_saves/` del árbol que camina `pc_to_anbernic`/`newest` cuando `pc_path`/`local_saves` es la raíz de la biblioteca | `config.py` (`EMULATOR_SAVES_DIR_NAME`, nueva), `web/handlers/sync_cable.py` (`_iter_files`), `sync/cable_engine.py` (`iter_files`), `web/cable_sync_daemon.py` (walk de `_iter_local` en el fallback legacy) | ✅ hecho 2026-09-21 — mismo patrón que la exclusión ya existente de `_descartados/`/`TRASH_DIR_NAME`: nueva constante `EMULATOR_SAVES_DIR_NAME = "emulator_saves"` en `config.py` (reemplaza el literal ya usado en `get_adb_sync_sources()`), excluida en los 3 walks (`dirs[:] = [...]`) igual que `TRASH_DIR_NAME`. Aplica a ambos lados del walk (PC y Anbernic) — inocuo si el dispositivo está limpio, corta la fuga si no. 2 tests nuevos (`test_iter_files_skips_emulator_saves` en `test_cable_engine.py`, `test_pc_to_anbernic_never_uploads_emulator_saves_folder` en `test_cable_sync_rom_skip_existing.py`). Suite completa (1419 tests) sin regresiones nuevas. **No limpia los 54 archivos ya filtrados en el dispositivo real** — eso sigue en `CABLE-SYNC-LEGACY-DUPS-1` (ya respaldados en `.rommgr/legacy_dups_backup_2026-09-21/`), este fix solo corta la fuga hacia adelante |

---

### SAVES-UX — Historial de saves y contexto en resolución de conflictos (idea usuario 2026-09-22)

Reducir el "miedo a sobrescribir" del pilar 3 más allá del backup-antes-de-
sobrescribir ya existente: dejar ver y restaurar versiones anteriores, y dar
más contexto que solo el timestamp al resolver un conflicto.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| SAVES-HISTORY-1 | **Replanteada tras investigar (2026-09-22)**: el historial+restauración ya existía y funcionaba (`rom_manager/backup/save_backup.py`, `GET /api/save-backups`, `POST /api/restore-backup`, UI en la ficha de juego `games.js:877-885,1090-1113`) para Cloud Sync, Cable Sync manual y renombrado. El gap real era el daemon SD auto-sync (`CABLE-UX-9a`), que usaba un segundo sistema aislado (`.rommgr/cable_sync_backups/<fecha>/`) invisible en esa UI | `web/cable_sync_daemon.py` (`_run_sd_auto_sync`), `rom_manager/backup/save_backup.py` | ✅ hecho 2026-09-22 (rama `feature/saves-ux-history-context`): daemon migrado a `backup_save()`, mismo patrón que `sync_cable.py`. Verificado contra el sistema de archivos real: `.rommgr/cable_sync_backups/` no existía (el daemon nunca disparó esa rama en la práctica) — nada que migrar. 1430 tests pass (3 ambientales), ruff+format limpios |
| SAVES-CONFLICT-CTX-1 | Al resolver un conflicto de sync, mostrar contexto además del timestamp (playtime asociado, tamaño). Solo Cloud Sync (Cable Sync no detecta conflictos hoy) | `sync/conflict_resolver.py`, `sync/save_syncer.py`, `web/handlers/sync_cloud.py`, `web/static/js/tabs/sync.js` | ✅ hecho 2026-09-22 (rama `feature/saves-ux-history-context`): `SyncDecision` con tamaños, `_decision_payload()` añade mtime/tamaño/playtime best-effort (match por stem contra `games`) solo para conflictos, UI pinta la línea de contexto bajo cada fila. 4 tests nuevos, 1434 pass, ruff+format limpios |
| SYNC-CONFLICT-MANUAL-1 | Revisión manual de conflictos de Cloud Sync desde la UI antes de sincronizar — por archivo, elegir PC/Consola/omitir en vez de que `conflict_policy` global decida siempre por todos. No aplica a Cable Sync (sin detección de conflictos hoy) | `sync/save_syncer.py`, `web/handlers/sync_cloud.py`, `web/static/js/tabs/sync.js` | ✅ hecho 2026-09-22 (rama `feature/saves-ux-history-context`): `sync_saves()` acepta `conflict_overrides` (gana sobre `conflict_policy` por archivo, `skip` no toca nada); selector por fila en el plan de dry-run, recogido al pulsar Sincronizar. 3 tests nuevos, 1437 pass, ruff+format limpios |

### EMU-SYNC-WATCH-1 — Cloud sync automático al cerrar un emulador PC (petición usuario 2026-09-19, máquina "Ruben" = PC2)
> **Estado (revisado 2026-10-20):** ✅ cerrada — mergeado en PR #321 (2026-09-19)

Petición del usuario: quiere sync entre sus 3 dispositivos (PC principal,
PC2 — esta máquina — y Anbernic). Al revisar el estado real: cable-sync
PC↔Anbernic y la app Android nativa (`ANDROID-SYNC`) ya están completos en
código; lo que faltaba en este PC2 era (a) el primer sync real contra
Dropbox (nunca se había hecho — cuenta correcta pero vacía, confirmado por
el usuario) y (b) RetroArch, recién instalado a petición del usuario
(`F:\Emuladores\Retroarch`, build standalone vía instalador gráfico oficial),
sin `[[sync.sources]]` configuradas todavía.

Hecho: **(1)** primer sync real de este PC2 ejecutado (`rommgr sync --apply`)
— 6 archivos subidos (Dolphin Wii, DuckStation, PCSX2), 0 errores, verificado
en Dropbox. **(2)** `[[sync.sources]]` de RetroArch (saves/states) + `[launchers] retroarch`
añadidas a `config.toml` de este PC2 (gitignored, no en el PR). **(3)**
`EMU-SYNC-WATCH-1`: petición explícita del usuario de que el sync se dispare
solo al cerrar RetroArch/PCSX2/DuckStation/Dolphin, no solo manual/al abrir
la app — daemon nuevo `_emulator_sync_watcher_loop` (`web/daemons.py`), opt-in
vía `config.sync.watch_processes` (vacío = desactivado), sondea `tasklist`
cada 10s (stdlib, sin dependencia nueva) y lanza el job `sync` existente al
detectar que un proceso vigilado pasó de corriendo a cerrado. Refactor previo
sin cambio de comportamiento: la lógica de `POST /api/sync` (antes un closure
anónimo en `_do_sync`) se extrajo a `run_cloud_sync_job()`
(`web/handlers/sync_cloud.py`), compartida ahora por el endpoint web y el
daemon nuevo.

**Descartado explícitamente**: el mismo patrón para la Anbernic (Android) —
requeriría un servicio en segundo plano + permiso especial `PACKAGE_USAGE_STATS`
(concesión manual en Ajustes), justo el patrón de daemon que `ANDROID-SYNC-9/10/11`
ya descartó a propósito por batería/complejidad. El sync periódico cada 15 min
que ya existe (`ANDROID-SYNC-12`) cubre el caso de uso sin ese coste | `web/daemons.py`
(`_emulator_sync_watcher_loop`, `_list_running_process_names`,
`_closed_watched_processes`), `web/handlers/sync_cloud.py` (`run_cloud_sync_job`,
extraída de `_do_sync`), `config.py` (`SyncConfig.watch_processes`) | ✅ mergeado
a `develop` (PR #321, 2026-09-19), 6 tests nuevos, 1355 tests totales. ✅
**verificado en vivo el mismo día**: partida real de Dragon Ball Budokai 3 en
PCSX2 → al cerrar el emulador, log `Emulador cerrado (pcsx2-qt.exe) —
lanzando cloud sync` 3s después → `Mcd001.ps2` subido a Dropbox con el
timestamp exacto del cierre, 0 errores. **Tarea programada de Windows**
(`RetroVault-AutoStart`, `pythonw.exe -m rom_manager serve --tray` al inicio
de sesión) creada y probada (`Start-ScheduledTask`) para que el watcher esté
vivo sin depender de arrancar `serve` a mano. **12 cores de RetroArch**
instalados según `platforms.toml` (`[cores.pc]`, primera opción documentada
por plataforma) directo del buildbot oficial de libretro, sin pasar por el
Online Updater: `fceumm`/`snes9x`/`mupen64plus_next`/`gambatte`/`mgba`/
`melonds`/`genesis_plus_gx`/`flycast`/`mame`/`fbneo`/`ppsspp` + `pcsx_rearmed`
para PSX (`duckstation` ya no existe en el buildbot — el fork activo es
`swanstation` — se usó la 2ª opción documentada). GameCube/Wii/3DS/PS2
deliberadamente fuera (usan los standalone ya configurados, no RetroArch) |

### ANDROID-APP-CLEANUP-1 — Desinstaladas las 4 apps sin uso ni RA (hecho 2026-09-27)
> **Estado (revisado 2026-10-20):** ✅ cerrada — hecho 2026-09-27

Petición directa del usuario. `pm list packages` confirmó que `com.retroarch.aarch64` ya no
estaba instalado (se quitó en alguna sesión anterior sin dejar rastro en el backlog).
Desinstaladas por ADB: `com.dsemu.drastic` (DraStic — tenía 69 MB de datos públicos en
`/storage/emulated/0/DraStic/`, incluyendo 7 saves `.dsv` con progreso real de NDS;
respaldado completo con `adb pull` a `E:\RetroVault\ROMS\_backup_android_cleanup_20260927\DraStic_publicdata\`
antes de desinstalar — la carpeta pública sobrevive a la desinstalación de todos modos, pero
mejor con backup fuera del dispositivo también), `io.recompiled.redream` y
`org.dolphinemu.mmjr` (ninguno tenía datos públicos que respaldar). Verificado con
`pm list packages` tras cada desinstalación: los 3 paquetes ya no aparecen | Dispositivo real (RG556) | ✅ hecho 2026-09-27 |
