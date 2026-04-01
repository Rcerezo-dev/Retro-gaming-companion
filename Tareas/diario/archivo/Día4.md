# ROM Manager Local — Día 4

## Contexto

Al cierre del Día 3-2 teníamos el frontend web completo con las operaciones básicas
(scan, match, plan, apply, sync, scraper, duplicados, settings). Esta sesión se centró
en pulir la experiencia del usuario y añadir herramientas de mantenimiento de biblioteca
y la integración con RetroAchievements.

---

## Objetivos del día

1. Corregir problemas detectados en pruebas del frontend (label, conflictos, credenciales)
2. Añadir herramientas de biblioteca: ZIP, M3U, multi-disco, huérfanos, health check
3. Integrar RetroAchievements para detectar ROMs sin soporte de logros

---

## Trabajo realizado

### Correcciones de bugs

| Bug | Causa raíz | Solución |
|-----|-----------|----------|
| Label "Saltados" confuso | Texto ambiguo | Renombrado a "Ya escaneados" |
| 1851 falsos conflictos en Plan | `target.exists()` devuelve `True` en Windows para renames de solo mayúsculas (NTFS insensible) | `_same_file()` usando `Path.samefile()` en `operation_planner.py` |
| Credenciales ScreenScraper no aplicaban sin reiniciar | Config cargada solo al arrancar el servidor | `_handle_save_config()` recarga el objeto en memoria tras escribir config.toml |
| ScreenScraper HTTP 403 | Parámetros vacíos `devid=""` enviados en la URL | Solo añadir esos parámetros cuando no estén vacíos |
| Carpeta de disco `3do` aparecía vacía en `/api/disc-folders` | Detección solo miraba el nombre de la carpeta | Verifica que la carpeta contenga archivos de disco reales antes de incluirla |

### Nuevos archivos Python

| Archivo | Propósito |
|---------|-----------|
| `src/rom_manager/renamer/file_renamer.py` | Rename atómico ROM+saves con rollback completo ante cualquier fallo |
| `src/rom_manager/converters/zip_extractor.py` | Extracción de ZIPs; omite archivos con .cue/.bin/.iso (flujo CHD) |
| `src/rom_manager/utils/m3u_generator.py` | Genera playlists .m3u agrupando archivos con `(Disc 1)`, `(Disc 2)`… |
| `src/rom_manager/utils/multidisc_verifier.py` | Verifica sets multi-disco: números consecutivos, extensión uniforme, archivos presentes |
| `src/rom_manager/utils/orphan_finder.py` | Detecta saves sin ROM asociada (mismo stem, extensión distinta) |
| `src/rom_manager/utils/health_checker.py` | Re-hashea todos los ROMs y compara con SHA1 almacenado; reporta corruptos/faltantes |
| `src/rom_manager/retroachievements/__init__.py` | Paquete RetroAchievements |
| `src/rom_manager/retroachievements/ra_platform_ids.py` | Mapeo plataforma → RA console ID (~30 plataformas) |
| `src/rom_manager/retroachievements/ra_client.py` | Cliente HTTP para API_GetGameList.php (h=1, f=1); caché en disco 1 semana |
| `src/rom_manager/retroachievements/ra_checker.py` | Cruza MD5s de la biblioteca contra RA; busca alternativas por título normalizado |

### Cambios en archivos existentes

**`src/rom_manager/planner/operation_planner.py`**
- `_same_file(a, b)` con `Path.samefile()` para detectar renames de solo mayúsculas
- Conflictos solo se generan si el destino existe Y no es el mismo archivo físico

**`src/rom_manager/config.py`**
- Nuevo campo `ra_api_key: str` cargado desde `[retroachievements] api_key`

**`src/rom_manager/web/server.py`**
- 4 nuevos jobs: `extract_zip`, `health_check`, `ra_check` + sus progress dicts
- 15+ nuevos endpoints POST/GET
- `_count_companion_saves()` para preview del plan
- `_handle_ra_check()`: job en background, caché RA, CSV de alternativas
- `GET /api/ra-check.csv`: descarga del CSV si hay alternativas
- `_build_config()` incluye `ra_api_key`
- `_handle_save_config()` acepta `retroachievements.api_key` y recarga en memoria

**`src/rom_manager/web/frontend.py`**
- Banner de preview en Plan con total de ROMs + saves afectados
- Colums "Saves" en tabla del plan
- Botón "Eliminar todos los duplicados" + ordenación por tamaño desc
- Explicación de Unknown en tab Assets
- Progress bar CHD, scraping, ZIP, health check, RetroAchievements
- 5 nuevos paneles en Tools: ZIP, M3U, multi-disco, huérfanos, health check
- Botones de limpieza: eliminar .zip y eliminar .cue/.bin originales
- Tab Settings: campo chdman + botón Probar, campo RA API key
- Panel RetroAchievements en Tools: badge con resultado, tabla de alternativas, enlace CSV
- Multi-folder scan (textarea en Overview)
- `loadTools()` auto-rellena rutas desde config + disc-folders

**`config.toml`**
- Añadido `[tools] chdman = "tools/chdman.exe"`
- `tools/chdman.exe` movido desde raíz del proyecto

**`.gitignore`**
- Añadido `tools/*.exe`

---

## Archivos modificados (lista completa)

```
src/rom_manager/planner/operation_planner.py        MODIFICADO
src/rom_manager/renamer/file_renamer.py              NUEVO
src/rom_manager/converters/zip_extractor.py          NUEVO
src/rom_manager/utils/m3u_generator.py               NUEVO
src/rom_manager/utils/multidisc_verifier.py          NUEVO
src/rom_manager/utils/orphan_finder.py               NUEVO
src/rom_manager/utils/health_checker.py              NUEVO
src/rom_manager/retroachievements/__init__.py        NUEVO
src/rom_manager/retroachievements/ra_platform_ids.py NUEVO
src/rom_manager/retroachievements/ra_client.py       NUEVO
src/rom_manager/retroachievements/ra_checker.py      NUEVO
src/rom_manager/config.py                            MODIFICADO
src/rom_manager/web/server.py                        MODIFICADO
src/rom_manager/web/frontend.py                      MODIFICADO
config.toml                                          MODIFICADO
tools/chdman.exe                                     MOVIDO (desde raíz)
.gitignore                                           MODIFICADO
```

---

## Estado al finalizar

- Todas las fases del proyecto marcadas como completas en MEMORY.md
- El servidor arranca y pasa pruebas de importación
- RetroAchievements integrado pero **no probado en producción** (requiere API key real)
- Tests de pytest no verificados en esta sesión (posible deuda técnica por cambios en planner)

---

## Siguiente sesión recomendada

Ver `Tareas/Siguientes-pasos.md` para la lista priorizada.
