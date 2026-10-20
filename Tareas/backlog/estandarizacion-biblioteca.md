## Estandarización de biblioteca multi-launcher (ES-DE + ROM hacks/fan projects) — → #337

Carpeta y convención de nombres única para PC/Anbernic que también sea
compatible con ES-DE (no solo RetroArch) y que sepa colocar ROM hacks/fan
projects (parchean una ROM oficial pero no matchean ningún hash No-Intro/
Redump — ej. "Twilight Princess - Dusklight" sobre la ROM base de Wii/
GameCube) en su plataforma real en vez de caer en `Unknown/`. Fusiona la idea
abierta `ESDE-CONFIG-CHECK` de `Roadmap-212-Ideas-Futuras.md` (movida aquí).

### ESDE-FOLDER-STD-1 — Confirmar y cerrar el hueco real de integración ES-DE (idea usuario 2026-09-22)

El proyecto ya genera `gamelist.xml` (`scraper/gamelist_writer.py`), metadata
Pegasus (`scraper/pegasus_writer.py`) y sistemas/cores
(`esde/systems_generator.py`, en uso hoy para iiSU vía `IISU-CONFIG-1`) — la
suposición de que "no hay nada" (ROADMAP-IDEAS, 2026-08-29) era incorrecta.
Falta decidir con el usuario qué hueco concreto queda: ¿`es_systems.cfg`/
rutas específicas de ES-DE en Android? (ver `DEVPROFILE-4`, marcado "sin
cambio" en su momento) ¿o ya está cerrado y solo falta documentarlo?

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| ESDE-FOLDER-STD-1 | Sesión de decisión con el usuario: listar qué genera hoy el proyecto para ES-DE contra lo que ES-DE necesita realmente en Android/PC, y cerrar la brecha si la hay | `scraper/gamelist_writer.py`, `scraper/pegasus_writer.py`, `esde/systems_generator.py` | ⬜ pendiente, decisión del usuario primero |

### ROMHACK-ORG-1 — Organizar ROM hacks / fan projects que no matchean catálogo oficial (idea usuario 2026-09-22)

Origen: `E:\Juegos nativos` contiene proyectos como "Twilight Princess -
Dusklight", un hack de fans sobre la ROM base de Wii/GameCube — no es un
dump oficial, no tiene entrada en No-Intro/Redump, así que no matchea por
hash. El usuario confirma que **no** quiere un catálogo propio de hacks
(demasiados proyectos de fans para mantenerlo) — el alcance real es que la
herramienta reconozca "esto no matchea pero tampoco es basura" y lo organice
en la carpeta de su plataforma real en vez de dejarlo en `Unknown/`.

| ID | Task | Archivo(s) | Estado |
|----|------|-----------|--------|
| ROMHACK-ORG-1 | Definir heurística para detectar ROM hacks sin catálogo (¿extensión+tamaño de la plataforma base, nombre, carpeta de origen?) y decidir destino: ¿misma carpeta de plataforma que el juego base, o subcarpeta `<plataforma>/hacks/`? Sin matching por hash — solo organización | `catalog/matcher.py`, `web/inbox_pipeline.py` | ⬜ sin diseñar — decisión de convención pendiente con el usuario antes de tocar código |

---

