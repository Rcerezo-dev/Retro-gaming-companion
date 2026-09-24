# DEVPROFILE-1..4 — Catálogo de plataformas único + perfil de dispositivo (PC)

> Diseñado 2026-08-31. Ver `Tareas/backlog.md` sección `DEVPROFILE` para el
> estado de cada tarea — este documento es el detalle de diseño, no se edita
> tarea a tarea. DEVPROFILE-5/6 (botones de restauración PC/Android) dependen
> de este bloque pero no forman parte de él.

## Contexto

`DEVPROFILE-0` (resuelto 2026-08-25, hardware real) fijó el límite duro: el
`retroarch.cfg` de la Anbernic **no es accesible sin root**. Consecuencia
para todo este bloque: cualquier cosa que dependa de escribir ese archivo
(DEVPROFILE-2) es **solo-PC**; lo que sí se puede mover entre dispositivos
(DEVPROFILE-3/4) son los ficheros de `config/<core>/`, remaps, autoconfig,
shaders y BIOS — accesibles en ambos lados sin root.

1..4 son la base de datos + mecanismo de sync; DEVPROFILE-5 (botón PC
`rommgr restore`) y DEVPROFILE-6 (botón Android "Restaurar este dispositivo")
son la UI que consume esa base una vez exista.

---

## 1. Estado real del código (verificado, no asumido)

Antes de diseñar el JSON de DEVPROFILE-1 hace falta saber qué existe ya,
porque hay más superficie duplicada de la que sugiere el ticket:

**Ya es la fuente real de nombres de plataforma** — no es prosa, es TOML y
código lo importa en producción:
```
src/rom_manager/detection/platforms.toml        # [extensions], [folders], [ambiguous]
src/rom_manager/detection/platform_detector.py  # _build_tables() lo carga, admite override en .rommgr/
```
Claves: nombres humanos (`"NES"`, `"SNES"`, `"Nintendo 64"`, `"GameCube"`).
Soporta ya un override de usuario sin perder las actualizaciones del
programa (mismo patrón que necesitará el catálogo de cores).

**Duplicado / desincronizable hoy:**
| Fuente | Qué contiene | Formato de clave | Problema |
|--------|-------------|-------------------|----------|
| `docs/architecture/platforms-cores.md` | Cores PC + Android recomendados, notas de calidad | prosa libre | Solo humano-mantenido, ya vimos que puede desincronizarse |
| `src/rom_manager/esde/systems_generator.py::_SYSTEMS` | Cores PC candidatos (DLL) para generar `es_systems.xml` | slugs ES-DE en minúsculas (`"gamecube"`, `"nes"`) — **no coincide** con `platforms.toml` |  |
| `src/rom_manager/detection/bios_checker.py::KNOWN_BIOS` | BIOS requerido por plataforma | nombre humano (`"PlayStation"`) — **sí coincide** con `platforms.toml` | Es el más fácil de reconciliar |
| `src/rom_manager/utils/lpl_generator.py` | Playlists `.lpl` | usa `_DEFAULT_CORE = "DETECT"` genérico, **no tiene asignación de core por plataforma** | El ticket original menciona "asignación de core por defecto" aquí — **verificar en DEVPROFILE-1a si ese comportamiento sigue siendo el deseado antes de tocarlo**; puede que no haya nada que migrar |

**Mecanismo de sync multi-carpeta que YA EXISTE** (relevante para DEVPROFILE-4,
ver §4):
```python
# config.py:194-201 — SyncConfig
sync_sources: list[SyncSource]   # [[sync.sources]] en config.toml
ra_config_dir / ra_config_remote # ya sincroniza config/<core>/*.opt (CFG-PORGAME)
cheats_dir / cheats_remote       # mismo patrón para .cht (MEJ-4)
```
`SyncSource.sync_all=True` sincroniza una carpeta entera sin filtrar por
extensión (ya se usa así para PPSSPP/Dolphin). `sync_cloud.py` y
`cable_sync_daemon.py` son los consumidores reales.

**Ya hay un lector/escritor de `retroarch.cfg` en producción** (relevante
para DEVPROFILE-2):
```python
# web/handlers/config.py:139 _detect_retroarch_install()
# ya localiza retroarch.cfg y lee content_directory de él
```
Y `retroarch_overrides_service.py` (CFG-PORGAME) ya trata los `.opt`
(mismo formato `clave = "valor"`) como texto opaco línea a línea — ese es
el patrón a reusar para escribir claves en `retroarch.cfg`, no un parser
nuevo.

---

## 2. DEVPROFILE-1 — Catálogo único de plataformas

**Decisión propuesta**: extender `platforms.toml` (ya es la fuente real
usada en producción) en vez de crear un árbol de datos paralelo. Añadir
secciones nuevas keyed por el mismo nombre humano que `[extensions]`:

```toml
[cores.pc]
"GameCube" = ["dolphin"]              # standalone, sin DLL — ver nota abajo
"NES"      = ["fceumm", "nestopia", "mesen"]

[cores.android]
"NES" = "FCEUmm"
"PlayStation" = "PCSX ReARMed"

[bios."PlayStation"]
required = ["scph5500.bin", "scph5501.bin", "scph5502.bin"]
optional = ["scph1001.bin"]
```

Pasos:
- **1a** — ✅ Resuelto (2026-08-31): `lpl_generator.py` usa
  `_DEFAULT_CORE = "DETECT"` a propósito — es el mecanismo documentado de
  RetroArch para que la playlist detecte el core al lanzar, no un hueco de
  asignación por plataforma. Asignarle un core fijo aquí sería una
  regresión (pisaría la detección de RetroArch y el override por-juego que
  ya gestiona `CFG-PORGAME`). **No se toca este archivo** — el ticket
  original asumía un hueco que no existe.
- **1b** — Diseñar el schema final (arriba es un borrador) y extender
  `_build_tables()` en `platform_detector.py` para exponer `cores_pc`,
  `cores_android`, `bios` igual que ya expone `PLATFORM_BY_EXTENSION`.
  Mantener el soporte de override en `.rommgr/platforms.toml` (ya existe,
  no reinventar).
- **1c** — Migrar `bios_checker.py::KNOWN_BIOS` primero (las claves ya
  coinciden en formato) — es la reconciliación más barata y sirve de
  prueba del schema antes de tocar `systems_generator.py`.
- **1d** — ✅ Resuelto (2026-08-31): **no** normalizar a nombre humano.
  `_SYSTEMS` tiene 3 entradas arcade-adjacentes (`"mame"`, `"fbneo"`,
  `"neogeo"`) donde `"mame"` y `"fbneo"` comparten canónico `"Arcade"` pero
  necesitan listas de cores **distintas** — fusionarlas por nombre de
  plataforma habría cambiado qué core gana cuando solo hay uno instalado
  (regresión de comportamiento). `[cores.pc]` en `platforms.toml` queda
  keyed por el slug ES-DE (`sys_def["name"]`, idéntico 1:1 a la clave que
  ya usaba `_SYSTEMS`) — migración sin cambio de semántica. `name`/
  `fullname`/`path`/`extension`/`theme`/`platform` (campos propios del XML
  de ES-DE) se quedan en Python, no hay duplicación de esos en ningún otro
  sitio.
- **1e** — `docs/architecture/platforms-cores.md`: no vale la pena
  generarlo automáticamente del TOML si nadie más lo lee en código —
  dejarlo como documentación humana, pero añadir una nota al principio
  ("`platforms.toml` manda; esto es solo guía visual") para que no se
  edite como si fuera la fuente de verdad.

---

## 3. DEVPROFILE-2 — Escribir claves en `retroarch.cfg` (solo PC)

Alcance ya recortado por DEVPROFILE-0: solo PC. Cuatro claves:
`savefile_directory`, `savestate_directory`,
`sort_savefiles_by_content_enable`, `sort_savestates_by_content_enable`.

- **2a/2b/2c** — ✅ Hecho (2026-08-31), `src/rom_manager/services/retroarch_cfg_writer.py`:
  `read_key()`/`_set_key()` (parser línea a línea, opaco fuera de las 4 claves
  gestionadas — mismo espíritu que `retroarch_overrides_service.py` pero a
  nivel de clave, no de archivo entero, porque `retroarch.cfg` tiene cientos
  de claves ajenas que no se pueden reemplazar en bloque) y
  `apply_savefile_layout(cfg_path, savefile_dir, savestate_dir)`: escribe
  `savefile_directory`/`savestate_directory` con los valores dados y activa
  `sort_savefiles_by_content_enable`/`sort_savestates_by_content_enable`
  (necesario para que el layout `saves/<core>/<rom>.srm` que asume
  `RemoteRouter` sea cierto por construcción). Backup `.bak` antes de escribir,
  no-op si ya está todo correcto, solo toca las claves que realmente cambian.
  `_handle_retroarch_check()` (`web/handlers/system.py`) refactorizado para
  reusar `read_key()` en vez de su propia regex duplicada. 9 tests nuevos
  (`tests/test_retroarch_cfg_writer.py`), suite completa en verde.

  Nota: la localización real del `.cfg` no usa `_detect_retroarch_install()`
  (escanea rutas candidatas) sino `config.retroarch_path` — ya configurado
  por el usuario en Settings y ya usado por `_handle_retroarch_check()` para
  lo mismo, más autoritativo que adivinar por candidatos.

- **2d** — ✅ Resuelto (2026-09-01): botón manual, no automático (confirmado
  con el usuario). `default_savefile_layout(library_root)` fija los valores
  por defecto (`library_root/saves`, `library_root/states` — mismo convenio
  que ya usa el sync a la nube D2 para `sync.saves_remote`/`states_remote`,
  ver `server.py::_implicit_tray`), sin pedirlos por UI. Botón "Aplicar
  layout de saves" en el panel RetroArch de Settings
  (`POST /api/retroarch-apply-savefile-layout`,
  `_handle_apply_retroarch_savefile_layout` en `web/handlers/system.py`,
  `applyRetroArchSavefileLayout()` en `js/tabs/esde.js`) reusa la misma
  resolución de `retroarch.cfg` que `_handle_retroarch_check` (junto al exe
  configurado). Refresca el diagnóstico tras aplicar.

---

## 4. DEVPROFILE-3 — Tokenizador de rutas `{ROMS}` / `{SAVES}` / `{SYSTEM}`

✅ Resuelto (2026-09-01). `src/rom_manager/services/path_tokenizer.py` —
`tokenize()`/`resolve()`, funciones puras sin I/O. Si una ruta cae bajo
varias raíces (una anidada dentro de otra, p. ej. `saves_dir` dentro de
`roms_dir`) gana la más específica (raíz con el path más largo). Una ruta
fuera de las tres raíces se devuelve tal cual — no es un error, son rutas
propias de emuladores standalone que no necesitan re-rooting (ver §5).
6 tests (`tests/test_path_tokenizer.py`).

Se usa al **guardar** el manifiesto de DEVPROFILE-4 (tokeniza rutas
absolutas del dispositivo origen) y al **restaurar** en DEVPROFILE-5/6
(sustituye por las rutas del dispositivo destino).

---

## 5. DEVPROFILE-4 — Manifiesto Tier A + backup al remoto

**Hallazgo clave: esto puede necesitar poco código nuevo.** El mecanismo de
sync multi-carpeta que moverá `config/<core>/*.cfg`,
`retroarch-core-options.cfg`, `config/remaps/`, `autoconfig/`, shaders,
`.opt` en bulk y BIOS/`system/` **ya existe** —
`SyncConfig.sync_sources: list[SyncSource]` con `sync_all=True`, consumido
por `sync_cloud.py`/`cable_sync_daemon.py` (mismo mecanismo que hoy mueve
carpetas completas de PPSSPP/Dolphin).

Alcance recortado — **backend y pantalla de Settings hechos (2026-09-01)**
(decidido explícitamente con el usuario: primero backend testeable, la UI en
otra sesión — ver más abajo):

- **4a** — ✅ backend. `src/rom_manager/services/device_profile.py::
  detect_tier_a_sources(ra_dir, remote_base)`. Resulta que la mayor parte de
  Tier A **ya estaba cubierta** sin código nuevo: `config/` (que ya sincroniza
  `config/<core>/*.opt` Y `config/remaps/`, porque remaps vive *dentro* de
  `config/`) y `cheats/` los mueve `build_cloud_sync_sources()` vía
  `config.sync.ra_config_dir`/`cheats_dir` (mecanismo D2 ya existente, sin
  tocar). Lo que de verdad faltaba era autodetectar 3 carpetas hermanas de
  `config/` bajo el directorio de instalación de RetroArch:
  `autoconfig/`, `shaders/`, `system/` (BIOS) — cada una solo se devuelve si
  existe en disco, con un remoto sugerido `<remote_base>/<carpeta>` (mismo
  patrón `<remote>:RetroSync/<categoría>` que ya usa `useRemoteForSync()` en
  `sync.js`). **`retroarch-core-options.cfg` (archivo suelto, no carpeta)
  queda fuera** — `SyncSource` sincroniza directorios, no archivos sueltos;
  marcado con `ponytail:` en el código, se añade si resulta que importa en
  la práctica. 5 tests (`tests/test_device_profile.py`).
  **Pantalla "Perfil del dispositivo" en Settings** — ✅ 2026-09-01.
  `_handle_device_profile_detect()` (`web/handlers/system.py`) localiza
  RetroArch igual que `_handle_retroarch_check` (junto al exe configurado),
  llama a `detect_tier_a_sources()` con `remote_base` derivado de
  `saves_remote`/`states_remote` (recorta el último segmento, p. ej.
  `dropbox:RetroSync/saves` → `dropbox:RetroSync`) y **excluye** candidatos
  cuyo `local_dir` ya está en `config.sync.sync_sources` — la pantalla solo
  pregunta por carpetas nuevas, volver a confirmar en cada visita sería
  ruido. Ruta `GET /api/device-profile-detect`
  (`web/handlers/esde/system.py`). El guardado **no necesitó endpoint
  nuevo**: `sync.sources` se añadió al `allowed` set de
  `_save_config()`/`POST /api/config` (`web/handlers/config.py`) —
  `write_config_toml()` ya soportaba listas de dicts como array-of-tables
  genérico, y `config.sync = new_cfg.sync` en el reload ya recarga
  `sync_sources` en memoria sin código adicional. UI en `tab-settings.html`
  (panel bajo RetroArch) + `loadDeviceProfileDetect()`/
  `saveDeviceProfileSources()` en `js/tabs/esde.js` (patrón calcado de
  `loadRetroArchCheck`), exportadas en `main.js`. El frontend envía
  `existing` (sin tocar) + los candidatos marcados con su remoto editado —
  nunca sobrescribe fuentes ajenas a Tier A que el usuario haya añadido a
  mano en `config.toml`. 2 tests nuevos en `tests/test_device_profile.py`.
- **4b** — ✅ backend. `export_profile_sources()`/`import_profile_sources()`
  en el mismo módulo: aplican el tokenizador (§4/DEVPROFILE-3) a
  `SyncSource.local_dir` solo al serializar/deserializar el perfil — el sync
  normal entre el mismo PC y la misma Anbernic sigue usando rutas absolutas
  sin tokenizar, porque ya son estables en ese par. Una fuente cuyo
  `local_dir` cae fuera de `roms_dir`/`saves_dir`/`system_dir` (un standalone
  como Dolphin) se serializa sin tokenizar — no tiene sentido re-rootearla
  entre dispositivos.
- **4c** — `retroarch.cfg` queda explícitamente fuera de esta lista (ver
  DEVPROFILE-0/2) — ninguna función de este módulo lo toca.

Si al construir la pantalla de Settings resulta que `sync_sources` no cubre
algún caso (p. ej. BIOS/`system/` necesita lógica distinta a un `SyncSource`
normal porque son pocos archivos grandes, no un árbol), es la señal de que
hace falta código nuevo ahí — pero no antes de intentar la reutilización.

---

## Orden recomendado

`DEVPROFILE-1c` (BIOS, más barato) → `1b/1d` (schema + migración ES-DE) →
`DEVPROFILE-2` (independiente, solo-PC, puede ir en paralelo) →
`DEVPROFILE-3+4` juntos en la misma rama (3 no tiene consumidor sin 4).

Cada tarea sigue la convención del repo: rama propia, PR a `develop`, sin
mezclar fases (mismo patrón que `ANDROID-SYNC-*`, ver
`Tareas/Roadmap-Android-Sync.md`).

**Estado 2026-09-01**: `1`, `2`, `3` y `4` (4a/4b/4c, backend + pantalla de
Settings) ✅, mergeados a `develop` en PR #270 y #271. La pantalla "Perfil
del dispositivo" (§5, 4a) se completó en rama
`feature/devprofile-4a-settings-ui` — `DEVPROFILE-4` ya es usable end-to-end
desde la UI. `5`/`6`/`7`/`8`/`9` sin empezar; `5`/`6` (botones de
restauración PC/Android) ya no están bloqueados por la pantalla de perfil.
