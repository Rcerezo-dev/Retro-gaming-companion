# Retro Vault — Roadmap activo

> Actualizado: 2026-03-20
> Historial completado en `diario/Roadmap-S28-S34d-completado.md`
> Completadas: S28 ✅ S29 ✅ S30 ✅ S31 ✅ S32 ✅ S33 ✅ S34 ✅ S34b ✅ S34c ✅ S34d(parcial) ✅
> La distribución (PyInstaller + instalador) es **SIEMPRE la última sesión**. Nunca antes.

---

## Criterio de ordenación

1. **Primero**: lo que añade valor real en el uso diario (sync, colección, lanzador)
2. **Después**: poder y comodidad (filtros, exportación, formatos nuevos)
3. **Luego**: experiencia visual avanzada y experimental
4. **Al final**: distribución — solo cuando todo lo anterior funcione end-to-end

---

## Tier 1 — Bugs y pendientes activos

### BUG-1 — Duplicados: resolución inteligente

| # | Qué | Detalle |
|---|-----|---------|
| B1-1 ✅ | **Fix "eliminar todos sin logros"** | Implementado: `_handle_ra_duplicate_discard_all` en server.py:3803 mueve a `_descartados/` y borra de BD. `discardAllRaDuplicates()` en JS llama `/api/ra-duplicates/discard-all`. |
| B1-4 | **Resolución inteligente: conservar la copia con logros** | Al resolver un duplicado (por SHA1 o por nombre canónico), marcar automáticamente para eliminación el que NO tiene soporte en RetroAchievements según el MD5 en `ra_checker`. La lógica: si uno tiene `ra_game_id` y el otro no → eliminar el que no tiene. Si ambos tienen o ninguno tiene → dejar que el usuario elija (pero proponer el de región Spain/Europe). |

---

### BUG-2 — Conversor CHD ✅

| # | Qué | Detalle |
|---|-----|---------|
| B2-2 ✅ | **"Eliminar .cue/.bin originales" no ejecuta** | Implementado en `chd_converter.py` línea 76 (`# B2-2`): si `.chd` ya existe y `delete_source=True`, elimina `.cue` y `.bin`. Botón standalone "Eliminar .cue/.bin originales" también disponible via `doCleanupCueBin()` → `/api/cleanup-cue-bin`. |

---

### BUG-3 ✅ — Resuelto

| # | Qué | Detalle |
|---|-----|---------|
| B3-4 ✅ | **Botón "eliminar" en duplicados de logros no hace nada** | Implementado: `_handle_ra_duplicate_discard` en server.py:3750. `deleteRaDuplicate()` en JS llama `/api/ra-duplicates/discard`, mueve a `_descartados/` y borra de BD con rollback si falla. |

---

### BUG-5 — Pendientes detectados en sesión 2026-03-19

| # | Qué | Detalle |
|---|-----|---------|
| B5-1 ✅ | **CHD: observabilidad de conversiones fallidas** | (a) Checkbox "Solo errores" sobre la lista — se activa automáticamente si hay fallos. (b) Contador `bin_count` por juego en el resultado (server + JS). (c) Resumen con badges colored ya existía. `applyChdFilter()` filtra en cliente sin nueva petición. |
| B5-2 ✅ | **CHD: validar conversión post-chdman** | Tras exit code 0, `chd_converter.py` verifica que el `.chd` exista y tenga `stat().st_size > 0`. Si no, borra el fichero vacío/corrupto y retorna `success=False` con mensaje claro. |
| B5-3 ✅ | **Arcade matching: verificar en hardware** | Código completo: `mame_loader.py` parsea MAME XML + FBNeo DAT; `matcher.py` usa `load_arcade_dir`; endpoint `/api/import-arcade-catalog` en server.py. Pendiente: confirmar en hardware con ROMs reales. |
| B5-4 ✅ | **ES-DE PSX: verificar flujo completo** | Código completo: `parse_bins_from_cue` corregido (B2-1), `set_detector.py` fija `.cue`/`.chd` duplicados (B6-2), scraper y gamelist export operativos. Pendiente: confirmar flujo completo en hardware. |
| B5-5 ✅ | **Pestaña Formatos: probar en hardware** | IDs HTML estables, JS sin cambios estructurales. Pendiente: confirmar en hardware que todos los paneles responden. |

---

### BUG-6 — Bugs detectados en uso real (2026-03-20)

| # | Qué | Detalle |
|---|-----|---------|
| B6-1 ✅ | **ES-DE: emuladores no lanzan juegos (rutas incorrectas)** | Implementado `GET /api/retroarch-check`: verifica exe, retroarch.cfg, cores dir, saves dirs, y si ES-DE apunta al mismo RetroArch. Panel "Diagnosticar" en Settings con tabla de checks + lista de cores clave instalados. |
| B6-2 ✅ | **PSX: juegos duplicados/triplicados (ej. Darkstalkers)** | Causa raíz: `.cue` tenía `set_type = "cue_sheet"` (no filtrado), `.chd` tenía `"single_file"` → ambos visibles. Fix 1: `set_detector.py` devuelve `"disc_auxiliary"` para `.cue` cuando existe `.chd` hermano. Fix 2: CHD converter actualiza la BD inmediatamente tras conversión. Bonus: `.iso` standalone ya no se filtra como `"disc_image"` (fix para PS2/DC). |
| B6-3 ✅ | **Scraper: resultados no persisten entre sesiones** | Causa raíz: el scraper usaba `repository.batch()` que hace un único commit al salir del contexto — cualquier excepción (error de red, 403, cancel) hacía rollback de **todos** los metadatos de esa sesión. Fix: cambiado a `repository.connect()` + `conn.commit()` después de cada `upsert_metadata`. Cada juego queda persistido en cuanto se procesa. |
| B6-4 ✅ | **Scraper: reintentar automáticamente hasta completar** | Implementado: retry por juego con backoff 5s→15s→30s (3 intentos). PermissionError es fatal (cuota/credenciales). Errores de red no detienen el job — el juego se cuenta en `network_errors` y el loop continúa. La descarga de imagen también protegida con try/except. UI muestra "⚠ N errores de red" en tiempo real. |
| B6-5 ✅ | **Inbox: pipeline no mueve las ROMs tras ejecutarse** | Causa raíz: el ZIP original quedaba en inbox; al siguiente run `extract_zip` lo re-extraía (los archivos extraídos ya no estaban — habían sido movidos a la biblioteca). Fix: los ZIPs procesados se mueven a `inbox/_processed/` (excluida del scan por prefijo `_`). Si `delete_source=True`, se borran directamente. |
| B6-6 ✅ | **RetroArch: revisar qué falta para funcionar completo** | Resuelto junto con B6-1: el mismo `GET /api/retroarch-check` verifica exe, cfg, cores disponibles (con badges por plataforma) y saves/states dirs. Si ES-DE apunta a un path distinto, aparece aviso de discrepancia. |
| B6-7 ✅ | **ES-DE: explorar frontend más visual como alternativa** | (1) gamelist.xml ahora exporta `<thumbnail>` + `<marquee>` (wheel) y `<screenshot>` — scraper descarga a `media/wheels/` y `media/screenshots/`. (2) Guía de temas en `docs/esde-themes.md` — recomendados: Art Book Next, Slate, Modern. |

---

### BUG-7 — ES-DE: integración real en PC (2026-03-21) ✅

| # | Qué | Detalle |
|---|-----|---------|
| B7-ES1 ✅ | **ES no lanza juegos (exit code 1)** | El port Aloshi 32-bit usa `cmd.exe /c` que rompe D3D11 en apps 64-bit bajo Windows 11. Fix: 7 wrappers `.bat` con `cd /d` previo al launch. Actualizado `es_systems.cfg`. |
| B7-ES2 ✅ | **ES muestra "sin archivos de juego"** | Los gamelists en `~/.emulationstation/gamelists/` tenían `<path>` apuntando al propio dir de gamelists. Causa original: el botón "ES-DE ↗" rellenaba el campo de export con esa ruta. Fix: borrados los 19 gamelists rotos; corregido el pipeline de export para no escribir nunca a ese directorio. |
| B7-ES3 ✅ | **Export de gamelist recreaba los ficheros rotos** | `server.py` (scraper auto-export + `_handle_export_gamelists`) detectaba `~/.emulationstation/gamelists/` y escribía copia secundaria ahí. Para ES-DE el gamelist va junto a los ROMs. Eliminada la escritura secundaria en ambos lugares. |
| B7-ES4 ✅ | **Botón "ES-DE ↗" asignaba ruta incorrecta** | `useEsdeGamelistDir()` y `_autoFillEsdeGamelistDir()` rellenaban el campo de export con `~/.emulationstation/gamelists/` → rutas `<path>` rotas. Corregido: el campo se queda vacío (= `library_root`). |
| B7-ES5 ✅ | **ES-DE mostraba cada track `.bin` como juego** | `.bin`, `.img`, `.mdf` eliminados de `<extension>` en PSX, PS2, Saturn y Dreamcast en `es_systems.cfg`. Solo quedan los formatos de entrada reales (`.cue`, `.chd`, `.gdi`, etc.). |
| B7-ES6 ✅ | **Botón "Copiar a ES-DE" copiaba imágenes al lugar incorrecto** | La función copiaba a `~/.emulationstation/gamelists/{plat}/images/`; ES-DE usa las imágenes vía ruta relativa en el gamelist. Botón eliminado del panel de detalle. |

---

### BUG-8 — ES-DE: sistemas y cores mal configurados (detectado 2026-03-21)

> Detectados en validación en hardware tras los fixes de Día 16.
> Todos son problemas de `es_systems.cfg` (rutas, extensiones, comandos).

| # | Sistema | Síntoma | Causa probable | Acción |
|---|---------|---------|----------------|--------|
| B8-1 | **Sistemas que no aparecen en ES-DE** | Algunas plataformas no se listan en la pantalla principal de ES | Sus entradas en `es_systems.cfg` apuntan a carpetas vacías o inexistentes, o no tienen ROMs con la extensión configurada | Auditar `es_systems.cfg`: verificar que `<path>` existe y contiene ROMs con las extensiones listadas. Añadir sistemas faltantes |
| B8-2 | **MAME: ROMs no aparecen** | La sección MAME no muestra juegos | `<path>` incorrecto o extensiones no incluyen `.zip` sin subcarpeta. MAME ROM sets son `.zip` planos, no en subcarpetas | Verificar path MAME en `es_systems.cfg`. Confirmar que los ZIPs del ROM set están en el directorio raíz (no anidados) |
| B8-3 | **MAME: ROMs no cargan** | Error al lanzar, probablemente falta `mame.exe` path o argumentos incorrectos | El `run_mame.bat` puede no tener el argumento correcto (`-rompath` o ROM sin extensión). MAME espera el nombre del set sin `.zip` | Revisar `run_mame.bat`. MAME se lanza como: `mame.exe <romname>` (sin extensión, sin ruta) + `-rompath <dir>` |
| B8-4 | **Neo Geo: no aparece / no carga** | Neo Geo corre sobre MAME/FBNeo — necesita `neogeo.zip` BIOS en el mismo dir que los ROMs | Sin BIOS `neogeo.zip` en el directorio de ROMs, ningún juego Neo Geo arranca | Verificar que `neogeo.zip` (BIOS) está en la misma carpeta que los ROMs Neo Geo. Puede usarse FBNeo core (RetroArch) como alternativa |
| B8-5 | **NDS: núcleo no funciona** | "El núcleo no funciona" al intentar lanzar | El core configurado no está instalado. Para NDS: `desmume_libretro.dll` o `melonds_libretro.dll` | Verificar en RetroArch → Cores qué core NDS está disponible. Actualizar `es_systems.cfg` con el core correcto |
| B8-6 | **N64: núcleo no funciona** | Igual que NDS | Core RetroArch incorrecto o usar Mupen64Plus standalone | Verificar: `mupen64plus_next_libretro.dll` (RA) o confirmar que `run_mupen64.bat` usa los argumentos correctos |
| B8-7 | **Master System: núcleo no funciona** | Igual | SMS corre en `genesis_plus_gx_libretro.dll` (mismo core que Genesis/MD) | Actualizar entry SMS en `es_systems.cfg` para usar `genesis_plus_gx` |
| B8-8 | **NES: núcleo no funciona** | Igual | Core correcto: `fceumm_libretro.dll` o `nestopia_libretro.dll` | Verificar cuál está instalado y actualizar `es_systems.cfg` |
| B8-9 | **Atari 2600: núcleo no funciona** | Igual | Core correcto: `stella2014_libretro.dll` o `stella_libretro.dll` | Verificar disponibilidad e instalar si falta |
| B8-10 | **PSX: no lanza (usa DuckStation, no RetroArch)** | El comando en `es_systems.cfg` puede estar apuntando a RetroArch en vez de `run_duckstation.bat` | PSX debería lanzarse con DuckStation standalone (`run_duckstation.bat "%ROM%"`) | Verificar `es_systems.cfg` entry PSX — `<command>` debe ser `run_duckstation.bat "%ROM%"`. DuckStation CLI: `duckstation-qt.exe -batch "%ROM%"` |
| B8-11 | **PS2: no lanza (usa PCSX2, no RetroArch)** | Igual que PSX | PS2 con PCSX2 standalone: `run_pcsx2.bat "%ROM%"`. PCSX2 CLI: `pcsx2-qt.exe "%ROM%"` | Verificar entry PS2 en `es_systems.cfg` y argumentos de `run_pcsx2.bat` |

**Plan de acción:**
1. Leer `es_systems.cfg` actual → auditar paths, extensiones, cores
2. Leer cada `run_*.bat` → verificar argumentos CLI de cada emulador
3. Para cores RetroArch: `GET /api/retroarch-check` ya lista cores disponibles — usarlo para saber qué hay instalado
4. Corregir `es_systems.cfg` y/o los `.bat` para cada sistema fallido

---

### BUG-9 — Mejoras detectadas en uso real (2026-03-21)

| # | Qué | Detalle |
|---|-----|---------|
| B9-1 | **Library Doctor: botón "resolver todos los conflictos"** | Las sugerencias del Library Doctor muestran la acción correcta (ej. "mover a megadrive/") pero no la ejecutan. Añadir un botón "Resolver todos" que aplique todas las acciones sugeridas de una vez (o por tipo). Similar al "eliminar todos" de duplicados. |
| B9-2 | **Compatibilidad RA: tabla demasiado estrecha** | La tabla de compatibilidad de logros sigue siendo demasiado estrecha para ver todas las columnas sin scroll lateral. Hacer la tabla con `overflow-x: auto` y `min-width` por columna, o permitir redimensionar columnas. |
| B9-3 | **Botón "copiar" en informe RA no copia nada** | El botón de copiar en la sección de RetroAchievements no hace nada. Valorar alternativa: botón "Descargar versión X" donde X es la versión del ROM que sí tiene logros (según los hashes de RA), con enlace/indicación de dónde conseguirla. |
| B9-4 | **Saves huérfanos: mover todos de golpe** | La sección de saves huérfanos da sugerencias individuales de qué hacer con cada save, pero no permite moverlos/archivarlos todos a la vez. Añadir botón "Mover todos a _huerfanos/" que archive todos en bloque. |
| B9-5 | **Guía de carpetas de saves en Anbernic** | Documentar la estructura correcta de carpetas de saves en la Anbernic (qué ruta usa RetroArch Android para cada plataforma). Crear subcarpeta `docs/guias/` para este tipo de documentación (junto a Guia-Termux-Anbernic y similares). |

---

### S34d — Formatos de archivo (pendientes)

| # | Qué | Detalle |
|---|-----|---------|
| 34d-2 | **Conversión CSO/ZSO → ISO (PSP)** | Sección para descomprimir `.cso`/`.zso` a `.iso` usando maxcso. Mostrar aviso si no se encuentra el binario. |
| 34d-3 ✅ | **Organizar en subcarpetas — multi-fichero** | `move_disc_set_to_subfolder()` en `file_renamer.py` mueve CUE+BINs (o GDI+tracks) y saves al subdirectorio. `parse_tracks_from_gdi()` en `chd_converter.py`. Plataformas: PSX, Saturn, PS2, Dreamcast, GameCube, Wii. Rollback atómico. `_DISC_SUBFOLDER_PLATFORMS` en `operation_planner.py`. |

---

## Tier 2 — Poder y comodidad

### S35 — Modo claro + Grid de plataformas con logos

| # | Qué | Detalle |
|---|-----|---------|
| 35-1 | **Modo claro** | Refactor CSS con variables CSS (`--bg`, `--fg`, `--accent`…). Toggle en Settings. Oscuro como default. |
| 35-2 | **Grid de plataformas con logos** | En Overview: tarjetas por plataforma con logo SVG inline. ~20 logos SVG embebidos (NES, SNES, GBA, PSX, PS2, N64, GB, GBC, GG, MD, SMS, NDS…). Sin dependencias de internet. |
| 35-3 | **QR de acceso** | Generar QR de la URL local en Settings para escanear con la consola/móvil. Implementación pure-Python (mini QR Level 1). |
| 35-4 | **Animaciones de panel** | Microanimaciones: carga de portada (skeleton), hover en cards, transición de estado de completado. |
| 35-5 | **Vista "Colección" estilo vitrina** | Ruta `/collection` — grid de carátulas a tamaño grande por plataforma, como una estantería virtual. Click abre el panel de detalle. |

---

## Tier 3 — Experiencia visual avanzada

### S36 — Modo presentación (TV mode) + Mapa de calor + Juego del día

| # | Qué | Detalle |
|---|-----|---------|
| 36-1 | **TV mode** | Ruta `/tv` — pantalla completa, grid de carátulas grandes, navegación por teclado/flechas. Sin ratón. |
| 36-2 | **Mapa de calor de actividad** | Cuadrícula estilo GitHub (últimos 365 días). Calculable desde `last_played_at` sin cambios en backend. |
| 36-3 | **Análisis de tiempo por plataforma** | Gráfico de barras mensual: cuántos juegos distintos tocaste en GBA este mes. Agrupa `last_played_at` por (plataforma, mes). |
| 36-4 | **"Juego del día"** | Tarjeta en Overview con sugerencia aleatoria de un juego no tocado en >6 meses. Botón "ignorar". |
| 36-5 | **Tracker de tiempo de juego (RetroArch log)** | Parsear logs de sesión de RetroArch para extraer tiempo jugado por juego. Mostrar en panel de detalle y mapa de calor. |

---

## Tier 4 — Automatización y robustez

### S37 — Health check + Delta sync + Notificaciones

| # | Qué | Detalle |
|---|-----|---------|
| 37-1 | **Health check programado** | Health check semanal en background. Notificar si algún ROM tiene hash diferente al registrado (corrupción silenciosa). |
| 37-2 | **Delta sync** | Solo transferir bytes que cambiaron en el save (bsdiff). Relevante para saves de PSX/N64 grandes. |
| 37-3 | **Notificaciones de escritorio** | Al terminar sync, detectar inbox o encontrar ROMs corruptos: toast nativo de Windows via `PowerShell` (sin dependencias). |
| 37-4 | **Reintentos inteligentes en sync** | Si rclone falla por timeout, reintento con backoff exponencial. Actualmente falla silenciosamente. |

---

## Tier 5 — Experimental / Largo plazo

### S38 — Multi-perfil + Modo headless

| # | Qué | Detalle |
|---|-----|---------|
| 38-1 | **Multi-perfil de saves** | Perfiles separados (usuario 1, usuario 2…) con su propia carpeta de sync y `last_played_at`. Útil para familias. |
| 38-2 | **Modo headless completo** | Todo desde CLI: `rommgr sync`, `rommgr inbox`, `rommgr health`. Sin levantar el servidor web. Útil para Task Scheduler. |
| 38-3 | **API REST documentada** | Generar `openapi.json` desde los endpoints existentes. Permite integraciones externas (Home Assistant, scripts personales). |

---

### S39 — MAME avanzado + Agente Claude

| # | Qué | Detalle |
|---|-----|---------|
| 39-1 | **Soporte MAME avanzado** | Lo que queda tras S34c: ROMs MAME split sets vs merged sets, CHDs de MAME (`.chd` con nombre de carpeta = set name), detección de samples y artwork directories. |
| 39-2 | **Agente Claude integrado** | Chat en la UI que responde preguntas sobre la biblioteca usando la BD y la API de Claude. "¿Qué juegos de PSX no he completado?", "¿Cuánto pesa mi colección de GBA?". |

---

### S40 — Distribución Windows — **ÚLTIMA SESIÓN, SIEMPRE**

> No tocar hasta que todo lo anterior funcione end-to-end en hardware real.

| # | Qué | Detalle |
|---|-----|---------|
| 40-1 | **Ejecutable PyInstaller** | `pyinstaller --onefile --noconsole` → `RetroVault.exe`. Bundle incluye `tools/chdman.exe`, `tools/adb.exe`. Abre navegador automáticamente. |
| 40-2 | **Icono** | `.ico` de 256×256. Diseño: logo vault + pixel art. |
| 40-3 | **Instalador NSIS o InnoSetup** | Instala en `%LOCALAPPDATA%\RetroVault\`. Acceso directo escritorio + menú inicio. Arranque con Windows. Desinstalador limpio. |
| 40-4 | **Icono de bandeja (tray)** | Minimizar a tray en vez de cerrar. Menú: "Abrir", "Sync ahora", "Salir". `pystray` + `Pillow`. |
| 40-5 | **Auto-update** | Comprobar GitHub Releases en arranque. Toast con link si hay versión nueva. Sin actualización automática (opt-in). |
| 40-6 | **GitHub Releases** | Pipeline: tag → PyInstaller → upload `.exe` firmado + `CHANGELOG.md` auto-generado. |

---

## Resumen visual

```
Tier 1 — Bugs y pendientes activos
  BUG-1   Duplicados: resolución inteligente                          [B1-4]  (B1-1 ✅)
  BUG-2   ✅ Resuelto
  BUG-3   ✅ Resuelto
  BUG-5   Observabilidad CHD + verificación arcade + ES-DE PSX        [B5-1..B5-5]
  BUG-6   ✅ Bugs uso real (2026-03-20)                               [B6-1..7 ✅]
  BUG-7   ✅ Bugs uso real (2026-03-21)                               [B7-1..B7-9]
  BUG-8   ES-DE: sistemas faltantes + cores incorrectos               [B8-1..B8-11]
  BUG-9   Library Doctor batch + RA tabla + saves huérfanos batch     [B9-1..B9-5] ← NUEVO
  S34d    Formatos: CSO/ZSO + subcarpetas PSX                         [34d-2, 34d-3]

Tier 2 — Poder y comodidad
  S35     Modo claro + logos plataforma + QR + vitrina

Tier 3 — Visual avanzado
  S36     TV mode + mapa de calor + análisis tiempo + juego del día

Tier 4 — Automatización
  S37     Health check + delta sync + notificaciones escritorio
  S38     Multi-perfil + modo headless + API REST

Tier 5 — Experimental
  S39     MAME avanzado + agente Claude integrado

  S40  🏁 DISTRIBUCIÓN — PyInstaller + NSIS + tray + auto-update
```

---

## Referencia: Formatos de archivo por plataforma (ES-DE / RetroArch)

> Todos los sistemas aceptan además `.zip` y `.7z`.

### Consolas Nintendo

| Sistema | Extensiones |
|---------|-------------|
| NES / Famicom | `.nes` `.unf` `.unif` `.nsf` |
| Famicom Disk System | `.fds` |
| SNES / Super Famicom | `.smc` `.sfc` `.fig` `.swc` `.bs` `.st` |
| Nintendo 64 | `.z64` `.v64` `.n64` `.ndd` `.u1` |
| GameCube | `.iso` `.gcm` `.rvz` `.wia` `.wbfs` `.ciso` `.gcz` `.m3u` |
| Wii | `.iso` `.rvz` `.wia` `.wbfs` `.ciso` `.gcz` `.wad` `.m3u` |
| Game Boy | `.gb` `.gbc` `.sgb` |
| Game Boy Color | `.gbc` `.gb` |
| Game Boy Advance | `.gba` `.agb` `.gbz` |
| Nintendo DS | `.nds` `.dsi` `.ids` `.srl` `.app` |
| Nintendo 3DS | `.3ds` `.3dsx` `.cia` `.csu` `.cci` `.cxi` `.app` |
| Virtual Boy | `.vb` `.vboy` `.bin` |
| Pokémon Mini | `.min` |

### Consolas Sony

| Sistema | Extensiones |
|---------|-------------|
| PlayStation (PSX) | `.bin` `.cue` `.iso` `.img` `.pbp` `.mdf` `.toc` `.cbn` `.m3u` `.chd` |
| PlayStation 2 | `.iso` `.bin` `.img` `.mdf` `.gz` `.cso` `.zso` `.chd` `.m3u` |
| PlayStation 3 | `.pkg` `.ps3` `.ps3dir` |
| PSP | `.iso` `.cso` `.pbp` `.elf` `.prx` `.ppdmp` `.chd` |
| PS Vita | `.vpk` `.psvita` |

### Consolas Sega

| Sistema | Extensiones |
|---------|-------------|
| Master System / Mark III | `.sms` `.bin` `.sg` |
| Game Gear | `.gg` `.bin` |
| Mega Drive / Genesis | `.md` `.bin` `.smd` `.gen` `.68k` `.sgd` `.chd` |
| Mega-CD / Sega CD | `.bin` `.cue` `.iso` `.chd` `.m3u` |
| 32X | `.32x` `.bin` `.smd` |
| Saturn | `.bin` `.cue` `.iso` `.mdf` `.img` `.chd` `.m3u` |
| Dreamcast | `.bin` `.cue` `.iso` `.gdi` `.elf` `.cdi` `.m3u` `.chd` |
| SG-1000 | `.sg` `.bin` `.sc` `.sf7` |

### Consolas Atari

| Sistema | Extensiones |
|---------|-------------|
| Atari 2600 | `.a26` `.bin` `.rom` `.cart` |
| Atari 5200 | `.a52` `.bin` `.car` |
| Atari 7800 | `.a78` `.bin` |
| Atari Lynx | `.lnx` `.lyx` `.o` |
| Atari Jaguar | `.j64` `.jag` `.rom` `.abs` `.cof` `.bin` |
| Atari Jaguar CD | `.bin` `.cue` `.chd` |
| Atari ST / STE / TT / Falcon | `.st` `.msa` `.stx` `.dim` `.ipf` `.m3u` |
| Atari XL/XE | `.xex` `.atr` `.xfd` `.atx` `.cdm` `.cas` `.car` `.bin` `.a8s` |

### Neo Geo / SNK

| Sistema | Extensiones |
|---------|-------------|
| Neo Geo | `.neo` `.zip` `.bin` |
| Neo Geo CD | `.bin` `.cue` `.chd` `.m3u` |
| Neo Geo Pocket / Color | `.ngp` `.ngc` `.ngpc` `.npc` |

### NEC

| Sistema | Extensiones |
|---------|-------------|
| PC Engine / TurboGrafx-16 | `.pce` `.tg16` |
| PC Engine CD | `.bin` `.cue` `.chd` `.m3u` |
| PC-FX | `.fx` `.img` `.iso` `.cue` `.chd` `.m3u` |
| SuperGrafx | `.pce` `.sgx` |

### Computadoras personales

| Sistema | Extensiones |
|---------|-------------|
| DOS (DOSBox) | `.bat` `.com` `.exe` `.conf` |
| ScummVM | `.scummvm` |
| Amiga | `.adf` `.adz` `.dms` `.fdi` `.ipf` `.hdf` `.hdz` `.lha` `.slave` `.info` `.cue` `.ccd` `.nrg` `.mds` `.iso` `.m3u` |
| Commodore 64 | `.d64` `.d71` `.d80` `.d81` `.d82` `.g64` `.g41` `.x64` `.t64` `.tap` `.prg` `.p00` `.crt` `.bin` `.nib` `.nbz` |
| MSX / MSX2 | `.rom` `.ri` `.mx1` `.mx2` `.col` `.dsk` `.cas` `.sg` `.sc` `.m3u` |
| ZX Spectrum | `.tzx` `.tap` `.z80` `.rzx` `.scl` `.trd` `.dsk` |
| Amstrad CPC | `.dsk` `.sna` `.kcr` `.voc` `.cpr` `.m3u` |
| Sharp X68000 | `.dim` `.img` `.d88` `.88d` `.hdm` `.dup` `.2hd` `.xdf` `.hdf` `.cmd` `.m3u` |

### Handhelds y otros

| Sistema | Extensiones |
|---------|-------------|
| WonderSwan / Color | `.ws` `.wsc` `.bin` `.pc2` |
| Game & Watch | `.mgw` |
| Vectrex | `.bin` `.gam` `.vec` |
| ColecoVision | `.bin` `.col` `.rom` |
| Intellivision | `.int` `.bin` `.rom` |
| 3DO | `.iso` `.bin` `.cue` `.chd` |

### Arcade

| Sistema | Extensiones |
|---------|-------------|
| MAME (genérico) | `.zip` `.7z` `.chd` |
| FBNeo (FinalBurn Neo) | `.zip` `.7z` `.chd` |
| CPS-1 / CPS-2 / CPS-3 | `.zip` `.7z` |


---

### BUG-7 — Bugs detectados en uso real (2026-03-21)

| # | Qué | Detalle |
|---|-----|---------|
| B7-1 ✅ | **Organizar: "Resolver con RA" siempre pide ejecutar comprobación** | Al pulsar "Resolver con RA" en la pestaña Organizar (duplicados), siempre aparece el aviso "ejecuta comprobación de RA primero" aunque ya se haya hecho. La lógica de detección de caché no reconoce que los datos ya están disponibles. |
| B7-2 ✅ | **Organizar: "Eliminar todos los duplicados" se bloquea a mitad** | Llegado un punto, el botón "Eliminar todos los duplicados" no elimina nada más. Posible causa: los registros ya eliminados quedan en la lista en memoria y se reintenta sobre rutas que ya no existen. |
| B7-3 ✅ | **Cable Sync: añadir assets y gamelists a la sincronización** | Añadir dos checkboxes en Cable Sync: (1) **Assets/imágenes** (archivos scrapeados — imágenes de portadas) para copiarlos a la tarjeta microSD o por ADB; (2) **gamelist.xml** para que EmulationStation en la Anbernic tenga los metadatos. La ruta destino en la Anbernic sería `/storage/emulated/0/RetroArch/roms/<plataforma>/gamelist.xml`. |
| B7-4 ✅ | **Inbox: ordenar resultados del análisis por plataforma** | Al analizar carpeta en Inbox, los juegos deberían aparecer agrupados por plataforma (ej. todos los GBA juntos, todos los SNES juntos), con los archivos `unknown` al final de la lista. |
| B7-5 ✅ | **ZIP extractor: proteger ROMs de MAME/arcade de ser descomprimidas** | Los archivos `.zip` de MAME son el formato nativo del ROM set — descomprimirlos los rompe. El extractor de ZIPs en la pestaña Formatos debe detectar si un ZIP está en una carpeta de plataforma arcade (`arcade`, `fbneo`, `mame`) y omitirlo con un mensaje claro. |
| B7-6 ✅ | **Conversor N64: verificar que la herramienta n64conv está disponible** | El conversor N64 → .z64 puede no tener disponible la herramienta necesaria. Añadir comprobación de existencia del ejecutable al cargar la pestaña, con mensaje claro si falta (igual que el check de chdman). |
| B7-7 ✅ | **Library Doctor: botones de acción directa** | Las sugerencias del Library Doctor (ej. "mover ROM a carpeta correcta") solo muestran texto. Cada acción sugerida debería tener un botón que la ejecute directamente desde la interfaz sin tener que hacerlo manualmente. |
| B7-8 ✅ | **RetroAchievements: tabla estrecha + botón copiar + columna en informe HTML** | (1) La tabla de compatibilidad de logros es demasiado estrecha — ampliar o hacer scrollable horizontalmente. (2) El botón de copiar la query de búsqueda debe usar el icono estándar de "copiar" (dos rectángulos con esquinas redondeadas), no texto. (3) La columna de logros RA debe aparecer también en el informe HTML de salud de biblioteca. |
| B7-9 ✅ | **Logs: exportar archivos de log de todos los módulos** | Crear una sección en Settings o en la pestaña de herramientas que permita descargar/ver los logs de todos los módulos (scanner, scraper, inbox, cable sync, CHD converter, sync rclone) para facilitar el diagnóstico de problemas. |
