# Retro Vault — Roadmap post-Día 18

> Creado: 2026-03-22 · Última actualización: 2026-03-24 (Día 20)
> Estado de partida: Tiers 1–4 completados. UI-1 y UI-3 completados en Día 18.
> Día 19: S40 (Android setup), S39-3 (tray icon), S39-4 (autostart toggle) completados.
> Día 20: QoL-IA (botón Internet Archive en ROMs faltantes) completado.
> Todo lo completado antes de Día 18 está en `Tareas/Roadmap-S28-Plus.md` (histórico).

---

## Estado actual resumido

| Capa | Estado |
|------|--------|
| Núcleo (scan, match, rename, CHD, ZIP) | ✅ completo |
| Sync cloud (rclone, multi-fuente, backoff, delta cache) | ✅ completo |
| Sync cable (ADB, SD card) | ✅ completo |
| Scraper + gamelists ES-DE | ✅ completo |
| RetroAchievements | ✅ código listo — ⚠ sin probar con key real |
| Automatización (health check, notificaciones, CLI headless) | ✅ completo |
| API REST OpenAPI 3.0 | ✅ completo (121 endpoints) |
| UI visual (cyberpunk, modo claro/oscuro, TV mode) | ✅ completo |
| UI layout (sidebar, cards mejoradas) | ✅ completo (Día 18) |
| Portabilidad / distribución | ✅ completo — tray icon ✅, PyInstaller ✅ |
| Validación en hardware | ⚠ pendiente |

---

## Tier 5 — Portabilidad y distribución

> Objetivo: que se pueda usar sin instalar Conda ni Python. Distribución como carpeta portable o instalador.

### ✅ S39-1 — Empaquetado con PyInstaller
- `pyinstaller --onedir` en el entorno Conda
- Incluir `tools/chdman.exe`, `tools/adb.exe`, `tools/rclone.exe`
- Incluir `src/rom_manager/web/static/` como `datas`
- Verificar que `tomllib`, `sqlite3`, `http.server` no dan problemas en el bundle
- Script `build.ps1` que genera `dist/RetroVault/`

### S39-2 — Instalador NSIS (opcional, si S39-1 funciona bien)
- Instalar en `%LOCALAPPDATA%\RetroVault\`
- Shortcut en escritorio + menú inicio
- Desinstalador limpio

### ✅ S39-3 — Tray icon (systray)
- `utils/tray_icon.py` — Win32 puro con `ctypes`, sin dependencias externas
- Menú: Abrir Retro Vault · Sync ahora · Inicio automático toggle · Salir
- Toast de bienvenida 1.5s tras registrar el icono; doble clic → abre el navegador
- `rommgr serve --tray` activa el icono

### ✅ S39-4 — Auto-start mejorado
- `/api/autostart-status` + `/api/autostart-toggle` (registro HKCU\...\Run)
- Panel dinámico en Settings: badge de estado + botón toggle con un clic

---

## Tier 6 — Rediseño UI (prioridad media-alta)

> El problema real: ~700 estilos inline en `frontend.py` pelean con las variables CSS.
> La solución no es más CSS encima — es refactorizar la estructura HTML.

### ✅ UI-1 — Sidebar + área de contenido (layout principal)
- ~~Reemplazar las 10 tabs horizontales por una **sidebar izquierda** con iconos + labels~~
- Implementado: sidebar colapsable con 5 grupos, iconos + labels, estado en localStorage
- `toggleSidebar()` en app.js, `.nav-item.active` reemplaza `nav button.active`

### UI-2 — Dashboard de inicio
- Pantalla de bienvenida con:
  - Stats clave: N juegos · N plataformas · último sync hace X
  - "Juego del día" visible desde home
  - Acciones rápidas: Sync ahora · Scan · Inbox (si hay archivos pendientes)
  - Indicador salud: X ROMs OK · Y problemas detectados
- Sustituye al "Overview" actual que es solo resultados del scanner

### ✅ UI-3 — Cards de juegos mejoradas
- ~~Portada más grande (sin texto encima de la imagen)~~
- Implementado: proporción 2:3, badge `play_status` superpuesto (▶ ✅ 💯 ⏸), estrella favoritos
- Título 12px semibold, hover sube 3px + glow neón

### UI-4 — Modal/página de detalle de juego
- Click en una card → modal con:
  - Portada grande
  - Metadatos completos (región, año, desarrollador, descripción)
  - Estado de saves (cuántos, última sync, backup disponible)
  - Logros RA (cuántos, enlace a retroachievements.org)
  - Notas del usuario
  - Botones: Editar metadata · Ver backups · Abrir carpeta

### UI-5 — Refactorizar inline styles a clases CSS
- Los ~700 `style="..."` en `frontend.py` son el origen de la inconsistencia visual
- Migrar a clases: `.panel-label`, `.stat-value`, `.actions-row`, `.hint`, etc.
- El CSS resultante es mantenible y el tema claro/oscuro funciona sin `!important`
- Tarea mecánica pero de alto impacto visual

### UI-6 — Empty states útiles
- Cuando no hay ROMs escaneadas → "Configura tu biblioteca en Ajustes → escanea"
- Cuando no hay sync configurado → paso a paso visual del wizard
- Cuando no hay portadas → placeholder con icono de plataforma + "Scraper disponible"

### UI-7 — Teclado + accesibilidad
- Shortcuts globales: `S` = sync, `F` = buscar, `T` = TV mode, `G` = grid/lista
- Navegación con Tab/Enter en modales
- `aria-label` en botones de icono

---

## Tier 7 — Features de calidad de vida

### ✅ QoL-IA — Botón "Link Internet Archive" en lista de ROMs faltantes
- Nueva columna "Internet Archive" en la tabla de ROMs faltantes (Colección)
- Botón `🔗 Link IA` por fila: copia URL `https://archive.org/search?query=...`
- Compatible con el monitor de portapapeles de JDownloader → añade descarga automáticamente
- Toast: "Link copiado — pégalo en JDownloader"

### QoL-1 — Quick scan en backend ⚠ (pendiente desde Fase 9)
- El modo rápido ya está en la UI pero `rom_scanner.py` no lo implementa
- Quick scan: solo hashear archivos cuyo mtime cambió desde el último scan
- Reduce de minutos a segundos en bibliotecas grandes ya indexadas

### QoL-2 — Notificaciones inbox
- Cuando `inbox_pipeline` procesa archivos exitosamente → toast + notificación desktop
- "3 juegos nuevos añadidos: Mario Kart (GBA), Zelda (SNES), Metroid (GBA)"

### QoL-3 — Historial de sync visual
- El historial existe como tabla plana; hacerlo visual
- Timeline con iconos (↑↓⚠) agrupado por día
- Filtro por dirección y por plataforma

### QoL-4 — Platform health dashboard
- Vista por plataforma mostrando:
  - ROMs escaneadas vs en DAT (% completitud colección)
  - ROMs con portada vs sin portada
  - ROMs con logros RA vs sin logros
  - Último sync de esa plataforma
- Identificar de un vistazo qué plataformas necesitan atención

### QoL-5 — Bulk metadata editor
- Seleccionar múltiples juegos y editar en batch: plataforma, estado, tags
- Útil para corregir clasificaciones erróneas tras un scan

### QoL-6 — Auto-detect rclone/ADB/chdman
- Al arrancar, comprobar si rclone/adb/chdman están en PATH o en `tools/`
- Si no están, mostrar aviso con enlace de descarga en Settings
- Actualmente el error solo aparece cuando intentas usarlos

### QoL-7 — Export RetroArch playlists (.lpl)
- Complemento al gamelist.xml: exportar `.lpl` para usar directamente en RetroArch
- Formato JSON estándar de RetroArch
- Útil para usuarios que no usan ES-DE pero sí RetroArch standalone

### QoL-11 — Backup automático pre-sync
- Antes de cualquier sync (cloud o cable), hacer snapshot versionado local automático
- Integra con el sistema de backup versionado (S29) ya existente
- Config: `[sync] pre_sync_backup = true` (default true)

### QoL-12 — Exportar colección completa
- Botón "Exportar biblioteca" → genera `.json` o `.csv`
- Campos: título, plataforma, SHA1, play_status, playtime, última partida
- Útil para backups externos o importar en otra instalación de Retro Vault

### QoL-13 — Indicador de estado en tray icon
- El icono cambia de color según el estado del sistema
- Gris = idle · Verde = sync en curso · Amarillo = conflictos pendientes · Rojo = error
- Usar `set_status()` ya disponible en `TrayIcon` para disparar el cambio

### QoL-14 — Modo offline explícito en dashboard
- Si rclone/ADB no están disponibles, mostrar badges "Sin conexión" en los paneles afectados
- En lugar de dejar que las funciones fallen silenciosamente cuando el usuario las intenta usar

### QoL-8 — Webhook / script post-sync
- Campo en Settings: "Ejecutar script tras sync exitoso"
- Útil para sincronizar con otros servicios, notificar a Discord, etc.
- `subprocess.Popen(user_script)` con timeout

### QoL-9 — Detección de consola en red (ADB over WiFi)
- Escanear LAN en busca del dispositivo Android via ADB WiFi
- Si se detecta → ofrecer sync directo sin cable ni SD
- `adb connect <ip>:5555`

### QoL-10 — Save diff viewer
- En la sección de backups, mostrar qué versión es más reciente y cuánto difiere (en bytes)
- Comparar tamaños y fechas de los N backups guardados
- Botón "Restaurar esta versión" con confirmación

---

## Tier 8 — Mejoras técnicas / deuda

### TEC-1 — Dividir frontend.py
- Actualmente ~2000+ líneas como cadena Python
- Dividir en `_render_tab_games()`, `_render_tab_sync()`, etc. en `frontend.py`
- O bien plantillas Jinja2 (pero añade dependencia) → preferible funciones Python puras

### TEC-6 — Test de integración E2E post-Día 18-19
- Ejecutar el agente `integration-tester` para verificar que el pipeline completo funciona
- Comprobar: scan → match → rename → inbox → sync → report
- Prioritario antes de añadir más features encima de los cambios recientes

### TEC-2 — Tests para módulos Día 18
- `test_delta_cache.py` — ya probado manualmente; formalizar como pytest
- `test_notifier.py` — mock `subprocess.Popen`, verificar args PowerShell
- `test_cli_headless.py` — `rommgr sync --apply`, `rommgr health` con biblioteca de prueba

### TEC-3 — Rate limiting y seguridad web
- Limitar peticiones a `/api/` a N/segundo por IP (protección básica en LAN)
- Cabeceras de seguridad: `X-Frame-Options`, `X-Content-Type-Options`
- Sanitización más robusta en rutas de archivo recibidas por la API

### TEC-4 — HTTPS para acceso LAN seguro
- Certificado autofirmado generado al primer arranque (`ssl.SSLContext`)
- Permite acceder desde móvil sin advertencias si se acepta el certificado
- Config: `[web] https = true`

### TEC-5 — Logging estructurado
- Logs actuales son texto plano; añadir rotación (`logging.handlers.RotatingFileHandler`)
- Endpoint `/api/logs` para ver las últimas N líneas desde la UI
- Nivel de log configurable en Settings

---

## Pendientes de validación en hardware

> Estas tareas requieren la consola física o una tarjeta SD real. No hay código que escribir.

| ID | Qué validar | Prerrequisito |
|----|-------------|---------------|
| HW-1 | Wrappers `.bat` en ES-DE (exit codes correctos) | ES-DE instalado en PC |
| HW-2 | Subcarpetas PSX en ES-DE (gamelist con rutas relativas) | Tener ISOs PSX |
| HW-3 | ADB cable sync PC↔Android | Cable USB + ADB drivers |
| HW-4 | RetroAchievements con API key real | Cuenta en retroachievements.org |
| HW-5 | Guía Termux en la Anbernic (sync WiFi directo) | Anbernic + WiFi + guía `Tareas/Guia-Termux-Anbernic.md` |
| HW-6 | `rommgr sync` desde Task Scheduler de Windows | Windows Task Scheduler configurado |

---

## Orden de implementación recomendado

```
Día 18:  UI-1 ✅ UI-3 ✅           → sidebar + cards mejoradas
Día 19:  S40 ✅ S39-3 ✅ S39-4 ✅   → Android setup + tray icon + autostart toggle
Día 20:  QoL-IA ✅ + S39-1 + UI-2 + UI-4   → Link IA + PyInstaller + dashboard + modal detalle
Día 21:  UI-5                      → refactorizar inline styles a clases CSS
Día 22:  QoL-1 + QoL-4            → quick scan + platform health
Día 23:  QoL-3 + QoL-10           → historial visual + save diff
Día 24:  QoL-11 + QoL-12          → backup pre-sync + exportar colección
Día 25+: TEC-1, TEC-2, TEC-6, resto QoL según uso real
```

> Regla fija: la validación en hardware (HW-1..HW-6) se puede hacer en cualquier momento
> en paralelo con el desarrollo — no bloquea ningún tier.
