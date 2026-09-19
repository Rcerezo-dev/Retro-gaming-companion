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

## Checklist para rammu (cuando haya acceso, "pasado mañana")

1. [ ] `cat config.toml` — confirmar `library_root` actual y si ya tiene
   `[[sync.sources]]` configuradas o solo `saves_remote`/`states_remote`
   (o ninguno de los dos).
2. [ ] Confirmar slugs de plataforma en minúscula bajo `library_root` (ya
   debería cumplirse — solo verificar, no debería hacer falta mover nada).
3. [ ] `POST /api/retroarch-check` (o el equivalente en la UI, pestaña
   Settings) — comprobar si `DEVPROFILE-7` reporta `savefile_drift` de
   nuevo. Si sí, pulsar "Aplicar layout de saves".
4. [ ] Añadir/editar `[[sync.sources]]` en el `config.toml` de rammu con los
   `local_dir` reales de cada emulador ahí instalado, pero **la misma
   convención de `remote` que la sección 3 de arriba** — mismos nombres de
   emulador/tipo que en PC2.
5. [ ] Rellenar `sync.saves_remote`/`sync.states_remote` igual que en la
   sección 4 (mismo valor en ambas máquinas).
6. [ ] `rommgr sync-status` (dry-run) en rammu — revisar que no proponga
   nada inesperado antes de `--apply`.
7. [ ] Con la Anbernic conectada a rammu: confirmar que `POST /api/sync`
   (o su botón en la web) sube/baja contra los mismos remotos que ya usa
   PC2 — un archivo subido desde PC2 debería aparecer como "ya sincronizado"
   (no como conflicto) al comprobar desde rammu, y viceversa.

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
