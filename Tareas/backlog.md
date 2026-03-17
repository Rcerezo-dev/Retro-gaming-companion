# Backlog activo — Retro Vault

> Archivo vivo. Actualizar en cada sesión.
> Última actualización: 2026-03-18 (Día 15)
> Roadmap detallado de mañana: `Tareas/Día15-Roadmap-S24-S26.md`
> Histórico: `Tareas/diario/`

---

## 🔴 Pendiente — Validación en hardware (requiere consola o SD)

| ID | Tarea | Notas |
|----|-------|-------|
| V1 | **Sync automático con SD card** | Configurar `anbernic_root` → insertar SD → verificar banner y log |
| V2 | **Migración a dos bases de datos** | Settings → "Migrar BD" → verificar conteos separados PC/Android |
| V3 | **Inbox end-to-end** ⭐ | Configurar `inbox_path` → soltar ZIP → verificar extracción + renombrado + movimiento |
| V4 | **RetroAchievements con API key real** | retroachievements.org → Settings → Web API Key → pegar en Ajustes |
| V5 | **Guía Termux en la consola** | Seguir `docs/guia-consola-android.md` — prerequisito para WiFi sync directo |
| B1-hw | **Renombrador Android no reduce la cola** | Con SD insertada → Organizar → filtrar consola → aplicar → ver errores |

---

## 🔴 Pendiente — Acciones del usuario (sin código)

| ID | Tarea | Notas |
|----|-------|-------|
| STRUCT-4 | **Configurar RetroArch PC** → Saving → Savefile Directory → `E:\Carpetas anbernic\saves\` | Prerequisito de STRUCT-3 |
| STRUCT-3 | **Actualizar config.toml** → `local_dir = "E:\\Carpetas anbernic\\saves"` | Hacer después de STRUCT-4 |
| ES-1 | **Descargar core genesis_plus_gx** en RetroArch → Online Updater → Core Updater | Necesario para Master System y Game Gear en EmulationStation |
| ES-2 | **Configurar Citra (3DS)** en EmulationStation | Indicar ruta completa en `es_systems.cfg` si no funciona |

---

## 🟡 Próximas sesiones de desarrollo

Ver detalle completo en `Tareas/Día15-Roadmap-S24-S26.md`.

| Sesión | Foco | Estado |
|--------|------|--------|
| 22 | Wizard de primer arranque | ✅ Hecho |
| 23 | DATs sin esfuerzo + Sync wizard rclone | ✅ Hecho |
| 24 | UX y pulido (shortcuts, estados vacíos, feedback inline) | ⏳ |
| 25 | Auth (PIN + QR de acceso LAN) | ⏳ |
| 26 | Distribución (PyInstaller + instalador + tray icon) | ⏳ |
| — | Backup de saves versionado | ⏳ nueva |
| — | Editor de metadatos inline | ⏳ nueva |
| — | "Missing in action" — colección vs DAT | ⏳ nueva |
| — | Timeline de operaciones (historial) | ⏳ nueva |

---

## ✅ Implementado (referencia rápida)

| Feature | Sesión | Nota |
|---------|--------|------|
| **Wizard de primer arranque** | S22 | `GET /api/wizard-detect`; autodetecta RetroArch + ADB; branding Retro Vault |
| **DATs sin esfuerzo** | S23 | `GET /api/catalog-status` + `POST /api/import-dats`; panel en Settings |
| **Sync wizard rclone** | S23 | `GET /api/rclone-status`; panel colapsable Sync con remotes dropdown |
| **Partir frontend.py** | S21 | CSS → `static/app.css`; JS → `static/app.js`; frontend.py 5891→1433 líneas |
| **Tests repository.py** | S20 | 20 tests con BD real en tmp_path |
| **Partir server.py** | S18-19 | `response_builders.py` + `cable_sync_daemon.py` + `inbox_pipeline.py` |
| **Batch run completo** | S15 | Scan → Match → ZIP → CHD → Health → RA en un clic |
| **Comparador PC vs Android** | S16 | `GET /api/library-diff` diff por SHA1 |
| **Rutas persisten** | S15 | `saveOvPaths()` guarda en `config.toml` |
| Cable Sync (ADB + SD) | Día 5 | PC↔Android vía ADB o sistema de archivos |
| Cloud Sync multi-fuente | Día 7 | Dropbox/OneDrive/GDrive; múltiples emuladores |
| Tracker de partidas | Día 10 | `last_played_at` + sección "Últimas partidas" |
| Estado de completado | Día 10 | `play_status` en BD + dropdown + filtro |
| Grid view con carátulas | Día 12 | Toggle tabla/mosaico; persistido en localStorage |
| Estructura ES-DE | Día 11-14 | Crear carpetas + organizar ROMs/saves/BIOS |
| Validación de config | S17 | `AppConfig.validate()` + warnings en Settings |
| Scanner incremental | Día 5 | mtime + `prune_stale_entries` |
| Renombrador atómico | Día 3 | `rename_rom_with_saves()` con rollback |
| CHD converter | Día 3 | cue→chd vía chdman |
| Scraper + gamelists | Día 8-9 | ScreenScraper + gamelist.xml ES-DE + Pegasus |
| RetroAchievements | Día 4 | Cross-ref MD5 + caché 1 semana |
| Duplicados (fix) | Día 11 | Rutas normalizadas; UI recarga tras borrar |
| UI/UX español | Día 11-12 | Traducción completa; device name genérico; errores accionables |
