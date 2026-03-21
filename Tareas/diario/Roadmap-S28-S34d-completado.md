# Retro Vault — Historial completado S28–S34d

> Archivado: 2026-03-20
> Reemplazado por: `Tareas/Roadmap-S28-Plus.md` (solo pendientes)
> Contiene todas las sesiones y bugs resueltos hasta esta fecha.

---

## S28 ✅ — Búsqueda + lanzador + favoritos + tags

| # | Qué |
|---|-----|
| 28-1 ✅ | Búsqueda global en tiempo real (debounce 200ms, busca título/plataforma/tag) |
| 28-2 ✅ | "Continuar jugando" mejorado — grid horizontal estilo Netflix con 5-6 juegos |
| 28-3 ✅ | Lanzar desde la UI — `POST /api/launch`, `config.launcher_cores`, `[launchers]` en config.toml |
| 28-4 ✅ | Preview de save-states — `GET /api/stateshot?id=` sirve `<rom>.state*.png` como base64 |
| 28-5 ✅ | Favoritos — `is_favorite` en BD, `POST /api/toggle-favorite`, filtro en Games |
| 28-6 ✅ | Tags personalizados — tabla `game_tags`, `POST/DELETE /api/tag`, chips en panel + filtro |

**Implementación:** `schema.py` columnas `is_favorite`, `notes`; tabla `game_tags`; `repository.py` toggle_favorite/add_tag/remove_tag; `config.py` retroarch_path + launcher_cores; endpoints toggle-favorite/tag/tags/game-tags/stateshot/launch.

---

## S29 ✅ — Backup de saves versionado

| # | Qué |
|---|-----|
| 29-1 ✅ | Backup pre-sync — copia a `.rommgr/saves-backup/{platform}/{game}/{timestamp}.ext` |
| 29-2 ✅ | Backup pre-rename — copia de seguridad previa si el save destino existe |
| 29-3 ✅ | Retención configurable — `backup_saves_keep_n` (default 5). Limpia las más antiguas |
| 29-4 ✅ | Vista de backups en panel de detalle — "Historial de saves" + botón "Restaurar" |
| 29-5 ✅ | Backup manual desde UI — botón "Hacer backup ahora" en pestaña Sync, genera ZIP |

---

## S30 ✅ — Editor de metadatos + Notas personales

| # | Qué |
|---|-----|
| 30-1 ✅ | Editar título canónico — collapsible "✏ Editar metadatos", `POST /api/set-metadata` |
| 30-2 ✅ | Editar año/género/publisher/developer/rating |
| 30-3 ✅ | Notas personales — textarea auto-save debounce 800ms, campo `notes` en `games` |
| 30-4 ✅ | Preview pre-scraping — `preview:true` muestra datos antes de aplicar |
| 30-5 ✅ | Scraping individual — botón "🔍 Re-scrapear", `POST /api/scrape-single` |

---

## S31 ✅ — Colección completa: Missing + Estadísticas

| # | Qué |
|---|-----|
| 31-1 ✅ | "Missing in action" — pestaña Colección con ROMs faltantes del DAT, filtro por plataforma |
| 31-2 ✅ | Estadísticas de completación — barras por plataforma, color según cobertura (≥80% verde, ≥40% amarillo, <40% rojo) |
| 31-3 ✅ | Wishlist de faltantes — tabla `wishlist`, `POST/GET /api/wishlist` |
| 31-4 ✅ | Export de faltantes — `GET /api/export-missing` → `missing_roms.csv` |
| 31-5 ✅ | "Buscar en Google" + copiar — query `Título Plataforma No-Intro site:archive.org` |

---

## S32 ✅ — Bundle de mejoras pequeñas

| # | Qué |
|---|-----|
| 32-1 ✅ | Badge de inbox en nav — contador rojo, polling 30s via `GET /api/inbox-count` |
| 32-2 ✅ | Filtro por plataforma en Duplicados — filtra grupos SHA1 y semánticos simultáneamente |
| 32-3 ✅ | Drag & drop en Inbox — zona dashed, `POST /api/inbox-upload` multipart/form-data |
| 32-4 ✅ | Timeline de operaciones — sección en Settings, `GET /api/operations-timeline?limit=100` |
| 32-5 ✅ | Playlists RetroArch (.lpl) — `utils/lpl_generator.py`, `POST /api/export-lpl`, un `.lpl` por plataforma |
| 32-7 ✅ | Export gamelist para Pegasus — `scraper/pegasus_writer.py` + endpoint + botón en Scraper |

---

## S33 ✅ — Filtros avanzados + Exportación + Comparador de saves

| # | Qué |
|---|-----|
| 33-1 ✅ | Filtros avanzados en Games — dropdowns género/año/sort_by desde `/api/games/filter-options` |
| 33-2 ✅ | Exportar biblioteca — `GET /api/export-library?format=csv\|json`, botones en toolbar |
| 33-3 ✅ | Comparador visual de saves — filas amarillas = save modificado después del último sync |
| 33-4 ✅ | Historial de sync por juego — panel de detalle, `GET /api/game-sync-history?source_path=` |

---

## S34 ✅ — Plataformas: ampliación de formatos y detección

| # | Qué |
|---|-----|
| 34-1 ✅ | `platforms.toml` externo — 180+ entradas, override en `.rommgr/platforms.toml` |
| 34-2 ✅ | Detección ampliada — FDS, WonderSwan, PC Engine, Atari ST, C64, ZX Spectrum, Amiga, ScummVM, etc. |
| 34-3 ✅ | Conversor N64 → .z64 — `converters/n64_converter.py`, byte-swap `.v64`/`.n64` en Python puro |
| 34-4 ✅ | Soporte `.zso` para PSP/PS2 |
| 34-5 ✅ | BIOS Checker — `detection/bios_checker.py`, 21 entradas, comprobación MD5, sección en Settings |
| 34-6 ✅ | Detección ES-DE — `GET /api/esde-status`, detecta carpeta/roms_path/gamelists desde `es_settings.xml` |

---

## S34b ✅ — Integración ES-DE + Library Doctor

| # | Qué |
|---|-----|
| 34b-1 ✅ | Fix columna Google en RA (ya estaba implementado) |
| 34b-2 ✅ | Fix error `'filename'` gamelist — alias SQL `g.original_filename AS filename` |
| 34b-3 ✅ | Fix ruta gamelist por defecto — `_autoFillEsdeGamelistDir()` + botón "ES-DE ↗" |
| 34b-4 ✅ | Dónde viven assets scrapeados — info en panel + botón "Copiar a ES-DE" → `GET /api/copy-assets-to-esde` |
| 34b-5 ✅ | "Library Doctor" — `GET /api/library-doctor`, detecta ROMs mal ubicados, CUE+BIN incompletos, carpetas vacías |
| 34b-6 ✅ | Info box estático sobre sets PSX multi-bin en sección CHD converter |
| 34b-7 ✅ | Soporte catálogo arcade base — `catalog/mame_loader.py`, pase 3 por stem, `config.catalogs_arcade_dir` |

---

## S34c ✅ — Arcade: plataforma MAME vs FBNeo

| # | Qué |
|---|-----|
| 34c-1 ✅ | Plataforma desde fuente del catálogo — `.xml` → MAME, `.dat` → FBNeo; `repository.update_match()` acepta `platform=` |
| 34c-2 ✅ | Catálogo desde `.rommgr/catalogs/arcade/` — `_handle_catalog_status` incluye desglose MAME/FBNeo |
| 34c-3 ✅ | Detección por carpeta para arcade — `platforms.toml`: `"mame"/"fbneo"/"cps1"/"cps2"/"arcade"` = "Arcade" |
| 34c-4 ✅ | Importador UI acepta carpeta completa — auto-detecta formato por contenido XML/DAT |

**Decisión de diseño:** No distinguir sub-DATs de FBNeo como plataformas separadas. FBNeo DAT → `"FBNeo"`. MAME solo si viene de `mame.xml`.

---

## S34d ✅ (parcial) — Pestaña "Formatos de archivo"

| # | Qué |
|---|-----|
| 34d-0 ✅ | Fix `parse_bins_from_cue` sin comillas — soporta `FILE nombre.bin BINARY` (sin comillas). Arregla Street Fighter Collection. |
| 34d-1 ✅ | Nueva pestaña "Formatos" — movidos desde Tools: CHD, ZIP, N64, M3U, LPL, Análisis, Multidisc. Tools queda con: Library Doctor, Estructura, Saves huérfanos, Health Check, RA, Informe, Pegasus, Limpieza. |

---

## BUG-1 (parcial) ✅ — Duplicados

| # | Qué |
|---|-----|
| B1-2 ✅ | Detectar duplicados por nombre canónico — `get_title_duplicate_groups()` en `repository.py`, sección "duplicados semánticos" en amarillo en la UI |
| B1-3 ✅ | Fix rename cuando el save destino ya existe — `file_renamer.py` renombra a `.sav.bak`, usa `os.replace` |

---

## BUG-2 (parcial) ✅ — Conversor CHD

| # | Qué |
|---|-----|
| B2-1 ✅ | chdman no encuentra el .bin — `chd_converter.py` lanza chdman con `cwd=cue_path.parent` |
| B2-3 ✅ | Validar .cue antes de lanzar chdman — verifica que todos los `.bin` existen antes de llamar chdman |
| B2-4 ✅ | No proponer conversión si los .bin ya no existen — `dry_run` marca como `failed` con mensaje descriptivo |

---

## BUG-3 (parcial) ✅ — Bugs uso real (2026-03-19)

| # | Qué |
|---|-----|
| B3-1 ✅ | Scan ADB no actualiza cards de Inicio — `_build_status` detecta ruta Android y usa `repository_android` |
| B3-2 ✅ | Rename falla con `[WinError 183]` — save existente se renombra a `.sav.bak` antes de renombrar |
| B3-3 ✅ | Duplicados con mismo título no aparecen — `get_title_duplicate_groups()` + sección semántica en UI |
| B3-5 ✅ | Botón "Actualizar" en Scraper no refresca — `loadScraperSummary()` añade `?t=Date.now()` |
| B3-6 ✅ | Informe de salud: columna "query Google", botón copiar, filtro de plataforma |
| B3-7 ✅ | ES-DE muestra subcopias — `get_metadata_for_platform` excluye `set_type IN ('disc_image','disc_auxiliary')` + `.bin .img .iso` eliminados de `<extension>` PSX |
| B3-8 ✅ | Rutas configuradas no persisten — inputs `ov-pc-path`/`ov-ab-path` tienen `onblur="saveOvPaths()"` |
| B3-9 ✅ | Export gamelist.xml no escribe en rutas que ES-DE lee — slug derivado de `_ES_PLATFORM_FOLDERS` |

---

## BUG-4 ✅ — Bugs uso real (segunda tanda)

| # | Qué |
|---|-----|
| B4-1 ✅ | RA informe: columna "query Google" — `_renderRaResult` y `_renderReportRa` tienen columna "Buscar" + `_googleQuery()` |
| B4-2 ✅ | Error `'filename'` al exportar gamelist.xml — alias SQL `g.original_filename AS filename` |
| B4-3 ✅ | "Estructura de biblioteca" solo crea en PC — cambiado a `config.anbernic_root` |
| B4-4 ✅ | Gamelist export: ruta sin valor por defecto — `_autoFillEsdeGamelistDir()` + botón "ES-DE ↗" |
| B4-5 ✅ | PSX games fuera de carpeta de plataforma — panel actualizado con aviso explícito + ícono 🔍 |
