# Arquitectura técnica — Retro Vault

> Documentación técnica del proyecto. Ver `.claude/CLAUDE.md` para reglas de trabajo y
> patrones críticos, y [`CONTRIBUTING.md`](../../CONTRIBUTING.md) para el flujo de desarrollo.
> Última regeneración desde el código: 2026-07-23 (verificado tras la release v1.1.0).

---

## Stack técnico

- **Python 3.11+** (desarrollo en 3.12; CI testea 3.11 y 3.12)
- **SQLite** vía `sqlite3` stdlib — dos BDs en `.rommgr/`: `library_pc.db` y `library_android.db`
- **tomllib** para `config.toml` — referencia completa de claves: [`config.toml.example`](../../config.toml.example)
- **Sin dependencias externas de runtime** (solo stdlib); dev-deps: pytest, ruff, pre-commit
- Binarios externos invocados como subprocesos:
  - **rclone** — cloud sync (bundled en `tools/` o PATH)
  - **chdman** — `tools/chdman.exe` (conversión a CHD; NO en PATH)
  - **adb** — `tools/adb.exe` (Cable Sync USB)
- Lanzador Windows: `scripts\rommgr.cmd` · directo: `python -m rom_manager <cmd>` (env conda `rom_manager`)
- Distribución: PyInstaller (`RetroVault.spec`) + Inno Setup (`installer/RetroVault.iss`)

---

## Estructura de módulos

```
src/rom_manager/
  cli.py                          # Entrypoint CLI (argparse)
  config.py                       # AppConfig + dataclasses anidadas:
                                  #   SyncConfig, CredentialsConfig (secretos repr=False),
                                  #   InboxConfig, BackupConfig; load_config()/save
  wizard.py                       # Wizard CLI de primer arranque

  catalog/
    catalog_loader.py             # DATs Logiqx XML + clrmamepro (sniffer de formato)
    dat_downloader.py             # Descarga de DATs desde libretro-database (lo usa
                                  #   installer/download_dats.py; el runtime web usa
                                  #   _run_dat_download en web/handlers/scan.py)
    mame_loader.py                # DATs arcade (MAME/FBNeo) + load_arcade_crc_index()
                                  #   (crc→{sets} para votación, ZIP-ROUTE-2)
    matcher.py                    # CatalogMatcher; confianza high/medium/low por SHA1;
                                  #   crc_index() crc32→(título,dat,plataforma) para
                                  #   identificar ZIPs por el header (ZIP-ROUTE-1)

  database/
    schema.py                     # Tablas + migraciones retrocompatibles
    repository.py                 # LibraryRepository = ensamblado de mixins (SRP-1c)
    repositories/                 # Un mixin por agregado:
      base.py                     #   _RepositoryBase: connect/batch/scan-runs/summary
      games.py  metadata.py       #   GamesMixin, MetadataMixin (tags/notas/scraping)
      sync.py   assets.py         #   SyncMixin (saves+sync log), AssetsMixin
      duplicates.py               #   DuplicatesMixin (+wishlist)
      play_history.py             #   PlayHistoryMixin (rating, sesiones, playtime)
      models.py                   #   Dataclasses compartidas

  detection/
    file_classifier.py            # ROM / save / asset / BIOS / desconocido
    platform_detector.py          # Plataforma por extensión/carpeta/cabecera
    region_parser.py              # (USA), [Europe], etc.
    filename_normalizer.py        # Normalización de títulos
    cue_validator.py              # Integridad de sets .cue+.bin
    set_detector.py               # Detección de sets multi-disco
    bios_checker.py               # Identificación de BIOS conocidas

  hashing/hash_calculator.py      # SHA1 + MD5 + CRC32 en una pasada (chunks 1 MB)
  scanner/
    rom_scanner.py                # scan_library() — incremental por mtime+tamaño
    asset_scanner.py

  planner/
    operation_planner.py          # build_plan(): pending / already_correct / conflicts
    collision_resolver.py         # Conflictos de nombre canónico
  renamer/
    file_renamer.py               # rename_rom_with_saves() — atómico con rollback;
                                  #   move_disc_set_to_subfolder() para sets de disco

  converters/                     # chd_converter (cue→chd), zip_extractor, n64_converter
  patch/                          # Aplicadores de parches: ips_applier, bps_applier, ups_applier
  esde/systems_generator.py       # Genera custom_systems/es_systems.xml para ES-DE
  backup/save_backup.py           # Backups versionados de saves (pre-sync/pre-rename)
  reports/reporter.py             # Informe de biblioteca (JSON/CSV)

  utils/                          # m3u_generator, multidisc_verifier, orphan_finder,
                                  # health_checker, dir_diff, lpl_generator,
                                  # library_report_html, state_reader (savestates RA),
                                  # notifier (toasts Windows), tray_icon,
                                  # update_checker + update_installer (auto-update)

  sync/
    rclone_transport.py           # Wrapper rclone (cloud)
    adb_transport.py              # ADB pull/push (Cable Sync) — rutas via shlex.quote
    save_syncer.py                # Lógica de sync + política de conflictos
    conflict_resolver.py  sync_log.py  delta_cache.py
    device_detector.py            # is_device_connected() (extraído de AppConfig)

  scraper/                        # screenscraper (REST), platform_ids,
                                  # gamelist_writer (ES-DE), pegasus_writer
  retroachievements/              # ra_client (API + caché 1 semana), ra_checker (MD5),
                                  # ra_platform_ids (~30 plataformas)
  services/                       # Lógica de negocio pura (sin ctx HTTP):
                                  # duplicates_service, ra_duplicates_service,
                                  # recommend_service (MEJ-5, "¿A qué juego hoy?")

  web/
    server.py                     # ThreadingHTTPServer + arranque de daemons
    router.py                     # Registro y dispatch de rutas
    auth.py                       # Sesiones + PIN (lockout por IP)
    lan.py                        # Exposición LAN (allow_lan, IPs locales)
    state.py                      # Estado mutable compartido (import a nivel de módulo)
    jobs/manager.py               # JobManager — único dueño del estado de jobs
    daemons.py                    # Arranque de watchers (inbox, health, cable)
    cable_sync_daemon.py          # Daemons ADB auto-sync y SD card sync
    inbox_pipeline.py             # Pipeline Inbox: ZIP → BIOS → scan → match → organize
    zip_router.py                 # ZIP-ROUTE-4: coloca en un paso los ZIPs identificados
                                  #   por el junk-scan (arcade directo — nunca por el
                                  #   Inbox —, colecciones extraídas por mayoría de
                                  #   miembros, resto vía inbox_pipeline)
    frontend.py                   # Ensambla la SPA desde static/partials
    builders/                     # Funciones puras de respuesta (SRP-1a):
                                  # common, library, duplicates, diff, folders, misc
    handlers/                     # Un módulo por dominio; register(router, ...):
                                  # scan, games, organize, duplicates, collection,
                                  # play_history, scraper, sync, sync_cable, sync_cloud,
                                  # cloud_auth, inbox, config, patches, update, system,
                                  # esde/ (conversions, reports, maintenance, doctor, system)
    static/
      index.html  app.css         # Shell de la SPA + estilos (tokens --rv-*)
      openapi.json                # Especificación OpenAPI de la API (~4600 líneas)
      js/                         # main.js, api.js, state.js, jobs.js, flow_wizard.js,
                                  #   components/ (modal, toast), tabs/ (un JS por pestaña)
      partials/                   # Un HTML por pestaña (tab-*.html) + _nav/_banners/_modals/_foot
```

Regla de dependencias: `handlers` → `services`/`builders` → `database`/`utils`/`sync`.
Los handlers son routers finos; la lógica de negocio vive en `services/` (ARC-SVC).

---

## Estructura de biblioteca en disco

```
<library_root>/
│
├── nes/   snes/   n64/   gb/   gbc/   gba/   nds/   3ds/
├── gamecube/   wii/   wiiu/   switch/
├── psx/   ps2/   ps3/   psp/   psvita/
├── megadrive/   mastersystem/   gamegear/   sega32x/   segacd/
├── dreamcast/   saturn/
├── atari2600/   atari5200/   atari7800/   atarilynx/   atarijaguar/
├── neogeo/   pcengine/
│   └── (cada carpeta tiene media/images/ y media/videos/ + gamelist.xml)
│
├── saves/{platform}/      ← saves por plataforma (27 subcarpetas)
├── states/{platform}/     ← savestates, misma estructura
├── bios/                  ← BIOS (scph1001.bin…) — no sincronizadas
├── inbox/                 ← ZIPs nuevos sin organizar (Pilar 2)
└── screenshots/           ← capturas en-juego
```

**Regla crítica:** los saves NUNCA van en `saves/` directamente — siempre en
`saves/{platform}/`. Garantiza que saves de distintas consolas no se mezclen y
que el sync sea auditable.

La consola Android replica la misma estructura bajo su `android_root`.
RetroArch Android guarda por defecto en `/storage/emulated/0/RetroArch/saves|states/` (plano);
configurar RetroArch → Ajustes → Directorio para que use subcarpetas por core.

---

## Configuración

Un único documento de referencia: [`config.toml.example`](../../config.toml.example)
(todas las claves soportadas, comentadas, con defaults). `config.py` la parsea en
`AppConfig` con sub-dataclasses por dominio: `sync: SyncConfig`,
`credentials: CredentialsConfig` (secretos con `repr=False` para no filtrarlos en
logs), `inbox: InboxConfig`, `backup: BackupConfig`.

Tras guardar config desde la web, `_handle_save_config()` **recarga** `load_config()`
en memoria — sin eso los cambios no se aplican hasta reiniciar.

---

## Base de datos

Dos BDs independientes con el mismo schema (`database/schema.py`):
`.rommgr/library_pc.db` (PC) y `.rommgr/library_android.db` (consola).

**REPAIR-TOOL-7**: el nombre engaña — no son "una BD por unidad de disco".
`rommgr scan <path>` (CLI) siempre escribe en `library_pc.db`,
independientemente de qué unidad local sea `<path>` (`E:\`, `H:\`, cualquier
carpeta montada en este PC) — es la BD de "todo lo escaneado bajo
`library_root`", no una BD por letra de unidad. La regla real que decide qué
BD usar es `_repo_for_path()` (`web/builders/common.py:141-167`): cualquier
ruta que caiga **fuera** de `config.library_root` va a `library_android.db`,
sin que tenga que ser una ruta ADB — el `/api/scan` genérico de la web
(`web/handlers/scan.py:320-325`), `/api/migrate-split-db` y el
`resolve-duplicates` de la CLI (`cli.py`, `repository_android.
exclude_duplicate_group`) también escriben ahí si el path cae fuera de
`library_root`. `/api/adb-scan` es el caso más habitual, no el único.
Confundir ambas BDs ya llevó a comparar contra datos de `library_android.db`
con 2 meses de antigüedad sin darse cuenta (ver `Tareas/backlog.md`,
`REPAIR-TOOL-7`).

| Tabla | Propósito |
|-------|-----------|
| `games` | Un registro por ROM: `source_path`, `platform`, `canonical_title`, `sha1/md5/crc32`, `match_confidence`, `play_status`, `user_rating`, `play_count`, `last_played_at` |
| `saves` | Saves detectados y su asociación a ROM |
| `assets` | Carátulas/vídeos/metadatos de scraping |
| `scan_runs` | Historial de escaneos |
| `file_operations` | **Toda** operación sobre archivos (rename, move, delete) — auditable |
| `save_sync_log` | Log de operaciones de sync |
| `game_metadata` | Metadatos extendidos (notas, descripciones) |
| `game_tags` | Tags por juego |
| `excluded_duplicates` | Duplicados descartados por el usuario |
| `wishlist` | Juegos deseados |

Migraciones: `schema.py` aplica `ALTER TABLE` retrocompatibles al conectar
(nunca destructivas). Acceso: `repository.connect()` para lecturas,
`repository.batch()` para escrituras en bulk.

---

## Patrones arquitecturales

### Jobs en background — JobManager (ARC-JM)
Todo el estado de jobs vive en **`web/jobs/manager.py`** (`JobManager`, con locking
correcto). No hay dicts de progreso globales: los handlers y daemons usan
`_state._job_manager`. Frontend: `startPolling()` cada 2s → `GET /api/job-status` →
`_applyJobStatus(s)`; cada resultado lleva `result_ts` para no re-mostrar toasts.

### Estado compartido — web/state.py (CLEAN-1)
El estado mutable global vive en `rom_manager.web.state`, importado **a nivel de
módulo** (no late imports; no hay ciclos porque ningún handler importa `server`):

```python
import rom_manager.web.state as _state

_state._auto_sync_status = {"state": "syncing"}   # reasignación → siempre via _state.xxx
progress = _state._cable_progress                  # mutación → binding local válido
```

### Renombrado atómico
```python
from rom_manager.renamer.file_renamer import rename_rom_with_saves
outcome = rename_rom_with_saves(source, target, save_extensions)
# outcome.success / outcome.saves_renamed / outcome.error — rollback si algo falla
```
PSX siempre por sets: `move_disc_set_to_subfolder()` (`file_renamer.py`) mueve cue+bins
a la subcarpeta del juego **conservando los nombres de los `.bin`** — nunca se reescribe
el `.cue` porque nunca se renombra un `.bin` suelto.
En Windows/NTFS, renames solo-mayúsculas: conflicto solo si `target.exists()` y
NO es el mismo archivo (`Path.samefile()` en `operation_planner.py`).

### Seguridad web
- PIN opcional con hash+salt (`web/auth.py`); lockout por IP tras intentos fallidos.
- `serve()` aborta si se expone a la red sin PIN (`InsecureExposureError`), salvo
  `allow_lan = true` (red doméstica) o `--allow-insecure`.
- Rutas Android en ADB siempre con `shlex.quote()` (SEC-1).
- `GET /api/config` nunca devuelve secretos, solo flags `*_set` (SEC-2).

### Static files
`GET /static/<archivo>` sirve desde `web/static/` con protección path-traversal.
La SPA se ensambla en `frontend.py` a partir de `partials/` (un HTML por pestaña)
y `js/tabs/` (un módulo JS por pestaña).

---

## API web

La referencia completa y actualizada es **`web/static/openapi.json`** (OpenAPI, ~200
endpoints), servida por el propio servidor. Rutas representativas:

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/status` | Estado global: library_root, first_run, jobs en curso |
| GET | `/api/games` | Lista de ROMs con filtros (platform, device, match) |
| GET | `/api/job-status` | Estado de todos los jobs (polling del frontend) |
| POST | `/api/scan` · `/api/match` · `/api/apply` | Pipeline scan → match → rename |
| POST | `/api/sync` · `/api/cable-sync` | Cloud sync (rclone) · sync USB (ADB) |
| POST | `/api/download-dat` | Auto-descarga de catálogos DAT |
| POST | `/api/config` | Guardar config.toml (allowlist de campos) |

---

## Dispositivos

| Dispositivo | OS | Emulador | Conexión al PC |
|-------------|----|---------|----|
| PC (Windows 10/11) | Windows | RetroArch + ES-DE | — |
| Consola Android (RG556) | Android puro | RetroArch Android | USB (ADB), SD card o SFTP (Termux) |

Rutas RetroArch Android: saves `/storage/emulated/0/RetroArch/saves/`,
states `/storage/emulated/0/RetroArch/states/`. Rutas por emulador standalone:
`EMULATOR_SAVE_PATHS_DEFAULT` en `config.py` (overrides via `[[emulator_paths]]`).
Detalle verificado en hardware: [`docs/sync/android-save-paths-RG556.md`](../sync/android-save-paths-RG556.md).

Cores por sistema: ver [`docs/architecture/platforms-cores.md`](platforms-cores.md)
y la config `[launchers]` (plataforma → core libretro).

---

## RetroAchievements — detalles API

- Endpoint: `GET https://retroachievements.org/API/API_GetGameList.php?i={console_id}&h=1&f=1&y={api_key}`
- Hash principal: **MD5** (no SHA1)
- Caché: `.rommgr/ra_cache/ra_hashes_{console_id}.json`, TTL 1 semana
- Progreso personal por juego: caché 1 h

---

## Convenciones de código

- `from __future__ import annotations` en todos los módulos
- `@dataclass(slots=True)` para estructuras de datos internas
- Extensiones de archivo siempre en minúsculas; `source_path` como `str(path.resolve())`
- Timestamps en UTC, ISO-8601, sin microsegundos
- Tests con BD real en `tmp_path` (pytest) — no mocks, no `:memory:`
- Lint/format: ruff (ver [`CONTRIBUTING.md`](../../CONTRIBUTING.md) y `pyproject.toml`)

---

## Historial de refactoring (para entender el estado actual)

| Hito | Qué se hizo |
|------|-------------|
| S18–S21 | `server.py` troceado: response builders, daemons, inbox pipeline; CSS/JS extraídos de `frontend.py` a `static/` |
| S22–S23 | Wizard de primer arranque; import de DATs |
| SRP-1a/b/c | `response_builders.py` → `web/builders/`; `handlers/esde.py` → paquete `esde/`; `repository.py` → mixins en `database/repositories/` |
| ARC-JM 1–6 | Migración completa al `JobManager`; eliminados los dicts globales de progreso y `srv_mod` |
| ARC-CFG 1–4 | `AppConfig` dividido en `SyncConfig` / `CredentialsConfig` / `InboxConfig` / `BackupConfig`; `device_detector` extraído |
| ARC-SVC | Capa `services/` — lógica de negocio fuera de los handlers |
| SEC 1–7 | shlex.quote en ADB, secretos fuera de la API, PIN forzado en exposición de red, rate-limit de auth |
| Día33–37 | DAT auto-download (clrmamepro parser), patch appliers (IPS/BPS/UPS), auto-update, PyInstaller + Inno Setup, LAN/PIN, WiFi-SFTP |

Detalle por sesión: `Tareas/diario/` y `Tareas/diario/archivo/`.
