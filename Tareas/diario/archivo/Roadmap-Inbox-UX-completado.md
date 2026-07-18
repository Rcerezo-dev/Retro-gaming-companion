# Roadmap — Pestaña Inbox: auditoría UX (2026-07-13)

Auditoría de la pestaña **Inbox** (`tab-inbox.html` + `js/tabs/inbox.js`)
desde la perspectiva de un usuario que suelta ROMs nuevos y espera que la
herramienta los organice sola — el Pilar 2 del proyecto ("día a día").
Cada ítem tiene ID `INBOX-UX-n`.

---

## Cierre del hilo abierto en el roadmap de Plan: ¿fusionar Inbox con Plan/Organizar?

El roadmap de Plan (`Tareas/Roadmap-Plan-UX.md`) dejó como hipótesis sin
verificar que "el pipeline automático de Inbox ya hace internamente lo que
Plan hace a mano". Habiendo leído ahora `inbox.js` completo: es cierto que
el pipeline de Inbox incluye internamente los mismos pasos de
planificar→renombrar→organizar (pasos 4-6 de 6, ver
`_STEP_LABELS`, `inbox.js:196-204`), pero **el ámbito y el propósito son
distintos, no redundantes**:

- **Plan/Organizar** trabaja sobre la biblioteca ya escaneada (Pilar 1:
  limpiar lo que ya tienes), con revisión humana del plan antes de aplicar.
- **Inbox** trabaja sobre una carpeta de staging con archivos **nuevos, aún
  no escaneados** (Pilar 2: día a día, sin intervención manual) — incluye
  pasos que Plan no tiene (extraer ZIPs, escanear, cotejar) precisamente
  porque parte de archivos que todavía no están en la base de datos.

**Conclusión: no fusionar.** Son dos pilares del proyecto declarados como
distintos en `CLAUDE.md`, con automatización deliberadamente distinta (Plan
exige revisión antes de aplicar; Inbox está pensado para no necesitarla).
La hipótesis original queda descartada con evidencia de código.

---

## Estado (2026-07-18, rama `fix/inbox-ux`) — COMPLETADO

- ✅ **INBOX-UX-1** — "Organizar todo" pide confirmación con `_showConfirm` y
  recuento fresco (total, ZIPs, no reconocidos, colisiones en destino, aviso
  si se eliminarán ZIPs). Si el análisis previo falla, confirma sin recuento
  (no bloquea).
- ✅ **INBOX-UX-2** — columna "Destino" en el análisis: carpeta de plataforma
  (misma regla que el paso 6, helper compartido `_platform_folder_name`) y
  aviso "⚠ ya existe" si hay un archivo con ese nombre en destino. Para ZIPs
  no se comprueba (lo que llega a destino es su contenido).
- ✅ **INBOX-UX-3** — `resolveInboxConflict` usa `_showConfirm`, no `confirm()`.
- ✅ **INBOX-UX-4** — los checkboxes se guardan solos al cambiarlos
  (`autoSaveInboxToggle`); el botón "Guardar ajustes" sigue para los paths.
- ✅ **INBOX-UX-5** — "N no reconocidos (no se tocan, se quedan en el Inbox)".
- ✅ **INBOX-UX-6** — error de conflictos con mensaje y guía de acción.

---

## UI Audit — Retro Vault (pestaña Inbox)

### 🔴 Crítico (rompe la experiencia)

**INBOX-UX-1 — "Organizar todo" no pide ninguna confirmación**
`runInbox()` (`inbox.js:160-186`) llama directamente a `/api/inbox-run` sin
ningún `confirm()` ni `_showConfirm` — a diferencia de **todas** las demás
acciones de esta magnitud auditadas hasta ahora (Duplicados, Plan,
Formatos), que sí piden confirmar antes de tocar archivos en masa. Un solo
clic en "Organizar todo" extrae ZIPs, escanea, cruza con catálogo, renombra
y mueve **todos** los archivos de la carpeta Inbox a sus carpetas de
plataforma — sin previsualización de qué se va a mover a dónde (ver
INBOX-UX-2) ni un paso de "¿seguro?". Lo único que atenúa el riesgo es que
el checkbox "Eliminar ZIPs originales" está desmarcado por defecto
(`tab-inbox.html:28`, sin `checked`) — pero el resto de la operación
(mover/renombrar) ocurre igualmente sin avisar.
Fix: añadir `_showConfirm` con el recuento de archivos a procesar
(`inbox-summary`/`d.total` ya está disponible tras "Analizar carpeta") antes
de lanzar `runInbox()`.

### 🟡 Moderado (confunde al usuario)

**INBOX-UX-2 — "Analizar carpeta" no muestra un plan real, solo una clasificación**
El botón "Analizar carpeta" (`scanInbox()`, `inbox.js:110-158`) enseña tipo
de archivo, plataforma detectada y tamaño — pero nunca el nombre de destino
(`from → to`) ni conflictos previstos, a diferencia de la tabla equivalente
en la pestaña Plan. Un usuario que analiza antes de organizar sigue sin
saber exactamente qué nombre final tendrá cada archivo ni si habrá
colisiones, hasta que ya se ha ejecutado el pipeline completo.
Fix: si `/api/inbox-scan` puede incluir una previsualización de destino
(aunque sea aproximada, sin garantizar el resultado final tras
extraer/cotejar), añadirla a la tabla.

**INBOX-UX-3 — `confirm()` nativo en la resolución de conflictos**
`resolveInboxConflict()` (`inbox.js:321-336`) usa `confirm()` del
navegador — mismo patrón ya señalado en Duplicados y Plan (diálogos nativos
mezclados con el modal propio `_showConfirm` en el resto de la app).
Fix: sustituir por `_showConfirm`.

**INBOX-UX-4 — El checkbox "Procesar automáticamente (daemon)" no indica que necesita guardarse aparte**
`inbox-auto-process` (`tab-inbox.html:31-34`) es solo un checkbox del DOM;
solo se envía al backend al pulsar "Guardar ajustes"
(`saveInboxSettings()`, `inbox.js:338-354`), un botón situado en otra fila
sin ninguna relación visual con el checkbox. Un usuario puede marcarlo,
asumir que el daemon ya está activo, y no darse cuenta de que no ha
guardado nada.
Fix: mover "Guardar ajustes" junto al checkbox, o guardar automáticamente
al cambiar el checkbox (como hacen otros toggles de la app).

### 🟢 Menor (pulido)

**INBOX-UX-5 — "No reconocidos" no explica qué pasará con esos archivos**
El resumen del escaneo muestra en rojo "N no reconocidos"
(`inbox.js:128`) sin decir si el pipeline los deja intactos, los mueve a
alguna carpeta, o falla — genera duda antes de pulsar "Organizar todo".
Fix: una nota corta ("no se tocan, permanecen en el Inbox").

**INBOX-UX-6 — Errores sin guía en la carga de conflictos**
`loadInboxConflicts()` (catch, `inbox.js:314-316`) muestra `e.message`
crudo, mismo patrón de mensajes sin acción ya señalado en otras pestañas.

---

## Top 3 por impacto

1. **INBOX-UX-1** — la única acción masiva de todo el proyecto auditado
   hasta ahora sin ningún paso de confirmación; prioridad por coherencia
   con el resto de la app y con las reglas de seguridad del proyecto.
2. **INBOX-UX-2** — sin previsualización de destino, la confirmación que se
   añada en INBOX-UX-1 tendría poco contenido útil que mostrar; conviene
   resolverlos juntos.
3. **INBOX-UX-4** — un checkbox que aparenta activarse pero no lo hace
   hasta un paso separado es la puerta de entrada más fácil a un malentendido
   silencioso.

## Fases sugeridas

- **Fase 1 (seguridad, 1 rama):** INBOX-UX-1 + INBOX-UX-2 juntos — la
  confirmación necesita datos del análisis para ser útil.
- **Fase 2 (quick wins):** INBOX-UX-3, INBOX-UX-5, INBOX-UX-6.
- **Fase 3 (claridad de ajustes):** INBOX-UX-4.
