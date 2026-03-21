# Día 15 — Roadmap: S24–S29 y nuevas ideas

> Fecha: 2026-03-18 | Actualizado: 2026-03-18
> Estado actual: S22 ✅ S23 ✅ S24 ✅ S25 ✅ S26 ✅ S27 ✅.
> Quedan S28 (búsqueda + lanzador + favoritos), S29 (distribución — siempre al final).
> Backlog histórico archivado en `Tareas/diario/`.

---

## Sesiones pendientes del plan original

### ✅ S24 — UX y pulido

> **COMPLETADA** — implementada en sesión de 2026-03-18.

Objetivo: que la app se sienta terminada para uso diario. Sin código nuevo, solo afinar lo que ya existe.

| # | Estado | Qué | Notas de implementación |
|---|--------|-----|------------------------|
| 24-1 | ✅ | **Keyboard shortcuts** | `G`→Games, `S`→Sync, `R`→recarga, `Esc`→cierra modales. Listener en `DOMContentLoaded` en `app.js`. |
| 24-2 | ✅ | **Estado vacío mejorado** | `_emptyState(icon, title, sub, ctaLabel, ctaFn)` en `app.js`. Aplicado en Games, Duplicados. |
| 24-3 | ✅ | **Feedback de guardado en Settings** | Spans `.cfg-saved` con clase `.visible` tras guardar. Map `_CFG_KEY_TO_CHECK` en `app.js`. |
| 24-4 | ✅ | **Confirmaciones destructivas** | Modal `#confirm-modal` reutilizable. `_showConfirm(title, body, fn)` / `_closeConfirm()` en `app.js`. Aplicado en borrar duplicados y junk. |
| 24-5 | ✅ | **Indicador "última sync"** | `#header-last-sync` en header. Actualizado vía `_updateAutoSyncBanner()` con `_relTime()`. |
| 24-6 | ✅ | **Responsive básico para consola** | `@media (max-width: 640px)` en CSS: `nav button min-height: 44px`, etc. |
| 24-7 | ✅ | **Acceso rápido desde Overview** | Parámetro `actions` en `card()`. Botones "Ver juegos", "Identificar →", "Ver" en tarjetas de Overview. |

---

### ✅ S25 — Auth (PIN + URL de acceso)

> **COMPLETADA** — implementada en sesión de 2026-03-18.

Objetivo: proteger el acceso a la UI cuando está expuesta en LAN (`web_host = 0.0.0.0`).

**Implementación:**

| # | Estado | Qué | Notas |
|---|--------|-----|-------|
| 25-1 | ✅ | **PIN de sesión** | Opt-in: solo activo si `web_pin_hash` está en `config.toml`. Hash SHA-256+salt (never en claro). `_hash_pin()` + `secrets.token_urlsafe`. |
| 25-2 | ✅ | **Cookie de sesión** | `rvm_session` cookie; TTL 24h (configurable `web_session_ttl`); HttpOnly + SameSite=Strict. Dict `_sessions` en memoria con expiración monotónica. |
| 25-3 | ✅ | **Middleware** | `_is_authenticated()` al inicio de `do_GET`/`do_POST`. Rutas exentas: `/login`, `/static/*`, `/api/auth`, `/api/auth/logout`. |
| 25-4 | ✅ | **Página de login** | `GET /login` → `_LOGIN_HTML` inline. PIN input + fetch POST `/api/auth` → redirect a `/`. |
| 25-5 | ✅ | **Endpoints auth** | `POST /api/auth` (login), `POST /api/auth/logout`, `GET /api/auth/status`, `POST /api/set-pin`, `POST /api/clear-pin`. |
| 25-6 | ✅ | **URL local** | `GET /api/local-url` devuelve IP LAN real (`socket` trick). Mostrada en Settings con botón "Copiar". |
| 25-7 | ✅ | **UI en Settings** | Sección "Acceso remoto — PIN y URL": input PIN + "Activar"/"Desactivar". Botón logout en header (solo visible si hay PIN configurado). |
| 25-8 | ⏸ | **QR de acceso** | Requiere dependencia externa (`qrcode`) o implementación QR manual. Reemplazado por URL + copiar. |

**Campos añadidos a `AppConfig`:** `web_pin_hash`, `web_pin_salt`, `web_session_ttl`
**Campos en `config.toml`:** `[web] pin_hash`, `[web] pin_salt`, `[web] session_ttl`

---

### ✅ S26 — ScreenScraper (cuenta de desarrollador)

> **COMPLETADA** — implementada en sesión de 2026-03-18.
> Credenciales en `config.toml`: `[screenscraper]` user/pass/dev_id/dev_pass. Dev account: kroq.

Objetivo: aprovechar la cuenta dev para obtener más datos, mejores rate limits y carátulas en alta calidad.

| # | Estado | Qué | Notas de implementación |
|---|--------|-----|------------------------|
| 26-1 | ✅ | **Rate limit automático** | `__post_init__` en `ScreenScraperClient`: si dev_id+dev_password → `min_interval = 0.35s`. Sin dev: 1.2s. |
| 26-2 | ✅ | **Más campos de metadatos** | `ScraperResult` añade `players`, `genres_list` (todos los géneros separados por coma). Extraídos en `_parse()`. |
| 26-3 | ✅ | **Imágenes de mayor resolución** | `_pick_media()` ahora prioriza `box-3D > box-2D`. Campos `screenshot_url` y `wheel_url` en `ScraperResult`. |
| 26-4 | ⏸ | **Scraping por lote** | Pospuesto — `jeuRecherche.php` no ofrece ventaja clara sobre `jeuInfos.php` con hashes. |
| 26-5 | ✅ | **Indicador de cuota** | `GET /api/ss-quota` en server.py. Barra visual en Settings con color adaptativo. Se auto-carga al abrir Settings. Quota capturada de `response.serveur` en cada llamada API. |

---

### ✅ S27 — Rediseño visual

> **COMPLETADA** — implementada en sesión de 2026-03-18.

Objetivo: que la app se sienta como un producto acabado y no como una herramienta interna. Todo lo que hay funciona — solo falta que se vea bien.

| # | Estado | Qué | Detalle / Notas |
|---|--------|-----|---------|
| 27-1 | ✅ | **Hero banner en Overview** | Tarjeta `.hero-game` con cover art + título + `_relTime()` para el último juego jugado. Clickable → abre panel detalle. |
| 27-2 | ⏸ | **Grid de plataformas con logo** | Requiere assets SVG/PNG embebidos por plataforma. Pospuesto. |
| 27-3 | ✅ | **Panel de detalle de juego** | Panel `.game-panel` (slide-in desde derecha). `openGamePanel(g)` / `closeGamePanel()`. `GET /api/game?id=` para metadatos scrapeados completos. Status editable inline con `gpSetStatus()`. Esc cierra. Click en filas de tabla y grid cards. |
| 27-4 | ✅ | **Color de acento por plataforma** | `_PLAT_HEX` map + `_platHex(plat)`. Aplicado en: borde izquierdo de filas de tabla, borde superior de grid cards, borde del panel de detalle, tarjeta hero. |
| 27-5 | ✅ | **Tipografía y espaciado** | `td { padding: 10px 12px }`, `th { padding: 9px 12px }` añadidos al final de CSS (sobreescriben las reglas originales). |
| 27-6 | ✅ | **Animaciones de transición** | `@keyframes tab-fade-in` (opacity 0→1, translateY 5px→0, 180ms). Clase `.fading-in` añadida y quitada en `showTab()` con `animationend`. |
| 27-7 | ⏸ | **Modo claro opcional** | Requiere refactor CSS completo con variables. Pospuesto. |
| 27-8 | ⏸ | **Pantalla de carga / splash** | Pospuesto — el servidor arranca rápido, impacto bajo. |

---

### S28 — Búsqueda + lanzador + favoritos

Objetivo: tres features de uso diario que transforman la app de "gestora de archivos" a "frontend de colección".

| # | Qué | Detalle |
|---|-----|---------|
| 28-1 | **Búsqueda global en tiempo real** | Campo de búsqueda en el nav que filtra juegos al escribir (debounce 200ms). Sin cambiar de pestaña ni pulsar Enter. Busca por título, plataforma y tags. |
| 28-2 | **"Continuar jugando"** | Sección en Overview con los últimos 5–6 juegos jugados con carátula grande tipo Netflix. Botón directo para lanzarlos. Los datos ya existen (`last_played_at` + artwork). |
| 28-3 | **Lanzar juego desde la UI** | Botón "▶ Abrir en RetroArch" en el detalle de cada juego. Ejecuta `retroarch.exe --libretro <core> <rom>`. Core detectado automáticamente por plataforma desde el mapeo que ya existe. |
| 28-4 | **Preview de estados de RetroArch** | RetroArch guarda un `.png` junto a cada `.state`. Mostrar esa miniatura en el panel de detalle del juego — ves exactamente dónde lo dejaste. |
| 28-5 | **Favoritos** | Estrella en cada juego para marcar favoritos. Filtro rápido en Games ("Solo favoritos"). Campo `is_favorite` en BD. |
| 28-6 | **Tags personalizados** | Etiquetas de texto libre por juego: "por completar", "co-op", "infancia", lo que sea. Tabla `game_tags` en BD. Filtro por tag en Games. |

---

## Nuevas ideas — qué más podría mejorar la herramienta

### 🎨 Rediseño visual e imágenes (nueva sección)

La interfaz actual funciona bien pero es muy utilitaria — fondo negro plano, sin jerarquía visual clara, sin identidad. Con los datos que ya tenemos (carátulas scrapeadas, plataformas, estadísticas) se puede hacer algo mucho más atractivo sin cambiar ninguna funcionalidad.

**Qué mejoraría concretamente:**

| # | Qué | Detalle |
|---|-----|---------|
| V-1 | **Hero banner en Overview** | Imagen del último juego jugado como fondo de la cabecera (con blur + overlay oscuro). Ya tenemos `last_played_at` y las carátulas en BD — solo falta mostrarlas. |
| V-2 | **Grid de plataformas con logo** | En lugar de barras de texto en Overview, mostrar las plataformas como tarjetas con su logo (SNES, GBA, PSX…). Logos como SVG inline o PNG embebido — no depende de internet. |
| V-3 | **Carátula prominente en detalle de juego** | Al hacer click en un juego, panel lateral con la carátula grande, título, plataforma, región, estado de completado y logros RA — todo junto, legible. |
| V-4 | **Color de acento por plataforma** | Cada plataforma tiene un color asociado (GBA → índigo, PSX → gris azulado, SNES → morado…). Se aplica en bordes de tarjetas y badges. Sutil pero da mucho carácter. |
| V-5 | **Tipografía y espaciado** | Aumentar ligeramente el tamaño de fuente base (13px → 14px), más padding en tarjetas, jerarquía clara H1/H2/body. Cambio mínimo, impacto grande. |
| V-6 | **Animaciones de transición suaves** | Fade al cambiar de pestaña (100ms), slide en paneles que se despliegan. Ya hay `transition` en algún sitio — generalizarlo. |
| V-7 | **Modo claro opcional** | Toggle en Settings. El oscuro sigue siendo el default. Útil si usas la app en un monitor brillante o compartes pantalla. |

**Coste estimado:** S24 ampliada o una sesión propia (S24-Visual). El grid de plataformas y el hero banner son los cambios más visibles y los más rápidos de implementar.

---

### 🔵 Alta prioridad (valor real, coste bajo-medio)

| Idea | Descripción | Sesión estimada |
|------|-------------|-----------------|
| **Backup de saves versionado** | Antes de sobreescribir un save, guardar copia en `.rommgr/saves-backup/{game}/{timestamp}.sav`. Configurable: últimas N copias. Crítico para saves corruptos de PSX/N64. | 1 sesión |
| **Editor de metadatos inline** | Click en un juego → editar título canónico, plataforma, región directamente en la UI. Ahora es solo lectura. | 1 sesión |
| **"Missing in action" — colección vs DAT** | Dado un DAT cargado, mostrar qué juegos del catálogo NO tienes. Lista por plataforma con título + región. Útil para completionistas. | 1 sesión |
| **Timeline de operaciones** | Vista en Settings → Historial: muestra `file_operations` en un timeline limpio. Quién renombró qué y cuándo. Ya tenemos los datos, falta el frontend. | 0.5 sesiones |
| **Detección de inbox al arrancar** | Al iniciar el servidor, si hay archivos en `inbox_path`, mostrar badge en el nav con el contador. Notificación pasiva. | 0.5 sesiones |
| **Filtro por plataforma en duplicados** | La pestaña Duplicados actualmente mezcla todo. Un dropdown de plataforma reduciría el ruido enormemente. | 0.5 sesiones |
| **Drag & drop en inbox** | Arrastrar archivos desde el explorador de Windows directamente a la ventana del navegador para añadirlos al inbox. API `DataTransfer` ya disponible en todos los navegadores modernos. | 0.5 sesiones |
| **Notas personales por juego** | Campo de texto libre en el panel de detalle: apuntar claves, trucos, donde lo dejé, configuración de controller. Guardado en BD, campo `notes` en tabla `games`. | 0.5 sesiones |
| **Organizar screenshots de RetroArch** | RetroArch guarda screenshots en su propia carpeta. Detectarlos, organizarlos por plataforma/juego igual que los saves, mostrarlos en el panel de detalle. | 1 sesión |

### 🟡 Media prioridad (buen valor, más trabajo)

| Idea | Descripción |
|------|-------------|
| **Health check programado** | Ejecutar health check semanalmente en segundo plano. Notificar si algún ROM tiene hash diferente al registrado (detección de corrupción silenciosa). |
| **Exportar a CSV/JSON** | Exportar la biblioteca completa a CSV o JSON para usar en otras apps (Notion, hojas de cálculo, etc.). |
| **Comparador visual de saves** | Para saves de misma plataforma: mostrar fecha de modificación PC vs consola antes del sync, con diferencia en tiempo de juego si está disponible. |
| **Plugin de plataforma (`platforms.toml`)** | Definiciones de plataforma en un archivo externo editable. Hoy están hardcodeadas en `platform_detector.py`. Permitiría añadir consolas sin cambiar el código. |
| **Soporte `.rvz` / `.nkit.iso`** | GameCube/Wii comprimidos via `dolphin-tool`. Alta demanda entre coleccionistas. |
| **Playlists RetroArch (`.lpl`)** | Además de `.m3u`, generar playlists en el formato nativo de RetroArch para que los juegos aparezcan directamente en sus menús sin configuración adicional. |
| **Filtros avanzados en Games** | Ya tenemos género, año, publisher y región del scraper en la BD. Exponer como dropdowns en Games. Ordenar por año, por plataforma, por horas jugadas. |
| **Estadísticas de colección** | Por plataforma: X de Y juegos del catálogo DAT (% completación). Quién tiene más cobertura. Gráfico de barras simple en Overview. |
| **Preview de metadatos pre-scraping** | Antes de aplicar el scraping, mostrar un diff: "título actual → título scrapeado, sin portada → portada encontrada". El usuario confirma antes de escribir. |

### 🟢 Largo plazo / experimental

| Idea | Descripción |
|------|-------------|
| **Delta sync** | Solo transferir bytes que cambiaron en el save, no el archivo entero. Relevante para PSX/N64 con saves grandes. Requiere formato de parche (bsdiff). |
| **Agente Claude integrado** | "Asistente de colección": pregunta qué plataforma quieres completar → busca en tu DAT → te dice qué te falta → sugiere dónde conseguirlo (legal). |
| **Análisis de tiempo de juego por plataforma** | Gráfico mensual de `last_played_at` por plataforma. ¿Cuánto jugaste a GBA este mes vs PSX? |
| **Modo headless completo** | Todo desde CLI sin web: `rommgr scan`, `rommgr sync`, `rommgr inbox`. Útil para automatización y servidores. |
| **API REST documentada** | Generar `openapi.json` desde los endpoints existentes. Permite integraciones externas. |
| **Modo presentación (TV mode)** | Pantalla completa con carátulas grandes y navegación por flechas. Pensado para mostrar la colección en un televisor, sin teclado ni ratón. |
| **Mapa de calor de actividad** | Cuadrícula estilo GitHub de los últimos 365 días. Días con actividad de juego marcados en verde. Dados `last_played_at`, se puede calcular sin cambios en el backend. |
| **"Juego del día"** | Tarjeta en Overview con una sugerencia aleatoria de un juego que no has tocado en más de 6 meses. Para redescubrir la biblioteca. |
| **Multi-perfil de saves** | Perfiles separados por persona con sus propios saves. Útil para familias. Cada perfil tiene su propia carpeta de sync y su propia `last_played_at`. |
| **Soporte MAME** | ROMs MAME tienen su propio formato de CHDs y DATs. Gestión especializada: split sets, merged sets, detección de samples y artwork. |
| **Notificaciones de escritorio** | Al terminar un sync, al detectar juegos en inbox o al encontrar ROMs corruptos: toast nativo de Windows vía PowerShell o `win10toast` (sin dependencias si se hace con PS). |

---

## Orden de trabajo recomendado

```
1. ✅ S24 — UX y pulido
2. ✅ S25 — Auth PIN + URL local
3. ✅ S26 — ScreenScraper dev (rate limit, metadatos extra, cuota)
4. ✅ S27 — Rediseño visual
   → Panel detalle de juego · hero last-played · colores por plataforma · fade de pestañas
5. S28 — Búsqueda + lanzador + favoritos
   → El panel de detalle (27-3) es la base del lanzador y favoritos
6. Backup de saves versionado
   → Protege datos reales; añadir al pipeline de sync en ≈1 sesión
7. S29 — Distribución
   → Siempre al final, cuando todo lo demás esté estable
```

---

### S29 — Distribución (PyInstaller + instalador)

Objetivo: que cualquier jugador pueda instalar Retro Vault sin saber qué es Python. **Solo cuando todo lo anterior funcione end-to-end.**

**Ejecutable:**
- `pyinstaller --onefile --noconsole` → `RetroVault.exe`
- Incluir `tools/chdman.exe`, `tools/adb.exe` en el bundle (`--add-data`)
- Abrir el navegador automáticamente al lanzar (`webbrowser.open`)
- Icono de la app (`.ico`) en el ejecutable

**Instalador Windows (NSIS o InnoSetup):**
- Instala en `%LOCALAPPDATA%\RetroVault\`
- Crea acceso directo en el escritorio y menú inicio
- Opción de arranque automático con Windows (clave de registro o carpeta Startup)
- Desinstalador limpio (borra solo el ejecutable, deja datos del usuario)

**Distribución:**
- GitHub Releases con el `.exe` firmado (o al menos con manifiesto UAC)
- `CHANGELOG.md` auto-generado desde commits
- Versión embebida en `__version__` y visible en Settings

**Icono de bandeja (tray):**
- Minimizar a tray en lugar de cerrar la ventana del navegador
- Menú contextual: "Abrir", "Sincronizar ahora", "Salir"
- Implementable con `pystray` + `Pillow` (únicas dependencias de distribución permitidas)

---

## Pendientes de validar en hardware (no cambian)

| ID | Tarea |
|----|-------|
| V1 | Sync automático con SD card |
| V2 | Migración a dos bases de datos |
| V3 | Inbox end-to-end ⭐ |
| V4 | RetroAchievements con API key real |
| V5 | Guía Termux en la consola |
| B1-hw | Renombrador Android no reduce la cola |

---

## Acciones de usuario pendientes (sin código)

| ID | Tarea |
|----|-------|
| STRUCT-4 | Configurar RetroArch PC → Saving → Savefile Directory → `E:\Carpetas anbernic\saves\` |
| STRUCT-3 | Actualizar config.toml → `local_dir` (después de STRUCT-4) |
| ES-1 | Descargar core `genesis_plus_gx` en RetroArch |
| ES-2 | Configurar Citra (3DS) en EmulationStation con ruta completa |
