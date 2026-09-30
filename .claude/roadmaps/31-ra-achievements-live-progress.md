# Roadmap 30 — `feature/ra-achievements-live-progress`

**Rama:** `feature/ra-achievements-live-progress`
**Base:** `develop`
**Prioridad:** 🟡 P3 — secundario (RA es "todo lo demás" según CLAUDE.md), y bloqueado por una dependencia externa
**Esfuerzo estimado:** S-M (~3-4 h una vez desbloqueado)
**Riesgo:** Bajo — solo lectura de la caché de RA ya existente

---

## Origen

`RA-PROGRESS-UI-1` (`Tareas/backlog.md`, RA/Scraper/SAGE → #208, idea
usuario 2026-09-22). Gancho visible del sistema RA una vez validada la API
key real.

**Bloqueado**: la memoria `phases.md` registra como pendiente real "probar
RetroAchievements con API key real — código listo (`ra_client.py`, caché 1
semana, `/api/ra-check` + panel Tools), nunca probado en producción.
Necesita que el usuario configure una API key real en Ajustes — no
automatizable sin eso." Esta rama no debería empezarse antes de que esa
validación ocurra — si `ra_client.py` tiene bugs no descubiertos por falta
de una key real, construir UI encima sería construir sobre datos sin
verificar.

---

## Objetivo

Mostrar progreso de logros (desbloqueados/totales) en la ficha de cada
juego, usando la caché de RA ya existente.

---

## Pasos

### Paso 0 — Precondición (no forma parte de esta rama)

Confirmar con el usuario que la API key real ya está configurada en
Ajustes y que `/api/ra-check` se ha corrido al menos una vez contra datos
reales (no solo contra los tests con mocks). Sin esto, no empezar el Paso 1.

### Paso 1 — Confirmar el shape de datos disponible

`ra_client.py` / `.rommgr/ra_cache/ra_hashes_{console_id}.json`: confirmar
qué campos trae la caché real (progreso por juego, o solo el hash-match
usado hoy por `ra-check`) — puede que haga falta una llamada nueva a
`API_GetGameInfoAndUserProgress.php` en vez de reutilizar solo el índice de
hashes actual.

### Paso 2 — Endpoint

Exponer progreso por juego (desbloqueados/totales) sobre la caché existente
— reutilizar el TTL de 1 semana ya establecido, no inventar una política de
caché nueva.

### Paso 3 — UI en la ficha de juego

`web/static/js/tabs/games.js`: badge o barra de progreso junto a los datos
ya mostrados por juego, solo quest visible cuando hay datos RA para ese
juego (no todos los juegos tienen soporte).

### Paso 4 — Tests

- Progreso se calcula correctamente sobre un fixture de caché conocido.
- Juego sin datos RA no rompe el render (badge ausente, no error).

### Paso 5 — Verificación

```bash
python -m pytest tests/ -q
ruff check src/rom_manager/retroachievements/ra_client.py
```

---

## Fuera de alcance

- Notificaciones en vivo de logros desbloqueados durante el juego — el
  proyecto no es un launcher/front-end de emuladores (CLAUDE.md), no hay
  proceso corriendo durante la partida que pueda detectarlo.
- Cualquier cambio a `ra_client.py` que no sea el mínimo necesario para
  exponer progreso — el Paso 0 existe justo para no construir sobre código
  sin validar en producción.

---

## Checklist

- [ ] Paso 0 — precondición confirmada (API key real validada, ver `phases.md`)
- [ ] Paso 1 — shape de datos de progreso confirmado
- [ ] Paso 2 — endpoint de progreso
- [ ] Paso 3 — UI en ficha de juego
- [ ] Paso 4 — tests nuevos
- [ ] Paso 5 — suite completa + ruff limpios
- [ ] Commit en rama, PR a `develop` — pendiente, requiere confirmación explícita del usuario
