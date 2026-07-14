# Roadmap — Anbernic: auditoría UX/UI, lógica y seguridad (2026-07-13)

Origen: auditoría de la pestaña Anbernic (`tab-anbernic.html`, `js/tabs/sync.js`,
`js/main.js`, `partials/_banners.html`, `handlers/sync_cloud.py`,
`handlers/system.py`, `handlers/esde/system.py`, `web/lan.py`). Hallazgo
central: **hay dos generadores de script de setup que se contradicen en la
misma pantalla, y uno de ellos ni siquiera existe como endpoint** — el comando
recomendado (paso 5) usa `/s` y crea `~/sync-saves.sh`, mientras el botón
"Descargar .sh" de al lado apunta a `/api/anbernic-setup.sh` (404, la ruta
nunca se registró) y la caja "Después del setup" documenta
`~/retrovault-sync.sh`, un script que el camino recomendado no crea. Además,
la instalación por defecto (`web_host="0.0.0.0"` + `web_allow_lan=true`) sirve
el rclone.conf con tokens OAuth a cualquier dispositivo de la LAN sin PIN.

Tareas registradas en `Tareas/backlog.md` §ANBERNIC-UX. Cada tarea = una rama → PR.
Todo es pilar 3 (sync de saves = valor diferencial).

Relación con hallazgos ya registrados (no duplicados aquí, solo referenciados):
- **CLOUD-UX-6** — `tvStartSync` postea a `/api/do-sync` inexistente: el panel
  Android (`android-detected-panel`) que ve la consola está roto.
- **CLOUD-UX-7** — el script de `/s` hardcodea `REMOTE="dropbox:/RetroSync/saves"`
  y las extensiones, e ignora `config.sync.saves_remote`; usa `rclone bisync`
  (motor distinto a `SaveSyncer`, sin política "ante duda no sobreescribir").

---

## ANBERNIC-UX-1 — Dos generadores de setup que se contradicen en la misma pantalla

**Problema.** Existen dos scripts de setup Termux distintos y la pestaña mezcla
ambos:

- El comando del paso 5 (`anb-cmd-full`) usa `GET /s`
  (`sync.js:402-403`, `sync_cloud.py:39-51`) → crea `~/sync-saves.sh` con
  `rclone bisync` y remote dropbox hardcodeado (CLOUD-UX-7).
- El botón "⬇ Descargar .sh" (`anb-script-download`) y todo el "Android setup
  panel" de Settings (`loadAndroidSetupPanel`, `sync.js:236-257`, con QR) usan
  `GET /api/anbernic-setup.sh` → generador `_build_anbernic_setup_sh`
  (`system.py:218-368`), que crea `~/retrovault-sync.sh` con
  `rclone copy --update` bidireccional y sí lee config
  (`config.sync.rclone_remote`, `system.py:223`).
- La caja "✅ Después del setup" (`tab-anbernic.html:156,159`) documenta
  `~/retrovault-sync.sh` — el script que el comando recomendado **no** crea.
  Quien siga la pantalla al pie de la letra ejecuta `/s` y después busca un
  script que no existe en su home.

**Propuesta.** Un único generador canónico. Consolidar en `/s` (URL corta,
tecleable en la consola) tomando de `_build_anbernic_setup_sh` lo bueno: leer
el remote de config y usar `rclone copy --update` en ambas direcciones (más
cercano a "newest gana / no sobreescribir" que bisync). Esto resuelve de paso
la parte de motor de CLOUD-UX-7. Borrar el generador que sobre.

**Archivos.** `handlers/sync_cloud.py` (`_build_bootstrap_script`),
`handlers/system.py` (`_build_anbernic_setup_sh` — eliminar),
`tab-anbernic.html` (caja resultado). **Esfuerzo.** M. **Hecho cuando** hay un
solo script generado, el nombre que crea coincide con el que documenta la
pestaña, y respeta el remote configurado.

---

## ANBERNIC-UX-2 — "Descargar .sh" y el panel de Settings apuntan a un endpoint que no existe (404)

**Problema.** `GET /api/anbernic-setup.sh` no está registrado en ningún
handler — solo aparece en `openapi.json:4597` y como builder muerto
(`_build_anbernic_setup_sh`, `system.py:218`; ninguna ruta lo llama). Afecta a:

- El botón "⬇ Descargar .sh" del paso 5 (`sync.js:415` fija el href) → 404.
- El "Android setup panel" de Settings entero: QR, URL y comando curl
  (`loadAndroidSetupPanel`, `sync.js:238-253`) apuntan todos a la ruta muerta.

**Propuesta.** Tras decidir el canónico en ANBERNIC-UX-1: apuntar el botón de
descarga y el panel de Settings a `/s` (o registrar la ruta si se conserva).
Evaluar si el panel de Settings sobra por completo — duplica la pestaña
Anbernic (consolidación de las dos superficies de setup).

**Archivos.** `sync.js` (`loadAnbernicTab`, `loadAndroidSetupPanel`),
`handlers/system.py`, `openapi.json`. **Esfuerzo.** S. **Hecho cuando** ningún
botón/QR de setup devuelve 404 y solo queda una superficie de setup Android.

---

## ANBERNIC-UX-3 — Seguridad: rclone.conf con tokens OAuth servido a toda la LAN sin autenticación

**Problema.** `/api/rclone-export-config` devuelve el rclone.conf completo
(tokens OAuth de Dropbox/Drive) por HTTP plano. El guard (`sync_cloud.py:27-34`)
solo exige PIN cuando `web_allow_lan=false` — pero los **defaults** son
`web_host="0.0.0.0"` y `web_allow_lan=true` (`config.py:430,432`): en la
instalación por defecto, cualquier dispositivo de la red puede descargar los
tokens en cualquier momento, sin PIN y sin que el usuario lo sepa. El script
de `/s` lo agrava normalizando el patrón (`curl … /api/rclone-export-config`,
`sync_cloud.py:650`).

**Propuesta.** Token de un solo uso / corta vida: al generar el script `/s`,
el PC incrusta un token aleatorio (p. ej. 10 min, un uso) y
`/api/rclone-export-config` lo exige cuando la request no es loopback.
Alternativa mínima: exigir PIN siempre en binding no-loopback para este
endpoint concreto (ignorando `web_allow_lan`, que fue pensado para la UI, no
para secretos). En ambos casos, avisar en la pestaña de que el setup expone
credenciales solo durante la ventana del token.

**Archivos.** `handlers/sync_cloud.py` (guard + `_build_bootstrap_script`),
posiblemente `web/state.py` (token efímero). **Esfuerzo.** M. **Hecho cuando**
un `curl` frío desde otro equipo de la LAN a `/api/rclone-export-config`
devuelve 403, y el flujo de setup desde la consola sigue funcionando.

---

## ANBERNIC-UX-4 — Fallback con la IP personal del usuario hardcodeada

**Problema.** `get_bootstrap_script` usa `"192.168.1.160"` (la IP de esta
casa) si `get_lan_ip()` devuelve None (`sync_cloud.py:48`). En cualquier otra
red, el script generado apuntaría a una máquina ajena — y es un dato personal
metido en el repo.

**Propuesta.** Usar el header `Host` de la propia request como fallback (la
consola ya llegó al servidor por esa dirección, es por definición válida); si
tampoco, fallar con mensaje claro en el script generado.

**Archivos.** `handlers/sync_cloud.py:48`. **Esfuerzo.** XS. **Hecho cuando**
no queda ninguna IP literal en el código y el script se genera bien sin
`get_lan_ip()`.

---

## ANBERNIC-UX-5 — La promesa del paso 1 es falsa: desde la consola no aparece ninguna guía

**Problema.** El paso 1 dice "al abrir esta URL en la Anbernic aparecerá
automáticamente una guía de instalación con todos los botones de descarga"
(`tab-anbernic.html:30-32`). Lo que aparece realmente en un navegador Android
es `android-detected-panel` (`_banners.html:21-52`, activado por
`_checkAndroidUserAgent`, `sync.js:285-292`, llamado en `main.js:731`): un
panel de **sync**, no de instalación — sin un solo botón de descarga, con
"PC conectado" y el dot verde hardcodeados (ninguna comprobación real), y cuyo
botón "Sincronizar saves ahora" muere siempre por CLOUD-UX-6. Para la consola
sin configurar (el público de esta pestaña) el panel es un callejón sin salida.

**Propuesta.** El panel Android distingue dos estados: consola ya configurada
→ panel de sync actual (con CLOUD-UX-6 arreglado); primera vez → botón grande
"Configurar esta consola" que lleva a una vista táctil con los pasos
(F-Droid/Termux/comando), que es lo que el paso 1 promete. Y comprobar el
estado real del servidor en vez del dot fijo (un ping a `/api/version` basta).
Corregir el texto del paso 1 mientras tanto.

**Archivos.** `_banners.html`, `sync.js` (`_checkAndroidUserAgent`, flujo TV),
`tab-anbernic.html`. **Esfuerzo.** M. **Hecho cuando** abrir la URL desde la
consola ofrece un camino de instalación real con botones, como promete el
paso 1.

---

## ANBERNIC-UX-6 — QR para no teclear la URL (y "Copiar URL" copia al portapapeles equivocado)

**Problema.** El paso más doloroso del flujo es teclear `http://192.168.x.x:7777`
con el teclado táctil de la consola. La app **ya tiene** generador de QR
(`renderQR`, `config.js:499`, usado en Settings) y no se usa aquí. Además
"📋 Copiar URL" (`copyAnbernicUrl`, `sync.js:423-428`) copia al portapapeles
**del PC** — inútil para escribir en la consola — y el consejo del paso 5
("si habías copiado la URL desde el PC mediante ADB, el portapapeles ya está
listo", `tab-anbernic.html:147`) alude a una función de portapapeles-por-ADB
que no existe en ninguna parte del código.

**Propuesta.** Canvas QR junto a `anb-ip-display` en el paso 1 (reutilizar
`renderQR`). Quitar o re-etiquetar "Copiar URL" y eliminar la frase del
portapapeles ADB (o implementarla de verdad con
`adb shell am broadcast`/`input text`, pero eso es otra tarea — YAGNI).

**Archivos.** `tab-anbernic.html`, `sync.js` (`loadAnbernicTab`).
**Esfuerzo.** XS. **Hecho cuando** el paso 1 muestra un QR escaneable y ningún
texto alude a funciones inexistentes.

---

## ANBERNIC-UX-7 — Sin comprobación de prerequisitos: el setup puede fracasar por causas que el PC ya conoce

**Problema.** La pestaña manda al usuario a la consola sin verificar nada de
lo que el propio PC puede comprobar:

- **Cloud sin configurar:** si rclone no tiene remotes, el script descarga un
  rclone.conf vacío/comentario y la consola queda a medias (el script solo
  imprime un AVISO, `sync_cloud.py:651-657`). `/api/rclone-status` existe y la
  pestaña no lo consulta.
- **Servidor inaccesible desde la LAN:** si `web_host` es loopback, la URL
  mostrada no funcionará nunca desde la consola; y en Windows el firewall
  puede bloquear el puerto — `_check_firewall` existe (`lan.py:52`) pero solo
  se usa en el arranque CLI (`cli.py:969`), la pestaña no avisa.

**Propuesta.** Banner de prerequisitos arriba de la pestaña con dos checks:
① "Cloud configurado" (`/api/rclone-status`, con enlace a la pestaña Cloud si
falta) y ② "Servidor accesible por red" (binding no-loopback + regla de
firewall, exponiendo `_check_firewall` en `/api/local-url` o un endpoint de
diagnóstico). Los pasos 1-5 se muestran igualmente, pero el usuario sabe qué
arreglar antes de ir a la consola.

**Archivos.** `tab-anbernic.html`, `sync.js` (`loadAnbernicTab`),
`handlers/esde/system.py` (`/api/local-url`), `web/lan.py`. **Esfuerzo.** S.
**Hecho cuando** con rclone sin remotes o firewall cerrado, la pestaña lo dice
antes de que el usuario toque la consola.

---

## ANBERNIC-UX-8 — Errores silenciosos y enlaces engañosos (pulido)

**Problema.** Menores agrupados:

- Si `/api/local-url` falla, `loadAnbernicTab` deja "Detectando…"/"Cargando…"
  para siempre (solo `console.warn`, `sync.js:418-420`); `copyAnbernicCmd`
  compara contra el literal `'Cargando…'` (`sync.js:432`).
- "⬇ Descargar Termux APK" (`anb-termux-apk-link`, `tab-anbernic.html:82`)
  abre la **página** de releases de GitHub, no un APK; el id sugiere que iba a
  resolverse por JS y nunca se implementó. En el navegador limitado de la
  consola, aterrizar en GitHub es perderse.

**Propuesta.** Estado de error visible en `anb-ip-display` con botón
reintentar (ya existe "↻ Actualizar IP", basta con mostrar el fallo); etiqueta
honesta "Ver releases de Termux" o resolver el asset APK real vía la API de
GitHub desde el PC.

**Archivos.** `sync.js`, `tab-anbernic.html`. **Esfuerzo.** XS. **Hecho
cuando** desconectar la red y abrir la pestaña muestra un error accionable, y
cada botón hace lo que dice su etiqueta.

---

## Orden recomendado

| # | ID | Tipo | Esfuerzo | Por qué este orden |
|---|----|------|----------|--------------------|
| 1 | ANBERNIC-UX-1 | Bug | M | Decide el script canónico; desbloquea 2 y resuelve el motor de CLOUD-UX-7 |
| 2 | ANBERNIC-UX-2 | Bug | S | Elimina los 404 y la superficie duplicada de Settings |
| 3 | ANBERNIC-UX-4 | Bug | XS | IP personal hardcodeada — quick win |
| 4 | ANBERNIC-UX-3 | Seguridad | M | Tokens OAuth expuestos a la LAN en la config por defecto |
| 5 | ANBERNIC-UX-5 | UX | M | El camino consola-primera-vez hoy es un callejón sin salida (con CLOUD-UX-6) |
| 6 | ANBERNIC-UX-7 | UX | S | Prerequisitos visibles antes de ir a la consola |
| 7 | ANBERNIC-UX-6 | UX | XS | QR — quita el paso más doloroso del flujo |
| 8 | ANBERNIC-UX-8 | UX | XS | Pulido de errores y etiquetas |

Notas sin tarea propia:

- **Validación en hardware (pendiente real):** comprobar en la RG556 si el
  Termux limpio trae `curl` — el one-liner `curl -s …/s | bash` falla en un
  Termux recién instalado si no lo trae (la guía manual
  `docs/sync/Guia-Termux-Anbernic.md` no usa curl en ningún paso). Añadir al
  checklist cuando se ejecute la guía en la consola.
- La ruta de la guía cambió a `docs/sync/Guia-Termux-Anbernic.md`
  (la memoria y algún doc aún citan `Tareas/Guia-Termux-Anbernic.md`).
- `_build_anbernic_setup_sh` tiene una línea sin efecto
  (`system.py:227` — expresión no asignada); irrelevante si se borra en
  ANBERNIC-UX-1/2.
