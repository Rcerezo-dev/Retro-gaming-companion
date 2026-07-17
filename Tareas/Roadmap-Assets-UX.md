# Roadmap — Pestaña Assets: auditoría UX (2026-07-13)

Auditoría de la pestaña **Assets** (`tab-assets.html` + `loadAssets()` en
`js/tabs/sync.js:70-111` — no tiene módulo propio, vive junto al código de
Cloud Sync) desde la perspectiva de un usuario que revisa qué carátulas,
vídeos y archivos huérfanos tiene su biblioteca. Es la pestaña más pequeña
auditada hasta ahora: una tabla de solo lectura por plataforma (ROMs,
imágenes, vídeos, XML, huérfanos) con un filtro y un desplegable "¿Qué son
los archivos Unknown?". Cada ítem tiene ID `ASSETS-UX-n`.

---

## UI Audit — Retro Vault (pestaña Assets)

### 🔴 Crítico (rompe la experiencia)

**ASSETS-UX-1 — La ruta mostrada como "Viendo: X" puede no ser la que realmente se consulta**
`_deviceRoot()` (`main.js:430-435`) resuelve la ruta activa leyendo
**directamente** el input `ov-ab-path` de la pestaña Inicio — sin fallback a
localStorage. Pero el texto de la barra de contexto de Assets
(`sync.js:85`) sí tiene fallback: `ov-ab-path` → `localStorage
('anbernic_path')` → `'(no configurado)'`. Si el usuario no ha visitado la
pestaña Inicio en esta sesión (el input está vacío en el DOM aunque exista
un valor guardado), la barra puede decir «Viendo: Android — /storage/.../ROMs»
(sacado del localStorage) mientras la llamada real a `/api/assets`
(`sync.js:76`) sale **sin parámetro `root`** porque `_deviceRoot()` devolvió
`null` — el backend cae al `library_root` del PC. El usuario ve una ruta de
Android en el encabezado y datos del PC en la tabla, sin ninguna pista de
que no coinciden.
`_deviceRoot()` es función compartida — el mismo problema aplica
previsiblemente a `collection.js` (líneas 170,243,312,333,354,612),
`organize.js` (52,322,469) y `games.js` (293,351), que la usan igual.
Fix: que `_deviceRoot()` tenga el mismo fallback a localStorage que ya usa
el texto de la barra (`sync.js:85`) — un solo cambio en `main.js` arregla
las cuatro pestañas a la vez.
✅ `main.js:429` — rama `anbernic` de `_deviceRoot()` cae a
`localStorage.getItem('anbernic_path')` antes de `null`, igual que `sync.js:98`.

### 🟡 Moderado (confunde al usuario)

**ASSETS-UX-2 — Mensaje "Ejecuta un Scan" también aparece cuando el filtro simplemente no tiene resultados**
`sync.js:92-94` — el filtro (`orphans`/`missing`) se aplica **antes** de
comprobar si la lista quedó vacía. Si el usuario elige "Solo huérfanos" y no
hay ninguno (buena noticia: biblioteca limpia), ve el mismo mensaje que si
nunca hubiera escaneado: «Sin datos de assets todavía. Ejecuta un Scan para
indexar la biblioteca» — genera dudas sobre si el escaneo falló cuando en
realidad todo está bien.
Fix: distinguir "sin datos en absoluto" (`d.stats.length === 0`, antes de
filtrar) de "el filtro no encontró nada" (mensaje distinto, ej. "✓ Sin
huérfanos con este filtro").
✅ `sync.js:104-110` — el chequeo de `d.stats.length === 0` ahora corre antes
del filtro (mensaje "Ejecuta un Scan..."); si el filtro deja la lista vacía
después, mensaje distinto "✓ Sin resultados para este filtro".

**ASSETS-UX-3 — Mensaje de error sin ninguna guía, a diferencia del resto del mismo archivo**
El catch de `loadAssets` (`sync.js:108-109`) solo muestra
`e.message` en crudo. El catch de `loadSync`, **en el mismo archivo, unas
líneas más arriba** (`sync.js:65`), sí da una pista accionable y un enlace:
"Comprueba que rclone está instalado... → Settings". Fix: replicar el mismo
patrón — sugerir revisar la ruta/configuración y enlazar a Ajustes si aplica.
✅ `sync.js:124` — catch de `loadAssets` añade "Comprueba la ruta configurada
en Ajustes" con enlace `showTab('settings')`, mismo patrón que `loadSync`.

### 🟢 Menor (pulido)

**ASSETS-UX-4 — La columna "Huérfanos" no tiene ninguna acción asociada**
La tabla muestra un recuento de assets huérfanos por plataforma
(`sync.js:104`) pero no hay forma de ver cuáles son ni de moverlos/eliminarlos
desde aquí — es puramente informativo. Un usuario que ve "12 huérfanos" no
tiene ningún botón ni enlace para actuar.
Fix: si existe ya un endpoint que liste los archivos concretos, añadir un
enlace "Ver" por fila; si no, dejarlo fuera de alcance por ahora (Assets es
secundario según los 3 pilares) pero anotarlo como limitación conocida.

**ASSETS-UX-5 — El estado vacío no enlaza a la acción que lo resuelve**
"Ejecuta un Scan para indexar la biblioteca" (`sync.js:94`) es texto plano,
sin botón ni enlace a la pestaña Organizar, a diferencia de otros mensajes
similares ya corregidos en otras pestañas (ej. el aviso de catálogos DAT en
Formatos, que sí lleva un botón directo). Fix: añadir un enlace
`onclick="showTab('plan')"` o el nombre correcto de la pestaña de scan.
✅ Resuelto junto con ASSETS-UX-2 — el estado vacío ahora enlaza a
`showTab('plan')` (pestaña "Organizar", donde vive el Scan).

---

## Top 3 por impacto

1. **ASSETS-UX-1** — la única pestaña de las auditadas hasta ahora donde el
   header puede mentir sobre qué datos se están mostrando; además es un bug
   compartido por 4 pestañas (Assets, Colección, Organizar, Juegos), así que
   arreglarlo aquí lo arregla en las cuatro.
2. **ASSETS-UX-2** — confundir "sin huérfanos" (bueno) con "nunca escaneado"
   (acción pendiente) puede hacer que el usuario repita un Scan innecesario.
3. **ASSETS-UX-3** — inconsistencia menor pero de arreglo trivial (copiar un
   patrón que ya existe 40 líneas más arriba en el mismo archivo).

## Fases sugeridas

- **Fase 1 (quick wins, 1 rama):** ASSETS-UX-2, ASSETS-UX-3, ASSETS-UX-5 —
  cambios de texto/lógica de pocas líneas.
- **Fase 2 (fix compartido):** ASSETS-UX-1 — tocar `_deviceRoot()` en
  `main.js` beneficia también a Colección, Organizar y Juegos; verificar las
  cuatro pestañas tras el cambio.
- **Fase 3 (alcance futuro, opcional):** ASSETS-UX-4 — solo si se decide que
  gestionar huérfanos desde Assets aporta valor suficiente frente a otras
  prioridades (Assets es secundario según los 3 pilares del proyecto).
