# Roadmap — Pestaña Plan (Organizar): auditoría UX + ¿fusión? (2026-07-13)

> ✅ **COMPLETADO (2026-07-17)** — Los 5 ítems (PLAN-UX-1..5) resueltos en la
> rama `fix/plan-ux`:
> - PLAN-UX-1: eliminada la promesa de reversibilidad en `doApply` y en la
>   barra de contexto ("Cada cambio queda registrado en la base de datos").
> - PLAN-UX-2: `doApply` y `applyKeepBoth` migrados de `confirm()` nativo a
>   `_showConfirm`.
> - PLAN-UX-3: retirado el dropdown `plan-device-filter` (obsoleto tras
>   DEVSEL-FIX-3) y su lógica en `loadPlan`.
> - PLAN-UX-4: ya cubierto por el fix de ASSETS-UX-1 — verificado que
>   `_deviceRoot` (main.js:436) tiene el fallback a `localStorage('anbernic_path')`.
> - PLAN-UX-5: la rama "unknown" era código muerto (el backend solo emite
>   `collision`/`disk`) — eliminada.
> - Extra: confirmaciones de descarte de colisiones alineadas con la
>   redacción de papelera de DUPLICADOS-UX-3 (`_descartados/`, 30 días).

Auditoría de la pestaña **Plan** (id interno `plan`, mostrada como
"Organizar" en la UI — `tab-plan.html` + `js/tabs/organize.js`) desde la
perspectiva de un usuario que revisa el renombrado pendiente antes de
aplicarlo (`rommgr plan` siempre antes de `apply`, regla del proyecto). Es
la pestaña más madura de las auditadas hasta ahora: tiene resumen, barra de
progreso, panel de errores, y explica bien la diferencia entre "colisión de
plan" y "conflicto de disco" con enlace cruzado a Duplicados. Los problemas
encontrados son más sutiles que en otras pestañas. Cada ítem tiene ID
`PLAN-UX-n`.

---

## ¿Fusionar Plan con otra pestaña?

A diferencia de Colección/Juegos, aquí **no encontré una duplicación clara
que pida fusión**:

- El solapamiento más obvio es con **Duplicados** — Plan reutiliza el mismo
  endpoint (`/api/duplicates/delete`, en `deleteCollisionDuplicates` y
  `_discardCollisionEntry`, `organize.js:411,436`) y el mismo concepto de
  "ganador RA" (`ra_role`) que la pestaña Duplicados. Pero la propia UI de
  Plan **ya explica correctamente** por qué son cosas distintas
  (`organize.js:226-233`: colisión de plan = incompatibilidad de *nombre*
  entre dos ROMs *distintos* según el catálogo; Duplicados = mismo
  *contenido* exacto por SHA1) y enlaza directamente a la otra pestaña. Esto
  es buen diseño ya existente, no algo que arreglar fusionando.
- El candidato real para una futura revisión es **Inbox** — por lo que sé
  del backlog (`INBOX-FIX-4`), el pipeline automático de Inbox ya ejecuta
  internamente los mismos pasos que Plan hace manualmente (build plan →
  rename → organize), solo que de forma automática. Plan sería entonces el
  "modo manual/revisable" del mismo proceso que Inbox hace "en automático".
  No he auditado todavía `tab-inbox.html`/`inbox.js` — lo dejo anotado como
  hipótesis a verificar cuando le toque su propio roadmap, no como
  recomendación firme hoy.

**Conclusión: no fusionar Plan con Duplicados** — la distinción ya está
bien comunicada en la UI actual. Sí vale la pena revisar Plan vs. Inbox más
adelante con evidencia de código de ambos.

---

## UI Audit — Retro Vault (pestaña Plan / Organizar)

### 🟡 Moderado (confunde al usuario)

**PLAN-UX-1 — "La operación es reversible" es una promesa que la UI no puede cumplir todavía**
`doApply()` (`organize.js:458`) muestra en su confirmación: "¿Renombrar N
archivos en disco?... **La operación es reversible.**" Pero
`MEJ-2` ("Deshacer último apply") sigue pendiente en el backlog (⬜, sin
implementar) — no existe ningún botón "Deshacer" en la app hoy. Es cierto
que el renombrado es técnicamente reversible en la base de datos (el
patrón de renombrado atómico lo permite), pero desde la perspectiva del
usuario no hay ninguna forma de deshacerlo con un clic; tendría que
identificar y revertir los cambios a mano. `applyKeepBoth()` (línea 310),
la acción hermana, ni siquiera menciona la reversibilidad — inconsistente
además de optimista.
Fix: no prometer reversibilidad hasta que `MEJ-2` exista, o matizarlo
("los cambios quedan registrados y se podrán deshacer en una futura
versión").

**PLAN-UX-2 — Las dos acciones de mayor riesgo usan el diálogo nativo, las de menor riesgo el modal propio**
`doApply()` (línea 458) y `applyKeepBoth()` (línea 310) — que renombran
archivos reales en toda la biblioteca — usan `confirm()` nativo del
navegador. `deleteCollisionDuplicates()` (línea 401) y
`_discardCollisionEntry()` (línea 429), en el mismo archivo, sí usan el
modal propio `_showConfirm` (disponible globalmente vía `window`, sin
necesidad de importarlo). Las acciones con más impacto real (renombrar
toda la biblioteca) tienen el diálogo menos cuidado de las cuatro.
Fix: migrar `doApply`/`applyKeepBoth` a `_showConfirm`, coherente con el
resto del archivo.

**PLAN-UX-3 — El filtro "Filtrar por dispositivo" quedó sin función útil tras DEVSEL-FIX-3**
`plan-device-filter` (`tab-plan.html:29-34`, opciones "Todos los
dispositivos"/"Solo PC"/"Solo Consola Android") solo filtra el array ya
recibido (`organize.js:100-102`). Pero `/api/plan`
(`handlers/organize.py:30-45`) ya resuelve **un único repositorio** vía
`get_repo_fn(source_root)` según el dispositivo activo global (el
selector PC/Consola de la barra superior) — desde que `DEVSEL-FIX-3`
eliminó el modo "Sistema completo", el backend nunca devuelve datos de
los dos dispositivos a la vez. Consecuencia: todas las filas de una
consulta ya comparten el mismo `device_tag`
(`web/builders/library.py:440-443`, derivado de si la ruta cae bajo
`library_root`), así que elegir "Solo PC" no cambia nada visible cuando ya
estás viendo PC, y elegir "Solo Consola Android" mientras ves PC vacía la
tabla por completo — con un mensaje de "nada pendiente" indistinguible de
"no hay conflictos", cuando en realidad el problema es que el filtro no
puede encontrar el otro dispositivo desde aquí. Es un control que sobrevivió
a la eliminación del modo que le daba sentido.
Fix: retirar el dropdown (el selector de dispositivo global ya cumple esa
función) o, si se prefiere mantenerlo por claridad visual, deshabilitar
las opciones que siempre devuelven vacío según el dispositivo activo.

**PLAN-UX-4 — El mismo bug de ruta ya documentado en Assets también aplica aquí**
`loadPlan()` (línea 52), `applyKeepBoth()` (línea 322) y `doApply()`
(línea 469) llaman a `window._deviceRoot()`, que no tiene el fallback a
`localStorage('anbernic_path')` que sí tiene el texto de la barra de
contexto (`organize.js:65`). Ya documentado como `ASSETS-UX-1` — mismo fix
(en `main.js`) lo resuelve aquí también, sin trabajo adicional en esta
pestaña.

### 🟢 Menor (pulido)

**PLAN-UX-5 — Los conflictos "unknown" no tienen ninguna explicación**
Los conflictos que no son `collision` ni `disk` (`organize.js:164`,
variable `unknown`) se listan en una tabla simple sin ningún texto
explicativo, a diferencia de los otros dos tipos que sí tienen un bloque
completo de contexto + acciones. Si esta categoría existe en la práctica,
el usuario no tiene pista de qué hacer con ella.
Fix: si `unknown` ocurre realmente, darle el mismo tratamiento
explicativo; si nunca ocurre en la práctica, considerar si sigue haciendo
falta la rama de código.

---

## Top 3 por impacto

1. **PLAN-UX-1** — prometer reversibilidad que no existe en la acción más
   destructiva de la pestaña (renombrar toda la biblioteca) es el hallazgo
   que más puede minar la confianza si algo sale mal.
2. **PLAN-UX-3** — un control de filtro que puede vaciar la tabla sin
   explicar por qué es el tipo de confusión silenciosa que hace dudar al
   usuario de si algo se rompió.
3. **PLAN-UX-2** — arreglo barato (reusar un modal ya existente) en las dos
   acciones de más impacto de toda la pestaña.

## Fases sugeridas

- **Fase 1 (mensajes):** PLAN-UX-1 — ajustar el texto de confirmación antes
  de que un usuario confíe en un "deshacer" que no existe.
- **Fase 2 (quick wins):** PLAN-UX-2, PLAN-UX-5.
- **Fase 3 (limpieza):** PLAN-UX-3 — retirar o corregir el filtro de
  dispositivo obsoleto.
- **Fase 4 (compartida):** PLAN-UX-4 — ya cubierta por el fix de
  `ASSETS-UX-1`, verificar tras aplicarlo que esta pestaña también queda
  bien.
