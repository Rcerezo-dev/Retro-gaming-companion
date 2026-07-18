# Roadmap — Pestaña Colección: auditoría UX + ¿fusión con Juegos? (2026-07-13)

Auditoría de la pestaña **Colección** (`tab-collection.html` +
`js/tabs/collection.js`) desde la perspectiva de un usuario que quiere ver
su biblioteca como galería y consultar estadísticas globales. Cada ítem
tiene ID `COLECCION-UX-n`. Además de la auditoría, esta pestaña plantea una
pregunta de arquitectura que respondo abajo con datos del propio código:
**¿deberían fusionarse Colección y Juegos?**

---

## ¿Fusionar Colección y Juegos?

Comparando el código de las dos pestañas (`tab-games.html`+`games.js` vs
`tab-collection.html`+`collection.js`):

- **Ambas pintan una galería de juegos casi idéntica.** Colección
  (`col-grid`, `collection.js:269-308`) y la vista cuadrícula de Juegos
  (`games-grid`, ya existente vía `setGamesView('grid')`) llaman al **mismo
  endpoint** `/api/games` y abren el **mismo panel de detalle**
  (`window.openGamePanel(g)`, `collection.js:278`). La diferencia es que
  Colección solo tiene 3 controles (buscar, plataforma, orden) mientras
  Juegos tiene 9 (buscar, plataforma, matched, tipo de archivo, estado de
  juego, favoritos, tags, género, año, orden) — Colección es un
  **subconjunto con menos filtros del mismo listado**, no una vista
  distinta.
- **El botón de exportar CSV/JSON da resultados distintos según la pestaña.**
  El de Juegos (`tab-games.html:46-47`, enlace directo a
  `/api/export-library?format=csv`) no manda `root` — ignora el
  dispositivo activo. El de Colección (`exportCollection()`,
  `collection.js:311-330`) sí manda `root=_deviceRoot()`. Pulsar "Exportar
  CSV" en una pestaña o en la otra puede dar un número de filas distinto
  sin que nada lo explique — ver COLECCION-UX-3.
- **Lo que Colección aporta y Juegos no tiene** son los paneles de
  análisis agregado: Estadísticas (gráfico de tarta + barras por
  estado/región), Uso de disco por plataforma, Comparar bibliotecas PC vs
  Android (con acciones de sync), Completitud vs catálogo DAT, y Wishlist.
  Esto **no es una galería** — es un dashboard de biblioteca completa, y no
  tiene sentido dentro de la ficha de un juego individual.

**Recomendación:** no fusionar mecánicamente las dos pestañas enteras, sino
separar las dos cosas que Colección mezcla hoy:
1. **Retirar la galería duplicada de Colección** (grid + buscar + plataforma
   + orden) — Juegos ya cubre ese caso de uso mejor. Cada tile que hoy abre
   `openGamePanel` desde Colección puede pasar a ser simplemente un enlace
   a Juegos con el filtro de plataforma ya aplicado.
2. **Quedarse solo con los paneles de análisis** (Stats, Disco, Diff PC/Android,
   Completitud, Wishlist) — posiblemente renombrando la pestaña a algo como
   "Análisis" o "Estadísticas", ya que dejaría de ser una "colección" para
   ser un dashboard.
Esto reduce mantenimiento (una sola galería, un solo export) sin perder
ninguna de las funciones únicas de Colección. Si se prefiere no tocar la
arquitectura ahora, al menos arreglar COLECCION-UX-3 (export inconsistente)
es obligatorio independientemente de la decisión de fusión.

---

## UI Audit — Retro Vault (pestaña Colección)

### 🔴 Crítico (rompe la experiencia)

**COLECCION-UX-1 — El botón "🏥 Health" no hace absolutamente nada**
`tab-collection.html:22` — `onclick="togglePlatformHealth()"`, sin ningún
argumento. Pero `togglePlatformHealth(platform)` (`esde.js:632-648`) espera
un `platform` y nunca alterna la visibilidad de `#platform-health-panel` —
a diferencia de sus hermanos `toggleDiskUsage`/`toggleCompleteness`/
`toggleDiff`/`toggleColStats` (`collection.js`), que sí hacen
`panel.classList.toggle('hidden')` antes de cargar datos. Además,
`togglePlatformHealth` escribe en `#platform-health-content`, que **no
existe** — el panel real usa `#ph-table` (`tab-collection.html:110`). Y el
botón "&#x27F3; Actualizar" del panel llama a `loadPlatformHealth()`
(`esde.js:650-661`), que es un TODO puro: siempre renderiza «Funcionalidad
pendiente: Salud por plataforma» sin llamar a ninguna API. Tres fallos
apilados en un solo botón — mismo patrón que HERR-UX-1/2/3 y
FORMATOS-UX-2, cuarta ocurrencia del antipatrón HTML/JS-ID-mismatch en la
app.
Fix: decidir si esta feature se implementa (requiere `/api/platform-health`
real) o se retira; si se mantiene, arreglar el toggle de panel y unificar
los IDs.

**COLECCION-UX-2 — Dos galerías divergentes para lo mismo**
Ver sección "¿Fusionar Colección y Juegos?" arriba. La galería de Colección
(`col-grid`) y la vista cuadrícula de Juegos apuntan al mismo endpoint y
abren el mismo panel, pero Colección solo expone 3 de los 9 filtros que
tiene Juegos — un usuario que filtra por tag/género/año/estado en Juegos y
luego cambia a Colección pierde todos esos filtros sin aviso, viendo una
lista distinta de la que esperaba.
Fix: ver recomendación de fusión arriba.

**COLECCION-UX-3 — Exportar CSV/JSON da resultados distintos según la pestaña**
El enlace de Juegos (`tab-games.html:46-47`) no manda `root`; el botón de
Colección (`exportCollection()`, `collection.js:311-313`) sí manda
`root=_deviceRoot()`. Mismo nombre de botón ("Exportar CSV"), mismo texto,
resultado potencialmente distinto (todas las plataformas vs. solo el
dispositivo activo) sin ninguna indicación de la diferencia.
Fix: unificar — que ambos exports incluyan (o ninguno incluya) el
dispositivo activo, y si se mantiene la diferencia, decirlo explícitamente
en el botón (ej. "Exportar CSV (solo PC)").

### 🟡 Moderado (confunde al usuario)

**COLECCION-UX-4 — "ROMs faltantes" es código muerto con la mejor funcionalidad de la pestaña**
`tab-collection.html:113-124` (`missing-section`), marcado en el propio
comentario como «LEGACY... hidden but preserved». `loadMissingRoms()`
(`collection.js:65-88`) es la única función que lo mostraría
(`sec.classList.remove('hidden')` dentro de sí misma), pero **ningún botón
de la UI la llama** — confirmado por búsqueda en toda la carpeta `static/`.
Es una lástima porque esta lista tiene funciones que el panel activo
("📋 Completitud", `loadCollectionStats()`) no tiene: copiar la búsqueda al
portapapeles, enlace directo a Internet Archive, y botón de Wishlist por
título. El panel vivo solo muestra una barra de progreso de cobertura.
Fix: decidir si se recupera esta vista (parece más útil) en vez de o junto
a la de Completitud, o se borra definitivamente el HTML/JS muerto.

**COLECCION-UX-5 — Cinco paneles-acordeón independientes sin "cerrar todos"**
Stats, Disco, Comparar, Completitud y Health (roto) son cinco toggles
independientes (`collection.js`) que no se cierran entre sí. Abrir varios
seguidos deja una página muy larga sin forma rápida de volver al estado
inicial salvo cerrarlos uno a uno.
Fix: opcional — cerrar los demás paneles al abrir uno, o añadir un botón
"Colapsar todo".

### 🟢 Menor (pulido)

**COLECCION-UX-6 — Filtro de plataforma duplicado con estilos distintos**
La barra de botones de plataforma de Colección (`col-platform-bar`,
`collection.js:182-197`) hace lo mismo que el `<select id="games-platform">`
de Juegos, pero como fila de botones en vez de desplegable — otra señal de
que ambas pestañas divergieron en vez de compartir un componente.

---

## Top 3 por impacto

1. **COLECCION-UX-2 (y la decisión de fusión)** — dos galerías del mismo
   dato con distinta potencia de filtrado es la raíz de la duda que motivó
   este roadmap; resolverla simplifica todo lo demás.
2. **COLECCION-UX-1** — un botón que no hace nada, apilando tres fallos
   distintos, es el hallazgo más grave a nivel de código.
3. **COLECCION-UX-3** — que "Exportar CSV" signifique cosas distintas según
   la pestaña es el tipo de inconsistencia que mina la confianza en los
   datos exportados.

## Fases sugeridas

- **Fase 1 (decisión de producto):** resolver la pregunta de fusión (ver
  sección superior) antes de tocar código — condiciona el resto de fases.
- **Fase 2 (si no se fusiona, quick wins):** COLECCION-UX-3, COLECCION-UX-6.
- **Fase 3 (panel roto):** COLECCION-UX-1 — implementar o retirar Platform
  Health.
- **Fase 4 (recuperar valor):** COLECCION-UX-4 — decidir destino de "ROMs
  faltantes"; COLECCION-UX-5 si el resto de paneles se mantienen tal cual.
