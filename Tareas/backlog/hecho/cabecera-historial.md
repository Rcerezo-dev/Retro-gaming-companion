# Backlog — historial de la cabecera (hasta 2026-09-30)

> Notas de sesión que vivían en la cabecera de `Tareas/backlog.md`. Solo referencia histórica.

# Retro Vault — Backlog

> Single source of truth for pending work. Updated every session.
> Last updated: 2026-07-23 (MEJ-2/3/4/5, VAL-FIX-4/5/7, INBOX-FIX-4,
> REV43-52, TEST-GAP-1 cerrados; release v1.1.0 publicada)
> 2026-08-29: archivadas ~33 secciones completadas a archivo.md; triage de
> docs/ideas/ + docs/_archive/feedback-2026-08-29.md (DEDUP-RENAME, HERR-FIX, PSX-ORPHAN-5,
> ZIP-ROUTE-7, ANBERNIC-PICK-6/7, SAGE-4, GAME-BLOCKLIST, 5 filas nuevas en
> ROADMAP-IDEAS)
> 2026-08-30: INBOX-ORPHAN-3 arreglado (fix + limpieza de 104 carpetas huérfanas
> reales) — ver INBOX-ORPHAN-4/5, hallazgos nuevos derivados de la investigación
> 2026-08-30: INBOX-FIX-6 arreglado (ZIPs de consola ahora se descomprimen tras
> el apply; guard de `extract_zip` corregido para no bloquear `.iso` sueltos de PS2)
> 2026-08-30: INBOX-ORPHAN-4 resuelto (4 duplicados GameCube borrados, mismo
> dump peor comprimido) — hallazgo nuevo INBOX-RA-HASH-GAP (RA no compara discos)
> 2026-08-31: hallazgos LIBRARY-SYNC-STALE-1 (biblioteca corregida el 08-30 sin
> sincronizar a la Anbernic) y GBA-SAVE-PATH-1 (GBA no encuentra saves tras
> instalar emuladores nuevos, bloqueado por ADB unauthorized)
> 2026-09-01: auditoría LIBRARY-AUDIT (issue #275) — bug real en `rommgr
> duplicates` (agrupa archivos sin hash como duplicados falsos), 126,4 GB en
> `Unknown/` sin organizar, 96,4 GB de ZIPs de consola sin descomprimir, ~14,4 GB
> seguros de recuperar en duplicados de consola (arcade excluido a propósito)
> 2026-09-19: hallazgo `ANDROID-DUP-1` — duplicados reales confirmados por ADB
> en vivo contra la RG556 (PSX, GBA) + carpetas Title Case/slug paralelas nunca
> consolidadas en el dispositivo (patrón `DUALFOLDER-12`, solo aplicado en PC);
> `library_android.db` desactualizada (último scan 2026-09-12); relanzado el
> scrape completo (22.840 ROMs pendientes)
> 2026-09-22: 8 ideas de mejora propuestas por el usuario añadidas como tareas
> nuevas (SAVES-UX, INBOX-UX, LIBRARY-UX, MOBILE-UI, RA-LIVE en sus epics de
> pilar existentes → #202/#203/#204/#206/#208) + nuevo epic "Estandarización de
> biblioteca multi-launcher" (→ #337, ESDE-FOLDER-STD-1 fusiona
> ROADMAP-IDEAS/ESDE-CONFIG-CHECK, ROMHACK-ORG-1 nuevo). Ninguna implementada
> todavía — todas ⬜ sin diseñar. Roadmap por rama creado (`.claude/roadmaps/
> INDEX.md`, 6 ramas nuevas 25-30, fases 1-6). Añadida 9ª tarea
> `SYNC-CONFLICT-MANUAL-1` (revisión manual de conflictos de Cloud Sync) tras
> verificar contra el código real que hoy se auto-resuelve siempre por policy
> global — agrupada en la rama `feature/saves-ux-history-context` (roadmap 25)
> por compartir fichero con `SAVES-CONFLICT-CTX-1`, no rama nueva
> 2026-09-26: `NATIVE-SAVE-SYNC-1` — biblioteca, emuladores y juegos nativos
> consolidados en `E:\RetroVault\` (`ROMS`/`EMULADORES`/`JUEGOS NATIVOS`);
> 129.654 filas reescritas en `library_pc.db`; sync de saves extendido a
> juegos nativos (Dusklight/Twilight Princess) reutilizando `sync_sources`
> sin código nuevo
> 2026-09-29: `CHD-CLEANUP-1` nuevo comando `rommgr clean-redundant-chd`
> (PR #376) aplicado real contra `psx/` en la Anbernic — 17/19 candidatos
> verificados por hash RA y borrados, 11,49 GB liberados, 0 errores; 2
> saltados de forma segura (sheets `.cue` rotas). `GDI-ORGANIZE-1` bug 1
> arreglado (PR #377) — `build_plan()` ya no adivina mal el destino de
> PSX/Saturn/Dreamcast/Wii cuando el origen no está en su carpeta de
> plataforma
> 2026-09-30: rescatadas `feature/saves-ux-history-context` (roadmap 25,
> PR #338) y `feature/inbox-ux-summary-metadata` (roadmap 26, PR #339) —
> llevaban abiertas desde el 22-25/09 con trabajo completo, bloqueadas por
> conflictos reales contra los 5 días de `develop` que avanzaron mientras
> tanto; roadmaps 28/29/30 renumerados a 29/30/31 (28 ya lo ocupaba
> `android-gdrive-provider`, sesión aparte) y el roadmap 27 (ya completado
> vía PR #340) retirado del índice por duplicado
> 2026-09-30 (continuación): instancia real (puerto 7777) reiniciada con el
> código de hoy. `ANDROID-DUP-CROSSFMT-VERIFY-1` cerrado del todo (89 grupos
> PSX verificados por hash real, 2 seguros aplicados, 0,48 GB). Dedup GBC
> aplicado (1268 grupos, 1,95 GB) + Sega Mega Drive/SNES/Game Boy/N64DD/1 PSX
> sha1-puro (96 grupos, 0,145 GB) — ~2,58 GB liberados en total, 0 errores
> reales, verificado en el dispositivo real. Causa raíz de las filas fantasma
> de `ANDROID-DUP-PSX-1` encontrada (scan `psx` interrumpido el 28/09, nunca
> reconciliado) — documentada, sin arreglar
> Completed tasks → `Tareas/diario/archivo/archivo.md`
> Arquitectura actual: `docs/architecture/architecture.md`
> Organizado por épica de GitHub (2026-08-15) — convención en `.claude/CLAUDE.md` § Gestión de tareas.

Regla de branching: una rama por tarea → PR a `develop`. Las sub-tareas que comparten
fichero o son la misma unidad de cambio se agrupan en una sola rama. Refactores
grandes de un fichero van **siempre separados**. Flujo completo: `CONTRIBUTING.md`.

---

