# Estructura estandarizada de sync — PC2 ("Ruben") ↔ rammu (PC principal) ↔ Anbernic

Diseñado sin acceso a rammu (2026-09-19), a partir de lo ya documentado en
`CLAUDE.md`, `Tareas/backlog.md` (`DEVPROFILE-*`, `LIBRARY-ANDROID-STALE-1`,
`STRUCT-3/4`) y `.claude/roadmaps/20-rammu-machine-pending.md`. Pendiente de
aplicar/verificar en rammu cuando haya acceso — ver "Checklist para rammu"
al final.

## Lo que NO hace falta unificar

`library_root` absoluto es y debe seguir siendo distinto por máquina
(`E:\Carpetas anbernic` en rammu, `F:\Juegos Retro` en Ruben) — `config.toml`
ya abstrae esto, y las rutas locales de cada emulador (`local_dir` en
`[[sync.sources]]`) son inevitablemente distintas por máquina (cada usuario
instala los emuladores donde quiere). Forzar rutas absolutas idénticas no
aporta nada y sería frágil.

## Lo que SÍ hay que unificar

### 1. Slugs de plataforma bajo `library_root` (ya decidido, solo confirmar en rammu)

Minúscula, convención Android (`gba`, `psx`, `n64`, `gb`, `gbc`...), nunca
Title Case (`Game Boy Advance`, `PlayStation`) — decisión ya tomada en
`DUALFOLDER-12` (2026-09-18) y consistente con lo que `LIBRARY-ANDROID-STALE-1`
confirmó que rammu YA usa hoy (`gb/`, `gba/`, `gbc/` en minúscula, verificado
2026-09-09). No debería hacer falta tocar nada aquí, solo confirmarlo.

### 2. `saves/` y `states/` planos bajo `library_root` (convenio "D2", ya existe)

`library_root/saves/` y `library_root/states/` — el mismo convenio que
`DEVPROFILE-2` ya escribe en `retroarch.cfg`
(`savefile_directory`/`savestate_directory`) vía el botón "Aplicar layout de
saves" (Settings → `POST /api/retroarch-apply-savefile-layout`).
`DEVPROFILE-7` ya detectó una vez que rammu se había desviado de esto
(`savefile_directory` apuntando a `E:\ROMs\saves`, ruta obsoleta) y se
corrigió aplicando el layout — es decir, **rammu ya debería cumplir este
convenio**, solo hay que re-verificarlo (puede haber vuelto a desviarse).

### 3. Convención de rutas remotas en Dropbox (el hueco real)

PC2 ya sigue un patrón limpio y consistente en sus `[[sync.sources]]`
(`config.toml`, gitignored):

```
dropbox:/RetroSync/saves/<emulador>/<tipo>
```

Ejemplos reales de esta máquina: `dropbox:/RetroSync/saves/retroarch/saves`,
`.../retroarch/states`, `.../dolphin/gc`, `.../dolphin/wii`,
`.../duckstation`, `.../pcsx2`. **Esta es la convención a copiar en rammu
tal cual**, con los mismos nombres de emulador/tipo — el `local_dir` de cada
entrada sí puede (y debe) apuntar a la ruta real de cada emulador en rammu.

### 4. Reconciliar los dos contratos de sync (decisión ya tomada: `sync.sources` gana)

Hay dos mecanismos de cloud sync en el proyecto que hoy no están
sincronizados entre sí:

- `sync.sources` (multi-fuente, el que de verdad usa el daemon de auto-sync
  de esta sesión — `EMU-SYNC-WATCH-1`/`CABLE-SYNC-WATCH-1`).
- `sync.saves_remote` / `sync.states_remote` (el contrato más simple que usa
  `rommgr sync-saves` por CLI y que la app Android nativa asume como origen
  de verdad — `Tareas/Roadmap-Android-Sync.md` §1).

El usuario ya decidió que `sync.sources` es el contrato canónico. Para no
tener que tocar código de la app Android (que sigue esperando
`saves_remote`/`states_remote`), la solución más barata es **rellenar esos
dos campos apuntando al mismo remoto que ya usa la entrada "RetroArch" de
`sync.sources`**:

```toml
[sync]
saves_remote = "dropbox:/RetroSync/saves/retroarch/saves"
states_remote = "dropbox:/RetroSync/saves/retroarch/states"
```

Así `rommgr sync-saves`, la app Android y el daemon de `sync.sources` leen
del mismo sitio en Dropbox sin divergir — sin tocar el código Kotlin de la
app. **Aplicar esto en ambas máquinas** (PC2 y rammu), no solo en rammu.

## Checklist para rammu — ejecutado 2026-09-22 (Día68, petición del usuario)

1. [x] `cat config.toml` — `library_root=E:\Carpetas anbernic`, ya tenía
   `[[sync.sources]]` (7 entradas) **y** `saves_remote`/`states_remote`,
   ambos ya con la convención `dropbox:/RetroSync/saves/<emulador>/<tipo>`
   pedida en la sección 3/4 de arriba — aplicado en algún momento sin
   marcar este checklist.
2. [x] Slugs de plataforma en minúscula bajo `library_root` — confirmado
   hoy mismo en la sesión (psx, gba, nds, gb... todo minúscula, verificado
   contra el dispositivo real vía ADB).
3. [x] `GET /api/retroarch-check` — **sí había `savefile_drift: true`**:
   `savestate_directory` roto (`":\states"`, sin unidad/ruta — probable
   corrupción o edición manual accidental de `retroarch.cfg`). Aplicado
   "Aplicar layout de saves" (`POST /api/retroarch-apply-savefile-layout`,
   backup automático en `retroarch.cfg.bak`) — corregido a
   `E:\Carpetas anbernic\states`. **Hallazgo real**: con la ruta rota,
   RetroArch llevaba desde marzo escribiendo savestates en su propio
   fallback (`E:\Emuladores\Retroarch\states\`, 9 subcarpetas por core,
   actividad hasta el día anterior) — nunca sincronizados. Migrados
   (copiados, sin borrar el origen) a la ruta correcta.
4. [x] `[[sync.sources]]` ya usaba la convención correcta (ver punto 1) —
   sin cambios necesarios, salvo retirar `MelonDS (NDS)` (`local_dir`
   apuntaba a una carpeta inexistente en este PC, melonDS no está
   instalado aquí — confirmado por el usuario, entrada eliminada).
5. [x] `saves_remote`/`states_remote` ya coincidían con la sección 4 (ver
   punto 1).
6. [x] `rommgr sync --quiet` (dry-run) — limpio tras el fix: 0 errores
   (antes 2: el directorio de states inexistente y MelonDS).
7. [x] **Aplicado en real** (confirmado por el usuario): `rommgr sync
   --apply` — 14 archivos subidos a Dropbox (incluye los savestates de
   RetroArch nunca respaldados), 0 descargados, 0 conflictos, 0 errores.
   Re-verificado tras retirar MelonDS: 255 archivos ya al día, 0
   pendientes, 0 errores. **Punto 7 original (comparar contra PC2/Ruben)
   sin hacer** — no hay acceso a esa máquina desde aquí, pendiente de
   validar cuando se pueda comparar ambos lados.

## Pendiente de decidir después (fuera de alcance de este documento)

- `DEVPROFILE-8b` (bases de datos SQLite sueltas, no carpetas — sin
  resolver en el backlog) y `DEVPROFILE-9` (`.lpl`, `.lrtl`, credenciales RA
  cifradas) — mismo bloqueo de diseño ya identificado antes de esta sesión,
  no algo nuevo que haya que resolver para este documento.
- Si en el futuro se quiere evitar mantener `sync.sources` a mano por
  máquina, `rommgr restore` (Device Profile) ya sabe reescribir
  `config.toml` completo desde un manifiesto con rutas tokenizadas
  (`{ROMS}`, `{SAVES}`...) — candidato natural para generar estas entradas
  automáticamente en vez de copiarlas a mano, pero es un cambio de alcance
  mayor que esta estandarización puntual.
