# Retro Vault — Contexto del proyecto

Herramienta local Python + interfaz web (`http://127.0.0.1:7777`) para gestionar ROMs retro y sincronizar saves entre PC y consola Android.
Backlog: `Tareas/backlog.md` es solo el **índice** (tabla de pendientes); el detalle vive en `Tareas/backlog/<epic>.md` y lo cerrado en `Tareas/backlog/hecho/`.
**Nunca leas un epic entero** (hasta 1.300 líneas): `grep -rn "ID-DE-TAREA" Tareas/backlog/` y lee solo esa sección. Estado de fases: memoria `phases.md`.
CI/CD y GitHub Actions: `docs/ci-cd.md` (lint+format+pytest, branch protection, CodeRabbit, hooks pre-commit/pre-push, recetas y gotchas).

## Los 3 pilares (en orden de prioridad real)

1. **Primera vez** — limpiar y organizar una biblioteca caótica (basura fuera, ZIPs descomprimidos, ROMs renombrados con nombre canónico No-Intro/Redump, en su carpeta de plataforma).
2. **Día a día** — Inbox: soltar un juego sin organizar y que la herramienta detecte plataforma, descomprima, empareje con catálogo y lo mueva solo, sin intervención manual.
3. **Uso cotidiano — sync de saves** (**valor diferencial real**): jugar en Anbernic o PC, que la partida aparezca sola en el otro lado, sin miedo a sobreescribir. Cualquier bug aquí es prioridad absoluta (pérdida de progreso).

Todo lo demás (RA checker, scraper, health check, duplicados, informes) es secundario. No es un launcher/front-end de emuladores — no reemplaza RetroArch/EmulationStation. Detalle: memoria `vision_core.md`.

---

## Entorno de ejecución

- Conda: `C:\Users\rammu\anaconda3\envs\rom_manager` (Python 3.12)
- Lanzador: `scripts\rommgr.cmd`
- Directo: `C:\Users\rammu\anaconda3\envs\rom_manager\python.exe -m rom_manager <cmd>`
- `chdman` en `tools/chdman.exe` — NO en PATH
- `adb` en `tools/adb.exe`

---

## Gestión de tareas: Issues (roadmap) + Backlog (detalle)

Dos capas, cada una con su rol — no duplicar contenido entre ellas:

- **GitHub Issues, label `epic`** — roadmap de alto nivel. Un issue por tema/pilar
  (p. ej. "Pilar 2 — Inbox automático", "Distribución / Release"). Se usan para
  visibilidad y discusión, no para el detalle de implementación — pero el cuerpo
  del issue lleva una checklist (`- [ ]`/`- [x]`) con los IDs de tarea de su
  sección del backlog, sincronizada dinámicamente (ver regla de checklist abajo).
- **`Tareas/backlog.md` + `Tareas/backlog/<epic>.md`** — desglose operativo (índice + detalle por epic). Cada epic tiene una sección propia
  con una tabla de tareas con ID (mismo patrón que `PHASE6-*` o `EMULATOR-COMPAT-*`
  ya existentes), y la sección enlaza al issue: `→ #NNN`. Este archivo sigue siendo
  la fuente de verdad para el trabajo del día a día.

Flujo al surgir un tema nuevo:
1. Crear el issue en GitHub con label `epic` (alto nivel, sin desglosar).
2. Añadir una sección correspondiente en `backlog.md` con tabla de tareas ID-tagged,
   enlazando al número de issue.
3. Trabajar siempre contra `backlog.md` (rama por tarea, PR a `develop`, como ya
   se describe abajo). El issue lleva una checklist en el cuerpo con los IDs de
   tarea de su sección — al marcar una tarea ✅ en el backlog, marca también su
   checkbox en el issue correspondiente (`gh issue edit NNN --body-file` o la API,
   nunca a mano en la web). No hace falta comentar cada tarea; se cierra el issue
   cuando su checklist esté 100% marcada.

No confundir con `.claude/roadmaps/*.md` — esos son roadmaps técnicos paso a paso
para una rama de refactor concreta (ver `.claude/roadmaps/INDEX.md`), un nivel de
detalle distinto y con su propio índice.

**Una sola fuente de estado**: `Tareas/backlog.md` (y los `backlog/<epic>.md` que indexa) es el único sitio que dice si
una tarea está hecha o pendiente. `.claude/roadmaps/*.md` es solo el plan (pasos,
código, criterios de verificación) — no lleva checklist de estado propio; cuando
ya no le queda nada pendiente en el backlog, se archiva a `.claude/roadmaps/archivo/`.
`.claude/roadmaps/INDEX.md` solo distingue Activo/Archivado/Obsoleto por rama, sin
repetir el detalle. Evita el patrón visto varias veces (roadmaps 08-11, 14, 17):
el mismo hecho actualizado en 2-3 sitios, y basta con que uno se quede atrás para
que el registro mienta.

---

## Reglas de trabajo

- `rommgr plan` siempre antes de `rommgr apply`
- Nunca eliminar ni sobreescribir sin política de conflictos documentada
- PSX siempre por sets: nunca renombrar `.bin` sin reescribir el `.cue`
- BIOS, assets y carpetas Android nunca se tratan como ROMs
- Toda operación sobre archivos se registra en SQLite
- La biblioteca debe ser compatible con RetroArch en Android Y en PC
- En sync: ante duda, no sobreescribir; guardar backup primero
- Sin dependencias externas de runtime (solo stdlib)
- Usa Siempre los principios SOLID 
        El Principio de responsabilidad única (Single Responsibility Principle)
        El Principio Abierto-Cerrado (Open-Closed Principle)
        El Principio de sustitución de Liskov (Liskov Substitution Principle)
        El Principio de segregación de interfaz (Interface Segregation Principle)
        El Principio de inversión de dependencia (Dependency Inversion Principle) 
- **No vuelvas a leer archivos ya leídos en esta sesión a menos que te lo pida. Minimiza las llamadas a herramientas y trabaja con lo que ya tienes en contexto.**

### Investigar antes de arreglar

Cuando aparece un síntoma (archivos que no deberían estar donde están, un
número que no cuadra, un flujo que se queda a medias): verifica primero contra
la biblioteca real o la BD, no contra suposiciones — y sigue la cadena hasta la
causa raíz en el código, no solo el síntoma. No implementes el fix en la misma
sesión salvo que el usuario lo pida explícitamente: documenta el hallazgo con
archivo:línea exactos y añádelo al backlog (sección en `Tareas/backlog/<epic>.md` + fila en la tabla de `Tareas/backlog.md`) para que se
implemente en su propia rama. Patrón ya usado en JUNK-FIX-*/INBOX-FIX-* (Día39).

---

## Patrones críticos

Detalle y código en [`docs/architecture/patterns.md`](../docs/architecture/patterns.md) — **léelo antes de tocar el área**. Regla corta de cada uno:

- **Jobs en background (web)**: `_job_lock`/`_jobs`/`_job_results`; el frontend sondea `/api/job-status` cada 2 s; `result_ts` evita toasts repetidos.
- **Rename atómico**: siempre `rename_rom_with_saves()`, nunca renombrar a mano (arrastra los saves).
- **Renames solo-mayúsculas (NTFS)**: conflicto solo si `target.exists()` y no `_same_file()`.
- **Config**: `_handle_save_config()` debe recargar `load_config()` en memoria tras guardar.
- **SQLite**: `repository.connect()` para leer, `repository.batch()` para escrituras en bulk.
- **Estado compartido**: vive en `rom_manager.web.state` (import a nivel de módulo); reasignar siempre vía `_state.xxx`.
- **ZIPs sueltos**: identidad por CRC32 del header, sin descomprimir; un ZIP arcade nunca se extrae ni pasa por el Inbox.
- **Estáticos**: `/static/app.css` y `/static/app.js` → `src/rom_manager/web/static/`.
