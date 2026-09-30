# Roadmap 27 — `feature/library-ux-dashboard-duplicates`

**Rama:** `feature/library-ux-dashboard-duplicates`
**Base:** `develop`
**Prioridad:** 🟡 P3 — Pilar 1, mejora de superficie sobre datos que ya se calculan hoy
**Esfuerzo estimado:** M (~5-6 h — dos paneles independientes, mayormente frontend)
**Riesgo:** Bajo — solo lectura, no toca ninguna operación de escritura sobre la biblioteca

---

## Origen

`LIBRARY-HEALTH-DASH-1`, `DUP-VISUAL-UI-1` (`Tareas/backlog.md`, Pilar 1 →
#202, idea usuario 2026-09-22). Objetivo: dar satisfacción inmediata de
"día uno" a quien llega con una biblioteca caótica, consolidando datos que
hoy están repartidos en reportes sueltos por pestaña.

---

## Objetivo

1. Vista única de salud de biblioteca (% organizada, GB en duplicados,
   huérfanos, ZIPs sin descomprimir).
2. Resolución de duplicados con portada side-by-side + flag de RA, en vez de
   solo tabla de texto.

---

## Pasos

### Paso 1 — `LIBRARY-HEALTH-DASH-1`: inventariar fuentes de datos existentes

Los números ya existen, repartidos: `web/builders/folders.py` (organización/
ZIPs sin descomprimir), `web/handlers/junk.py` (`/api/junk-scan`, basura),
duplicados (`services/ra_duplicates_service.py` / builder de duplicados).
Confirmar los endpoints exactos de cada dato antes de diseñar el panel — el
objetivo es agregar, no recalcular.

### Paso 2 — Endpoint agregado (opcional) o composición en frontend

Decidir: ¿un endpoint nuevo `GET /api/library-health` que agregue las
llamadas ya existentes en el backend, o el frontend llama a los 3-4
endpoints ya existentes y compone la vista? Preferir la segunda opción si
ninguno es costoso — menos superficie nueva de backend (principio de menor
cambio).

### Paso 3 — Panel en pestaña Inicio

Tarjeta con los indicadores clave (% organizada, GB duplicados, huérfanos,
ZIPs sin descomprimir), cada uno enlazando a su pestaña/reporte detallado
existente — el dashboard es un resumen con acceso rápido, no reemplaza los
reportes actuales.

### Paso 4 — `DUP-VISUAL-UI-1`: vista side-by-side

`web/static/js/tabs/duplicates.js`: por cada grupo de duplicados, mostrar
portada (si hay metadata scrapeada) + flag de RA (reutilizar
`services/ra_duplicates_service.py`, ya tiene la lógica de qué versión tiene
logros) en vez de solo la tabla de texto actual. Mantener la tabla como
fallback cuando no hay portada disponible.

### Paso 5 — Tests

- Dashboard: los números mostrados coinciden con los que devuelven los
  endpoints existentes (test de integración, no solo de UI).
- Duplicados: el flag de RA se muestra igual que en el flujo de texto
  existente (mismo dato, presentación distinta).

### Paso 6 — Verificación

```bash
python -m pytest tests/ -q
ruff check src/rom_manager/web/builders/folders.py src/rom_manager/web/handlers/junk.py
```

---

## Fuera de alcance

- Cambiar cómo se calculan duplicados/huérfanos/basura — esta rama solo
  presenta los datos ya calculados de otra forma.
- Acciones masivas desde el dashboard (borrar/organizar en bloque desde ahí)
  — el dashboard es de lectura, las acciones siguen en sus pestañas.

---

## Checklist

- [x] Paso 1 — fuentes de datos confirmadas: `/api/status` (juegos, duplicados,
      GB desperdiciados), `/api/library-doctor` (`by_type.misplaced_rom`,
      `by_type.empty_dir`), `/api/library-extras` (nuevo campo `misplaced_zips`,
      suma de categorías `confidence == "misplaced"` del junk-scan, excluyendo
      BIOS que ya tenía su propio contador)
- [x] Paso 2 — composición en frontend (ninguna llamada es costosa;
      `/api/library-extras` ya cachea 15 min en el backend) — sin endpoint
      agregado nuevo
- [x] Paso 3 — panel de salud en Inicio (`ov-health-dash` en
      `tab-overview.html`, `_loadLibraryHealth()` en `overview.js`):
      % organizada, GB duplicados, carpetas huérfanas, ZIPs sin organizar —
      cada tarjeta enlaza a su pestaña/reporte existente (Herramientas o
      Revisión de copias)
- [x] Paso 4 — duplicados side-by-side con flag RA: portada de 28x28 por fila
      en `_renderReviewEntry` (`review_copies.js`), `onerror` la quita → cae al
      layout de solo texto de siempre. El flag RA ya existía (`raBadge`, sin
      cambios). Requirió exponer `id` (antes ausente) en las entries de
      `_build_review_queue`/`_review_groups_for_repo` (`web/builders/duplicates.py`)
      para poder llamar a `/api/asset-image?game_id=`. Sin portada para copias
      de la consola (`is_device`) — `/api/asset-image` solo resuelve contra la
      BD del PC, gap preexistente fuera de alcance de esta rama
- [x] Paso 5 — tests nuevos
      (`tests/web/test_library_extras.py::test_library_extras_misplaced_zips`,
      `tests/test_builders_duplicates.py::test_sha1_duplicate_group_entries_carry_game_id`)
- [x] Paso 6 — suite completa (1435 passed) + ruff limpios en los archivos tocados
- [x] Commit en rama, PR a `develop` — PR #340 abierta 2026-09-24
