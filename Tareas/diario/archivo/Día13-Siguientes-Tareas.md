# Día 13 — Siguientes tareas

> Fecha estimada: próxima sesión
> Contexto: el pipeline está verde, la BD optimizada, la UI limpia y las features de grid view y cable preview implementadas.

---

## 🔴 STRUCT-6 — Estructura ES-DE completa + organización en ambos dispositivos (NUEVO, ALTA PRIORIDAD)

> **Contexto:** Ya existe código de estructura (`_handle_create_library_structure`, `_handle_organize_library`) pero está incompleto. El usuario quiere la estructura EmulationStation canónica clonada en PC y consola Android, con organización automática de ROMs, saves y BIOS.

### Gaps detectados en el código actual

| Gap | Descripción | Archivo / Línea |
|-----|-------------|-----------------|
| GAP-1 | `_STANDARD_PLATFORM_FOLDERS` incompleto — falta Atari 2600/5200/7800, Lynx, Jaguar, PSVita, WiiU, Switch, 3DS | `server.py:64` |
| GAP-2 | Organizador solo mueve ROMs — los saves quedan dispersos, no van a `saves/` | `server.py:2058` |
| GAP-3 | Organizador no detecta ni mueve BIOS a `bios/` | `server.py:2058` |
| GAP-4 | Crear estructura solo funciona en PC — no tiene opción para el dispositivo Android | `server.py:2026` |

### Estructura canónica (EmulationStation / ES-DE)

```
<library_root>/             ← E:\Carpetas anbernic\  (PC)  ó  /storage/emulated/0/ROMs/  (Android)
│
├── nes/
│   ├── media/images/
│   ├── media/videos/
│   └── gamelist.xml
├── snes/
├── n64/
├── gb/  gbc/  gba/  nds/  3ds/
├── gamecube/  wii/  wiiu/  switch/
├── psx/  ps2/  ps3/  psp/  psvita/
├── dreamcast/  saturn/
├── megadrive/  mastersystem/  gamegear/  sega32x/  segacd/
├── neogeo/  pcengine/
├── atari2600/  atari5200/  atari7800/  atarilynx/  atarijaguar/
│
├── saves/          ← TODOS los saves de RetroArch (plano, por nombre de archivo)
├── bios/           ← BIOS (scph1001.bin, bios_CD_E.bin, etc.)
└── inbox/          ← ZIPs nuevos sin organizar (Pilar 2)
```

### Tareas de implementación

| ID | Tarea | Esfuerzo |
|----|-------|----------|
| STRUCT-6a | **Completar `_STANDARD_PLATFORM_FOLDERS`** con todas las plataformas de `_ES_PLATFORM_FOLDERS` | 5 min |
| STRUCT-6b | **Organizador mueve saves junto al ROM** → cuando mueve un ROM, también mueve su save asociado (mismo stem, extensiones `.sav .srm .state .ogg`) a `saves/` | 30 min |
| STRUCT-6c | **Detectar y mover BIOS** → archivos con extensión `.bin` en la raíz y en subcarpetas que no sean ROMs conocidos → `bios/` (dry_run primero) | 30 min |
| STRUCT-6d | **Crear estructura en Android** → si hay ruta de dispositivo configurada y accesible (SD montada), crear el mismo árbol en el dispositivo | 30 min |
| STRUCT-6e | **UI: checkbox "También en consola Android"** en el panel "Estructura de biblioteca" → activa STRUCT-6d | 20 min |

### Notas de implementación

- **Saves**: extensiones de save conocidas están en `config.save_extensions` — usarlas para distinguir saves de ROMs en la misma carpeta
- **BIOS**: no hay lista canónica de BIOS en el código; usar heurística: archivos `.bin` en raíz o en subcarpetas sin ROM conocido del mismo nombre → candidato BIOS. Mostrar preview con dry_run antes de mover.
- **Android**: si la ruta Android no está accesible, mostrar warning pero no bloquear la creación en PC
- **Idempotente**: la herramienta ya usa `exist_ok=True` — se puede ejecutar varias veces sin problema

---

## ⚠️ Tareas de usuario (sin código)

### STRUCT-4 — Configurar RetroArch PC
1. RetroArch → **Settings → Saving → Savefile Directory** → `E:\Carpetas anbernic\saves\`
2. Mueve manualmente los saves existentes a esa carpeta

### STRUCT-3 — Actualizar config.toml (después de STRUCT-4)
```toml
[[sync.sources]]
name      = "RetroArch"
local_dir = "E:\\Carpetas anbernic\\saves"   # antes apuntaba a la raíz
```

### V4 — RetroAchievements con API key real
retroachievements.org → Settings → Web API Key → pegar en Ajustes de la app

---

## 🔴 Validación en hardware

| ID | Tarea | Prerequisito |
|----|-------|--------------|
| V1 | Sync automático con SD card | STRUCT-4 hecho |
| V2 | Migración a dos bases de datos | — |
| V3 | Inbox end-to-end ⭐ Pilar 2 | inbox_path configurado |
| V5 | Guía Termux en la consola Android | — |
| B1 | Renombrador en consola Android no reduce la cola | SD conectada |

---

## 🟡 Features de producto (código)

### F7 — "Missing in action"
Cruzar colección con DAT completo para ver qué juegos faltan por plataforma. Lista de deseos en BD.
**Esfuerzo:** 4-6 h · **Archivos:** `catalog/`, `database/`, `server.py`, `frontend.py`

### F9 — WiFi sync directo (Termux)
**Prerequisito:** V5 completado.
**Esfuerzo:** 6-8 h

### F11 — Plugin de plataforma (`platforms.toml`)
Mover definiciones de plataforma a archivo externo.
**Esfuerzo:** 5-7 h

---

## 🟢 Pulido UX (código rápido, del audit Día 12)

| ID | Fix | Esfuerzo |
|----|-----|----------|
| B-UI-1 | Empty state Android más específico | 15 min |
| B-UI-2 | Botón "Recalcular plan" en conflictos de disco | 30 min |
| B-UI-3 | Mensaje de duplicados más descriptivo | 10 min |
| B-UI-4 | Tooltips en botones destructivos | 15 min |

---

## 🛠️ Skills recomendados

| Skill | Cuándo |
|-------|--------|
| `/test-pipeline` | Al inicio de cada sesión |
| `/db-check` | Tras STRUCT-6 si se añaden columnas |
| `/ui-audit` | Tras STRUCT-6e (nuevo checkbox Android) |
| `/revisar` | Tras implementar F7 |

---

## Orden recomendado para esta sesión

1. **STRUCT-6a/b/c/d/e** — herramienta de estructura completa (código, ~2 h)
2. **STRUCT-4** (tú) → después **V3 Inbox** con la consola
3. **V1 SD sync** con la SD física
4. **B-UI-1/2/3/4** — pulido rápido entre pruebas
5. Si todo verde → **F7 "Missing in action"**
