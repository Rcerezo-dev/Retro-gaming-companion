# Día 13 — Grandes pasos: a dónde va la app

> Fecha: 2026-03-17
> Propósito: visión de conjunto sin filtros — qué es la app, qué no es, qué hay que hacer de verdad.

---

## 1. Qué es realmente esta app

No es un gestor de ROMs genérico. Es **una herramienta personal para una persona específica** (tú) que tiene:
- Una colección caótica de juegos en el PC
- Una consola Android (RG 556 u otra) donde los juega
- El deseo de poder alternar dispositivos sin perder el progreso

Esos tres puntos definen los **tres pilares reales**, por orden de valor:

| Pilar | Qué resuelve | Estado |
|-------|-------------|--------|
| **1. Primera vez** | Limpiar el caos: ZIPs, nombres incorrectos, duplicados, BIOS dispersas | ✅ Funcional (pipeline scan → match → organize) |
| **2. Inbox** | Soltar juegos nuevos y que se organicen solos | 🟡 Implementado, sin probar end-to-end |
| **3. Sync de saves** | Jugar en PC o consola sin perder partidas | 🟡 Implementado cloud; falta WiFi directo |

Todo lo demás — scraper, RetroAchievements, gamelist.xml, health checker — son **mejoras de calidad de vida**, no el núcleo. Son valiosas, pero no deberían crecer a costa de los tres pilares.

---

## 2. El siguiente salto grande: de "funcional" a "usable de verdad"

El código existe. Lo que falta es que **funcione sin fricción** en el mundo real.

### 2a. Inbox end-to-end (Pilar 2) — prioridad máxima
El flujo que el usuario quiere: *"suelo un ZIP, la app lo pone donde toca"*.

El código existe. Lo que bloquea la prueba real:
- `inbox_path` debe estar configurado en `config.toml`
- La biblioteca debe tener DATs cargados para hacer el match
- Las carpetas de plataforma deben existir (STRUCT-6 ya resuelto)

**Próximo paso concreto:** probar el flujo completo con 3 ROMs reales.

### 2b. WiFi sync directo (Pilar 3 sin nube)
El sync cloud via Dropbox funciona, pero tiene latencia (PC → nube → consola). La consola y el PC están en la misma red. Lo correcto es **sync directo por WiFi**, sin pasar por internet.

Prerequisito: Termux + sshd en la consola (guía escrita, pendiente de ejecutar).
Una vez hecho: `rclone` puede sincronizar directamente vía SFTP, sin Dropbox.

### 2c. Dispositivo configurable (deuda técnica de UX)
Ahora mismo el código tiene referencias a "Anbernic", "RG556", rutas hardcodeadas.
La idea correcta: en Ajustes, el usuario pone el nombre de su consola y sus rutas. Todo el resto de la app usa ese nombre. Sin cambios de código para cada dispositivo.

**Archivos a tocar:** `config.py` (añadir `device_name`, `device_android_root`), `frontend.py` (ya usa `_devName`), `server.py` (ya usa `android_root`). Es un cambio de ~2h que elimina toda la deuda.

---

## 3. Features de producto que sí importan (y en qué orden)

### Alta prioridad (uso diario)
1. **Tracker de tiempo de juego** — leer el `mtime` del save para inferir "última vez jugado" y acumular tiempo aproximado. No requiere hook de RetroArch; es una heurística aceptable. Ver pestaña "Juegos" con columna "Última partida".
2. **Estado de completado** — columna en BD: `Jugando / Completado / Abandonado / Sin empezar`. Editable desde la pestaña Games. Filtreable. Esto convierte la app de inventario a bitácora de partidas.
3. **Grid view con carátulas** — las imágenes ya están descargadas (scraper). Solo falta mostrarlas. Toggle tabla ↔ mosaico en la pestaña Games.

### Media prioridad (colección)
4. **"Missing in action"** — cruzar colección con DAT completo para saber qué juegos de una plataforma no tienes. Lista de deseos en BD.
5. **Dashboard de colección** — gráficos: ROMs por plataforma, porcentaje con carátula, con logros RA, renombrados. Un número "puntuación de la colección".

### Baja prioridad (técnico)
6. **Plugin de plataforma (`platforms.toml`)** — mover las definiciones de plataforma a un archivo externo. Hace la app extensible sin tocar código.
7. **Soporte `.rvz`/`.nkit.iso`** — GameCube/Wii comprimidos. Requiere `dolphin-tool`.
8. **Modo headless / CLI completo** — scripting y automatización sin abrir la web.

---

## 4. El horizonte: distribución

La app podría convertirse en algo que cualquier persona con una consola Android retro pueda instalar. Un ejecutable único (PyInstaller), sin Python, sin conda, sin config manual.

Para llegar ahí falta:
- Configuración inicial guiada (wizard de primer arranque) — detectar dispositivo, crear estructura, configurar sync
- Autenticación básica si `host = 0.0.0.0` (para acceder desde la consola)
- Tests de integración sólidos antes de distribuir
- Nombre definitivo: **Retro Vault** o **Retro Companion**

No es urgente, pero es el norte. Cada decisión de diseño debería ser compatible con ese destino.

---

## 5. Estructura de documentación — el problema real

Hay 25+ archivos en `Tareas/` y llevan nombres como `Día1.md`, `Día13-Siguientes-Tareas.md`. Esto tiene dos problemas:

**Problema 1: la información útil está enterrada.**
Si quiero saber "¿cuál es el estado del scraper?" tengo que revisar 5 archivos de días distintos. La información que debería estar en un sitio está fragmentada por fecha.

**Problema 2: la carpeta mezcla cosas distintas.**
- Diarios de sesión (Día1.md a Día9.md) — narrativa, no consulta
- Planes de tareas (DíaX-Siguientes-Tareas.md) — se quedan obsoletos inmediatamente
- Guías técnicas (Guia-Termux-Anbernic.md) — documentación real, debería estar en `docs/`
- Roadmaps (Día10-Mejoras-Pendientes.md) — este archivo

**Mi recomendación: reestructuración ligera (no drástica)**

```
proyecto/
├── docs/                    ← documentación técnica duradera (ya existe)
│   ├── architecture.md      ← NUEVO: extraído de CLAUDE.md
│   ├── library-structure.md ← ya existe
│   ├── sync-cloud.md        ← ya existe
│   ├── sync-cable.md        ← ya existe
│   └── android-sync.md      ← ya existe
│
├── Tareas/                  ← notas de trabajo con Claude
│   ├── roadmap.md           ← ESTE ARCHIVO (renombrado)
│   ├── backlog.md           ← NUEVO: backlog activo vivo (reemplaza los DíaX-Siguientes-Tareas)
│   ├── diario/              ← NUEVO: subcarpeta con todos los Día1-12.md archivados
│   └── guias/               ← NUEVO: Guia-Termux y similares
│
└── .claude/
    ├── CLAUDE.md            ← MÁS CORTO: solo estado, reglas, patrones críticos
    ├── commands/            ← slash commands (ya existe)
    ├── agents/              ← agentes custom (ya existe)
    └── memory/              ← memoria persistente (ya existe en ~/.claude)
```

**El cambio más impactante sería acortar CLAUDE.md.**
Ahora mismo carga en cada conversación con toda la arquitectura, el config.toml, las ideas futuras, las decisiones técnicas. Mucho de eso ya está en memoria y en `docs/`. Un CLAUDE.md de 60-80 líneas que diga "estado actual, reglas de trabajo, patrones críticos — el resto está en docs/" sería más efectivo.

---

## 6. Lo que NO hay que hacer

- No añadir dependencias externas de runtime (la stdlib es un activo, no una limitación)
- No rediseñar la arquitectura de BD por ahora (SQLite es suficiente para años)
- No intentar soportar todos los dispositivos / frontends / formatos — foco en el caso de uso real
- No crecer la interfaz en complejidad antes de validar los pilares en hardware real

---

## Próxima sesión recomendada

1. **Inbox end-to-end** en hardware (configura `inbox_path`, prueba con 3 ROMs reales)
2. **Dispositivo configurable** en Settings (2h, elimina toda la deuda de "Anbernic")
3. Si todo verde → **Tracker de tiempo de juego** (columna `last_played` en BD + columna en UI)


---

## Notas post-sesión (2026-03-17) — implementado

**Las tres preguntas del final de sesión, resueltas:**

### A — ¿Voy a perder saves al implementar las carpetas ES-DE?
No. El renombrador (`file_renamer.py`) ya arrastraba saves por stem con rollback atómico.
El organizer (`_handle_organize_library`) siempre hace dry-run por defecto: verás exactamente qué se moverá antes de aplicar. Si hay un conflicto (el archivo ya existe en destino), lo reporta como error y NO sobreescribe.

### B — La tool de estructura ahora crea TODO
`_handle_create_library_structure` / `POST /api/create-library-structure` crea de una pasada:
- 27 carpetas de plataforma con `media/images/` y `media/videos/`
- `saves/` + `saves/{platform}/` para las 27 plataformas
- `states/` + `states/{platform}/` para las 27 plataformas
- `bios/`, `inbox/`, `screenshots/`

### C — La estructura es compatible con la Anbernic y no mezcla saves
Los saves van a `saves/{platform}/` (ej. `saves/gba/Castlevania.sav`).
Nunca se mezclan saves de distintas consolas en el mismo directorio.
Para que RetroArch Android haga lo mismo: Ajustes → Directorio → activar "Usar directorio del sistema" en archivos de guardado.


quiero además que me digas qué necesitaría esta app para conseguir que no sea sólo para mí, sino también sea util para cualquier jugador retro que no quiera comerse mucho la cabeza configurando