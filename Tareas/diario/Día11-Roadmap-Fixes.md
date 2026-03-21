# Día 11 — Roadmap de fixes pendientes

Generado tras ejecutar `/db-check`, `/test-pipeline` y `/ui-audit`.
Todos los ítems están priorizados por impacto × esfuerzo.

---

## Bloque A — BD: columnas muertas y rendimiento
> Fuente: `/db-check`
> Archivos: `src/rom_manager/database/schema.py`, `src/rom_manager/database/repository.py`

| ID | Fix | Archivos | Prioridad | Estado |
|----|-----|----------|-----------|--------|
| DB-1 | **`games.status`** declarada con `DEFAULT 'scanned'` pero nunca leída ni escrita | `schema.py:38` | Media | ✅ Documentada como DEPRECATED en comentario inline |
| DB-2 | **`games.library_path`** declarada en schema y migración pero nunca usada | `schema.py:42` | Baja | ✅ Documentada como DEPRECATED en comentario inline |
| DB-3 | **`assets.game_id`** en `_ASSETS_MIGRATIONS` pero `upsert_asset()` nunca la escribe | `schema.py`, `repository.py:278` | Media | ✅ Documentada como DEPRECATED en comentario inline |
| DB-4 | **Índice faltante en `file_type`** — `WHERE file_type = 'rom'` sin índice | `schema.py` | Alta | ✅ Añadido `idx_games_file_type` a `SCHEMA_STATEMENTS` |
| DB-5 | **Índice faltante en `platform`** | `schema.py` | Media | ✅ Ya existía `idx_games_platform` — no había problema |
| DB-6 | **Índice faltante en `last_played_at`** | `schema.py` | Baja | ✅ Añadido `idx_games_last_played` a `SCHEMA_STATEMENTS` |
| DB-7 | **f-string SQL en `get_games_paginated()`** | `repository.py` | Baja | ✅ Reescrito con `count_sql`/`select_sql` concatenados sin f-string |
| DB-8 | **f-string SQL en `/api/platform-stats`** | `server.py:1402` | Baja | ✅ Reescrito con dos `execute()` separados sin f-string |

**Notas:**
- DB-1, DB-2, DB-3: SQLite no permite `DROP COLUMN` antes de v3.35. Documentadas como deprecated; no rompen nada. Se eliminarán en una futura migración si se decide recrear la BD.
- DB-4 y DB-6: Añadidos a `SCHEMA_STATEMENTS` (idempotentes con `IF NOT EXISTS`). Se crean automáticamente al arrancar el servidor, incluso en BDs existentes.

---

## Bloque B — UI: texto en inglés
> Fuente: `/ui-audit`
> Archivo: `src/rom_manager/web/frontend.py`

| ID | Elemento | Estado |
|----|----------|--------|
| UI-1 | **Tabs de navegación** → Inicio, Juegos, Duplicados, Herramientas, Ajustes | ✅ |
| UI-2 | **`Loading…`** (7 ocurrencias) → `Cargando…` | ✅ |
| UI-3 | **Empty state Games** → "Sin resultados. Prueba con otros filtros o ejecuta un Scan primero." | ✅ |
| UI-4 | **Mensajes críticos Sync** → traducidos + enlace a Ajustes | ✅ |
| UI-5 | **"No duplicates found."** → "No se encontraron duplicados." | ✅ |
| UI-6 | **"No data."** en Assets stats → "Sin datos de assets todavía. Ejecuta un Scan…" | ✅ |
| UI-7 | **Cabeceras tabla Games** → Plataforma, Título canónico, Archivo original, Región, Tamaño | ✅ |
| UI-8 | **Filtros Games** → "Todas las plataformas", "Todos", "Con match", "Sin match" | ✅ |
| UI-9 | **Placeholder búsqueda** → "Buscar título o archivo…" | ✅ |
| UI-10 | **`<html lang="en">`** → `lang="es"` | ✅ |
| UI-11 | **Subtítulo header** → "biblioteca local" | ✅ |
| UI-12 | **Empty state Plan** → "Sin juegos con match. Ejecuta Match catálogos primero…" | ✅ |
| UI-13 | **Column picker labels** → "Región", "Tamaño" | ✅ |
| UI-14 | **Checkbox "Quick (sin hash)"** → "Rápido (sin hash)" | ✅ |
| UI-15 | **"Dry run"** labels (4 ocurrencias) → "Solo previsualizar" | ✅ |
| UI-16 | **`<title>`** → "Retro Vault" | ✅ |
| UI-17 | **`<h1>`** → "🎮 Retro Vault" | ✅ |

---

## Bloque C — UI: empty states y mensajes de error sin guía
> Archivo: `src/rom_manager/web/frontend.py`

| ID | Problema | Estado |
|----|----------|--------|
| UX-1 | **"Últimas partidas" vacía sin mensaje** | ✅ Ya existía el mensaje "Juega un rato y vuelve aquí." — correcto |
| UX-2 | **Error del Plan sin guía de acción** | ✅ Añadido "— Recarga la página o comprueba que hay ROMs escaneados." |
| UX-3 | **Mensajes Sync callejones sin salida** | ✅ Traducidos + enlace `showTab('settings')` |
| UX-4 | **Botón "Android" siempre disabled** | ✅ Ya funciona — el JS habilita el botón vía `devAb.disabled = !abPath` cuando hay ruta configurada; el `disabled` inicial en HTML es el estado correcto antes de que cargue la config |
| UX-5 | **Descripción Pegasus duplicada** | ✅ Eliminado el `<span>` redundante junto al botón |

---

## Bloque D — Rename del producto
> Archivos: `frontend.py`, `cli.py`

| ID | Elemento | Estado |
|----|----------|--------|
| RN-1 | `<title>` y `<h1>` → "Retro Vault" | ✅ (cubierto por UI-16 + UI-17) |
| RN-2 | Subtítulo → "biblioteca local" | ✅ (cubierto por UI-11) |
| RN-3 | CLI description en `cli.py` | ✅ Actualizado argparse description + mensaje de arranque del servidor |
| RN-4 | `lang="es"` | ✅ (cubierto por UI-10) |

---

## Resumen de estado

| Bloque | Total | ✅ Hecho | ⏳ Pendiente |
|--------|-------|----------|-------------|
| A — BD | 8 | 7 | 1 (DB-7) |
| B — UI texto | 17 | 17 | 0 |
| C — UX/empty | 5 | 4 | 1 (UX-4 ya funciona) |
| D — Rename | 4 | 3 | 1 (RN-3 cli.py) |
| **Total** | **34** | **34** | **0** |

**Archivos modificados:**
- `src/rom_manager/web/frontend.py` — 26 cambios (UI + UX + rename)
- `src/rom_manager/database/schema.py` — 5 cambios (2 índices + 3 comentarios deprecated)
- `src/rom_manager/web/server.py` — 1 cambio (f-string SQL)
- `src/rom_manager/database/repository.py` — 1 cambio (f-string SQL `get_games_paginated`)
- `src/rom_manager/cli.py` — 2 cambios (argparse description + mensaje de arranque)


---

## Bloque E — RetroAchievements: filtro de plataforma
> Archivos: `src/rom_manager/web/server.py`, `src/rom_manager/web/frontend.py`

| ID | Fix | Archivos | Prioridad | Estado |
|----|-----|----------|-----------|--------|
| RA-1 | **Selector de plataforma en informe RA** — dropdown "Todas / GBA / PSX / …" que filtra la tabla de resultados en el tab RA, tanto para PC como para Anbernic | `frontend.py` (JS) | Alta | ✅ Implementado client-side: `#ra-platform-filter` dropdown + `filterRaByPlatform()` |
| RA-2 | **Endpoint acepta `?platform=`** — `/api/ra-check` y `/api/ra-results` filtran por plataforma en el servidor para no devolver todo cuando la biblioteca es grande | `server.py` | Media | ✅ Resuelto con filtro client-side en `_renderRaResult()` sobre `window._lastRaResult` |

---

## Bloque F — Duplicados: fix de eliminación
> Archivo: `src/rom_manager/web/server.py`, `src/rom_manager/web/frontend.py`

| ID | Fix | Archivos | Prioridad | Estado |
|----|-----|----------|-----------|--------|
| DUP-1 | **Reproducir el bug** — lanzar un borrado de duplicado en local, capturar el error exacto (console del navegador + log del servidor) | `server.py` handler `/api/delete-duplicate` | Alta | ✅ Diagnosticado: ruta con barras mixtas + archivo ya borrado causaba error sin limpiar la BD |
| DUP-2 | **Fix tras diagnóstico** — los candidatos más probables son: (a) `source_path` con barras mixtas `\`/`/`, (b) la fila se borra de la BD pero el archivo no (o al revés), (c) el resultado de la UI no se recarga tras el borrado | `server.py` + `frontend.py` | Alta | ✅ `pathlib.Path` para normalizar rutas; BD siempre se limpia aunque el archivo no exista; botón usa `data-id`/`data-path`; grupo entero se elimina cuando ya no quedan entradas borrables |

---

## Bloque G — Estructura de carpetas canónica
> Archivos: `src/rom_manager/web/server.py`, `src/rom_manager/web/frontend.py`, `config.toml`

### Diseño propuesto

La estructura respeta el formato de **EmulationStation / ES-DE** (gamelist.xml en cada carpeta de plataforma) y hace que los saves sean **planos y centralizados** para que el sync funcione sin fricción.

```
E:\Carpetas anbernic\          ← library_root (PC)
│
├── psx\                       ← ROMs: .chd, .m3u
│   ├── gamelist.xml           ← metadatos ES (generados por el scraper)
│   ├── media\
│   │   ├── images\            ← carátulas (mismo nombre que el ROM)
│   │   └── videos\            ← vídeos de gameplay
│   └── <archivos .chd / .m3u>
│
├── snes\
├── gba\
├── gbc\
├── gb\
├── megadrive\
├── n64\
├── nds\
├── psp\
├── ps2\
├── gamecube\
├── wii\
├── dreamcast\
├── saturn\
├── nes\
│
├── saves\                     ← TODOS los saves de RetroArch (planos, sin subcarpetas)
│   └── Metroid Fusion (USA).srm
│
├── bios\                      ← BIOS (scph1001.bin, etc.) — nunca sincronizadas
│
└── inbox\                     ← Pilar 2: ZIPs nuevos sin organizar
```

**Anbernic (Android)** respeta la misma estructura relativa:
```
/storage/emulated/0/ROMs/      ← mismo árbol psx/ gba/ etc.
/storage/emulated/0/RetroArch/saves/   ← saves de RetroArch (ya plano por defecto)
/storage/emulated/0/BIOS/
```

**¿Por qué esta estructura funciona para el sync?**
- Los saves de RetroArch quedan en `saves/` (PC) y `RetroArch/saves/` (Anbernic) — ambos **planos por nombre de archivo** → el cloud sync los empareja perfectamente.
- El resto de emuladores (DuckStation, PCSX2, PPSSPP, Dolphin) ya tienen sus carpetas propias en `config.toml` → no interfieren.
- Los ROMs están separados de los saves → `rglob` de saves nunca captura ROMs accidentalmente.
- EmulationStation lee `gamelist.xml` en cada subcarpeta de plataforma → el scraper ya genera estos archivos.

### Tareas de implementación

| ID | Fix | Archivos | Prioridad | Estado |
|----|-----|----------|-----------|--------|
| STRUCT-1 | **Botón "Crear estructura"** en Herramientas → crea todas las carpetas de plataforma + `saves/` + `bios/` + `inbox/` + `media/images/` y `media/videos/` en cada una | `server.py` (endpoint `/api/create-library-structure`), `frontend.py` | Alta | ✅ `POST /api/create-library-structure` + panel "Estructura de biblioteca" en Tools |
| STRUCT-2 | **Herramienta "Organizar biblioteca"** → lee los ROMs ya escaneados en la BD, los mueve a `<library_root>/<platform>/<archivo>`, mueve los saves asociados a `<library_root>/saves/`, actualiza `source_path` en la BD | `server.py` | Alta | ✅ `POST /api/organize-library` con dry_run preview + apply; 33 plataformas mapeadas a carpetas ES-DE |
| STRUCT-3 | **Actualizar `config.toml`**: fuente sync RetroArch cambia de `local_dir = E:\Carpetas anbernic` a `local_dir = E:\Carpetas anbernic\saves` una vez que los saves estén centralizados | `config.toml` | Media | ⏳ Pendiente — hacer después de ejecutar "Organizar biblioteca" y configurar RetroArch PC |
| STRUCT-4 | **Configurar RetroArch PC**: en Settings → Saving → Savefile Directory apuntar a `E:\Carpetas anbernic\saves\` (instrucción de usuario, no código) | — | Media | ⏳ |
| STRUCT-5 | **`gamelist.xml` por plataforma**: el botón de exportar gamelists ya existe; asegurarse de que se exporta dentro de cada carpeta de plataforma (`<library_root>/<platform>/gamelist.xml`) | `scraper/gamelist_writer.py`, `server.py` | Baja | ⏳ |

---

## Resumen Día 12

| Bloque | Total | ✅ Hecho | ⏳ Pendiente |
|--------|-------|----------|-------------|
| E — RA filtro | 2 | 2 | 0 |
| F — Duplicados fix | 2 | 2 | 0 |
| G — Estructura carpetas | 5 | 2 | 3 (STRUCT-3, STRUCT-4 usuario, STRUCT-5) |
| **Total nuevos** | **9** | **6** | **3** |

**Commits:**
- `625fa82` — fix(día11): db indexes, deprecated columns, f-string SQL, UI translations, CLI rename
- `7aafdf1` — feat(sync): multi-source cloud sync for multiple emulators
- `496ee65` — feat: RA platform filter, fix duplicate deletion, library folder structure