# ROM Manager Local — Siguientes pasos

*Actualizado: Día 5 (2026-03-10)*

---

## 🔴 Crítico — bloquea el objetivo principal

### 1. Ejecutar guía Termux en la Anbernic
La guía `Tareas/Guia-Termux-Anbernic.md` existe. Falta ejecutarla físicamente en la consola.

**Pasos pendientes:**
- Instalar Termux en la Anbernic RG 556
- Seguir la guía paso a paso
- Verificar que `rclone sync` baja correctamente los saves desde Dropbox
- Documentar si hay problemas de rutas o permisos en Android

### 2. Deduplicación Anbernic→PC en Cable Sync (por SHA1)
Diseñado en el Día 5, pendiente de implementar. Flujo acordado:

1. Conectar SD card de la Anbernic al PC
2. Escanear la SD card desde Overview (ya funciona)
3. Los ROMs quedan en la BD con su SHA1
4. La pestaña Duplicates muestra qué ROMs de la Anbernic ya están en el PC
5. **Añadir** en Cable Sync un flag "Omitir ROMs ya presentes en la biblioteca (por SHA1)" que consulte la BD en lugar de rehashear

**Qué implementar:**
- Añadir `repository.sha1_exists(sha1) -> bool` (SELECT EXISTS)
- En `_handle_cable_sync`, cuando direction es `anbernic_to_pc` y la opción está activada: calcular SHA1 del archivo de la Anbernic antes de copiar → skip si ya existe en BD
- Checkbox en la UI del Cable Sync: "Omitir ROMs duplicados (comprueba SHA1 en BD)"

### 3. Probar RetroAchievements en producción
La integración está implementada pero no probada con una API key real.

**Qué verificar:**
- Obtener API key en retroachievements.org → Settings → Web API Key
- Configurarla en la pestaña Settings del frontend
- Ejecutar "Comprobar compatibilidad RA" y verificar resultados
- Comprobar que el CSV se genera bien para >10 juegos con alternativa
- Verificar que la caché funciona (segunda ejecución debe ser instantánea)

**Posible problema conocido:** si los resultados son 0, revisar `ra_client._parse_game_list()` — posible mismatch en la clave `"Hashes"`.

---

## 🟡 Importante — mejora significativa

### 4. Pasar los tests tras los cambios del Día 4 y 5

```bash
scripts\rommgr.cmd pytest tests/ -x
```

Los cambios que pueden haber roto tests:
- `operation_planner.py` (fix NTFS samefile)
- `ScanResult` (nuevo campo `pruned`)
- Firma de `build_plan`

### 5. Quick scan mode (backend)
El botón "Quick (sin hash)" ya existe en la UI y pasa `quick=True` al servidor.

**Falta:** en `rom_scanner.py`, cuando `quick=True`, saltar el hashing y guardar `sha1=''`, `md5=''`, `crc32=''`. El match y el RA check no funcionarán hasta hacer un scan completo posterior.

### 6. ScreenScraper: campos devid/devpassword en Settings
Si el usuario tiene credenciales de desarrollador de ScreenScraper, debería poder configurarlas desde la UI.

**Qué añadir:**
- Campos `screenscraper_dev_id` y `screenscraper_dev_pass` en Settings tab
- Añadir a la lista `allowed` de `_handle_save_config()`
- Recargar en memoria tras guardar

### 7. Actualizar panel RetroAchievements: invalidar caché
Añadir checkbox "Forzar recarga (ignorar caché)" en el panel de RA. La caché dura 1 semana.

---

## 🟢 Calidad de vida — menor prioridad

### 8. Vista de historial de scans
La tabla `scan_runs` existe en la BD pero no hay vista en el frontend. Útil para saber cuándo fue el último scan y cuántos archivos encontró/purgó.

### 9. Región parser mejorado
`region_parser.py` sigue siendo limitado. Muchos juegos tienen `region = null` aunque el nombre incluya `(USA)`, `(Europe)`, etc.

### 10. Tab Sync: vista de saves individuales
El tab Sync muestra el log de operaciones pero no los saves en sí.

### 11. Packaging como app
Decisión arquitectural pendiente: servidor local vs pywebview+PyInstaller. No urgente.

### 12. Validación de archivos .cue antes de convertir a CHD
`chdman` falla con error críptico si falta un .bin. Mejor detectarlo antes.

---

## Notas técnicas

### Cómo arrancar el servidor
```bash
scripts\rommgr.cmd serve
# o directamente:
C:\Users\rammu\anaconda3\envs\rom_manager\python.exe -m rom_manager serve
```

### Cómo ejecutar los tests
```bash
scripts\rommgr.cmd pytest tests/ -v
```

### Rutas importantes
- Config: `config.toml` (raíz del proyecto)
- BD: `.rommgr/library.sqlite`
- Caché RA: `.rommgr/ra_cache/ra_hashes_{console_id}.json`
- Logs: `.rommgr/logs/`
- chdman: `tools/chdman.exe`

### Flujo recomendado para importar ROMs de la Anbernic al PC
1. Insertar SD card de la Anbernic en el PC → aparece como letra de unidad (ej. `F:\`)
2. Scan de `F:\` desde Overview (calcula SHA1 de todo)
3. Pestaña Duplicates → muestra qué ROMs de la Anbernic ya están en el PC
4. Cable Sync → Anbernic → PC → solo saves (sobreescribir está bien)
5. *(futuro)* Cable Sync → Anbernic → PC → ROMs con flag "omitir duplicados por SHA1"

### API de RetroAchievements
- Endpoint: `GET https://retroachievements.org/API/API_GetGameList.php?i={console_id}&h=1&f=1&y={api_key}`
- Hash principal: MD5
- Respuesta: array JSON con `ID`, `Title`, `NumAchievements`, `Points`, `Hashes` (array de MD5)
