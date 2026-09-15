# Roadmap 12 — `fix/dual-folder-title-case-slug`

**Rama:** `fix/dual-folder-title-case-slug`
**Base:** `develop`
**Prioridad:** 🟠 P2 — no hay pérdida de datos activa, pero cada uso del Inbox/`organize-source` sobre una plataforma con carpeta legada Title Case sigue creando un segundo directorio paralelo
**Esfuerzo estimado:** M (~4-6 h: 5 consolidaciones triviales + 6 con dedup real + guard de código)
**Riesgo:** Medio — mueve/descarta archivos reales de la biblioteca (hasta 57 GB en el caso `PlayStation`); bajo si se sigue el mismo patrón ya validado hoy con `GBA-DUAL-FOLDER-1`/`PS2-DUAL-FOLDER-1` (plan/dry-run, backup implícito vía `_descartados/`, nunca sobrescribir)

---

## Origen

`GBA-DUAL-FOLDER-1` (`Tareas/backlog.md`, hallazgo 2026-09-14) y `PS2-DUAL-FOLDER-1`
(hallazgo 2026-09-15) documentan el mismo patrón: `_ES_PLATFORM_FOLDERS`
(`web/handlers/system.py:15-70`) es el mapeo que usa tanto `canonical_rel_posix()`
(`sync/android_paths.py`, cable-sync hacia la Anbernic) como
`_platform_folder_name()` (`web/inbox_pipeline.py:40-43`, organización en el PC) —
siempre el slug en minúsculas (`ps2`, `gba`...). Decisión del usuario 2026-09-15
(sesión de hoy): el slug es el canónico también en el PC, precisamente porque es
la misma tabla que ya usa la herramienta que crea las carpetas en la Anbernic —
no una convención nueva, la que ya existe.

**Medición completa 2026-09-15** contra `F:\Juegos Retro` (máquina "Ruben") de las
13 plataformas con las dos carpetas presentes a la vez (`GBA-DUAL-FOLDER-1`/
`PS2-DUAL-FOLDER-1` ya resueltas a mano hoy, quedan 11):

| Par (Title Case → slug) | Title Case | slug | Patrón |
|---|---|---|---|
| `Game Boy` → `gb` | 2 arch, 1.2M | 9597 arch, 3.9G | 🟢 trivial — Title Case casi vacío |
| `Game Gear` → `gamegear` | 646 arch, 179M | 0 arch, 0 | 🟢 trivial — slug vacío |
| `Master System` → `mastersystem` | 0 arch, 4.0K | 3 arch, 28K | 🟢 trivial — Title Case vacío |
| `Neo Geo` → `neogeo` | 288 arch, 1.8G | 0 arch, 16K | 🟢 trivial — slug vacío |
| `PlayStation` → `psx` | 611 arch, 57G | 0 arch, 0 | 🟢 trivial pero grande (57 GB a mover) |
| `Game Boy Color` → `gbc` | 81 arch, 80M | 13 arch, 13M | 🟡 ambos con contenido — dedup real |
| `Nintendo 3DS` → `3ds` | 1 arch, 2.0G | 1 arch, 2.0M | 🟡 1 archivo cada lado, tamaños muy distintos — verificar si es el mismo juego antes de asumir nada |
| `Nintendo 64` → `n64` | 22 arch, 517M | 360 arch, 5.3G | 🟡 ambos con contenido — dedup real |
| `Nintendo DS` → `nds` | 338 arch, 16G | 3 arch, 193M | 🟡 **patrón invertido** — aquí Title Case es el grande, no asumir "el slug siempre gana" |
| `Sega Mega Drive` → `megadrive` | 492 arch, 646M | 711 arch, 893M | 🟡 ambos con contenido — dedup real |
| `Super Nintendo` → `snes` | 611 arch, 853M | 679 arch, 879M | 🟡 ambos con contenido — dedup real |

5 pares son mover-y-listo (un lado vacío o casi). 6 pares necesitan el mismo
dedup real que ya usa el cable-sync (`filter_duplicate_winners`,
`services/ra_duplicates_service.py`) por `canonical_title`/SHA1 antes de tocar
nada — **no asumir que el lado más grande siempre gana** (`Nintendo DS` es el
contraejemplo medido hoy).

**Causa raíz de por qué sigue pasando**: `_platform_folder_name()`
(`web/inbox_pipeline.py:40-43`) siempre devuelve el slug — nunca comprueba si ya
existe una carpeta Title Case con contenido real para esa plataforma antes de
crear/usar el slug. Sin un guard, cualquier plataforma nueva que llegue al Inbox
con una carpeta legada Title Case reproduce este mismo patrón.

---

## Objetivo

1. Consolidar los 11 pares restantes al slug canónico (los 2 primeros,
   `GBA-DUAL-FOLDER-1`/`PS2-DUAL-FOLDER-1`, ya resueltos a mano el 2026-09-15).
2. Añadir un guard en el Inbox para que esto no vuelva a pasar con ninguna
   plataforma futura.

---

## Pasos

### Paso 1 — Consolidación trivial (5 pares, un lado vacío/casi vacío)

`Game Boy`→`gb`, `Game Gear`→`gamegear`, `Master System`→`mastersystem`,
`Neo Geo`→`neogeo`, `PlayStation`→`psx`. Mismo patrón ya usado hoy a mano para
PS2 (`shutil.move` de los pocos archivos del lado perdedor al slug, luego
`rommgr scan` de refresco) — no hace falta dedup real porque no hay colisión de
contenido. Verificar antes de mover que los 2 archivos de `Game Boy/` y el
archivo de `Nintendo 3DS/2.0MB` (ver Paso 2) no son en realidad el mismo caso
mal clasificado en la medición.

### Paso 2 — Dedup real (6 pares con contenido en ambos lados)

`Game Boy Color/gbc`, `Nintendo 3DS/3ds`, `Nintendo 64/n64`, `Nintendo DS/nds`,
`Sega Mega Drive/megadrive`, `Super Nintendo/snes`. Reutilizar
`filter_duplicate_winners()` (`services/ra_duplicates_service.py`, ya genérico
por plataforma, usado hoy por el envío GBA→Anbernic) para identificar
ganador/perdedor por `canonical_title` + logros RA — **no una comparación
ingenua de tamaño de carpeta**. El perdedor va a `_descartados/` (reversible),
nunca se borra directo. Caso especial `Nintendo 3DS`: solo 1 archivo por lado,
comprobar a mano si son el mismo juego (títulos distintos) antes de tratarlo
como duplicado — con esa diferencia de tamaño (2 GB vs 2 MB) es más probable
que sean cosas distintas (un `.3ds` completo vs. un `.cia`/parche).

### Paso 3 — Guard en el Inbox

`_platform_folder_name()` (`web/inbox_pipeline.py:40-43`): antes de devolver el
slug, comprobar si ya existe una carpeta Title Case (`PLATFORM_BY_FOLDER`,
`detection/platform_detector.py`) para la misma plataforma **con contenido
real** (no solo `media/`) que el slug no tenga — si la hay, avisar/loguear en
vez de crear el slug en silencio. Decidir si el guard bloquea (fuerza a
resolver el dual-folder primero) o solo avisa y sigue creando el slug (más
simple, consistente con la decisión "el slug es el canónico" — el aviso es
para que el usuario sepa que hay limpieza pendiente, no para bloquear el
Inbox del día a día).

### Paso 4 — Tests

- Test de `_platform_folder_name()`/el guard nuevo: carpeta Title Case con
  contenido + slug vacío → aviso; slug con contenido → sin aviso.
- No hace falta test de la migración de datos en sí (es una operación manual
  de biblioteca real, no una función pura) — solo del guard de código.

### Paso 5 — Verificación

```bash
python -m pytest tests/ -q
ruff check src/rom_manager/web/inbox_pipeline.py
ruff format --check src/rom_manager/web/inbox_pipeline.py
```

Tras cada consolidación de datos: `rommgr scan` sobre `F:\Juegos Retro` y
confirmar 0 errores, huérfanos limpiados = archivos movidos.

---

## Fuera de alcance

- Migrar el resto de la biblioteca a slugs si aparecen más plataformas con
  este patrón fuera de las 13 ya medidas — este roadmap cubre exactamente las
  11 pendientes de hoy.
- Cambiar `_ES_PLATFORM_FOLDERS` en sí (la tabla ya es correcta, el problema
  es la falta de guard, no el mapeo).

---

## Checklist

- [ ] Paso 1 — 5 pares triviales consolidados
- [ ] Paso 2 — 6 pares con dedup real consolidados
- [ ] Paso 3 — guard en `_platform_folder_name()`
- [ ] Paso 4 — tests nuevos
- [ ] Paso 5 — suite completa + ruff limpios
- [ ] Commit en rama, PR a `develop` — pendiente, requiere confirmación explícita del usuario
