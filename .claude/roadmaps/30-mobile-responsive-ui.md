# Roadmap 29 — `feature/mobile-responsive-ui`

**Rama:** `feature/mobile-responsive-ui`
**Base:** `develop`
**Prioridad:** 🟡 P3 — UX transversal, no bloquea ningún pilar
**Esfuerzo estimado:** M (~5-6 h — CSS responsive + ajustes puntuales de layout, sin backend)
**Riesgo:** Bajo — solo frontend (`app.css`, partials HTML), sin tocar lógica

---

## Origen

`MOBILE-UI-1` (`Tareas/backlog.md`, UX → #206, idea usuario 2026-09-22).
La app está pensada hoy para desktop; gestionar la biblioteca desde el
móvil en la misma red (el servidor ya es local-first en `127.0.0.1:7777`,
accesible desde otros dispositivos de la LAN si se expone la IP) no
requiere cambios de arquitectura, solo que el layout responda.

---

## Objetivo

Layout usable en pantalla de móvil para las pestañas de uso más frecuente
(Inicio, Juegos, Cable/Cloud) sin reescribir la UI ni añadir un layout
paralelo.

---

## Pasos

### Paso 1 — Auditoría de breakpoints actuales

`web/static/css/app.css`: confirmar si ya hay algún `@media` existente
(aunque sea parcial) antes de añadir uno nuevo — reutilizar la convención si
existe.

### Paso 2 — Sidebar colapsable

`.sidebar` (menú lateral de pestañas, ya usado en `HERR-FIX-4` como
referencia) pasa a menú hamburguesa/overlay por debajo de un breakpoint
(ej. 768px), en vez de ocupar espacio fijo.

### Paso 3 — Tablas con scroll horizontal

Mismo patrón que ya usa Juegos (`#games-list-view{overflow-x:auto}`,
`tab-games.html`) — aplicar a las tablas de Herramientas/Duplicados que
`HERR-FIX-4` ya identificó como causa probable de layout roto (sin
contenedor `overflow-x:auto`), matando dos pájaros: el bug ya documentado y
el soporte móvil.

### Paso 4 — Controles táctiles

Revisar tamaño mínimo de botones/inputs en las pestañas priorizadas
(Inicio, Juegos, Cable/Cloud) — objetivo táctil razonable (≥40px), sin
rediseñar controles que ya funcionan en desktop.

### Paso 5 — Verificación manual

Probar en viewport móvil real (DevTools +, si es posible, un móvil real en
la misma red) las 3 pestañas priorizadas: navegar, abrir un juego, lanzar un
sync. No hay test automatizado razonable para esto — verificación visual.

---

## Fuera de alcance

- Rediseño completo de la UI o un layout paralelo "modo móvil" — el
  objetivo es que la UI existente responda, no una app distinta.
- Pestañas secundarias (Formatos, SAGE, etc.) — priorizar las de uso
  diario primero; extender después si hace falta.
- PWA/instalable — no pedido.

---

## Checklist

- [ ] Paso 1 — auditoría de breakpoints existentes
- [ ] Paso 2 — sidebar colapsable
- [ ] Paso 3 — tablas con scroll horizontal (resuelve de rebote `HERR-FIX-4`)
- [ ] Paso 4 — controles táctiles verificados
- [ ] Paso 5 — verificación manual en viewport/móvil real
- [ ] Commit en rama, PR a `develop` — pendiente, requiere confirmación explícita del usuario
