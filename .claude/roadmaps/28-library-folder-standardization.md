# Roadmap 28 — `feature/library-folder-standardization`

**Rama:** `feature/library-folder-standardization`
**Base:** `develop`
**Prioridad:** 🟡 P3 — cross-cutting (Pilar 1 + compatibilidad multi-launcher), ninguna de las dos tareas es un bug
**Esfuerzo estimado:** S para la decisión (Paso 1), M-L para `ROMHACK-ORG-1` una vez decidida la convención
**Riesgo:** Bajo-medio — `ROMHACK-ORG-1` toca el pipeline de Inbox/organize; debe respetar "nunca eliminar ni sobreescribir sin política de conflictos documentada"

---

## Origen

`ESDE-FOLDER-STD-1`, `ROMHACK-ORG-1` (`Tareas/backlog.md`, epic nuevo
"Estandarización de biblioteca multi-launcher" → #337, idea usuario
2026-09-22). `ESDE-FOLDER-STD-1` fusiona la idea ya abierta
`ROADMAP-IDEAS/ESDE-CONFIG-CHECK` (2026-08-29), que asumía sin verificar que
no había integración ES-DE — el código real ya genera `gamelist.xml`,
metadata Pegasus y systems/cores.

`ROMHACK-ORG-1` nace de un ejemplo real del usuario: `E:\Juegos nativos`
contiene "Twilight Princess - Dusklight", un hack de fans sobre la ROM base
de Wii/GameCube — no es un dump oficial, no tiene entrada en No-Intro/
Redump, no matchea por hash. El usuario confirmó explícitamente que **no**
quiere un catálogo propio de ROM hacks (demasiados proyectos de fans para
mantenerlo) — el alcance real es solo organización, no matching.

---

## Objetivo

1. Cerrar la duda real de qué falta (si algo) en la integración ES-DE.
2. Que un ROM hack/fan project sin match de catálogo se organice en su
   carpeta de plataforma real en vez de caer en `Unknown/`.

---

## Pasos

### Paso 1 — `ESDE-FOLDER-STD-1`: sesión de decisión (sin código)

Listar contra el código real qué genera hoy el proyecto para ES-DE:

- `scraper/gamelist_writer.py` — `gamelist.xml`
- `scraper/pegasus_writer.py` — metadata Pegasus
- `esde/systems_generator.py` — sistemas/cores (ya en uso para iiSU vía
  `IISU-CONFIG-1`)

Confirmar con el usuario, uno por uno: ¿esto ya cubre su caso de uso con
ES-DE en Android/PC? Si falta algo concreto (p. ej. `es_systems.cfg`/rutas
específicas — ver `DEVPROFILE-4`, marcado "sin cambio" en su momento),
documentarlo como su propia tarea antes de implementar nada. Si no falta
nada, cerrar `ESDE-FOLDER-STD-1` como "confirmado, sin cambio" y
documentarlo en el backlog — no inventar trabajo que no hace falta.

### Paso 2 — `ROMHACK-ORG-1`: decidir la heurística de detección

Sin catálogo propio de hacks (decisión ya tomada por el usuario), la señal
de "esto es un hack, no basura" tiene que salir de otra parte. Opciones a
evaluar con el usuario antes de implementar:

- Extensión + tamaño compatible con la plataforma base, combinado con que
  el archivo NO matchea ningún hash conocido (ya lo sabe el pipeline hoy,
  es lo que hoy lo manda a `Unknown/`).
- Carpeta de origen como señal (si el usuario suelta algo en una carpeta
  `Juegos nativos`/`hacks`, tratarlo distinto que algo suelto en el Inbox
  genérico).
- Nombre del archivo (heurística más débil y menos fiable — mismo problema
  que ya documentó `ARCADE-DAT-CONTAMINATION` sobre confiar en el nombre).

### Paso 3 — Decidir el destino final

¿Misma carpeta de plataforma que el juego base (`gamecube/`, `wii/`) o una
subcarpeta dedicada (`gamecube/hacks/`)? Confirmar con el usuario — afecta a
cómo Juegos/ES-DE los lista después.

### Paso 4 — Implementación

`catalog/matcher.py` (punto donde hoy se decide "sin match" →
`Unknown/`) y `web/inbox_pipeline.py` (paso de organización): cuando un
archivo no matchea pero pasa la heurística del Paso 2, organizarlo según lo
decidido en el Paso 3 en vez de dejarlo en `Unknown/`. Sin matching por
hash — solo organización.

### Paso 5 — Tests

- Un archivo con la heurística de hack (ej. tamaño/extensión de plataforma
  conocida, sin match de hash) se organiza en el destino decidido, no en
  `Unknown/`.
- Un archivo realmente no reconocible (basura real) sigue cayendo en
  `Unknown/` sin falsos positivos.

### Paso 6 — Verificación

```bash
python -m pytest tests/ -q
ruff check src/rom_manager/catalog/matcher.py src/rom_manager/web/inbox_pipeline.py
```

---

## Fuera de alcance

- Cualquier forma de matching/catálogo para ROM hacks — decisión explícita
  del usuario de no mantener eso.
- Metadata/scraping específico para hacks (portada, descripción) — fuera de
  pedido original, no inventar.

---

## Checklist

- [ ] Paso 1 — decisión ES-DE cerrada con el usuario (o confirmado "sin cambio")
- [ ] Paso 2 — heurística de detección de ROM hacks decidida
- [ ] Paso 3 — destino final (misma carpeta vs subcarpeta) decidido
- [ ] Paso 4 — implementación en matcher/inbox_pipeline
- [ ] Paso 5 — tests nuevos
- [ ] Paso 6 — suite completa + ruff limpios
- [ ] Commit en rama, PR a `develop` — pendiente, requiere confirmación explícita del usuario
