# ROM Manager — Día 8: Roadmap de sesión

*Fecha: 2026-03-15*

> Notas brutas del usuario convertidas en fixes numerados con diagnóstico y plan de implementación.
> Los fixes de sesiones anteriores que siguen pendientes se retoman aquí.

---

## Resumen de estado

| # | Fix | Prioridad | Estado |
|---|-----|-----------|--------|
| D8-1 | BD obsoleta: Anbernic sigue mostrando 6563 juegos | 🔴 Alta | ✅ Hecho |
| D8-2 | Renombrador no toca los archivos en disco (solo BD) | 🔴 Alta | ✅ Hecho |
| D8-3 | Resolver conflictos eliminando la versión sin logros RA | 🟡 Media | ✅ Hecho |
| D8-4 | 124 grupos de "Duplicados por versión" no aparecen en la sección de eliminar | 🟡 Media | ✅ Hecho |
| D8-5 | Tools: sub-pestañas por dispositivo con rutas auto-rellenadas | 🟡 Media | ✅ Hecho |
| D8-6 | Fix 3 heredado: Cable Sync no iguala conteos | 🟡 Media | ✅ Hecho |
| D8-7 | Fix 14 heredado: auto-generar informe tras scan/sync | 🟢 Baja | ✅ Hecho |
| D8-18 | Fix 18: Cable Sync logging + modo seguro | ✅ Hecho | ✅ Esta sesión |
| D8-P3 | Pilar 3 — Daemon de auto-sync al conectar dispositivo | 🔴 Alta | ✅ Hecho |
| D8-P2 | Pilar 2 — Inbox pipeline: drop → organizar automáticamente | 🔴 Alta | ✅ Hecho |
| D8-P1 | Pilar 1 — Wizard primera vez | 🔴 Alta | ✅ Hecho |

---

## Detalle por fix

---

### 🔴 D8-1 — BD obsoleta: el conteo de Anbernic no se actualiza

**Síntoma (literal del usuario):**
> "Las cards de juegos no se actualizan bien — Anbernic tiene 6563 juegos desde hace un montón de scans, pero yo he visto que se han borrado juegos y archivos."

**Diagnóstico:**
- `prune_stale_entries` solo se ejecuta sobre la raíz que se escanea en ese momento.
  Si el usuario escanea solo el PC, los registros de la Anbernic en BD quedan intactos aunque los archivos ya no existan.
- Overview muestra el total de `games` en BD sin filtrar por si el archivo existe en disco → número siempre crece, nunca baja salvo scan explícito de la Anbernic.
- El conteo "6563" refleja registros históricos, no el estado real del dispositivo.

**Plan:**
1. En `_build_status()` añadir indicador visual de "datos sin confirmar" para la Anbernic si el último scan de esa ruta tiene más de N días.
2. Botón "Escanear Anbernic ahora" en la card de la Anbernic en Overview → lanza scan solo sobre `ab_root`.
3. `prune_stale_entries` debe respetar `source_root`: solo poda registros cuyo `source_path` empiece por la raíz escaneada — **verificar que esto ya es así** y que no poda registros de la otra raíz.
4. Mostrar en la card de cada dispositivo: "Último scan: hace X días" + aviso amarillo si > 7 días.

**Implementado:**
- `web/server.py` — `_build_status()`: ahora acepta `project_root`, calcula `scan_days_ago` y `stale` (True si > 7 días o nunca escaneado) buscando el mejor match en `last_scans_by_root`. Devuelve `scan_days_ago` y `stale` en el JSON.
- `web/frontend.py` — HTML: header de la columna Anbernic renombrado a "Consola Android", añadidos `ov-ab-stale-badge` (badge amarillo "⚠ Datos sin confirmar") y `ov-ab-scan-btn` (botón "Escanear ahora").
- `web/frontend.py` — `loadOverview()`: muestra/oculta el badge y botón según `ab.stale`. Añade "hace X días" como subtítulo de la card de Último scan.
- `web/frontend.py` — Nueva función `quickScanAndroid()`: lanza scan sobre `abPath` igual que `quickScanPC()`.
- `scanner/rom_scanner.py` — ya filtraba correctamente por `source_root` en `prune_stale_entries` (no requirió cambios).

**Archivos afectados:** `web/server.py` (`_build_status`), `web/frontend.py` (Overview cards, JS).

---

### 🔴 D8-2 — Renombrador actualiza la BD pero no los archivos en disco

**Síntoma (literal del usuario):**
> "¿Puede ser que cuando renombras los juegos, los renombras en el archivo SQLite y no en el propio archivo de cada juego?"
> "Después de renombrar, me aparece 'renombrar 1015 archivos' al menos en la Anbernic — es decir, ¿no se ha renombrado ninguno?"

**Diagnóstico:**
- `rename_rom_with_saves()` hace el rename en disco + actualiza BD. Si funcionara solo en BD, el contador de pendientes nunca bajaría.
- Hipótesis más probable: los archivos de la Anbernic están en una ruta de red/SD que el proceso no tiene permisos de escritura → `rename_rom_with_saves()` falla silenciosamente, no actualiza BD, y la operación queda en "pendiente" para siempre.
- Hipótesis secundaria: el plan se genera con `source_root` del PC pero la BD tiene registros de la Anbernic con rutas `E:\...` que no existen en ese momento (SD desconectada) → se generan operaciones inválidas.
- El contador "1015" probablemente mezcla archivos PC y Anbernic. Si se aplicaron los del PC y falló la Anbernic, el número no baja del total correcto.

**Plan:**
1. En `_handle_apply()`, al procesar cada operación, capturar el error concreto de `rename_rom_with_saves()` y registrarlo en el log de resultado.
2. En la UI (pestaña Organizar), tras aplicar, mostrar tabla de errores con columna "razón" — distinguir "archivo no encontrado" de "sin permisos" de "ruta en dispositivo desconectado".
3. Añadir filtro en el plan por `source_root` (ya existe `source_root` param) y exponer en la UI un selector "Aplicar solo archivos del PC / solo Anbernic" para evitar intentar renombrar archivos en dispositivo ausente.
4. Verificar en `operation_planner.py` que `build_plan()` excluye archivos cuya ruta no existe en disco en este momento (o al menos los marca como "dispositivo desconectado").

**Implementado:**
- `web/server.py` — `_handle_apply()`: añadido `error_details` al resultado del job (lista completa de hasta 50 errores con nombre de archivo + razón).
- `web/server.py` — `_build_plan()`: añadido parámetro `library_root`, que clasifica cada operación pendiente con `device: "pc"` o `device: "android"` según si el path empieza por `library_root`.
- `web/server.py` — GET `/api/plan`: pasa `library_root` al llamar a `_build_plan`.
- `web/frontend.py` — Tab Organizar: añadido selector desplegable "Todos / Solo PC / Solo Consola Android" que filtra la lista de operaciones en el cliente. La columna "Dispositivo" se muestra en la tabla.
- `web/frontend.py` — `loadPlan()`: aplica el filtro de dispositivo sobre `d.pending` antes de renderizar. El botón "Renombrar N" refleja solo las operaciones del filtro activo.
- `web/frontend.py` — `doApply()`: tras completar, si hay `error_details`, muestra un panel colapsable "X archivo(s) con errores" con la lista de fallos y razón.
- `web/frontend.py` — Nuevo panel `#apply-error-details` en el HTML del tab Organizar.

**Archivos afectados:** `web/server.py` (`_handle_apply`, `_build_plan`), `web/frontend.py` (tab Organizar).

---

### 🟡 D8-3 — Resolver conflictos de nombre eliminando la versión sin logros RA

**Síntoma (literal del usuario):**
> "La manera de resolver conflictos poniéndoles nombre '1, 2' no me gusta: cuando haya conflictos de nombres, quiero que elimines el duplicado que NO tenga logros."

**Diagnóstico:**
- El resolver actual (`keep_both`) añade sufijos `(1)`, `(2)` a los archivos en conflicto → el usuario acaba con 2 archivos donde quería 1.
- La BD tiene datos de RetroAchievements (campo `ra_supported` o `ra_achievements`) para muchos juegos.
- Si hay 2 ROMs con mismo hash de destino y una tiene soporte RA y la otra no, es preferible quedarse con la que tiene RA y eliminar (o mover a `_descartados/`) la otra.

**Plan:**
1. En `operation_planner.py`, añadir nuevo resolver de conflicto: `keep_ra_winner`.
2. En la UI (pestaña Organizar), botón "Resolver conflictos (modo RA)" que usa este nuevo resolver.
3. Registrar en BD las operaciones de descarte.

**Implementado:**
- `web/server.py` — Nuevo endpoint POST `/api/apply-ra-conflicts`: itera sobre todos los conflictos del plan, busca MD5 en el caché local de RA, decide ganador (más logros gana), mueve el perdedor a `_descartados/` junto a su ubicación y lo elimina de la BD. Devuelve `{resolved, skipped_no_ra, errors}`.
- `web/server.py` — Nuevo método `_handle_apply_ra_conflicts()` en la clase Handler.
- `web/frontend.py` — Nuevo botón "Resolver con RA (N)" junto al botón "Resolver conflictos" en la barra de formato del tab Organizar. Solo visible cuando hay conflictos de tipo `disk`.
- `web/frontend.py` — Nueva función `doResolveRaConflicts()` que llama al endpoint y refresca el plan.

**Archivos afectados:** `web/server.py`, `web/frontend.py`.

---

### 🟡 D8-4 — 124 grupos de "Duplicados por versión" no aparecen en la sección de eliminar

**Síntoma (literal del usuario):**
> "En la sección duplicados por versión, abajo, me distingue 124 grupos, pero estos no se listan en la sección de arriba, donde podría eliminar todos los grupos manteniendo solo el que no tenga logros."

**Diagnóstico:**
- Los 124 grupos "por versión" no tenían botón de eliminación porque el criterio de "cuál es mejor" no estaba resuelto.
- Ahora con la lógica RA de D8-3, se puede aplicar aquí.

**Plan:**
1. Renderizar los grupos "por versión" igual que los grupos por SHA1: tabla expandible por grupo.
2. Para cada grupo, mostrar botón "Eliminar sin logros" por grupo.
3. Botón "Eliminar todos sin logros (lote)" para procesar los 124 de una vez.

**Implementado:**
- `web/server.py` — Nuevo endpoint POST `/api/ra-duplicates/discard`: mueve un archivo concreto (por `path`) a `_descartados/` y lo elimina de BD. Método `_handle_ra_duplicate_discard()`.
- `web/server.py` — Nuevo endpoint POST `/api/ra-duplicates/discard-all`: procesa todos los grupos devueltos por `_build_ra_duplicates()` y descarta los que no tienen soporte RA. Método `_handle_ra_duplicate_discard_all()`.
- `web/frontend.py` — Botón "Eliminar todos sin logros" (`#btn-ra-dups-discard-all`) en la cabecera de la sección RA Duplicates. Aparece solo cuando hay grupos cargados.
- `web/frontend.py` — `deleteRaDuplicate()`: migrado de `/api/duplicates/delete` a `/api/ra-duplicates/discard` (usa path en lugar de game_id).
- `web/frontend.py` — Nueva función `discardAllRaDuplicates()`.
- `web/frontend.py` — `loadRaDuplicates()`: muestra/oculta el botón batch según si hay grupos.

**Archivos afectados:** `web/server.py`, `web/frontend.py`.

---

### 🟡 D8-5 — Tools: sub-pestañas por dispositivo con rutas auto-rellenadas

**Síntoma (literal del usuario):**
> "La pestaña Tools debería tener como una subpestaña para cada dispositivo (al menos entre Anbernic y PC). Si aplicara todo, debería usar la carpeta raíz de Anbernic en la pestaña Anbernic, y la carpeta raíz de PC en la pestaña PC. Además, las rutas que debería coger serían también las de uno u otro sitio sin tener que metérselas yo manualmente."

**Plan:**
1. Añadir selector de contexto en la cabecera de Tools.
2. Al seleccionar, todas las rutas de Tools se pre-rellenan con `library_root` (PC) o `anbernic_path` (Android).
3. Persistir en `localStorage`.

**Implementado:**
- `web/frontend.py` — HTML Tools: añadido selector de contexto "PC / Consola Android" usando los botones `.dev-btn` al inicio del tab Tools. Muestra el path activo.
- `web/frontend.py` — Nueva función `setToolsContext(ctx)`: actualiza estilos de botones, guarda en `localStorage`, rellena todos los inputs de paths en Tools (zip-path, chd-path, orphan-path, folder-analysis-path, junk-path, health-path).
- `web/frontend.py` — Nueva función `_initToolsContext()`: restaura el contexto desde `localStorage` al abrir el tab Tools.
- `web/frontend.py` — `showTab('tools')`: llama a `_initToolsContext()`.

**Archivos afectados:** `web/frontend.py`.

---

### 🟡 D8-6 — Fix 3 heredado: Cable Sync no iguala los conteos

**Síntoma original:** Después de Cable Sync en modo "Igualar ambos", el número de juegos en PC y Anbernic es diferente.

**Plan:**
1. Al terminar Cable Sync con `direction=newest`, ofrecer "¿Escanear ambas raíces ahora?".
2. Añadir conteos reales de archivos en disco.
3. Resaltar si los conteos difieren.

**Implementado:**
- `web/server.py` — Cable sync job: tras completar el sync en modo filesystem (no ADB), cuenta archivos reales en PC y Anbernic usando `_iter_files` + `_wanted`. Añade `pc_file_count` y `ab_file_count` al resultado.
- `web/frontend.py` — `_renderCableSyncResult()`: muestra "PC: X archivos | Consola: Y archivos" si están disponibles. Si difieren > 5% muestra aviso amarillo. Cuando `direction=newest` y `copied > 0`, muestra botones "Escanear PC" y "Escanear consola" para actualizar la BD.

**Archivos afectados:** `web/server.py` (cable sync job), `web/frontend.py`.

---

### 🟢 D8-7 — Fix 14 heredado: auto-generar informe tras scan/sync

**Síntoma:** El informe de biblioteca debe estar siempre disponible sin que el usuario lo pida manualmente.

**Plan (simplificado):**
1. Al finalizar cualquier scan completo, guardar el resultado de `_build_library_report()` en `.rommgr/last_report.json`.
2. En Overview, mostrar "Informe disponible — generado hace X minutos" con link a `/api/report/html`.
3. El botón "Generar informe" en Tools sigue existiendo para forzar regeneración.

**Implementado:**
- `web/server.py` — Scan job `run()`: tras completar el scan (y si no fue cancelado), llama a `_build_library_report()` y guarda el resultado en `.rommgr/last_report.json`. El fallo en este paso es silencioso (no aborta el scan).
- `web/server.py` — `_build_status()`: ahora acepta `project_root`. Si existe `.rommgr/last_report.json`, calcula `last_report_at` (timestamp ISO) y `last_report_mins_ago` (entero). Ambos se devuelven en el JSON de `/api/status`.
- `web/frontend.py` — HTML Overview: añadido `#ov-report-notice` div amarillo debajo del config summary.
- `web/frontend.py` — `loadOverview()`: tras cargar el status del PC, si `last_report_at` está disponible, muestra el notice con "generado hace X min" y enlace a `/api/report/html`.

**Archivos afectados:** `web/server.py` (scan job, `_build_status`), `web/frontend.py` (Overview).

---

### ✅ D8-18 — Fix 18: Cable Sync logging persistente + modo seguro

**Implementado esta sesión.**

- Log de operaciones en `.rommgr/cable_sync_ops.log` (append por sesión).
- Cada línea: timestamp, tag `[COPY]`/`[SAFE]`/`[ERROR]`/`[ADB←]`/`[ADB→]`, origen → destino.
- Nuevo parámetro `safe_mode` (por defecto `True`): nunca sobreescribe archivos existentes en destino.
- Contador `safe_mode_skipped_overwrites` en el resultado del job.
- Frontend: checkbox "Modo seguro" (marcado por defecto, en amarillo), entradas `SAFE` en amarillo en la lista de detalles, sección colapsable "Ver log de operaciones" con botón de actualizar.
- Endpoint GET `/api/cable-sync-log` → devuelve las últimas 500 líneas del log.

---

## Orden de implementación sugerido

```
1. D8-2  → Bug crítico: renombrador no funciona en Anbernic (bloquea el flujo principal)
2. D8-1  → BD obsoleta: conteo incorrecto genera desconfianza en la app
3. D8-3  → Resolver conflictos con RA (base para D8-4)
4. D8-4  → Grupos de duplicados por versión con botón de eliminar (depende de D8-3)
5. D8-5  → Tools por dispositivo (UX, independiente)
6. D8-6  → Fix 3 Cable Sync count mismatch (diagnóstico + resumen mejorado)
7. D8-7  → Auto-generar informe (mejora de confort, baja prioridad)
```

---

### ✅ D8-9 — Auditoría de rutas: separación PC / Consola Android en todas las funciones

**Síntoma (literal del usuario):**
> "Quiero que compruebes que absolutamente TODAS LAS FUNCIONES del código separen perfectamente lo que hacen, y tienen claro cuál es la ruta de Anbernic y la de PC."
> Ejemplo: en Tools > Anbernic, la función solo debería recibir `E:\Carpetas anbernic\dreamcast`. En "Verificar sets multi-disco" aparecen mezcladas `E:\Carpetas anbernic\dreamcast`, `E:\Carpetas anbernic\ps2`, `E:\Carpetas anbernic\psx`, `E:\Carpetas anbernic\wii`.

**Diagnóstico:**
- Varias funciones (multidisc verifier, health checker, orphan finder, plan builder...) operan sobre `library_root` sin distinguir si una subcarpeta pertenece al PC o a la Anbernic.
- El escáner almacena `source_path` de todos los archivos en la misma BD sin marcar el dispositivo de origen.
- Cuando el usuario selecciona "Anbernic" en Tools, las funciones que usan la BD pueden devolver resultados de ambos dispositivos mezclados.

**Plan:**
1. Auditar todas las funciones de `server.py` que aceptan `source_root` / `path` como parámetro y verificar que filtran los resultados estrictamente a esa raíz.
2. En funciones que operan sobre BD (plan, multidisc, orphans, health, duplicates), añadir filtro `WHERE source_path LIKE ?` con el prefijo de raíz seleccionado.
3. En funciones que operan sobre disco (zip, chd, health checker), verificar que el `root` pasado es exactamente el que el usuario indicó — sin expandir a `library_root` si no se pidió.
4. Añadir campo `device` (`"pc"` / `"android"`) en BD a nivel de `scan_runs` y propagar a `games` para filtrado más robusto.
5. Documentar en cada endpoint qué raíz acepta y qué garantía da sobre la separación.

**Estado:** ✅ Implementado (arquitectura dos-BD)

**Implementado:**

- `config.py` — Añadido campo `database_path_android: Path` → `.rommgr/library_android.db`. El campo `database_path` ahora apunta a `library_pc.db` (renombrado de `library.sqlite`).
- `web/server.py` — Nueva función `_repo_for_path(path_str, repo_pc, repo_android, config)`: normaliza separadores de ruta (Windows `/` vs `\`) y devuelve el repositorio correcto según si la ruta está bajo `library_root` (PC) o no (Android).
- `web/server.py` — `make_handler()` acepta `repository_android` opcional. Crea `_repo_android` y helper interno `_get_repo(path_str)`.
- `web/server.py` — `_build_status()`: acepta `repository_android`, añade `android_total_games`, `android_total_saves`, `android_last_scan_at`, `pc_db`, `android_db` al JSON de respuesta.
- `web/server.py` — `/api/games`: usa `_get_repo(root)` para enrutar al repo correcto según la raíz solicitada.
- `web/server.py` — `/api/plan`: usa `_get_repo(source_root)` para construir el plan en la BD correcta.
- `web/server.py` — `/api/duplicates`: delegado a nueva función `_build_duplicates_two_repos()` que detecta duplicados dentro de cada BD por separado y duplicados cruzados (mismo SHA1 en ambas BDs).
- `web/server.py` — `/api/assets`: usa `_get_repo(src_root)`.
- `web/server.py` — Scan job: cada ruta escaneada determina su repo con `_get_repo(str(source))`.
- `web/server.py` — ADB scan (`_handle_adb_scan`): siempre usa `_repo_android`.
- `web/server.py` — `_handle_apply`: usa `_get_repo(source_root)` para el plan y `_get_repo(str(op.source_path))` para cada rename en BD.
- `web/server.py` — Nuevo endpoint `POST /api/migrate-split-db`: migra registros con rutas no-PC de `library_pc.db` a `library_android.db` (idempotente).
- `web/server.py` — `_build_config()`: añade `pc_db_path`, `pc_db_size`, `android_db_path`, `android_db_size`.
- `web/server.py` — `serve()`: acepta `repository_android` y lo pasa a `make_handler()`.
- `cli.py` — Crea `repository_android = LibraryRepository(config.database_path_android)` y lo pasa a `serve()`.
- `web/frontend.py` — Overview: etiquetas `library_pc.db` / `library_android.db` bajo cada columna.
- `web/frontend.py` — Settings > BD: muestra tamaño de cada BD. Botón "Migrar BD a dos DBs" llama a `/api/migrate-split-db`. Nueva función `migrateSplitDb()`.

**Funciones auditadas y verificadas:**
- `_handle_scan`, `_handle_adb_scan`: enrutadas al repo correcto.
- `_handle_apply`: enrutado por `source_root` y por cada `op.source_path`.
- `_handle_match`: usa repo PC global (correcto — solo matchea juegos ya escaneados; no filtra por ruta).
- `_handle_health_check`: opera sobre todos los juegos de la BD; el checker ya filtra por ruta de disco proporcionada por el usuario.
- `_handle_ra_check`: opera sobre todos los ROMs; los resultados se filtran por plataforma.
- `_handle_cable_sync`: SHA1 check usa repo PC (destino correcto).
- Funciones de disco (CHD, ZIP, M3U, orphan finder): ya reciben ruta explícita del usuario, no usan BD para el filtrado de archivos.

---

### ✅ D8-P1 — Pilar 1: Wizard de primera vez

**Implementado:**

**`src/rom_manager/web/server.py`:**
- `_jobs["setup"] = False` — nuevo job key.
- `_setup_progress: dict` — progreso de los 5 pasos del pipeline.
- `_build_status()`: añadidos campos `first_run` (True cuando library_root existe y no hay scan_runs), `setup_complete` (True cuando hay scans y matches), y `setup_checklist` (dict con 4 checks: library_root_set, scanned, catalogs_loaded, matched).
- `_run_setup_pipeline(library_root, options, repository, config)`: función de módulo que ejecuta los 5 pasos en background: limpieza junk, extracción ZIPs, scan, match catálogos, build plan. No aplica renames — solo prepara el plan.
- `Handler._handle_setup_run(data)` — lanza pipeline como job background.
- `GET /api/setup-status` — devuelve setup_running, setup_progress, setup_result.
- `POST /api/setup-run` — acepta library_root, clean_junk, extract_zips, scan, match.
- `/api/job-status` — añadidos setup_running, setup_progress, setup_result.

**`src/rom_manager/web/frontend.py`:**
- Modal `#wizard-modal` con 3 páginas: bienvenida/config, progreso en tiempo real, resultado con estadísticas.
- Banner `#ov-setup-banner` en Overview con checklist de 4 items, visible cuando first_run o !setup_complete.
- Auto-show del wizard en `loadOverview()` si first_run y sin localStorage 'wizard_dismissed'.
- Funciones JS: showWizard, closeWizard, startSetup, _renderWizSteps, _pollSetupProgress, _showSetupResult, wizardGoToOrganize.
- startPolling() incluye !s.setup_running en la condición de parada.
- Auto-scan tras ZIP extraction: lanza quickScanPC() automáticamente con deduplicación por result_ts.

**Archivos afectados:**
- `src/rom_manager/web/server.py` (`_build_status`, job setup, endpoints)
- `src/rom_manager/web/frontend.py` (modal, banner, JS functions, polling)

---

### 🔴 D8-P3 — Daemon de auto-sync al conectar dispositivo

**Objetivo:**
El sync de saves se dispara automáticamente cuando el usuario conecta la consola Android por USB,
sin que tenga que abrir la interfaz web ni pulsar ningún botón.

**Implementación:**

**`src/rom_manager/config.py`:**
- Añadidos 5 campos nuevos a `AppConfig` (con `@dataclass(slots=True)` requería `field()`):
  - `auto_sync_enabled: bool` (default `True`)
  - `auto_sync_direction: str` (default `"newest"`)
  - `auto_sync_android_path: str` (default `"/storage/emulated/0/RetroArch"`)
  - `auto_sync_known_devices: list` (default `[]` — cualquier dispositivo)
  - `conflict_policy: str` (default `"newest"`)
- `load_config()` lee estos campos de la sección `[sync]` de `config.toml` con fallback a defaults.
- `write_config_toml()` ahora maneja valores `list` (los serializa como array TOML).

**`src/rom_manager/web/server.py`:**
- Estado global: `_auto_sync_enabled`, `_auto_sync_last_devices`, `_auto_sync_status`.
- `_auto_sync_loop(config, get_repo_fn)`: thread daemon que:
  - Pollea ADB cada 10 s usando `list_devices()` del módulo `adb_transport`.
  - Detecta seriales nuevos (comparando con el set anterior).
  - Si hay dispositivo nuevo Y auto-sync activado Y no hay cable_sync en curso Y `library_root` configurado:
    lanza `_run_auto_sync()` en un thread separado (para no bloquear el daemon).
  - Cooldown de 30 s entre syncs para evitar re-disparos.
  - Filtra por `auto_sync_known_devices` si está configurado.
  - `_run_auto_sync()` replica la lógica de `_handle_cable_sync` en modo ADB para saves únicamente:
    soporta `newest`, `pc_to_anbernic` y `anbernic_to_pc`. Escribe en el mismo log persistente.
  - Todo envuelto en `try/except` — nunca crashea el daemon.
- `serve()`: lee `config.auto_sync_enabled` e inicia el daemon thread si está activado.
- `GET /api/auto-sync-status`: devuelve `{enabled, status, config}`.
- `POST /api/auto-sync-toggle`: activa/desactiva el daemon en caliente.
- `POST /api/auto-sync-save`: guarda dirección, ruta Android y política de conflictos en `config.toml`.
- `_handle_save_config()`: recarga también los nuevos campos de auto-sync.
- `_handle_auto_sync_save()`: método dedicado para los ajustes del daemon.

**`src/rom_manager/web/frontend.py`:**
- **Banner global** (sobre el header): muestra estado sincrionizando / último sync / desactivado.
  - Verde pulsante cuando sincroniza, verde tenue con timestamp del último sync, amarillo si desactivado.
  - Oculto cuando está en espera sin historial.
- **Card de auto-sync** en el tab Cable Sync (antes de las instrucciones):
  - Toggle ON/OFF con animación CSS.
  - Dropdowns para dirección (más reciente / PC→consola / consola→PC) y política de conflictos.
  - Input para ruta Android.
  - Botón "Guardar ajustes" → `POST /api/auto-sync-save`.
  - Texto de estado en tiempo real.
- **Sección "Inicio automático"** en Settings: instrucciones para añadir al startup de Windows.
- `startAutoSyncPolling()`: timer de 5 s separado del polling principal (2 s).
- `toggleAutoSync()`: llama a `POST /api/auto-sync-toggle`, actualiza UI con toast.
- `saveAutoSyncSettings()`: recoge los 3 campos y llama a `POST /api/auto-sync-save`.
- Los dropdowns se pre-rellenan desde `data.config` en la primera respuesta de `/api/auto-sync-status`.

**Archivos afectados:**
- `src/rom_manager/config.py`
- `src/rom_manager/web/server.py`
- `src/rom_manager/web/frontend.py`

---

### D8-P2 — Pilar 2: Inbox pipeline

**Objetivo:**
El usuario suelta ROMs o ZIPs en una carpeta "Inbox". La herramienta los detecta, extrae,
escanea, cruza con catálogos No-Intro/Redump, renombra a nombre canónico y los mueve a la
subcarpeta de plataforma correcta dentro de `library_root`. Sin intervención manual.

**Implementado:**

**`src/rom_manager/config.py`:**
- Añadidos 4 campos a `AppConfig`:
  - `inbox_path: str` — carpeta inbox a vigilar
  - `inbox_target_root: str` — destino (vacío = usa `library_root`)
  - `inbox_auto_process: bool` — procesar automáticamente cuando el daemon detecte archivos
  - `inbox_delete_source: bool` — borrar ZIP original tras organizar
- `load_config()` lee sección `[inbox]` de `config.toml` con defaults vacíos/False.

**`src/rom_manager/web/server.py`:**
- `_jobs["inbox"] = False` — nuevo job key.
- `_inbox_progress: dict` — progreso de los 6 pasos del pipeline.
- `_inbox_watcher_status: dict` — estado del daemon de vigilancia.
- `_build_inbox_scan(inbox_path)` — función de módulo que analiza la carpeta inbox:
  - Itera archivos superficiales (no subcarpetas con `_`).
  - Para ZIPs: abre y mira extensión del primer contenido para adivinar plataforma.
  - Devuelve `{files, total, total_bytes, by_platform, zips, unrecognized, inbox_path}`.
- `_run_inbox_pipeline(...)` — función de módulo que ejecuta los 6 pasos:
  1. Extrae ZIPs (usa `extract_zip()` existente).
  2. Escanea inbox con `scan_library()`.
  3. Coteja catálogos con `CatalogMatcher`.
  4. Planifica renames con `build_plan()` filtrando a `inbox_path`.
  5. Aplica renames con `rename_rom_with_saves()` y actualiza BD.
  6. Mueve a `target_root/{platform_folder}/{filename}` y actualiza `source_path` en BD.
  - Cleanup: borra ZIPs originales si `delete_source=True`.
  - Informa progreso en `_inbox_progress` en cada paso.
- `_platform_folder_name(platform)` — mapea IDs de plataforma a nombres de carpeta legibles.
- `_PLATFORM_FOLDERS` — diccionario de 28 plataformas.
- `Handler._handle_inbox_run(data)` — método de la clase Handler, lanza el pipeline como job.
- `GET /api/inbox-scan?path=...` — analiza carpeta y devuelve resumen.
- `POST /api/inbox-run` — lanza pipeline como job background.
- `GET /api/inbox-status` — estado actual del job inbox.
- `GET /api/inbox-watcher-status` — estado del daemon.
- `/api/job-status` — añadidos `inbox_running`, `inbox_progress`, `inbox_result`.
- `_build_config()` — añadidos `inbox_path`, `inbox_target_root`, `inbox_auto_process`, `inbox_delete_source`.
- `_handle_save_config()` — acepta y guarda claves `inbox.*`; recarga campos en memoria.
- `serve()` — lanza daemon `_inbox_watcher_with_repo` que cada 30 s comprueba si hay archivos
  nuevos en inbox y lanza el pipeline automáticamente si `inbox_auto_process=True`.
- `_watcher_now()` — helper UTC timestamp.

**`src/rom_manager/web/frontend.py`:**
- Nav: nuevo botón `<button id="nav-inbox">Inbox</button>`.
- `showTab()`: rama `if (name === 'inbox') loadInbox()`.
- `startPolling()`: condición de parada incluye `!s.inbox_running`.
- `_applyJobStatus()`: llama a `_applyInboxProgress(s)`.
- HTML tab `#tab-inbox`:
  - Inputs para carpeta inbox y destino; botón "Usar library".
  - Checkboxes "Eliminar ZIPs originales" y "Procesar automáticamente".
  - Botones "Analizar carpeta" y "Organizar todo".
  - Panel de resumen con conteos por plataforma.
  - Tabla de archivos (nombre, tipo, plataforma, tamaño, estado).
  - Barra de progreso de 6 pasos con etiqueta de archivo actual.
  - Panel de resultado colapsable con errores.
  - Info del daemon watcher.
- Funciones JS:
  - `loadInbox()` — carga config, pre-rellena campos.
  - `scanInbox()` — llama `GET /api/inbox-scan`, renderiza tabla.
  - `runInbox()` — llama `POST /api/inbox-run`, arranca polling.
  - `_applyInboxProgress(s)` — actualiza barra de progreso y etiqueta.
  - `_renderInboxResult(r)` — renderiza resultado final con estadísticas.
  - `saveInboxSettings()` — guarda ajustes en config.toml.
  - `fillInboxTarget()` — rellena destino con `library_root`.
  - `_pollInboxWatcher()` — muestra estado del daemon.

**Archivos afectados:**
- `src/rom_manager/config.py`
- `src/rom_manager/web/server.py`
- `src/rom_manager/web/frontend.py`