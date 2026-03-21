# Mejoras pendientes — Retro Vault / Retro Companion

*Última actualización: 2026-03-16 (sesión tarde)*

Recopilación de todo lo que falta por implementar o validar, ordenado por prioridad.

---

## 🔴 Prioridad alta — Validar en hardware real

> Todo el código está escrito. Hay que probarlo con la consola y la SD conectadas para confirmar que funciona end-to-end.

### V1 — Sync automático con tarjeta SD
El daemon detecta inserción de la SD mirando si `anbernic_root` (en Settings) se vuelve accesible. Pasos para validar:
1. Configurar `anbernic_root` → ruta donde monta la SD (p.ej. `E:\Carpetas anbernic`)
2. Insertar la tarjeta → esperar ≤ 8 s → verificar banner "Tarjeta SD detectada"
3. Confirmar que los saves se sincronizan (ver log en `.rommgr/cable_sync_ops.log`)

**Riesgo:** `ab_path.exists()` puede no detectar bien la raíz de la SD en Windows si monta como MTP en lugar de letra de unidad.
**Archivo:** `server.py` → `_sd_card_sync_loop`

### V2 — Migración a dos bases de datos
Al abrir la app por primera vez tras el cambio a `library_pc.db` / `library_android.db`:
1. Settings → botón "Migrar BD a dos DBs"
2. Verificar que los juegos de la consola (rutas fuera de `library_root`) pasan a `library_android.db`
3. Verificar que Overview muestra conteos separados para PC y consola

**Archivo:** `server.py` → `_handle_migrate_split_db`

### V3 — Inbox end-to-end
1. Configurar `inbox_path` en la pestaña Inbox
2. Soltar un ZIP de un juego conocido (p.ej. GBA)
3. "Analizar carpeta" → debe detectar plataforma
4. "Organizar todo" → extraer, escanear, cruzar con DAT, renombrar, mover a la carpeta correcta

### V4 — RetroAchievements con API key real
El código está listo. Solo falta poner la API key real en Settings y comprobar que la tabla de resultados se rellena correctamente.
**Obtener la key:** retroachievements.org → Settings → Web API Key

### V5 — Guía Termux en la consola Android
Ejecutar el proceso descrito en `Tareas/Día6-Guia-Termux.md` en la consola real para habilitar sync vía rclone desde Android.

---

## 🟡 Prioridad media — Bugs conocidos por confirmar

### B1 — Renombrador en consola Android no reduce la cola
**Síntoma:** archivos pendientes de renombrar en la consola que nunca bajan.
**Hipótesis:** la SD estaba desmontada al intentar renombrar, o la ruta en BD no coincide con la ruta actual de la SD.
**Cómo depurar:** con la SD insertada → Organizar → filtrar "Solo Consola Android" → aplicar → ver panel `#apply-error-details`.
**Archivo:** `server.py` → `_handle_apply`

### ~~B2 — `prune_stale_entries` puede borrar datos de la consola~~ ✅ Verificado seguro
La función filtra estrictamente por `source_root` del scan activo. Las dos BDs son independientes; escanear solo el PC no toca `library_android.db`.

### ~~B3 — Resolver conflictos RA sin caché local~~ ✅ Corregido
`POST /api/apply-ra-conflicts` ahora detecta si el caché RA no existe y muestra un mensaje claro: "Sin datos RA en caché — ejecuta primero la comprobación de RetroAchievements".

---

## 🟢 Prioridad baja — Mejoras de UX

### ~~U1 — Botón "Volver a lanzar el asistente" en Settings~~ ✅ Implementado
Panel "Herramientas" añadido en Settings con botón que limpia `wizard_dismissed` y relanza el wizard.

### ~~U2 — Notificación de escritorio al terminar el sync~~ ✅ Implementado
`_sendNotif()` y `_requestNotifPermission()` añadidos. Se disparan en sincronización cloud y Cable Sync al completar.

### U3 — Preview de diferencias antes del Cable Sync
Antes de iniciar la sincronización, mostrar: "X saves en PC · Y saves en consola · Z se copiarán". Requiere un pre-scan rápido por ADB.
**Archivo:** `server.py` → nuevo endpoint `/api/cable-sync-preview`

### ~~U4 — Informe automático post-scan para la consola Android~~ ✅ Implementado
El worker de scan ahora genera el informe cacheado para cada ruta escaneada (PC y Android), usando el repo correcto para cada una.

---

## 🔵 Features nuevas — Roadmap de producto

### ~~F1 — Quick scan (mtime)~~ ✅ Ya estaba implementado
El scanner ya omite el hashing de archivos sin cambios (mtime + size), y el botón Quick en la UI pasa `quick=True` al backend. Completado desde días anteriores.

### ~~F10 — Acceso a la UI desde la consola Android~~ ✅ Implementado
Selector `web_host` añadido en Settings (`127.0.0.1` solo local / `0.0.0.0` red local). Se guarda en `config.toml` como `web.host`. Requiere reiniciar el servidor para que surta efecto.

### ~~F2 — Tracker de tiempo de juego~~ ✅ Implementado
Columna `last_played_at` añadida a `games`. El scanner actualiza el campo cuando detecta que un save ha cambiado de mtime. El Overview muestra la sección "Últimas partidas" con los 5 juegos jugados más recientemente.
- `database/schema.py` — migración `last_played_at TEXT`
- `database/repository.py` — `get_games_paginated` devuelve `last_played_at`; ordenación disponible
- `server.py` — `_build_status` incluye `recently_played[]` en la respuesta
- `scanner/rom_scanner.py` — actualiza `last_played_at` al detectar cambio en save
- `frontend.py` — sección "Últimas partidas" en Overview

### ~~F3 — Estado de completado por juego~~ ✅ Implementado
Columna `play_status` añadida. Dropdown por fila en Games (Jugando / Completado / 100% / Abandonado). Filtro en la barra de Games. Guardado en BD vía `POST /api/set-play-status`.
- `database/schema.py` — migración `play_status TEXT`
- `database/repository.py` — `set_play_status()`, filtro en `get_games_paginated`
- `server.py` — endpoint `POST /api/set-play-status`, filtro en `/api/games`
- `frontend.py` — dropdown por fila, select de filtro `games-play-status`

### ~~F4 — Carátulas en la lista de Games~~ ✅ Implementado
Endpoint `GET /api/asset-image?game_id=N` sirve la imagen desde `game_metadata.box_art_path`. Columna thumbnail (32×32) añadida como primera columna en la tabla de Games.
- `server.py` — endpoint `/api/asset-image`
- `frontend.py` — `<img>` con `onerror="this.style.display='none'"` por si no hay imagen

### F5 — Vista de cuadrícula ("grid view")
Alternar entre tabla y mosaico de carátulas. Pendiente de implementar.
**Archivo:** `frontend.py`
**Esfuerzo:** medio (2-3 h)

### ~~F6 — Dashboard de colección (por plataformas)~~ ✅ Implementado
Endpoint `GET /api/platform-stats` + gráfico de barras CSS en Overview. Muestra hasta 15 plataformas ordenadas por cantidad de ROMs.
- `server.py` — endpoint `/api/platform-stats`
- `frontend.py` — sección colapsable "ROMs por plataforma" con barras CSS en Overview

### F7 — "Missing in action" (lista de deseos)
Cruzar la colección con la lista completa de No-Intro para ver qué juegos de cada plataforma no tienes.
**Archivos:** `catalog/`, `server.py`, `frontend.py`
**Esfuerzo:** grande (4-6 h)

### F8 — Trophy room
Visualizar logros de RetroAchievements ganados por el usuario (la API de RA tiene historial de logros por usuario).
**Archivos:** `retroachievements/`, `server.py`, `frontend.py`
**Esfuerzo:** grande (4-6 h)

### F9 — WiFi sync directo (sin cable ni nube)
Levantar un servidor HTTP mínimo en la consola con Termux y hacer push/pull directo cuando estén en la misma red. Elimina la dependencia de Dropbox para el sync en casa.
**Archivos:** `sync/` (nuevo transport), `server.py`, `frontend.py`
**Esfuerzo:** grande (6-8 h)

### F11 — Plugin de plataforma (`platforms.toml`)
Un archivo de configuración externo que defina extensiones, IDs de ScreenScraper/RA y rutas por plataforma. Añadir plataformas nuevas sin tocar código Python.
**Archivos:** `detection/platform_detector.py`, `scraper/platform_ids.py`, `retroachievements/ra_platform_ids.py`
**Esfuerzo:** grande (5-7 h)

### ~~F12 — Exportador Pegasus Metadata Format~~ ✅ Implementado
Nuevo módulo `scraper/pegasus_writer.py`. Endpoint `POST /api/export-pegasus`. Botón "Exportar Pegasus Metadata" en la pestaña Tools (morado). Genera `metadata.pegasus.txt` por plataforma con título, año, género, descripción y ruta de carátula.
- `scraper/pegasus_writer.py` — módulo nuevo
- `server.py` — endpoint `/api/export-pegasus`
- `frontend.py` — botón en Tools y div resultado `#pegasus-result`

---

## 💡 Ideas a largo plazo (sin fecha)

- **Ejecutable distributable** — PyInstaller → un `.exe` único que cualquier persona pueda instalar sin saber Python.
- **Soporte `.rvz` / `.nkit.iso`** — formatos comprimidos de GameCube/Wii con `dolphin-tool`.
- **Delta sync** — transferir solo los bytes que cambiaron (relevante para save states grandes de PSX/N64).
- **Sync daemon en background** — proceso que detecta cuando la consola se conecta a la red y lanza el sync automáticamente, sin abrir la web.
- **Tests de integración end-to-end** — simular scan + match + plan + apply sobre una carpeta temporal con ROMs ficticias.
- **Modo headless / CLI completo** — hacer todo desde la terminal sin abrir la web.
- **Nombre definitivo** — Retro Vault o Retro Companion. Elegir antes de cualquier distribución pública.
