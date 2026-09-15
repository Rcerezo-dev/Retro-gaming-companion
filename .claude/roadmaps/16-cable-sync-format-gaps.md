# Roadmap 16 — `fix/cable-sync-format-gaps`

**Rama:** `fix/cable-sync-format-gaps`
**Base:** `develop`
**Prioridad:** 🟡 P3 — no bloquea el día a día (el resto de plataformas sincroniza bien), pero deja PSX/GameCube sin espejo completo en la máquina "rammu"
**Esfuerzo estimado:** S-M (~2-3 h de código + tiempo de transferencia real por ADB, fuera del control de la rama)
**Riesgo:** Bajo — son huecos de cobertura ya acotados, no bugs de comportamiento incorrecto activo

---

## Origen — máquina "rammu" (RG556, `E:\Carpetas anbernic`)

Dos hallazgos de `CABLE-ROM-FIX` (`Tareas/backlog.md`) sin resolver:

### `CABLE-ROM-FIX-5` — GameCube pendiente por espacio

Sync real de `arcade` a la RG556 (2026-08-27) terminó solo (`copied=3192
skipped=49 errors=2`, los 2 errores son el hipo transitorio conocido de
daemon ADB, no relacionado con los archivos). `gamecube` (34,3 GB) quedó sin
lanzar esa sesión, pendiente desde entonces — no es un bug, solo una corrida
que no llegó a completarse.

### `CABLE-ROM-FIX-6` — desajuste de formato PSX

Medido 2026-09-11 cruzando PC (`E:\Carpetas anbernic\`) contra el dispositivo
(ADB, `ROMs/`) por título: **el problema de formato es exclusivo de PSX**.
`ps2`/`gamecube` no tienen bloqueante de formato — solo espacio
(`CABLE-ROM-FIX-3`, ya en curso). En PSX: de 129 títulos que el dispositivo
tiene como `.cue`/`.bin`, **70 (54%) ya están convertidos a `.chd` en el
PC** — esos 70 (127 archivos, 32,75 GB) son exactamente el patrón que causó
el incidente de `TRASH-FIX-5` (un espejo `delete_extra=true` los interpreta
como "extra" a borrar por comparar solo ruta/nombre exacto, no contenido, sin
reconocer que `.chd` y `.cue`/`.bin` del mismo disco son el mismo juego).

**🟡 Decisión pendiente del usuario, sin decidir todavía**: dos caminos
alternativos, ninguno implementado:
(a) convertir también el dispositivo a `.chd` (requiere `chdman` corriendo en
Android o transferir el `.chd` ya convertido del PC);
(b) enseñar al espejo de Cable Sync a comparar por contenido cross-formato
(mismo patrón ya usado en `DUP-CROSSFMT-8`/`ARCADE-DAT-CONTAMINATION-12` para
otros casos de "mismo juego, contenedor distinto").

---

## Objetivo

1. Completar el sync de `gamecube` pendiente (`CABLE-ROM-FIX-5`) — sin
   cambio de código, solo ejecución.
2. Decidir y, si procede, implementar el reconocimiento cross-formato
   `.chd`≡`.cue`/`.bin` para que el espejo PSX deje de bloquearse
   (`CABLE-ROM-FIX-6`).

---

## Pasos

### Paso 1 — Lanzar el sync de `gamecube` pendiente

Sin código nuevo: `POST /api/cable-sync` con `pc_path`/`android_path`
apuntando a `gamecube/` (mismo patrón ya usado para `arcade` en
`CABLE-ROM-FIX-3`/`-5`). Confirmar espacio libre en la SD antes de lanzar
(34,3 GB necesarios) — el guard de espacio libre ya existe
(`CABLE-ROM-FIX-2`, `AdbTransport.free_bytes()`).

### Paso 2 — Decisión de diseño para `CABLE-ROM-FIX-6`

Presentar al usuario los dos caminos (convertir el dispositivo a `.chd` vs.
enseñar al espejo a comparar cross-formato) con sus trade-offs:
- (a) implica más trabajo en el dispositivo (transferir/convertir 32,75 GB) y
  duplica esfuerzo si el PC ya tiene el `.chd` — pero deja el dispositivo en
  el mismo formato canónico que el PC.
- (b) no mueve ningún archivo, solo cambia la lógica de comparación del
  espejo — más barato, pero el dispositivo se queda con `.cue`/`.bin` sin
  convertir indefinidamente (más espacio ocupado por disco sin necesidad,
  ~32,75 GB extra en la SD comparado con sus `.chd` equivalentes).

### Paso 3 — Implementar la opción decidida

Si se opta por (b) (comparación cross-formato): reutilizar el patrón ya
existente de `DUP-CROSSFMT-8`/`ARCADE-DAT-CONTAMINATION-12` (comparación por
contenido/título normalizado, no por nombre de archivo exacto) en el punto
del espejo de Cable Sync que decide qué es "extra" (`web/handlers/sync_cable.py`,
rama `delete_extra`) — antes de marcar un `.cue`/`.bin` del dispositivo como
"extra a borrar", comprobar si existe un `.chd` equivalente en el lado PC
para el mismo título antes de proponerlo para borrado.

Si se opta por (a) (convertir el dispositivo): investigar si `chdman` es
viable en Android (RG556 sin root, ver limitaciones ya documentadas en
`DEVPROFILE-0`) — probablemente no viable sin convertir en el PC y
transferir el resultado, lo que vuelve a acercarse al coste de (b) pero
moviendo datos en vez de solo comparación.

### Paso 4 — Tests (si se implementa código, opción b)

- Espejo con un `.cue`/`.bin` en el dispositivo y su `.chd` equivalente en
  el PC → no se marca como "extra a borrar".
- Espejo con un `.cue`/`.bin` en el dispositivo sin ningún equivalente en el
  PC (título realmente exclusivo del dispositivo) → sigue marcándose como
  "extra" normalmente (no debe volverse permisivo en exceso).

### Paso 5 — Verificación

```bash
python -m pytest tests/ -q
ruff check src/rom_manager/web/handlers/sync_cable.py
```

Verificación real: dry-run de un espejo PSX contra el dispositivo tras el fix
— los 70 títulos ya convertidos a `.chd` en el PC deben dejar de aparecer
como "a borrar" en el plan.

---

## Fuera de alcance

- El caso `Crash Bandicoot - The Wrath of Cortex.chd` (contenido exclusivo
  del dispositivo, sin equivalente en el PC en ningún formato) — no es un
  mismatch de formato, es contenido que solo existe en un lado, categoría de
  riesgo distinta que no bloquea nada de este roadmap.
- Resolver el espacio de `ps2`/`gamecube` más allá del Paso 1 — eso es
  `CABLE-ROM-FIX-3`, ya en curso fuera de este roadmap.

---

## Checklist

- [ ] Paso 1 — sync de `gamecube` completado
- [ ] Paso 2 — decisión de diseño confirmada por el usuario
- [ ] Paso 3 — opción decidida implementada
- [ ] Paso 4 — tests nuevos (si aplica)
- [ ] Paso 5 — suite completa + ruff limpios + verificación real contra el dispositivo
- [ ] Commit en rama, PR a `develop` — pendiente, requiere confirmación explícita del usuario
