# Retro Vault — Contexto del proyecto

> Se carga automáticamente en cada conversación.
> Arquitectura detallada en `docs/architecture.md`. Backlog activo en `Tareas/backlog.md`.

---

## Qué es este proyecto

Herramienta local Python + interfaz web (`http://127.0.0.1:7777`) para gestionar una colección de ROMs retro y sincronizar saves entre PC y consola Android.

**Los tres pilares reales:**
1. **Primera vez** — limpiar el caos: ZIPs, nombres incorrectos, duplicados, BIOS dispersas
2. **Inbox** — soltar juegos nuevos y que se organicen solos en la carpeta correcta
3. **Sync de saves** — jugar en PC o consola sin perder progreso (el valor diferencial)

---

## Estado actual (Día 15 — 2026-03-18)

| Módulo | Estado | Notas |
|--------|--------|-------|
| Scanner | ✅ | Incremental (mtime), quick mode, stale pruning |
| Catálogo DAT | ✅ | No-Intro y Redump XML Logiqx; match SHA1; importador desde cualquier carpeta |
| Renombrador | ✅ | Atómico con rollback, mueve saves junto al ROM |
| Conversión CHD | ✅ | chdman en `tools/chdman.exe` (v0.286) |
| Extractor ZIP + Inbox | ✅ | Pipeline completo; pendiente de prueba en hardware |
| Generador M3U | ✅ | Multi-disco PSX/Saturn |
| Duplicados | ✅ | Por SHA1; excluye copias PC↔Android intencionales |
| Scraper | ✅ | ScreenScraper (CRC/MD5/SHA1 + fallback nombre) |
| Gamelists | ✅ | gamelist.xml ES-DE + exportador Pegasus |
| RetroAchievements | ✅ | Cross-reference MD5; caché 1 semana |
| Cable Sync | ✅ | PC↔Android vía ADB o sistema de archivos |
| Cloud Sync (rclone) | ✅ | Dropbox/OneDrive/GDrive; multi-fuente; wizard de setup |
| Tracker de partidas | ✅ | `last_played_at` en BD; sección "Últimas partidas" |
| Estado de completado | ✅ | `play_status` en BD; dropdown + filtro |
| Grid view | ✅ | Toggle tabla/mosaico con carátulas |
| Estructura ES-DE | ✅ | Crear carpetas + organizar ROMs/saves/BIOS |
| Wizard primer arranque | ✅ | Autodetecta RetroArch + ADB; `GET /api/wizard-detect` |
| Tests | ✅ | 8 archivos de test; BD real en tmp_path (no mocks) |
| Interfaz web | ✅ | SPA stdlib Python; CSS/JS en static/; sin dependencias externas |

**Pendientes de validar en hardware:** V1-V5, B1, STRUCT-3/4 — ver `Tareas/backlog.md`.
**Completadas:** S24 (UX) ✅ S25 (Auth PIN) ✅ S26 (ScreenScraper dev) ✅ S27 (Rediseño visual) ✅ S28 (búsqueda+lanzador+favoritos+tags) ✅ S29 (backup saves versionado) ✅ S30 (editor metadatos + notas) ✅
**Próximas sesiones:** S31 (colección completa: missing+estadísticas) — ver `Tareas/Roadmap-S28-Plus.md`.

---

## Entorno de ejecución

- Conda: `C:\Users\rammu\anaconda3\envs\rom_manager` (Python 3.12)
- Lanzador: `scripts\rommgr.cmd`
- Directo: `C:\Users\rammu\anaconda3\envs\rom_manager\python.exe -m rom_manager <cmd>`
- `chdman` en `tools/chdman.exe` — NO en PATH
- `adb` en `tools/adb.exe`

---

## Reglas de trabajo (NO cambiar sin discutirlo)

- `rommgr plan` siempre antes de `rommgr apply`
- Nunca eliminar ni sobreescribir sin política de conflictos documentada
- PSX siempre por sets: nunca renombrar `.bin` sin reescribir el `.cue`
- BIOS, assets y carpetas Android nunca se tratan como ROMs
- Toda operación sobre archivos se registra en SQLite
- La biblioteca debe ser compatible con RetroArch en Android Y en PC
- En sync: ante duda, no sobreescribir; guardar backup primero
- Sin dependencias externas de runtime (solo stdlib)

---

## Patrones críticos a recordar

### Jobs en background (web)
```python
# _job_lock, _jobs dict, _xxx_progress dict, _job_results dict
# Frontend: startPolling() cada 2s → /api/job-status → _applyJobStatus(s)
# result_ts en cada resultado para evitar toasts infinitos (_shownResultTs)
```

### Rename atómico
```python
from rom_manager.renamer.file_renamer import rename_rom_with_saves
outcome = rename_rom_with_saves(source_path, target_path, save_extensions)
# outcome.success, outcome.saves_renamed, outcome.error
```

### Fix renames solo-mayúsculas en Windows (NTFS)
```python
# operation_planner.py — _same_file() con Path.samefile()
# Conflicto solo si target.exists() AND NOT _same_file(source, target)
```

### Config recarga en memoria obligatoria tras guardar
```python
# _handle_save_config() DEBE recargar load_config() y actualizar todos los campos
# Sin esto los cambios no se aplican hasta reiniciar el servidor
```

### SQLite
```python
with repository.connect() as conn:  # lecturas
    rows = conn.execute("SELECT ...").fetchall()
# repository.batch() para escrituras en bulk
```

### Módulos externos que necesitan estado de server.py (late import)
```python
# cable_sync_daemon.py e inbox_pipeline.py usan late imports para evitar circular imports:
def _auto_sync_loop(config, get_repo_fn):
    import rom_manager.web.server as _srv   # importar dentro de la función
    # Variables REASIGNADAS → siempre via _srv.xxx
    _srv._auto_sync_status = {"state": "syncing"}
    # Variables MUTADAS (.update, []=) → local binding válido
    _cable_progress = _srv._cable_progress
```

### Static files
```
GET /static/app.css  →  src/rom_manager/web/static/app.css
GET /static/app.js   →  src/rom_manager/web/static/app.js
# Protegido contra path traversal: "/" y "\" rechazados en filename
```

---

## Tu visión

La interfaz tiene que ser preciosa y generar mínima fricción — prestarle atención la primera vez, pero que el sync de saves sea completamente automático después. Tracker de tiempo de juego. Nombre definitivo: **Retro Vault** o **Retro Companion**. Sin referencias a marcas de consola específicas — "consola Android" o nombre configurable por el usuario en Settings. El inbox es clave: soltar juegos en ZIP y que la app los descomprima, identifique plataforma y los coloque en los sitios correctos (PC y consola).
