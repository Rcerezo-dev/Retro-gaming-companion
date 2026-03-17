# Día 15 — Roadmap: S24–S26 y nuevas ideas

> Fecha: 2026-03-18
> Estado actual: S22 y S23 terminadas. Quedan S24 (UX), S25 (Auth), S26 (distribución).
> Backlog histórico archivado en `Tareas/diario/`.

---

## Sesiones pendientes del plan original

### S24 — UX y pulido

Objetivo: que la app se sienta terminada para uso diario. Sin código nuevo, solo afinar lo que ya existe.

| # | Qué | Por qué importa |
|---|-----|-----------------|
| 24-1 | **Keyboard shortcuts** | `Esc` cierra modales, `S` activa pestaña Sync, `G` Games, `R` refresca. Reduce fricción repetitiva. |
| 24-2 | **Estado vacío mejorado** | Cuando no hay datos, guiar al usuario con un CTA claro ("Escanea tu biblioteca → botón aquí") en lugar de texto gris plano. |
| 24-3 | **Feedback de guardado en Settings** | Tras guardar config, mostrar un checkmark inline junto a cada campo guardado en lugar de solo un toast. |
| 24-4 | **Confirmaciones destructivas** | Antes de eliminar duplicados o archivos junk, mostrar un resumen ("Se eliminarán 3 archivos, liberando 1.2 GB") con preview. |
| 24-5 | **Indicador "última sync"** | En el header o en la pestaña Sync, mostrar "Último sync: hace 2 horas" siempre visible. |
| 24-6 | **Responsive básico para consola** | Cuando se abre desde la consola Android (pantalla pequeña), la navegación debe ser usable. Mínimo: nav colapsable, botones con touch area suficiente. |
| 24-7 | **Acceso rápido desde Overview** | Botones de acción directa en las tarjetas de Overview ("Sync ahora", "Ver juegos", "Ver duplicados") sin tener que cambiar de pestaña. |

---

### S25 — Auth (PIN + QR)

Objetivo: proteger el acceso a la UI cuando está expuesta en LAN (`web_host = 0.0.0.0`).

**PIN de sesión:**
- 4–6 dígitos configurables en Settings
- Se pide al abrir la app si `web_host = 0.0.0.0`
- Guardado como hash bcrypt o SHA256+salt en config.toml (nunca en claro)
- Cookie de sesión con TTL configurable (por defecto 24 h)
- Sin PIN → no se activa aunque estés en LAN (opt-in)

**QR de acceso:**
- En Settings: botón "Generar QR" que genera la URL `http://<ip_local>:7777`
- El QR se muestra en pantalla para escanearlo con la consola/móvil
- Útil para abrir la UI sin escribir la IP manualmente

**Backend:**
- Middleware de autenticación en `do_GET`/`do_POST` antes de cualquier endpoint
- Endpoint `POST /api/auth` con el PIN → devuelve token de sesión
- Página de login minimalista servida cuando no hay sesión válida

---

### S26 — Distribución (PyInstaller + instalador)

Objetivo: que cualquier jugador pueda instalar Retro Vault sin saber qué es Python.

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

## Nuevas ideas — qué más podría mejorar la herramienta

### 🔵 Alta prioridad (valor real, coste bajo-medio)

| Idea | Descripción | Sesión estimada |
|------|-------------|-----------------|
| **Backup de saves versionado** | Antes de sobreescribir un save, guardar copia en `.rommgr/saves-backup/{game}/{timestamp}.sav`. Configurable: últimas N copias. Crítico para saves corruptos de PSX/N64. | 1 sesión |
| **Editor de metadatos inline** | Click en un juego → editar título canónico, plataforma, región directamente en la UI. Ahora es solo lectura. | 1 sesión |
| **"Missing in action" — colección vs DAT** | Dado un DAT cargado, mostrar qué juegos del catálogo NO tienes. Lista por plataforma con título + región. Útil para completionistas. | 1 sesión |
| **Timeline de operaciones** | Vista en Settings → Historial: muestra `file_operations` en un timeline limpio. Quién renombró qué y cuándo. Ya tenemos los datos, falta el frontend. | 0.5 sesiones |
| **Detección de inbox al arrancar** | Al iniciar el servidor, si hay archivos en `inbox_path`, mostrar badge en el nav con el contador. Notificación pasiva. | 0.5 sesiones |
| **Filtro por plataforma en duplicados** | La pestaña Duplicados actualmente mezcla todo. Un dropdown de plataforma reduciría el ruido enormemente. | 0.5 sesiones |

### 🟡 Media prioridad (buen valor, más trabajo)

| Idea | Descripción |
|------|-------------|
| **Health check programado** | Ejecutar health check semanalmente en segundo plano. Notificar si algún ROM tiene hash diferente al registrado (detección de corrupción silenciosa). |
| **Exportar a CSV/JSON** | Exportar la biblioteca completa a CSV o JSON para usar en otras apps (Notion, hojas de cálculo, etc.). |
| **Comparador visual de saves** | Para saves de misma plataforma: mostrar fecha de modificación PC vs consola antes del sync, con diferencia en tiempo de juego si está disponible. |
| **Plugin de plataforma (`platforms.toml`)** | Definiciones de plataforma en un archivo externo editable. Hoy están hardcodeadas en `platform_detector.py`. Permitiría añadir consolas sin cambiar el código. |
| **Soporte `.rvz` / `.nkit.iso`** | GameCube/Wii comprimidos via `dolphin-tool`. Alta demanda entre coleccionistas. |
| **Modo oscuro/claro** | Toggle de tema. El oscuro ya es el default; el claro sería util para usar en monitores brillantes. |

### 🟢 Largo plazo / experimental

| Idea | Descripción |
|------|-------------|
| **Delta sync** | Solo transferir bytes que cambiaron en el save, no el archivo entero. Relevante para PSX/N64 con saves grandes. Requiere formato de parche (bsdiff). |
| **Agente Claude integrado** | "Asistente de colección": pregunta qué plataforma quieres completar → busca en tu DAT → te dice qué te falta → sugiere dónde conseguirlo (legal). |
| **Análisis de tiempo de juego por plataforma** | Gráfico mensual de `last_played_at` por plataforma. ¿Cuánto jugaste a GBA este mes vs PSX? |
| **Modo headless completo** | Todo desde CLI sin web: `rommgr scan`, `rommgr sync`, `rommgr inbox`. Útil para automatización y servidores. |
| **API REST documentada** | Generar `openapi.json` desde los endpoints existentes. Permite integraciones externas. |

---

## Orden de trabajo recomendado para mañana

```
1. S24 — UX y pulido (24-1 a 24-4 como mínimo)
   → Empezar por keyboard shortcuts y estados vacíos: impacto visible inmediato

2. Backup de saves versionado (nueva, alta prioridad)
   → Protege datos reales; se puede añadir al pipeline de sync en ≈1 sesión

3. Timeline de operaciones (nueva, 0.5 sesiones)
   → Los datos ya existen; solo falta el frontend

4. S25 — Auth PIN
   → Solo si planeas compartir la app con otras personas en tu red

5. S26 — Distribución
   → Dejar para el final; necesita S24 terminada para que el resultado sea presentable
```

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
