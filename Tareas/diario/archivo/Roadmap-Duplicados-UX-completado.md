# Roadmap — Pestaña Duplicados: auditoría UX (2026-07-13)

> ✅ **COMPLETADO (2026-07-17)** — Los 7 ítems (DUPLICADOS-UX-1..7) se
> implementaron en la rama `fix/duplicados-ux` (commit `023aafe`, PR #132,
> mergeado en `develop`). Verificado ítem a ítem contra el código actual.

Auditoría de la pestaña **Duplicados** (`tab-duplicates.html` +
`js/tabs/duplicates.js`) desde la perspectiva de un usuario que quiere
liberar espacio eliminando copias redundantes sin miedo a perder algo. A
diferencia de otras pestañas auditadas, aquí **no hay botones muertos** —
todo lo que se pulsa llama a algo real. Los problemas son de otro tipo:
un desajuste entre lo que se confirma y lo que realmente se borra, y
mensajes inconsistentes sobre si una acción se puede deshacer. Cada ítem
tiene ID `DUPLICADOS-UX-n`.

---

## UI Audit — Retro Vault (pestaña Duplicados)

### 🔴 Crítico (rompe la experiencia)

**DUPLICADOS-UX-1 — "Eliminar todos los duplicados" borra más de lo que confirma si hay un filtro de plataforma activo**
El filtro de plataforma (`dup-platform-filter`, `tab-duplicates.html:5-7`) es
**puramente visual**: `_renderDupContent` (`duplicates.js:381-386`) solo
filtra el HTML que se pinta. Pero `deleteAllDuplicates()`
(`duplicates.js:64-109`) calcula el número de archivos a confirmar contando
filas **visibles en el DOM ya filtrado**
(`document.querySelectorAll('#dup-content .dup-group[id] .btn.danger')`,
línea 65) y al confirmar llama a `/api/duplicates/delete-all` con
`{ source_root: '' }` (línea 76) — **sin ningún parámetro de plataforma**.
El backend (`delete_all_duplicates`, `services/duplicates_service.py:90`)
no tiene forma de restringir por plataforma en absoluto: borra duplicados de
**toda la biblioteca**, en ambos dispositivos. Un usuario que filtra "Solo
SNES", ve "se eliminarán 5 archivos" en el diálogo de confirmación, y pulsa
Eliminar, en realidad está borrando los duplicados de **todas** las
plataformas — el número que confirmó no es el número que se ejecuta.
Fix: o bien pasar el filtro de plataforma al backend y que
`delete_all_duplicates` lo respete, o bien deshabilitar/advertir
explícitamente el botón "Eliminar todos" mientras haya un filtro activo
("Elimina TODAS las plataformas, no solo la vista filtrada").

### 🟡 Moderado (confunde al usuario)

**DUPLICADOS-UX-2 — Toasts rotos: se pasa `true`/`false` en vez del tipo esperado**
`deleteAllDuplicates` llama `showToast('No hay duplicados...', false)`
(línea 67) y `showToast('Error: ' + e.message, true)` (línea 103);
`deleteDuplicate` hace lo mismo en su catch (línea 134,
`showToast('Error al eliminar: ' + e.message, true)`). `showToast(msg,
type)` (`components/toast.js`) espera un string (`'ok'|'err'|'info'`) que
aplica como clase CSS — un booleano se convierte en la clase literal
`"true"`/`"false"`, que no existe en `app.css`, así que el toast aparece sin
ningún color/borde. El resto de funciones **del mismo archivo** (líneas 86,
95, 158, 178, 268...) sí usan los strings correctos — es inconsistencia
local, no un patrón nuevo de tipos inventados.
Fix: cambiar `true`→`'err'` y `false`→`'info'` en los 3 sitios.

**DUPLICADOS-UX-3 — Mensajes contradictorios sobre si el borrado se puede deshacer**
`deleteDuplicate`, `deleteAllDuplicates`, `resolveDuplicateRA` y
`markAsIntentionalCopy` (vía `_showConfirm`, líneas 111-184) dicen todos
**"Esta operación no se puede deshacer"**. Pero el backend de todas estas
acciones (`delete_duplicate`, `services/duplicates_service.py:49-54`) usa
`discard_to_trash()` — el mismo mecanismo de papelera unificada de AUD-3
(`_descartados/`, purga a los 30 días) que usa `deleteRaDuplicate`
(`duplicates.js:255`), cuyo mensaje dice en cambio **"Se moverá a
_descartados/. Esta acción es difícil de deshacer"** — más preciso, pero
inconsistente con el resto de la misma pestaña para el mismo mecanismo
subyacente. El usuario ve dos redacciones distintas para la misma garantía
real de recuperación.
Fix: unificar la redacción — todas las confirmaciones de borrado deberían
mencionar `_descartados/` y el plazo de 30 días de forma consistente (o
todas usar la versión corta, pero no mezclar ambas).

**DUPLICADOS-UX-4 — Diálogos nativos `confirm()` junto a la ventana modal propia, en el mismo archivo**
`deleteRaDuplicate` (línea 255) y `discardAllRaDuplicates` (línea 323) usan
`confirm()` nativo, mientras `deleteAllDuplicates`, `deleteDuplicate`,
`resolveDuplicateRA` y `markAsIntentionalCopy` usan `_showConfirm` — que
`duplicates.js` **ya importa en la línea 6** (`import { _showConfirm } from
'../components/modal.js'`). No es un componente ausente, es no usarlo en 2
de los 6 sitios que deberían.
Fix: sustituir los 2 `confirm()` por `_showConfirm`.

**DUPLICADOS-UX-5 — "Copia intencional ✓" es una acción silenciosa y permanente sin forma de revisarla o deshacerla**
`markAsIntentionalCopy` (`duplicates.js:168-184`) llama a
`/api/duplicates/exclude` y el grupo desaparece de la lista para siempre —
confirmado por búsqueda: **no existe en ningún sitio de la UI** una lista de
"grupos excluidos" ni un botón para revertirlo. Si el usuario se equivoca al
marcar un grupo, la única forma de deshacerlo es tocar la base de datos
directamente. El propio diálogo de confirmación tampoco avisa de que es
permanente ("No aparecerá más en la lista de duplicados", sin más).
Fix: añadir al menos una lista de solo lectura de grupos excluidos (en
Ajustes o al final de esta pestaña) con botón "Quitar exclusión", y
mencionar en el diálogo que es una acción sin UI de deshacer hoy.

**DUPLICADOS-UX-6 — Texto en inglés "Tools" en dos sitios de una pestaña en español**
`tab-duplicates.html:22` ("Requiere que hayas ejecutado la comprobación RA
en **Tools** al menos una vez") y `duplicates.js:331`
("...ejecuta primero la comprobación RA en Tools para cargar el caché")
dicen "Tools" — que además **no es el nombre real de ninguna pestaña**; la
pestaña se llama "Herramientas". Doble fallo: idioma mezclado + nombre
incorrecto.
Fix: cambiar ambas apariciones a "Herramientas".

### 🟢 Menor (pulido)

**DUPLICADOS-UX-7 — El estado vacío filtrado no tiene la misma calidad que el estado vacío general**
Cuando no hay duplicados en absoluto, `_renderDupContent` usa el componente
`_emptyState` con icono, texto explicativo y botón "Ir a Inicio"
(`duplicates.js:392`) — buen patrón, mejor que el de varias pestañas ya
auditadas. Pero si el filtro de plataforma no encuentra nada
(`duplicates.js:390`), el mensaje es solo texto plano "Sin duplicados en
X.", sin botón para quitar el filtro y ver el resto.
Fix: añadir un enlace "Quitar filtro" en ese caso, reutilizando el mismo
`<select>` reset.

---

## Top 3 por impacto

1. **DUPLICADOS-UX-1** — el único hallazgo de esta pestaña con riesgo real de
   pérdida de datos no consentida: el usuario confirma un número y se borra
   otro, mayor, en otras plataformas. Prioridad absoluta según las reglas
   del proyecto (nunca eliminar sin política de conflictos clara).
2. **DUPLICADOS-UX-3** — dos redacciones distintas sobre si una acción "se
   puede deshacer" mina la confianza en todos los botones de borrado de la
   pestaña, no solo en el que tiene el texto raro.
3. **DUPLICADOS-UX-2** — el bug de tipos boolean en toasts es el más barato
   de arreglar (3 líneas) con el mayor "quick win" de percepción visual.

## Fases sugeridas

- **Fase 1 (seguridad, 1 rama):** DUPLICADOS-UX-1 — antes que nada, porque
  es el único riesgo de pérdida de datos no consentida de esta pestaña.
- **Fase 2 (quick wins):** DUPLICADOS-UX-2, DUPLICADOS-UX-4, DUPLICADOS-UX-6,
  DUPLICADOS-UX-7 — cambios de pocas líneas cada uno.
- **Fase 3 (confianza y reversibilidad):** DUPLICADOS-UX-3 (unificar
  redacción) y DUPLICADOS-UX-5 (UI mínima de exclusiones).
