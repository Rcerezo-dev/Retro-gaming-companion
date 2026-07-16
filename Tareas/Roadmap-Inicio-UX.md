# Roadmap — Pestaña Inicio: auditoría UX (2026-07-13)

Auditoría de la pestaña **Inicio** (`tab-overview.html` + `js/tabs/overview.js`)
desde la perspectiva de un usuario que abre la app por primera vez.
Cada ítem tiene ID `INICIO-UX-n` para poder referenciarlo desde el backlog.

---

## UI Audit — Retro Vault (pestaña Inicio)

### 🔴 Crítico (rompe la experiencia)

**INICIO-UX-1 — Botones rápidos del dashboard rotos (Sync / Scan / Inbox)**
`tab-overview.html:26-28` — los `onclick` contienen comillas escapadas al
estilo Python: `onclick="showTab(\'sync\')"`. Los partials se sirven tal cual
(frontend.py solo resuelve `<!--INCLUDE:...-->`, no procesa escapes), así que
el navegador recibe `showTab(\'sync\')` → **SyntaxError** al hacer clic. Los 3
botones de acción rápida de la barra superior no hacen nada. Residuo de la
extracción de `frontend.py` (los `\'` eran escapes del string Python).
Fix: quitar los backslashes (`onclick="showTab('sync')"`).

**INICIO-UX-2 — Canvas con colores `var(--c-*)` inválidos (gráficos rotos/engañosos)**
`overview.js:270` — el array `colors` del gráfico mensual usa strings
`'var(--c-blue)'` como `ctx.fillStyle`. Canvas **no resuelve variables CSS**:
la asignación se ignora y se queda el fillStyle anterior → barras negras o del
color de la serie previa. El propio código lo reconoce en la línea 322
("canvas can't resolve CSS vars") pero solo lo corrige para el texto de la leyenda.
`overview.js:166` — mismo bug en `_getHeatmapColor`: intensidad 0 devuelve
`'var(--c-deep)'` (ignorado) → tras pintar una celda verde, las celdas sin
actividad siguientes **se pintan verdes** (heatmap miente).
Fix: reemplazar por hex literales en ambos sitios.

**INICIO-UX-3 — Dos heatmaps de actividad duplicados**
`tab-overview.html:254-267` ("Mapa de actividad — últimos 365 días", canvas
S36-2) y `tab-overview.html:301-305` ("Actividad — últimas 52 semanas", grid
CSS, D). Miden lo mismo con dos estéticas distintas y ambos se renderizan.
Para un usuario nuevo es confuso y duplica llamadas. Fix: quedarse con el grid
CSS (D, `loadActivityHeatmap` — usa endpoint dedicado `/api/activity-heatmap`
y clases de tema) y borrar el canvas S36-2 (además es el que tiene el bug
INICIO-UX-2 del heatmap).

### 🟡 Moderado (confunde al usuario)

**INICIO-UX-4 — Tarjetas de stats en inglés**
`overview.js:449-455` y `537-543` — labels "Games", "Matched", "Unmatched",
subs "% matched", "wasted"; `overview.js:731` "game(s)" en el grid de
plataformas; `overview.js:432-436` "(not set)" en el resumen de config.
El resto de la pestaña está en español. Fix: "Juegos", "Identificados",
"Sin identificar", "X% identificados", "desperdiciados", "juego(s)",
"(sin configurar)".

**INICIO-UX-5 — No se explica qué son los archivos no-gaming (petición directa del usuario)**
La tarjeta "Assets" (`overview.js:453`) muestra un número sin contexto; BIOS,
saves y la infraestructura MAME ni aparecen. Un usuario primerizo ve "Assets: 214"
y no sabe si es bueno, malo o borrable. **Propuesta**: sección "Qué hay en tu
biblioteca además de juegos" con tarjetas explicativas (ver Fase 3 abajo).
Reutiliza las categorías ya definidas en `builders/folders.py:51-96`
(`_ZIP_CAT_BIOS`, `_ZIP_CAT_INFRA`, confianza por categoría) — no inventar
una clasificación nueva.

**INICIO-UX-6 — Errores crudos sin acción**
`overview.js:514,546,668` — si `/api/status` falla, la columna muestra
`e.message` pelado (p. ej. "Failed to fetch") sin explicar qué pasó ni ofrecer
reintento. Fix: mensaje en español + botón "Reintentar" que relance
`loadOverview()`.

**INICIO-UX-7 — El wizard usa `alert()` nativo**
`overview.js:811,836` — validación y errores del asistente con `alert()`,
mientras el resto de la app usa toasts (`showToast`). Rompe la estética en el
peor momento posible: la primera ejecución. Fix: usar toast/mensaje inline en
el modal.

**INICIO-UX-8 — Tres nombres para la misma acción de escanear**
"⟳ Scan" (barra dashboard), "Scan" (Gestión de biblioteca), "Escanear ahora"
(columna Android). Misma operación, tres etiquetas, dos idiomas. Fix:
"Escanear" en todos; el botón de la barra puede decir "Escanear PC".

**INICIO-UX-9 — "salud biblioteca: sin datos" es un callejón sin salida**
`overview.js:477` — si nunca se ejecutó el health check muestra "sin datos"
sin decir cómo obtenerlos. Fix: convertirlo en link/CTA "Ejecutar health check
→" (Herramientas).

**INICIO-UX-10 — Triple fetch de `/api/status` y triple `/api/games?limit=10000`**
`loadOverview` pide `/api/status` 3 veces (`:446`, `:561`, `:634` — solo cambia
el cache-buster) y el heatmap canvas, la sugerencia y el gráfico mensual piden
cada uno `/api/games?limit=10000` (`:111`, `:195`, `:237`). En una biblioteca
grande, abrir Inicio dispara ~6 peticiones pesadas. En red local va "solo
lento", pero es el primer tab que ve el usuario. Fix: un solo fetch de cada
endpoint compartido entre secciones (se elimina 1 de los 3 `/api/games` gratis
al borrar el heatmap duplicado de INICIO-UX-3).

### 🟢 Menor (pulido)

**INICIO-UX-11 — Clicabilidad de tarjetas invisible**
`overview.js:45` — las tarjetas clicables solo se distinguen por
`cursor:pointer` y `title="Ver lista"`. Fix: clase CSS con hover visible
(borde/elevación) y chevron.

**INICIO-UX-12 — Leyenda del heatmap con colores hardcoded oscuros**
`tab-overview.html:260-266` — hexes fijos sobre fondo que depende del tema.
Se resuelve solo si INICIO-UX-3 elimina ese bloque.

**INICIO-UX-13 — Sugerencia de juego con imagen rota visible**
`overview.js:288` — `<img src="">` hasta que carga; si no hay asset, `onerror`
la oculta pero el layout salta. Fix: placeholder 🎮 como en las continue-cards.

**INICIO-UX-14 — "Fix plataformas" mezcla idiomas**
`tab-overview.html:205` — botón "Fix plataformas". Fix: "Corregir plataformas".

✅ Lo que ya está bien (no tocar): botones Scan/Identificar con estado
cargando + disabled (`scan.js:64-179`), banner de primera configuración con
checklist, guía plegable "Cómo usar Retro Vault", empty states de la columna
Android con próximo paso claro, tooltip de "salud biblioteca".

---

## Roadmap de implementación

Cada fase = una rama/PR pequeña. Orden por impacto/esfuerzo.

### Fase 1 — Bugs visibles (esfuerzo: XS, impacto: alto)
- [x] INICIO-UX-1: quitar `\'` de los onclick del dashboard bar
- [x] INICIO-UX-2: hex literales en canvas (colores mensual + heatmap)
- [x] INICIO-UX-3: eliminar heatmap canvas duplicado (S36-2) y su leyenda

### Fase 2 — Idioma y consistencia (esfuerzo: S)
- [x] INICIO-UX-4: labels de tarjetas en español
- [x] INICIO-UX-8: unificar "Escanear"
- [x] INICIO-UX-14: "Corregir plataformas"
- [x] Verificación final por grep sobre overview.js/tab-overview.html (el
      agente `localization-pass` audita frontend.py, pero las cadenas de
      Inicio viven ahora en partials/js)

### Fase 3 — Tarjetas explicativas de archivos no-gaming (esfuerzo: M) ⭐ petición usuario
Nueva sección en Inicio, debajo de las columnas PC/Android, visible solo si
hay datos (`total_assets > 0` o el junk-scan encontró categorías):

```
┌─ Además de juegos, tu biblioteca contiene… ──────────────────────┐
│ 🧬 BIOS (12)          🖼 Assets (214)        💾 Saves (89)        │
│ Firmware que las      Carátulas y logos     Tus partidas         │
│ consolas necesitan    para los menús.       guardadas. Se        │
│ para arrancar (PSX,   Retro Vault los       sincronizan con      │
│ GBA…). Sin ellas      descarga del          la consola desde     │
│ algunos juegos no     scraper. Borrables    Cable Sync. NUNCA    │
│ funcionan. NO borrar. y regenerables.       borrar a mano.       │
│                                                                   │
│ 🕹 Infraestructura MAME (7)      🗑 Basura detectada (31, 480 MB) │
│ ZIPs de bios/devices de arcade.  Manuales, .txt, instaladores…   │
│ No son jugables pero MAME los    Revisar y limpiar desde         │
│ necesita. NO borrar.             [Herramientas → Limpieza]       │
└──────────────────────────────────────────────────────────────────┘
```
- [x] Datos: `GET /api/library-extras` (maintenance.py) agrega conteos desde
      el junk-scan completo (`_full_junk_scan`, compartido con /api/junk-scan)
      + archivos de `bios/`; assets/saves siguen viniendo de `/api/status`.
- [x] Tarjetas con: qué es, por qué está ahí, y qué hacer (NO borrar / borrable /
      gestionar desde X) — el matiz "no borrar" es el valor real de la sección.
- [x] Cada tarjeta clicable → tab correspondiente (Assets, Games con filtro save,
      Herramientas → Limpieza).
- [x] Colapsable con estado en localStorage (`extras_collapsed`).

### Fase 4 — Errores y callejones sin salida (esfuerzo: S)
- [x] INICIO-UX-6: errores en español + botón Reintentar
- [x] INICIO-UX-7: wizard sin `alert()`
- [x] INICIO-UX-9: CTA en "salud: sin datos"

### Fase 5 — Rendimiento y pulido (esfuerzo: S-M)
- [x] INICIO-UX-10: un solo fetch de `/api/status` y `/api/games` por carga
- [x] INICIO-UX-11: hover visible en tarjetas clicables
- [x] INICIO-UX-13: placeholder en imagen de sugerencia

> Implementado completo en la rama `fix/inicio-ux` (2026-07-16), una sola PR
> en vez de 5 — los cambios eran pequeños y todos sobre los mismos 2 archivos.
> INICIO-UX-12 se resolvió solo al borrar el bloque en INICIO-UX-3.
