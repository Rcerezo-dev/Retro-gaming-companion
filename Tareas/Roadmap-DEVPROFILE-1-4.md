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

Función pura, sin dependencias del resto del bloque:
```python
def tokenize(path: Path, roms_dir: Path, saves_dir: Path, system_dir: Path) -> str: ...
def resolve(token_path: str, roms_dir: Path, saves_dir: Path, system_dir: Path) -> Path: ...
```
Se usa al **guardar** el manifiesto de DEVPROFILE-4 (tokeniza rutas
absolutas del dispositivo origen) y al **restaurar** en DEVPROFILE-5/6
(sustituye por las rutas del dispositivo destino). No tiene entidad propia
más allá de esto — considerar fusionarlo en el mismo PR que DEVPROFILE-4 en
vez de una rama separada, ya que no tiene uso sin él (evita un PR que solo
añade una función sin consumidor).

---

## 5. DEVPROFILE-4 — Manifiesto Tier A + backup al remoto

**Hallazgo clave: esto puede necesitar poco código nuevo.** El mecanismo de
sync multi-carpeta que moverá `config/<core>/*.cfg`,
`retroarch-core-options.cfg`, `config/remaps/`, `autoconfig/`, shaders,
`.opt` en bulk y BIOS/`system/` **ya existe** —
`SyncConfig.sync_sources: list[SyncSource]` con `sync_all=True`, consumido
por `sync_cloud.py`/`cable_sync_daemon.py` (mismo mecanismo que hoy mueve
carpetas completas de PPSSPP/Dolphin).

Alcance recortado:
- **4a** — En vez de un "manifiesto" nuevo, generar automáticamente las
  entradas `SyncSource` de Tier A (auto-detectadas a partir de
  `ra_config_dir` — ya existe la detección, ver `_detect_retroarch_install()`
  y su contraparte Android) y dejar que el usuario las confirme en una
  pantalla nueva de Settings ("Perfil del dispositivo") — no un mecanismo
  de sync paralelo.
- **4b** — Aplicar el tokenizador (§4) a `SyncSource.local_dir` solo en el
  momento de export/import entre dispositivos distintos — el sync normal
  entre el mismo PC y la misma Anbernic no lo necesita, porque las rutas ya
  son estables en ese par.
- **4c** — `retroarch.cfg` queda explícitamente fuera de esta lista (ver
  DEVPROFILE-0/2) — el manifiesto documenta esto para que DEVPROFILE-5/6 no
  intenten restaurarlo.

Si al implementar 4a resulta que `sync_sources` no cubre algún caso (p. ej.
BIOS/`system/` necesita lógica distinta a un `SyncSource` normal porque son
pocos archivos grandes, no un árbol), es la señal de que hace falta código
nuevo ahí — pero no antes de intentar la reutilización.

---

## Orden recomendado

`DEVPROFILE-1c` (BIOS, más barato) → `1b/1d` (schema + migración ES-DE) →
`DEVPROFILE-2` (independiente, solo-PC, puede ir en paralelo) →
`DEVPROFILE-3+4` juntos en la misma rama (3 no tiene consumidor sin 4).

Cada tarea sigue la convención del repo: rama propia, PR a `develop`, sin
mezclar fases (mismo patrón que `ANDROID-SYNC-*`, ver
`Tareas/Roadmap-Android-Sync.md`).
