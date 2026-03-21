# ROM Manager — Día 9: Log de continuación

*Fecha: 2026-03-15 — Escrito al final de la sesión del Día 8*

---

## Qué se hizo en el Día 8 (resumen rápido)

| Fix | Resultado |
|-----|-----------|
| D8-1 a D8-7 | BD obsoleta, renombrador, conflictos RA, duplicados por versión, Tools por dispositivo, Cable Sync conteos, auto-informe tras scan |
| D8-9 | Arquitectura dos-BD: `library_pc.db` + `library_android.db` |
| D8-18 | Cable Sync logging persistente + modo seguro |
| D8-P3 | **Daemon auto-sync**: detecta Anbernic por ADB cada 10s y sincroniza saves solo |
| D8-P2 | **Tab Inbox**: pipeline completo drop → extrae → escanea → cruza con DAT → renombra → carpeta de plataforma |
| D8-P1 | **Wizard primera vez**: modal guiado 3 pasos + banner checklist en Overview |
| SD card | **Daemon SD card**: detecta inserción de tarjeta (letra de unidad) cada 8s y sincroniza saves automáticamente |
| Paths | `anbernic_root` persistido en `config.toml`, rutas de Cable Sync guardadas en localStorage |

---

## Estado real de los 3 pilares

| Pilar | Estado |
|-------|--------|
| 1 — Setup inicial | ✅ Wizard implementado. Pendiente: **probar en real** con la biblioteca del usuario |
| 2 — Inbox | ✅ Implementado. Pendiente: **probar en real** + verificar que el pipeline completo funciona end-to-end |
| 3 — Sync saves | ✅ Daemon SD card implementado. **Pendiente crítico: probar que detecta la tarjeta y sincroniza** |

---

## Tareas pendientes para la próxima sesión

### 🔴 Prioridad alta — Probar y validar en real

#### P1. Validar sync automático con tarjeta SD
El daemon `_sd_card_sync_loop` detecta inserción de `config.anbernic_root` como directorio. Hay que:
1. Configurar `anbernic_root` en Settings (ruta donde monta la SD, p.ej. `E:\Carpetas anbernic`)
2. Insertar la tarjeta → esperar ≤ 8 segundos → verificar que el banner muestra "Tarjeta SD detectada"
3. Verificar que se sincronizan saves en `.rommgr/cable_sync_ops.log`
4. Si no funciona: revisar `_sd_card_sync_loop` en `server.py` — puede ser que `ab_path.exists()` no detecte bien la raíz de la SD en Windows

**Archivo clave:** `src/rom_manager/web/server.py` → función `_sd_card_sync_loop`

#### P2. Validar migración a dos BDs
Al arrancar la app por primera vez tras el cambio:
1. Ir a Settings → botón "Migrar BD a dos DBs"
2. Verificar que los juegos de la Anbernic (rutas que NO empiezan por `library_root`) pasan a `library_android.db`
3. Verificar que Overview muestra conteos separados para PC y Anbernic

**Si la migración falla:** revisar `_handle_migrate_split_db` en `server.py`

#### P3. Validar Inbox end-to-end
1. Configurar `inbox_path` en la nueva pestaña Inbox
2. Soltar un ZIP de un juego conocido (p.ej. un GBA)
3. Pulsar "Analizar carpeta" → debe detectar plataforma
4. Pulsar "Organizar todo" → debe extraer, escanear, cruzar con DAT, renombrar, mover a `Game Boy Advance/`
5. Si falla en algún paso: el progress bar mostrará en qué paso se detuvo

---

### 🟡 Prioridad media — Bugs conocidos pendientes de confirmar

#### B1. Renombrador en Anbernic: ¿funciona en disco?
**Síntoma reportado:** 1015 archivos pendientes de renombrar en la Anbernic que nunca bajan.
**Hipótesis:** los archivos están en la SD (montada como `E:\`) y la ruta en BD no coincide, o la SD estaba desmontada al intentar renombrar.
**Cómo reproducir:** con la SD insertada, ir a Organizar → filtrar "Solo Consola Android" → intentar aplicar renombrados → ver panel de errores (D8-2 añadió `error_details`).
**Archivos clave:** `web/server.py` → `_handle_apply`, `web/frontend.py` → panel `#apply-error-details`

#### B2. `prune_stale_entries` y la Anbernic
**Riesgo:** si el usuario escanea solo el PC (sin SD insertada), `prune_stale_entries` podría borrar registros de la Anbernic de `library_android.db` porque sus rutas no existen en ese momento.
**Verificar:** leer `scanner/rom_scanner.py` → `prune_stale_entries` → comprobar que filtra por `source_root` y NO toca registros de otra raíz.
**Si falla:** añadir filtro `WHERE source_path LIKE ?` estricto al source_root del scan actual.

#### B3. Resolver conflictos con RA winner
`POST /api/apply-ra-conflicts` busca en el caché local de RA. Si el caché no existe (primera vez o caducado), no resuelve nada. Verificar que muestra mensaje útil en ese caso.

---

### 🟢 Prioridad baja — Mejoras de UX pendientes

#### U1. Wizard: botón "Volver a mostrar asistente"
El wizard se descarta guardando `wizard_dismissed` en localStorage. Añadir botón en Settings para resetearlo y poder relanzar el wizard.

#### U2. Informe automático post-scan para Anbernic
El scan post-sync (D8-7) genera informe del PC. Debería generar también informe de la Anbernic cuando se escanea `library_android.db`.

#### U3. Notificación de escritorio cuando termina el sync
Usar la Web Notifications API (`new Notification(...)`) para mostrar una notificación del sistema cuando el daemon termina el sync automático. El usuario no tiene que tener la web abierta para saberlo — aparece en la bandeja de Windows.

#### U4. Cable Sync: mostrar diferencia de archivos antes de sincronizar
Antes de pulsar "Iniciar sincronización", mostrar un resumen: "X saves en PC, Y saves en Anbernic, Z serán copiados". Requiere un pre-scan rápido.

---

## Contexto técnico importante para la próxima sesión

### Dos bases de datos
```
.rommgr/
  library_pc.db        ← datos del PC (library_root)
  library_android.db   ← datos de la Anbernic (anbernic_root)
```
- `_repo_for_path(path)` → devuelve el repo correcto según si la ruta empieza por `library_root`
- `repository` = PC, `repository_android` = Anbernic (globals en server.py)

### config.toml tras esta sesión
```toml
[library]
library_root = "E:\\Carpetas anbernic"     # PC library
anbernic_root = ""                          # ← NUEVO: ruta SD card, rellenar en Settings

[sync]
auto_sync_enabled = true
auto_sync_direction = "newest"
auto_sync_android_path = "/storage/emulated/0/RetroArch"
conflict_policy = "newest"

[inbox]
path = ""
target_root = ""
auto_process = false
delete_source = false
```

### Daemon SD card
- Función: `_sd_card_sync_loop` en `server.py`
- Comprueba cada 8s si `Path(config.anbernic_root).exists()`
- Al detectar inserción → llama `_run_sd_auto_sync` en hilo separado
- Log en `.rommgr/cable_sync_ops.log`
- Estado visible en banner superior de la app

### Daemon ADB (sigue activo)
- Función: `_auto_sync_loop` en `server.py`
- Comprueba cada 10s dispositivos ADB
- Ambos daemons coexisten — si ADB falla, SD card sigue funcionando

### Jobs en background
```python
_jobs = {
    "scan": False, "match": False, "convert_chd": False,
    "scrape": False, "extract_zip": False, "health_check": False,
    "ra_check": False, "cable_sync": False, "apply": False,
    "inbox": False, "setup": False,
}
```

---

## Archivos modificados esta sesión (para git)

```
src/rom_manager/config.py
src/rom_manager/cli.py
src/rom_manager/web/server.py
src/rom_manager/web/frontend.py
src/rom_manager/utils/m3u_generator.py
src/rom_manager/utils/multidisc_verifier.py
src/rom_manager/utils/library_report_html.py
Tareas/Día8.md
Tareas/FIXES_necesarios.md
Crear_acceso_directo.ps1  (nuevo)
```
