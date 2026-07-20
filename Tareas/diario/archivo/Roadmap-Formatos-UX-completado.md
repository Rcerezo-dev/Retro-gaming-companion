# Roadmap — Pestaña Formatos: auditoría UX (2026-07-13)

Auditoría de la pestaña **Formatos** (`tab-formats.html` + funciones repartidas
en `js/tabs/tools.js`, `js/tabs/esde.js`, `js/tabs/config.js`,
`js/tabs/duplicates.js`, `js/jobs.js`) desde la perspectiva de un usuario que
convierte y organiza sus ROMs (CHD, CSO, ZIP, N64, M3U, .lpl, análisis de
carpeta, verificación multi-disco). Cada ítem tiene ID `FORMATOS-UX-n` para
referenciarlo desde el backlog.

A diferencia de la pestaña Herramientas (`Roadmap-Herramientas-UX.md`), aquí
la mayoría de botones SÍ están conectados a su handler (todas las funciones
están expuestas en `window` vía `main.js:195-`). Los problemas son de otro
tipo: un panel-stub, un selector de contexto compartido que pisa rutas sin
avisar, y falta de coherencia en diálogos nativos vs. componentes propios.

---

## UI Audit — Retro Vault (pestaña Formatos)

### 🔴 Crítico (rompe la experiencia)

**FORMATOS-UX-1 — El selector de contexto PC/Android pisa rutas de esta pestaña sin avisar**
`duplicates.js:345-367` (`setToolsContext`) se ejecuta cada vez que se abre
**Formatos o Herramientas** (`main.js:485-486`, sin condición de "solo la
primera vez") y sobrescribe incondicionalmente `zip-path`, `chd-path` y
`folder-analysis-path` — los tres viven en `tab-formats.html` — con la ruta
del contexto activo (PC o Android), sin comprobar si el usuario ya escribió
algo (a diferencia de `_setIfEmpty`, que si respeta valores existentes,
`config.js:249-255`). Además rellena un ID muerto (`health-path`, no existe
en ningún parcial) y dos deja huérfanos: `cso-path`, `verify-chd-path` y
`m3u-path` no se tocan, así que tras cambiar de contexto la pestaña queda con
rutas de dos "mundos" distintos a la vez. Ya documentado parcialmente como
HERR-UX-7; aquí es más grave porque el efecto secundario recae sobre inputs
de otra pestaña y se repite en cada apertura, no solo una vez.
Fix: `setToolsContext` solo debe rellenar inputs vacíos (o pedir confirmación
si hay contenido), incluir todos los paths relevantes de Formatos, y eliminar
`health-path`.

**FORMATOS-UX-2 — "Análisis de carpeta" es un panel-stub que aparenta funcionar**
`tab-formats.html:192-204` — input `folder-analysis-path` (con botón
`library_root` y persistencia en localStorage) + botón "Analizar carpeta" +
`div` de resultado, exactamente igual que cualquier otro panel funcional de
la pestaña. Pero `doFolderAnalysis` (`esde.js:1120-1131`) es un TODO: ignora
la ruta introducida y siempre renderiza «Funcionalidad pendiente: análisis de
carpetas», sin importar qué carpeta se puso. Mismo patrón que HERR-UX-2
(Buscar huérfanos). El texto descriptivo del panel promete "extensiones
encontradas, sets PSX con .bin faltante, formatos que necesitan conversión" —
ninguna de esas tres cosas existe hoy.
Fix: implementar contra `/api/folder-analysis` (crear el endpoint) o retirar
el panel hasta que exista — un panel completo que siempre dice "pendiente" es
peor que no tenerlo.

### 🟡 Moderado (confunde al usuario)

**FORMATOS-UX-3 — Diálogos nativos (`alert`/`confirm`) en vez de los componentes propios de la app**
`tools.js` usa `alert()` para validar rutas vacías en `doConvertChd:37`,
`doConvertCso:115`, `doExtractZip:197`, `doCleanupZips:170`,
`doCleanupCueBin:183`, `doGenerateM3U:220`, `doVerifyMultidisc:297`,
`doVerifyChd:524`, y `confirm()` nativo en `doCleanupZips:172`,
`doCleanupCueBin:184` (y `organizeLibrary:498`, fuera de esta pestaña) — pese
a que la app ya tiene su propio sistema de toasts (`showToast`, usado en
`doN64Convert:435,438`) y un modal de confirmación propio
(`_showConfirm`/`_closeConfirm`, expuesto en `main.js:250`). Los diálogos
nativos bloquean el hilo, no respetan el tema oscuro de la app y rompen la
experiencia visual en 9+ puntos de la pestaña.
Fix: sustituir por `showToast(..., 'err')` para validaciones y `_showConfirm`
para las confirmaciones destructivas.

**FORMATOS-UX-4 — El botón "library_root" muestra un nombre de variable interna, no una etiqueta**
`tab-formats.html:16,58,88,148,198` — cinco botones (uno por cada panel con
ruta) tienen literalmente el texto `library_root` como label visible, en
inglés y en snake_case, cuando el resto de la pestaña está en español legible
("Solo previsualizar", "Eliminar tras convertir"...). Es la config interna
filtrándose a la UI.
Fix: renombrar a algo como "Usar carpeta de biblioteca" o un icono con
tooltip — un solo cambio de texto/CSS que se replica en los 5 sitios.

**FORMATOS-UX-5 — Escaneos síncronos sin estado de carga ni bloqueo de botón**
"Generar M3U" (`doGenerateM3U`, `tools.js:217`), "Verificar" (multi-disco,
`doVerifyMultidisc:295`), "Escanear" (N64, `doN64Scan`, `tools.js:405`) y
"Generar .lpl" (`doExportLpl:388`) hacen `fetch` síncrono sin deshabilitar su
propio botón ni cambiar su texto (solo el div de resultado dice "Buscando…"/
"Verificando…"). En una biblioteca grande, nada impide pulsar dos veces y
lanzar la operación por duplicado. Contraste: CHD/CSO/ZIP/verify-CHD sí
deshabilitan y renombran su botón porque pasan por el patrón de jobs con
polling (`jobs.js`). `autodetectM3UFolders` sí lo hace bien (`tools.js:248`) —
es el único de este grupo que deshabilita su botón.
Fix: deshabilitar botón + cambiar texto a "…" en los 4 casos, siguiendo el
patrón ya usado en `autodetectM3UFolders`.

### 🟢 Menor (pulido)

**FORMATOS-UX-6 — Filtro "solo errores" con default inconsistente entre paneles gemelos**
En "Convertir a CHD", `chd-filter-errors` solo empieza marcado si hay fallos
reales (`_renderChdResult`, `tools.js:76-78`). En "Verificar integridad CHD",
`verify-chd-filter-errors` empieza **siempre** marcado
(`tab-formats.html:75`), muestre o no muestre corruptos. Son dos paneles casi
idénticos con lógica de default distinta.
Fix: unificar — el de verificación siendo el más usado repetidamente,
probablemente el criterio "solo si hay fallos" es más cómodo también ahí.

**FORMATOS-UX-7 — Mensajes de error sin guía accionable en la mitad de los casos**
`doCleanupZips`/`doCleanupCueBin` (`tools.js:178,190`) añaden "Verifica que
los archivos no estén en uso por otro programa" tras el error. Pero
`doConvertChd`, `doConvertCso`, `doExtractZip`, `doVerifyChd` (mismos
archivos) solo muestran `'Error: ' + e.message`, sin ninguna sugerencia,
aunque comparten la misma clase de fallos (archivo bloqueado, ruta
inaccesible).
Fix: añadir la misma pista genérica a los 4 catch que la omiten.

**FORMATOS-UX-8 — Resultados vacíos sin sugerencia de siguiente paso**
"No se encontraron grupos multi-disco." (`doGenerateM3U`, `tools.js:236`) y
"No se encontraron ROMs de N64 en esa carpeta." (`doN64Scan`, `tools.js:413`)
no dicen qué revisar (¿ruta correcta? ¿nomenclatura "(Disc N)"?). El
verificador de multi-disco sí da esa pista en un caso similar
(`tools.js:346`: "revisa que los nombres incluyan (Disc N)").
Fix: reutilizar la misma frase de ayuda en los dos mensajes vacíos.

**FORMATOS-UX-9 — El botón "library_root" falla en silencio**
`fillToolPath` (`config.js:406-411`) tiene un `catch(e) { /* silent */ }`: si
`/api/config` falla, pulsar el botón no hace absolutamente nada y el usuario
no tiene forma de saber si el problema es la ruta, la red o el propio botón.
Fix: en el catch, mostrar un toast de error.

**FORMATOS-UX-10 — Persistencia de rutas incompleta entre sesiones**
`_initToolPath` (`config.js:295-301`) solo restaura desde localStorage
`zip-path`, `orphan-path`, `chd-path`, `m3u-path`, `report-path` y
`folder-analysis-path`. Los inputs `cso-path`, `verify-chd-path`,
`verify-multidisc-path`, `lpl-output-dir` y `n64-path` no se guardan — tras
recargar la página hay que volver a escribirlos aunque sean del mismo
`library_root` de siempre.
Fix: añadir las 5 líneas de `_initToolPath` que faltan (mismo patrón, sin
diseño nuevo).

---

## Top 3 por impacto

1. **FORMATOS-UX-1** — el selector de contexto pisando `chd-path`/`zip-path`/
   `folder-analysis-path` en cada apertura de pestaña es el más dañino: el
   usuario escribe una ruta, cambia de contexto en otra pestaña, y al volver
   su ruta ha desaparecido sin explicación.
2. **FORMATOS-UX-2** — "Análisis de carpeta" prometiendo tres funcionalidades
   que no existen es el mismo antipatrón que ya rompió confianza en
   Herramientas (HERR-UX-1/2); decidir reconectar o retirar.
3. **FORMATOS-UX-3** — 9 sitios con `alert()`/`confirm()` nativos rompen la
   experiencia visual más veces que cualquier otro hallazgo de esta pestaña.

## Fases sugeridas

- **Fase 1 (quick wins, 1 rama):** FORMATOS-UX-4, FORMATOS-UX-6,
  FORMATOS-UX-7, FORMATOS-UX-8, FORMATOS-UX-9, FORMATOS-UX-10 — cambios de
  texto/una línea cada uno.
- **Fase 2 (contexto compartido):** FORMATOS-UX-1 — junto con HERR-UX-7, ya
  que es la misma función (`setToolsContext`) vista desde el otro lado.
- **Fase 3 (panel muerto):** FORMATOS-UX-2 — decidir implementar vs. retirar.
- **Fase 4 (consistencia):** FORMATOS-UX-3 (toasts/confirm propios) y
  FORMATOS-UX-5 (loading state en escaneos síncronos).
