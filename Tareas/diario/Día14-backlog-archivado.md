# Backlog activo — Retro Vault

> Archivo vivo. Actualizar en cada sesión. La información histórica está en `Tareas/diario/`.
> Última actualización: 2026-03-17 (Día 14)
> Roadmap completo por sesiones: `Tareas/Día14-Roadmap-App-Universal.md`

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
| ES-2 | **Configurar Citra (3DS)** en EmulationStation — la ruta actual `citra` asume que está en PATH | Indicar ruta completa en `es_systems.cfg` si no funciona |

---

## 🟡 Próximas sesiones de desarrollo

Ver detalle completo en `Tareas/Día14-Roadmap-App-Universal.md`.

| Sesión | Foco | Estado |
|--------|------|--------|
| 15 | Persistencia rutas + batch run completo | ✅ Hecho |
| 16 | Comparador de bibliotecas PC vs Android (B3) | ✅ Hecho |
| 17 | JobRunner (eliminar código duplicado) + validación config | ✅ Hecho |
| 18-19 | Partir server.py en módulos | ✅ Hecho |
| 20 | Tests para repository.py | ✅ Hecho |
| 21 | Partir frontend.py (CSS/JS a archivos externos) | ✅ Hecho |
| 22 | Wizard de primer arranque | ✅ Hecho |
| 23 | DATs sin esfuerzo + Sync wizard | ✅ Hecho |
| 24 | UX y pulido | ⏳ |
| 25 | Auth (PIN + QR) + skills/agentes Claude | ⏳ |
| 26 | Distribución (PyInstaller + instalador) | ⏳ |

---

## 🟢 Ideas a largo plazo (sin fecha)

- **Soporte `.rvz` / `.nkit.iso`** — GameCube/Wii comprimidos con `dolphin-tool`
- **Delta sync** — solo transferir bytes que cambiaron (saves de PSX/N64)
- **"Missing in action"** — cruzar colección con DAT completo → lista de juegos que no tienes
- **Plugin de plataforma** (`platforms.toml`) — definiciones de plataforma en archivo externo
- **Modo headless / CLI completo** — todo desde terminal sin abrir la web
- **Nombre definitivo** — Retro Vault o Retro Companion

---

## ✅ Implementado (referencia rápida)

| Feature | Sesión / Día | Nota |
|---------|-------------|------|
| **Validación de config** | Día 14 / S17 | `AppConfig.validate()` + warnings en Settings (rutas, credenciales) |
| **Helper `_start_job`** | Día 14 / S17 | Patrón JobRunner aplicado a `match` y `health_check` |
| **Comparador de bibliotecas PC vs Android** | Día 14 / S16 | `GET /api/library-diff` diff por SHA1 + sección en pestaña Sync |
| **Rutas persisten entre sesiones** | Día 14 / S15 | `saveOvPaths()` ahora guarda en `config.toml`, no solo localStorage |
| **Partir server.py (S19)** | S18-19 | Daemons → `cable_sync_daemon.py` + `inbox_pipeline.py`; server.py 5080→2916 líneas |
| **Tests repository.py** | S20 | 20 tests, BD real en tmp_path; cubre upsert, match, duplicados, prune, rollback |
| **Partir frontend.py (S21)** | S21 | CSS → `static/app.css` (13 KB), JS → `static/app.js` (222 KB); frontend.py 5891→1433 líneas |
| **Batch run completo (6 tools)** | Día 14 / S15 | Scan → Match → ZIP → CHD → Health → RA en un clic |
| **Saves separados por plataforma** | Día 14 | `saves/{platform}/` y `states/{platform}/` — nunca se mezclan consolas |
| **Tool de estructura completa** | Día 14 | Crea saves/, states/, screenshots/ + subcarpetas por plataforma de una pasada |
| **EmulationStation configurado** | Día 14 | `es_systems.cfg` con rutas correctas, cores reales, `</systemList>` al final |
| **Arcade en la app** | Día 14 | `arcade` añadido a `_ES_PLATFORM_FOLDERS` y `_STANDARD_PLATFORM_FOLDERS` |
| F2 Tracker de tiempo de juego | Día 10 | `last_played_at` en BD + sección "Últimas partidas" en Overview |
| F3 Estado de completado | Día 10 | `play_status` en BD + dropdown por fila + filtro |
| F4 Carátulas en lista Games | Día 10 | Endpoint `/api/asset-image` + thumbnail en tabla |
| F5 Grid view con carátulas | Día 12 | Toggle ☰/⊞ en Games, persistido en localStorage |
| F6 Dashboard por plataformas | Día 10 | `/api/platform-stats` + barras CSS en Overview |
| F10 Acceso desde consola Android | Día 10 | Selector `web_host` en Settings (`0.0.0.0`) |
| F12 Exportador Pegasus | Día 10 | `scraper/pegasus_writer.py` + botón en Tools |
| STRUCT-1/2/6 Estructura ES-DE | Día 11-14 | Crear carpetas + organizar ROMs/saves/BIOS |
| Cable Sync (ADB + SD) | Día 5 | PC↔Android vía ADB o sistema de archivos |
| Cloud Sync multi-fuente | Día 7 | Dropbox/OneDrive/GDrive; múltiples emuladores |
| **Wizard de primer arranque (S22)** | S22 | `GET /api/wizard-detect` auto-detecta RetroArch + ADB; branding "Retro Vault" en wizard |
| **DATs sin esfuerzo (S23)** | S23 | `GET /api/catalog-status` + `POST /api/import-dats`; panel en Settings con estado y botón importar |
| **Sync wizard rclone (S23)** | S23 | `GET /api/rclone-status`; panel colapsable en Sync: estado, remotes dropdown, guardar config |
| UI/UX | Día 11-12 | Traducción completa español, device name genérico, errores con guía |
| DB fixes | Día 11-12 | Índices, safe ALTER TABLE, f-strings SQL eliminados |
| RA filtro de plataforma | Día 11 | Dropdown en informe RetroAchievements |
| Duplicados fix | Día 11 | Rutas normalizadas, BD consistente, UI recarga tras borrar |
| docs/architecture.md | Día 13-14 | Estructura completa + integración ES documentada |
