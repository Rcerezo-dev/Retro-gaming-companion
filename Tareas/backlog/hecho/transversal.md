# Hecho — Transversal — Calidad de código, DX y referencia (sin epic)

> Secciones ✅ de `Tareas/backlog/transversal.md` (todas sus tareas cerradas). Referencia.

### JOBS-SQLITE-LOCK-1 — Dos jobs de escritura pesada en paralelo (`scrape` + `apply`/`inbox`) chocan por `database is locked` (hallazgo 2026-09-28, máquina "Ruben")

Origen: durante `JUNK-SCAN-RUBEN-1`, el scrape de `SAGE-1` (muchas
escrituras pequeñas, una por juego) y `zip-route-apply`/Inbox (escrituras
masivas: 3.301 archivos organizados) corrieron **a la vez** contra el mismo
`library_pc.db` — el scrape murió con `{"error": "database is locked"}` a
mitad de cola. No hubo pérdida de datos (lo ya escrito quedó guardado,
cobertura real subió de 27,78% a 38,36% antes de morir) y el job se
relanzó sin problema tras terminar el job pesado — pero es un fallo
silencioso: ningún otro job avisa "hay otro job pesado corriendo, esto
puede fallar", el usuario solo ve `scrape_running: false` sin explicación
si no revisa `scrape_result.error` a mano.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| JOBS-SQLITE-LOCK-1 | Ningún job de escritura (`scrape`, `apply`, `inbox`, `zip-route-apply`) comprueba si ya hay otro corriendo antes de empezar — `job_manager` sí lleva un flag `_running` por nombre de job, pero no hay coordinación **entre** jobs distintos. Dos caminos posibles, sin decidir: (a) que `_do_scrape`/otros escritores reintenten con backoff ante `sqlite3.OperationalError: database is locked` en vez de abortar (SQLite ya soporta `PRAGMA busy_timeout`, comprobar si `LibraryRepository.connect()` ya lo fija); (b) un guard simple "no lances un job de escritura pesada si `apply`/`inbox`/`scrape` ya están corriendo", igual que ya existe para el mismo job (`job_manager.cancel_event`) pero cruzado entre nombres | `web/jobs/manager.py`, `database/repository.py` (`connect()`), `web/handlers/scraper.py` (`_do_scrape`) | ✅ opción (a) implementada 2026-09-28 — confirmado que `LibraryRepository.connect()`/`_open_conn()` ya fijaba `PRAGMA busy_timeout=30000` + `sqlite3.connect(..., timeout=30)`, pero una ráfaga de escrituras de otro job (`zip-route-apply`, cientos de transacciones cortas seguidas) puede agotar igualmente esos 30s. `_commit_with_retry()` nuevo en `scraper.py`: reintenta solo `sqlite3.OperationalError` con "locked" en el mensaje (5 intentos, 2s de espera), aplicado en los 3 `commit()` de la ruta de escritura. 3 tests con conexión falsa (sin BD real). Opción (b) (guard cruzado entre jobs) descartada por ahora — el retry ya resuelve el síntoma real sin añadir coordinación nueva entre nombres de job |

---

### JUNK-SCAN-EXCLUDE-TRASH-1 — El junk-scan re-escanea su propia papelera `_descartados/` como basura activa (hallazgo 2026-09-28, máquina "Ruben", durante `JUNK-SCAN-RUBEN-1`)

`utils/trash.py::_iter_trash_files()` (línea 64-66) se protege explícitamente
contra re-procesar contenido ya descartado — en cuanto el `os.walk` entra en
una carpeta `_descartados`, corta `dirnames[:] = []` con el comentario
`# no anidar`. Esa misma protección **nunca se aplicó** al walker del
junk-scan (`web/builders/folders.py:321`, `_excluded_dirs = {"saves", "bios",
"android", "system volume information"}` — falta `_descartados`).

**Consecuencia real, verificada contra la biblioteca real**: 94 de 120
archivos del bucket "review" de `JUNK-SCAN-RUBEN-1` ya estaban dentro de
alguna `_descartados/` — re-contados como basura activa en cada scan, sin
poder resolverse nunca (`zip-route-apply` no toca contenido ya descartado,
así que el bucket parece "atascado" sin estarlo de verdad). Peor: repetir
`junk-delete`/extracciones sobre contenido ya en `_descartados` crea
`_descartados/_descartados/` anidado — **111 carpetas así confirmadas hoy**
en la biblioteca real — y esos archivos quedan **invisibles para
`purge_trash()`** (el mismo corte de `os.walk` que protege contra
re-listarlos también impide verlos un nivel más adentro), huérfanos para
siempre sin limpiarse solos. Sin pérdida de datos, pero desperdicia espacio
en disco y falsea cualquier medición de junk-scan futura.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| JUNK-SCAN-EXCLUDE-TRASH-1a | Añadir `_descartados` a `_excluded_dirs` en `_build_junk_scan()` — mismo patrón de una línea que `saves`/`bios`/`android` | `web/builders/folders.py:321` | ✅ arreglado 2026-09-28 — referencia `utils/trash.TRASH_DIR_NAME` en vez de hardcodear el string; test nuevo `test_junk_scan_skips_descartados_trees`. Suite completa 1457/1457, ruff+format limpios |
| JUNK-SCAN-EXCLUDE-TRASH-1b | Limpiar las 111 carpetas `_descartados/_descartados/` ya existentes — mover su contenido un nivel arriba (al `_descartados/` padre) antes de que `purge_trash()` pueda verlas, o extender `purge_trash()`/`_iter_trash_files()` para que si encuentra un `_descartados` anidado lo trate como parte del mismo padre en vez de ignorarlo | `utils/trash.py` o script de sesión (dato, no código) | ✅ hecho 2026-09-28 — script de sesión (no productizado): recorridas las 111 carpetas anidadas (más profundas primero, por si había más de un nivel), movido cada archivo al `_descartados/` padre con el mismo criterio de colisión que `discard_to_trash()` (sufijo numérico si el destino ya existe). **3.661 archivos recuperados, 0 colisiones, 111 carpetas anidadas eliminadas** (verificado: `find` real confirma 0 `_descartados/_descartados` restantes). Ahora sí visibles para `purge_trash()` |

---

### DOCS-AUDIT-1 — Seguimiento de la auditoría de documentación (2026-09-20)

Plan en `.claude/roadmaps/archivo/24-docs-audit-followups.md` (roadmap
archivado — ambas tareas cerradas). Surgido de una
auditoría completa de la documentación del proyecto: se corrigieron ya los
hallazgos "rompe confianza"/"desactualizado" (roadmap 23, `docs/ci-cd.md`,
`Roadmap-212-Ideas-Futuras.md`, `Validacion-STORAGE-MGR.md`) y se archivaron
`Día56`/`Día57`, `Roadmap-DEVPROFILE-1-4/5-6.md` y `docs/Feedback/29/8.md`.
Quedan 2 puntos cosméticos que requerían una decisión de convención en vez
de solo corregir un dato:

| ID | Task | Esfuerzo | Estado |
|----|------|----------|--------|
| DOCS-AUDIT-1a | Decidir convención de archivo para informes puntuales sueltos en `Tareas/` (`zip-route-identificacion.md`, `psx-cue-rotos-2026-08-30.md`) — ¿carpeta `Tareas/archivo/` nueva, o nota de cierre en cabecera igual que `Validacion-STORAGE-MGR.md`? Aplicar retroactivamente y documentar en regla 5 de `.claude/roadmaps/INDEX.md` | XS | ✅ hecho (2026-09-28) — decisión del usuario: nota de cierre en cabecera, sin carpeta nueva. Aplicada a los 2 archivos existentes (`zip-route-identificacion.md`, `psx-cue-rotos-2026-08-30.md`) y documentada en la regla 5 de `.claude/roadmaps/INDEX.md` |
| DOCS-AUDIT-1b | Actualizar 8 comentarios de código que citan la ruta vieja de `Roadmap-DEVPROFILE-1-4.md`/`-5-6.md` (movidos a `Tareas/diario/archivo/*-completado.md` el 2026-09-20) — `esde/systems_generator.py:28`, `detection/platform_detector.py:70`, `detection/platforms.toml:242`, `web/handlers/system.py:493,583`, `services/device_profile.py:137`, `services/path_tokenizer.py:8`, `services/retroarch_cfg_writer.py:5` | XS | ✅ hecho (2026-09-24) — 8/8 comentarios apuntan ahora a `Tareas/diario/archivo/Roadmap-DEVPROFILE-{1-4,5-6}-completado.md`; 1451 tests + ruff limpios |

### CHDMAN-TEST-COMPRESS-1 — `chdman.exe` local falla comprimiendo CHDs de test sintéticos diminutos (hallazgo 2026-09-06)

Investigado tras bloquear el pre-push hook de `feature/anbernic-pick-5-other-category`
tres sesiones seguidas (Día54, Día55 rondas 1 y 2) con el mismo fallo en
`tests/test_chd_converter.py::test_convert_bin_to_chd_end_to_end`,
`test_convert_directory_apply_picks_up_bare_bins` y
`test_convert_bin_to_chd_rejects_on_ra_hash_mismatch` — siempre dado por
"preexistente, sin relación con el cambio de turno" pero nunca investigado
hasta la raíz.

| ID | Task | Files | Status |
|----|------|-------|--------|
| CHDMAN-TEST-COMPRESS-1 | **Causa raíz confirmada**: los 3 tests comparten la imagen PSX sintética de `_build_psx_image()` (`tests/test_ra_hash_psx.py:53`, 23 sectores / 54.096 bytes — deliberadamente mínima para hashear un solo sector). Reproducido **fuera de Python**, invocando `tools/chdman.exe createcd` directamente sobre el `.cue`/`.bin` sintéticos: `chdman - MAME... 0.251` falla con `Error during compression: Compression error` / `Fatal error occurred: 1` en los 3 codecs por defecto (`cdlz`/`cdzl`/`cdfl`), pero **crea el CHD sin error con `-c none`** (`chdman info` confirma: Hunk Size 19.584 B, 3 hunks, Total Units 24) — es un bug/límite de esta versión de `chdman.exe` comprimiendo discos de un puñado de hunks, no algo en `_run_chdman_createcd()`/`convert_bin_to_chd()` (`converters/chd_converter.py:278-297,399-451`, que ya propaga correctamente el stderr de chdman). **No afecta a la biblioteca real** — ningún juego real tiene un `.bin` de 54 KB, así que el bug nunca se dispara fuera de estos 3 tests | `tests/test_chd_converter.py`, `tests/test_ra_hash_psx.py:53`, `tools/chdman.exe` (v0.251) | ✅ barrido binario a mano (23/24 fallan, 28+ ya funciona) confirmó el umbral real ≈28 sectores; `_build_psx_image()` ahora usa `total_sectors = 64` (margen de sobra) en vez de 23, con relleno de sectores 23..63 (solo header, sin datos — el hash RA solo lee hasta el sector 22, tamaño de EXE declarado 0, así que no afecta a ningún test de hash). Sin tocar `chd_converter.py` ni `_run_chdman_createcd()` — el bug es 100% del binario `chdman.exe` local, el fix vive solo en el fixture de test. Suite completa 1204/1204 en verde (antes 1201/1204, los 3 de siempre fallando) |

---

### HEALTH-CHECK-1 — 1.522 archivos "desaparecidos" en el último Health Check semanal (hallazgo, sin investigar)

Origen: el usuario preguntó por una notificación de escritorio que recordaba como "0 ROMs verificados, sin problemas" — viene de `web/daemons.py:113-125`, notificación nativa (no toast de la app) que manda el daemon `_health_scheduler_loop` una vez por semana (`_HEALTH_CHECK_INTERVAL_DAYS = 7`). El registro real (`.rommgr/health_schedule.json`) no tiene ningún "0" — la última corrida (2026-08-26T23:37:33Z) encontró `last_ok=11474, last_corrupted=2, last_missing=1522`. Lo del "0" que recuerda el usuario es casi seguro una ejecución mucho más antigua (p. ej. la primera, antes del escaneo inicial) cuyo popup de Windows ya desapareció — no hay nada raro en el mecanismo de scheduling en sí (funciona como está diseñado, cada 7 días).

Lo que sí es un hallazgo real y sin explicar: **1.522 archivos marcados "missing"**, ~12% de una biblioteca de ~13.000 juegos. `check_library_health` (`utils/health_checker.py:68-71`) solo comprueba la ruta guardada en `games.source_path` contra el disco (`path.exists()`) sobre el repo PC (`E:\Carpetas anbernic\`, confirmado montado y accesible ahora mismo) — no se ha verificado si esos 1.522 son missing real (archivos borrados/movidos fuera de la app) o un falso positivo (p. ej. el disco `E:\` desconectado justo durante esa corrida del 26/08, o una ruta relativa/de red que fallaba en ese momento). No investigado más a fondo esta sesión — un health check completo re-hashea toda la biblioteca (lento) y no se ha lanzado sin permiso explícito.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| HEALTH-CHECK-1a | Investigar los 1.522 "missing" del Health Check del 2026-08-26: ejecutar (con permiso del usuario, es lento) un Health Check nuevo desde la pestaña Herramientas y comparar — si el número baja mucho, confirma que fue un falso positivo transitorio (disco desconectado); si se mantiene, hay que mirar los `source_path` concretos que fallan (¿todos en una misma subcarpeta/plataforma? ¿rutas con caracteres especiales?) | `utils/health_checker.py`, `.rommgr/health_schedule.json` | ✅ investigado 2026-10-04 sin lanzar el Health Check (no hizo falta hashear): ver hallazgo bajo la tabla |
**Hallazgo 2026-10-04 (HEALTH-CHECK-1a)**: el 2026-10-02 el Health Check ya daba `missing=478` (no 1.522; `health_schedule.json`: `ok=35784`). Contrastado `games.source_path` con el disco (`os.path.exists`, solo lectura, sobre `library_pc.db`, 36.264 filas): **478 siguen sin existir, y no son pérdida de ROMs reales de la biblioteca actual**:
- **462** bajo `E:\Emuladores\…` (441 en `MAMEgfx`, + assets de RetroArch/Dolphin/DuckStation/Flycast/PCSX2; extensiones `.bin`/`.zip`/`.fx`) — carpetas de emulador indexadas como ROMs por un scan de `E:\` del 2026-03-21; esa carpeta ya no existe en esa ruta (consolidada en `E:\RetroVault\EMULADORES`, NATIVE-SAVE-SYNC-1) y `Emuladores` ya está en las exclusiones del scanner (`config.py:~629`, ZIP-ROUTE-8). Ninguna con `canonical_title`, ninguna con copia viva por sha1.
- **12** en `E:ds\` (11 `.3ds` + 1 `.cia`, creadas 2026-03-16): la carpeta ya no existe y no hay copia viva con el mismo sha1 en la biblioteca → **única parte que podría ser pérdida real**; comprobar con el usuario si se borraron a propósito (p. ej. solo viven en la Anbernic) antes de purgarlas.
- **2** en `E:\HoYoPlay\…` (`.bin` de un launcher, no ROMs) y **2** zips de Virtual Console bajo `E:\RetroVault\ROMS\…` con copia viva (movidos por el pipeline, fila vieja sin podar).

**Causa raíz**: `prune_stale_entries(source_root, seen_paths)` (`games.py:377-430`, llamado en `rom_scanner.py:196`) solo borra filas **bajo la raíz que se acaba de escanear** (`_under_root`, `:396-399`). Al cambiar la raíz de la biblioteca de `E:\` a `E:\RetroVault\ROMS`, las filas de las raíces antiguas quedan fuera de todo prune futuro y el Health Check las cuenta como "missing" para siempre. No hay ruta del código que las limpie. Por eso el número bajó de 1.522 a 478 (las movidas dentro de la raíz nueva sí se podaron) pero no llega a 0.

Efecto: el Health Check semanal avisa de problemas inexistentes (ruido que enmascararía un "missing" real).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| HEALTH-CHECK-1b | Purgar las **489 filas fuera de la raíz de biblioteca** de `library_pc.db` (478 que ya no existen + 11 ficheros ajenos que sí existen: Bootcamp y HoYoPlay; ver `ZIP-ROUTE-7`) (backup previo de la BD; las 12 de `E:ds` y el resto solo tras confirmar con el usuario) **y** evitar que reaparezcan: que `prune_stale_entries` (o el Health Check) también limpie filas cuya raíz de scan ya no se escanea | `database/repositories/games.py:377-430`, `scanner/rom_scanner.py:196`, `utils/health_checker.py` | ✅ 2026-10-04 (rama `fix/health-check-1b-prune-orphans`): `find_orphans_outside_roots`/`prune_orphans_outside_roots` en `database/repositories/games.py` + `rommgr health --prune-orphans [--apply]` (dry-run por defecto; solo borra filas de la BD, nunca archivos; ignora rutas de dispositivo y unidades no montadas; raíces activas = `library_root` + las escaneadas en los últimos 30 días). Test en `tests/test_repository.py`. **Aplicado en la BD real**, con copia previa en `.rommgr/backup_health_check_1b_20261004/library_pc.db`: **476 filas borradas** (462 `E:\Emuladores`, 12 `E:ds` — confirmado por el usuario que se borraron a propósito —, 2 `E:\HoYoPlay`); `games` 36.264 → 35.788. Quedan 2 sin archivo dentro de la raíz (zips de Virtual Console; los poda el scan normal) y **11 ficheros ajenos que sí existen** (Bootcamp, HoYoPlay) sin tocar a propósito — decisión del usuario si se des-indexan. Hallazgo aparte, previo a esta tarea: **8.276 filas de `game_metadata` con `game_id` que ya no existe en `games`** (0 tags huérfanos) — sin investigar el origen (¿borrados antiguos que no usaron el cascade?) |

---

### ANDROID-ARCADE-ZIP-1 — El ADB scan nunca indexaba arcade de verdad (hallado 2026-10-02, Anbernic conectada)

Origen: petición del usuario ("los arcade tienen nombres extraños, no los está
cogiendo bien") con la Anbernic conectada por USB. `library_android.db` tenía
551 filas `platform='Arcade'` — **las 551 eran residuo fantasma de un scan de
`H:\` de 2026-03-23** (`source_path` tipo `E:\Emuladores\MAME\bgfx\shaders\...`,
rutas de Windows). **0 filas apuntaban a una ruta real del dispositivo** — la
app nunca había escaneado `/storage/521D-04EA/ROMs/arcade` (ningún `scan_run`
con ese `source_root` en los 15 registrados).

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| ANDROID-ARCADE-ZIP-1 | **Causa raíz real, no solo "nunca escaneado"**: el ADB scan (`_do_adb_scan`) tenía `.zip` metido en la lista de extensiones a ignorar siempre (pensada para ZIPs del Inbox sin extraer) — pero en arcade/MAME/FBNeo el ZIP **es** el ROM, nunca se extrae (`converters/zip_extractor.py::_ARCADE_FOLDER_NAMES`, mismo criterio ya usado en otras partes). Primer escaneo real de `arcade/` tras conectar la Anbernic: `roms_detected=388` de `files_seen=10643` — **0 de los 1.746 `.zip` reales se indexaron**, solo los 267 `.rom`+111 `.bin`+9 `.chd`+1 `.ini` sueltos que ensuciaban la carpeta (coincide exacto con `SELECT extension, COUNT(*)` contra la BD tras el scan) | `web/handlers/scan.py:519-558` (`_do_adb_scan`, rama de skip-list) | ✅ **arreglado y verificado en vivo 2026-10-02** — `.zip` solo se ignora si NINGÚN segmento de la ruta está en `_ARCADE_FOLDER_NAMES` (reutilizada, no reinventada); dentro de una carpeta arcade se trata como ROM igual que el resto. Test nuevo (`test_adb_scan_arcade_zip_is_rom_not_skipped`, `tests/web/test_adb_scan_hashing.py`) reproduce el caso exacto. Re-escaneado contra la Anbernic real tras el fix: **`roms_detected` 388 → 10.409** — descubre de paso 2 colecciones completas nunca vistas antes, anidadas una carpeta más abajo de lo esperado: `arcade/mame/` (7.423 `.zip` reales) y `arcade/fbneo/` (852 `.zip` + 14 `.nv` + 1 `.hi`) — no son basura, el fix ya las indexa bien |

**Limpieza real ejecutada en el dispositivo (misma sesión, con confirmación explícita del usuario sobre el alcance)**: de los 378 `.rom`/`.bin` sueltos en la raíz de `arcade/`, clasificados por CRC32 contra `load_arcade_crc_index()` (mismo catálogo de `ZIP-ROUTE-2`) cruzado con los `.zip` ya presentes en la carpeta:
- **110 `.bin`** (`fs_*`/`vs_*`) = shaders bgfx de MAME, misma contaminación que `ZIP-ROUTE-8` pero copiada físicamente al dispositivo — **borrados**.
- **33 `.rom`** cuyo CRC32 coincide con un set que ya tiene su `.zip` en la misma carpeta = duplicado exacto redundante — **borrados**.
- 3 carpetas vacías (`gpu_drivers/`, `MAME 2003-Plus/`, `FinalBurn Neo/` con su `fbneo/` anidado también vacío) — **borradas**.
- Verificado antes y después por recuento exacto (`ls | grep -c`): 2.147→2.001 archivos en la raíz, 110→0 shaders, 267→234 `.rom` (−33 exacto).
- **235 `.rom` restantes (80 juegos reales identificados por CRC: Pole Position, 64th Street, Rock'n Rage, Gunforce, Tetris, EDF, Puzzle Bobble 3, DoDonPachi 2…) NO tienen `.zip` en el dispositivo — decisión explícita del usuario: no tocar hoy.** 27 de 30 comprobados al azar ya existen como `.zip` en `library_pc.db`, pero no verificado al 100% para los 80 — **candidato a `ANDROID-ARCADE-ORPHAN-CHIPS-1`** si se quiere cerrar del todo (verificar los 50 restantes + decidir si se borran del dispositivo o se re-sincroniza el `.zip` bueno desde el PC).
- Nota de herramienta: el borrado por ADB vía bucle en el host (`while read ... | adb shell rm`, uno por archivo) dio falsos positivos de éxito — la causa real fue CRLF en el fichero de lista (`Path.write_text()` en Windows sin `newline=""`) haciendo que tanto el `rm` como el `[ -e ]` de verificación comprobaran una ruta con un `\r` colgando que nunca existió. Solución real: `adb push` de la lista (LF puro) + un único `adb shell` que borra todo en un bucle del propio dispositivo — mucho más robusto que N invocaciones de `adb shell` desde el host.

---

### DC-GDROM-FIRST-SECTOR-1 — Los logros de Dreamcast no se reconocían pese a dumps correctos (hallado 2026-10-02)

Origen: petición del usuario ("añadí Sonic Adventure pero RetroArch no reconoce
que tenga logros, y creo que debería"), misma sesión que `ANDROID-ARCADE-ZIP-1`
con la Anbernic conectada.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| DC-GDROM-FIRST-SECTOR-1 | **`_hash_dreamcast_from_cd_image()`/`_hash_track1_header()` leían siempre "sector 0" literal y `_root_dir_location()` siempre "sector 16" literal** — correcto para PSX/Saturn (`first_sector≈0`), pero roto para Dreamcast: un GD-ROM real codifica las direcciones MSF embebidas y los punteros de directorio ISO9660 en la dirección **absoluta del disco** (el área de alta densidad empieza en LBA ~45000), no relativa al inicio del archivo de la pista 3 — `_CdImage._detect_geometry()` ya detectaba `first_sector≈45000` correctamente, pero el resto del código nunca lo usaba para leer el IP.BIN ni el PVD. Descargado de verdad el track 3 de "Sonic Adventure (USA)" de la Anbernic (1,1 GB) para verificar: `compute_dreamcast_ra_hash()` devolvía `None` sobre un dump perfectamente válido | `retroachievements/ra_cd_image.py:116` (`_root_dir_location`), `retroachievements/ra_hash_saturn_dreamcast.py:60,96` (`_hash_track1_header`, `_hash_dreamcast_from_cd_image`) | ✅ **arreglado y verificado contra el hash real de RetroAchievements 2026-10-02** — las 3 lecturas ahora usan `cd.first_sector` en vez de un literal (`cd.first_sector` siempre resuelve a offset de archivo 0 sin importar su valor, así que PSX/Saturn con `first_sector≈0` no cambian de comportamiento; `cd.first_sector + 16` para el PVD sigue el mismo esquema de direccionamiento que ya usan los punteros de directorio). **Verificación con datos reales, no solo tests sintéticos**: el hash calculado tras el fix para el track 3 real de "Sonic Adventure (USA)" (`cb73faf2595353269a7846a034517420`) coincide EXACTO con uno de los 3 hashes registrados en RA para ese juego (`.rommgr/ra_cache/ra_hashes_40.json`, ConsoleID 40 = Dreamcast, 100 logros). 1 test de regresión nuevo (`test_compute_dreamcast_ra_hash_gdrom_high_density_offset`, reproduce el offset de 45000 con una imagen sintética), suite PSX/Saturn/Dreamcast completa en verde (20 pass) sin regresión. **No explica necesariamente el síntoma original en RetroArch** (RetroArch/Flycast calculan el hash con su propio código en C, independiente de esta reimplementación en Python usada solo para el caché/dedup interno de esta app) — pero confirma que el dump de Sonic Adventure del usuario es válido y tiene logros reales disponibles, así que el problema real está en la configuración de RetroArch/Flycast (logros activados, sesión iniciada, versión del core), no en el archivo |

**Comprobación de config real por ADB (misma sesión)**: `cheevos_enable=true`, `cheevos_username="kroq"`, `cheevos_token` presente (sesión real iniciada), `cheevos_hardcore_mode_enable=false`, `cheevos_verbose_enable=true` en `/storage/emulated/0/Android/data/com.retroarch/files/retroarch.cfg` — la configuración de RetroArch está bien. Hallazgo más probable: **hay 4 copias de Sonic Adventure en el dispositivo** (`(World) (XBLA).cdi`, `(USA)...gdi`, `(Europe)...gdi`, `Sonic Adventure 2 (Europe)...gdi`) — la `.cdi` de XBLA es un relanzamiento digital, build distinta del juego, casi seguro sin hash registrado en RA aunque el usuario la haya lanzado pensando que era la misma copia. No se pudo verificar la carpeta `logs/` de RetroArch (vacía, puede que este firmware la redirija a logcat) ni la versión del core Flycast (en almacenamiento privado de la app, sin acceso por ADB sin root). → ver `DUP-ALT-RELEASE-1` abajo, la detección de duplicados ahora sí vincula este caso.

---

### DUP-ALT-RELEASE-1 — Detectar relanzamientos digitales (XBLA/PSN/Virtual Console...) como posible duplicado (petición del usuario, 2026-10-02)

Origen: tras `DC-GDROM-FIRST-SECTOR-1`, petición directa del usuario ("puedes modificar la lógica para que detectemos también este tipo de duplicados").

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| DUP-ALT-RELEASE-1 | `Sonic Adventure (World) (XBLA).cdi` nunca aparecía vinculado a `Sonic Adventure (USA)...gdi`/`(Europe)...gdi` en la cola de revisión de duplicados — no comparte sha1 (build distinta) ni `canonical_title` (XBLA no está en ningún DAT No-Intro/Redump, así que `canonical_title=None` para siempre, sin importar cuántas veces se re-escanee). La unión fuzzy por región (`DUP-REGION-1`) tampoco lo cubre: excluye Dreamcast a propósito por estar en `_MULTI_DISC_RISK_PLATFORMS` (riesgo de fusionar discos reales de un multi-disco) | `detection/filename_normalizer.py` (`is_alternate_release_tag`, nueva), `web/builders/duplicates.py::_review_groups_for_repo` (nueva pasada `alt_release_groups`), `web/static/js/tabs/review_copies.js` (etiqueta `alt_release`) | ✅ **hecho 2026-10-02** — nueva pasada deliberadamente separada de `DUP-REGION-1`: agrupa por `(platform, normalize_for_match(canonical_title o filename))` igual que el resto, pero **solo une un grupo si al menos un miembro lleva una etiqueta explícita de relanzamiento digital** (`(XBLA)`/`(PSN)`/`(Virtual Console)`/`(Arcade Archives)`/`(eShop)`/`(Switch Online)`/`(GOG)`/`(Steam)`, mismo patrón acotado que `is_non_canonical_variant()`) — un multi-disco real nunca lleva esa etiqueta en un disco sí y en otro no, así que no reabre el riesgo que excluye Dreamcast de la unión por región. También se añade a `variant_tier` (mismo mecanismo de `ANDROID-DUP-SORT-TIEBREAK-1`) para que el dump original se recomiende sobre el relanzamiento aunque ninguno tenga todavía logros RA puntuados. Reproducido el caso exacto end-to-end (2 tests nuevos en `tests/test_builders_duplicates.py` + 2 en `tests/test_filename_normalizer.py`), suite completa 1528/1531 (los 3 fallos son tests preexistentes no relacionados que esperan "sin ADB conectado" — fallan solo porque la Anbernic sigue físicamente conectada en esta sesión, pasan bien en CI). **Hueco relacionado — arreglado también 2026-10-02, misma sesión** (el usuario pidió seguir): nueva `get_saturn_dreamcast_disc_hash()` en `ra_disc_hash_cache.py` (análoga a `get_psx_disc_hash()`/`get_gamecube_wii_disc_hash()`, mismo patrón de caché por `(mtime, size)`, console IDs 33=Saturn/40=Dreamcast), conectada en 2 sitios: `ra_checker._DISC_HASH_CONSOLE_IDS` (ahora `{12, 16, 20, 33, 40}`, cubre también el chequeo RA normal vía `check_library()`) y `_review_groups_for_repo`'s unión por hash de disco. **Hallazgo más grande de lo esperado al implementarlo**: el desempate `ra_tier`/`score_by_idx` (el que de verdad decide qué entrada se recomienda) usaba `r["md5"]` — un hash de archivo completo genérico (`hash_calculator.py`/`AdbTransport.md5_recursive`, el mismo paso para cualquier plataforma) — para **las 5 consolas de disco (PSX incluida)**, no solo Dreamcast/Saturn; RA hashea datos de arranque, no el contenedor, así que esa comparación nunca podía coincidir para ningún disco, nunca se había notado porque la mayoría de grupos de discos no llevan ninguna entrada con logros reales para notar la diferencia. Arreglado enrutando `score_by_idx` por `get_ra_console_id()` + los mismos getters de hash de disco que ya usa la unión, para las 5 consolas. 9 tests nuevos (4 en `tests/test_ra_disc_hash_cache.py` para la función nueva, 1 end-to-end en `tests/test_builders_duplicates.py` reproduciendo Sonic Adventure USA vs XBLA con caché RA real simulada — confirma que `ra_supported`/`recommended` ahora sí distinguen la copia con logros). Suite completa 1533/1536 (mismos 3 fallos preexistentes de "sin ADB" por tener la Anbernic conectada, no relacionados) |

---

### DUP-ALT-RELEASE-2 — Un relanzamiento digital que cae en el mismo clúster que un set multi-disco real desaparece entero de la cola de revisión (hallazgo 2026-10-02, auditoría completa de `DUP-ALT-RELEASE-1` sobre `library_pc.db`/`library_android.db` reales, a petición del usuario)

Origen: auditoría pedida por el usuario sobre toda la biblioteca (no solo Dreamcast) buscando relanzamientos digitales sin emparejar. 239 ROMs con tag de relanzamiento en total (223 PC / 16 Android). La mayoría de los "sin pareja" son falsos positivos esperados (inyecciones Virtual Console de Wii/3DS de OTRA plataforma — SMS/MD/NeoGeo/Arcade/PCEngine — archivadas bajo `platform=Wii`/`platform=Nintendo 3DS`; el agrupamiento por `(platform, fuzzy_key)` es correcto en no unirlas, la pareja real si existe está en otra plataforma). Pero uno de los casos sí es un bug real.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| DUP-ALT-RELEASE-2 | `has_alt_release_dup = any(i in alt_release_linked_idxs for i in idxs) and not is_disc_set` (`web/builders/duplicates.py:1304`) usa el mismo guard `not is_disc_set` que `has_region_dup`/`has_crossfmt_dup`/`has_disc_hash_dup` — pero `_is_disc_set()` (líneas 78-111) solo necesita ≥2 números de disco distintos en TODO el clúster para activarse, y al activarse apaga las 4 razones a la vez para el clúster completo, no solo para el par de discos. Un relanzamiento digital de un juego multi-disco que cae en el mismo clúster que sus discos reales pierde su única razón posible (`alt_release`) y el grupo sale con `reasons=set()` → `if not reasons: continue` (línea 1477-1481) lo descarta entero. Caso real en `library_android.db`: `Magical Drop III (Europe) (Disc 1)...chd` + `(Disc 2)...chd` + `Magical Drop III (USA) (NG) (Virtual Console).chd` — el VC nunca aparece en `/api/duplicates` | `web/builders/duplicates.py:1304` (`has_alt_release_dup`), `:78-111` (`_is_disc_set`), `:1120-1153` (unión `alt_release_groups`), `:1477` (`if not reasons: continue`) | ✅ **arreglado y verificado 2026-10-02**, petición explícita del usuario ("añade tanto como puedas a la lógica del programa"). **Causa raíz real, más profunda de lo que parecía al documentar**: no era solo el guard final — `normalize_for_match()` quita `(Disc N)` junto con región/tag de relanzamiento, así que el `fuzzy_key` de la unión `alt_release_groups` (línea 1142) colapsa Disc 1, Disc 2 Y el relanzamiento en el mismo bucket, y la unión los fusiona a los TRES como "duplicados entre sí" antes incluso de llegar al guard final — fusión semánticamente incorrecta independientemente de cómo se calculen luego las razones. **Fix de dos partes**: (1) `_is_disc_set()` ahora excluye los miembros con `is_alternate_release_tag()` del recuento de números de disco (un relanzamiento nunca es "disco N" de nada, mismo patrón que ya excluye miembros sin tag de disco — `DUP-DISC-SET-1`); (2) la unión `alt_release_groups` ahora llama a `_is_disc_set()` sobre cada bucket antes de fusionarlo, y si el bucket ya es un set multi-disco real, **no fusiona nada por fuzzy_key** — deja que el paso de `disc_hash` (más abajo, basado en hash RA real, no en nombre) vincule el relanzamiento solo con el disco específico que de verdad coincide. Reproducido end-to-end con los 2 archivos reales descargados por ADB de la Anbernic + el hash RA real: antes del fix, `total_groups: 0`; después, `total_groups: 1` con `reasons: ['disc_hash', 'title']`, exactamente `{Disc 1, Virtual Console}` (Disc 2 correctamente fuera del grupo, sin tocar). 2 tests nuevos en `tests/test_builders_duplicates.py` (`test_alt_release_in_a_real_multi_disc_set_links_only_the_matching_disc`, con `get_psx_disc_hash` monkeypatcheado igual que el test ya existente de Dreamcast). Suite completa: 1534 pass / 10 skip / 3 fail — los 3 fallos son los mismos preexistentes "sin ADB conectado" de siempre (la Anbernic seguía físicamente conectada en esta sesión), no relacionados |

**Verificación de hash RA real (los 5 consolas de disco, pedida explícitamente por el usuario) — y giro importante al bajar los archivos reales de Android por ADB**: `Magical Drop III (USA) (NG) (Virtual Console).chd` (PC) hashea (`519b1420d26175106d0459cdb40bdb7a`) EXACTO IGUAL que el Disc 1 real de Android (`Magical Drop III (Europe)...(Disc 1)...chd`, descargado y hasheado para confirmar) — **no es un relanzamiento digital genuino, es el mismo Disc 1 con una etiqueta "(Virtual Console)" puesta mal** (probable mal etiquetado de un release de scene), corrigiendo la hipótesis inicial ("un relanzamiento con logros, contradice la asunción del código"). El Disc 2 de Android no tiene hash RA propio (normal, RA solo registra el disco de arranque). `Castlevania - Symphony of the Night (Japan)...(XBLA).chd` (Android) también hashea exacto igual (`bf7e0e90d8e8d5738c7332bc6af666da`) que `(USA).chd`, que ya existe nativamente en el propio Android. `Sonic Adventure (World) (XBLA).cdi`: `library_android.db` no tenía fila para `Sonic Adventure (USA)/(Europe)` — **no es un hueco de biblioteca, es la BD desactualizada**: el dispositivo sí tiene el `.gdi` completo (4 pistas, ~1,2 GB, verificado por `adb ls`), y `DC-GDROM-FIRST-SECTOR-1` (sesión anterior) ya había confirmado sus logros RA reales descargando la pista 3. `library_android.db` necesita un rescan ADB para que ese `.gdi` aparezca — pendiente, no abordado en esta sesión. `.rvz` (GameCube) y `.cdi` como único dump (Dreamcast) siguen sin ser formatos soportados por `compute_gamecube_ra_hash`/`compute_dreamcast_ra_hash` — no verificables sin convertir antes.

**Limpieza aplicada en Android (confirmación explícita del usuario, "sí, bórralas"), 2026-10-02**: borradas por ADB (`rm`, hard delete directo — no fue el flujo normal de soft-discard a `_descartados/` de `ra_duplicates_service.py`, fue una limpieza puntual pedida en la conversación) las 3 copias redundantes confirmadas por hash: `Sonic Adventure (World) (XBLA).cdi`, `Castlevania - Symphony of the Night (Japan)...(XBLA).chd`, `Magical Drop III (USA) (NG) (Virtual Console).chd` — las 3 verificadas por hash RA real contra la copia que se queda, no por nombre. Filas correspondientes borradas de `library_android.db` con `cascade_delete_games_by_source_path` (mismo helper que usa `ra_duplicates_service._delete_row`), confirmado 0 filas restantes para esas `source_path`. **No se tocó nada en PC**: ahí cada uno de esos 2 archivos (`Sonic Adventure XBLA`, `Magical Drop III VC`) es la ÚNICA copia existente — borrarlos habría dejado esos juegos sin nada. `Magical Drop III` en PC le falta el Disc 2 para estar completo (candidato futuro: traer el set de 2 discos real desde Android).

**Segunda ronda, mismo día**: tras el fix, se relanzó el rescan ADB real contra el servidor web ya corriendo (`POST /api/adb-scan`, igual que haría la UI) para `dreamcast/` (85 ROMs, 0 podados — confirma que el `.gdi` real de Sonic Adventure ya estaba limpio en BD) y `psx/` (1432 ROMs, 57 filas obsoletas podadas, incluidas las 3 borradas arriba). Se verificaron por hash RA real los 2 casos `(Virtual Console)` de PSX que quedaban sin comprobar: **ambos resultaron ser el mismo patrón de mal etiquetado que `Magical Drop III`**, no relanzamientos reales — `Metal Slug X (USA) (NG) (Virtual Console).chd` hashea exacto igual (`c40bd37eaa2b2cc2f037a8d0318bcc26`) que `Metal Slug X (Europe).chd`; `Street Fighter Alpha 2 (Europe) (Virtual Console) (New 3DS).chd` hashea exacto igual (`079d330187f5770b109e58840479424e`) que `(USA).chd` y que `(Europe) (Track 1).bin`. Las 3 copias `(NG) (Virtual Console)` de este lote PSX concreto resultaron ser mal etiquetado, 0 de 3 relanzamientos genuinos — borradas las 2 restantes en Android (confirmación explícita del usuario), filas limpiadas igual que las anteriores.


---

### SYNC-DELTA-REMOTE-1 — la caché delta ignora el remote: tras Dropbox→Drive, 229 saves del PC nunca suben a Drive (hallazgo 2026-10-04)

**Síntoma**: `rommgr sync --apply` dice `↑0 … Δ:229` y `gdrive:/RetroSync/saves/` no tiene `duckstation/` (ni los 205 saves de RetroArch/6 PSX/6 GC/10 Wii del PC).
**Causa raíz**: `DeltaCache` (`sync/delta_cache.py:63`, `content_changed`) guarda el hash por `relative` sin el remote. `save_syncer.py:202-209` salta el upload si el hash coincide con el de la última sync — que fue contra `dropbox:`. Al cambiar `remote =` a `gdrive:/` esos ficheros parecen "ya sincronizados" y no se suben. Instanciada en `cli.py:646,1059,1719` y `web/handlers/sync_cloud.py:427,521`.
**Arreglo propuesto** (rama propia): incluir el remote en la clave de la caché, o invalidar `delta_sync_cache.json` al cambiar de remote. Workaround inmediato: borrar `<data_dir>/delta_sync_cache.json` y volver a `sync --apply`.

| ID | Task | Estado |
|----|------|--------|
| SYNC-DELTA-REMOTE-1 | `DeltaCache.bind_remote()` (llamado desde `sync_saves`) descarta el caché si cambia el remote + `tests/test_delta_cache_remote.py` | ✅ 2026-10-04 (verificado: Drive ya tiene `duckstation/` etc.; `sync` en seco = 479 al día) |

