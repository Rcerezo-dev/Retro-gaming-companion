# Día 3 — Tareas del frontend

He estado probando el frontend, y he visto los siguientes problemas:

## Estado de las tareas

| # | Tarea | Estado |
|---|-------|--------|
| 1 | Botón de scan se bloquea al estar corriendo | ✅ Hecho |
| 2 | Columna de plataforma no se muestra | ✅ Hecho |
| 3 | Guardar cada scan para no tener que volver a correrlo | ✅ Hecho (datos persisten en SQLite) |
| 4 | Opciones de match, plan, duplicados en el frontend | ✅ Hecho |
| 5 | Proceso mejor explicado para usuarios | ✅ Hecho |
| 6 | App nativa en lugar de servidor local | ❌ Pendiente (decisión de diseño) |
| 7 | Scan lento: ¿es necesario procesar todo el archivo? | ❌ Pendiente |
| 8 | Checks antes de renombrar con previsualización | ⚠️ Parcial |

---

## Detalle

### ✅ 1. Botón de scan se bloquea durante el proceso
`btn-scan` se deshabilita al lanzar el scan y sólo se reactiva al terminar o fallar. El servidor también detecta si ya hay un scan en curso (`_jobs["scan"]`) y devuelve `already_running`. Lo mismo aplica al botón de Match.

### ✅ 2. Columna de plataforma
La tabla de Games muestra la columna Platform correctamente. El servidor devuelve `platform` en `/api/games` y el frontend la renderiza con fallback a `''`.

### ✅ 3. Persistencia de scans
Los datos escaneados se guardan en SQLite. Al reiniciar el servidor, la pestaña Games sigue mostrando los juegos del último scan sin necesidad de volver a escanear. No hay historial de scans pasados con línea de tiempo, pero los datos persisten.

### ✅ 4. Opciones de match, plan y duplicados en el frontend
- **Match catálogos**: ✅ Botón en el panel de Acciones (Overview)
- **Plan / renombrado**: ✅ Pestaña Plan con vista previa y botón "Aplicar renombrado"
- **Ver duplicados**: ✅ Pestaña Duplicates muestra grupos con rutas y espacio desperdiciado
- **Eliminar duplicados desde la UI**: ✅ Botón Delete por entrada (la primera copia se marca "keep"; las demás son borrables con confirmación)

### ✅ 5. Proceso mejor explicado para usuarios
Añadida guía de 4 pasos (① Scan → ② Match → ③ Plan → ④ Apply) en la pestaña Overview, con descripción de cada fase.

### ❌ 6. App nativa vs servidor local
Decisión de arquitectura no tomada. Opciones a evaluar:
- Seguir como servidor local (Flask/stdlib HTTP) con webview embebido (pywebview)
- Empaquetar como app con PyInstaller + webview
- Mantener el servidor local y acceder desde el navegador (estado actual)

### ❌ 7. Scan lento para archivos grandes
El scanner actualmente calcula SHA1+MD5+CRC32 leyendo el archivo completo en chunks de 1 MB. Para ROMs grandes (ISO de PS2, Wii, etc.) esto puede tardar varios segundos por archivo. Posibles mejoras pendientes:
- Modo "quick scan": sólo nombre de archivo → confianza baja, sin hash
- Hash parcial (primeros/últimos N MB) para detección rápida con fallback a hash completo si hay colisión
- Cachear el hash en SQLite y saltarlo si `mtime` no cambió

### ⚠️ 8. Checks antes de renombrar con previsualización
- **Checkboxes de Región y Revisión**: ✅ Implementados en la pestaña Plan; el plan se recarga en tiempo real al marcar/desmarcar
- **Incluir SHA en el nombre**: ❌ No implementado
- **Orden personalizable de los componentes**: ❌ No implementado
- La previsualización existe pero sólo refleja región/revisión, no otros campos

---

## Próximos pasos sugeridos

1. ~~Añadir botón "Eliminar duplicados seleccionados" en la pestaña Duplicates~~ ✅
2. Implementar modo quick scan (hash opcional) para reducir tiempos en librerías grandes
3. ~~Texto de onboarding / flujo guiado en la UI~~ ✅
4. Evaluar si empaquetar como app con pywebview

---

## Evaluación de huecos del proyecto (Día 3, sesión 2)

Estado actual de la herramienta: el PC está casi completo. El problema es que **el objetivo real del proyecto son dos dispositivos**, y solo uno de ellos tiene soporte real.

### 🔴 Crítico — bloquea el objetivo principal

#### 1. El lado Anbernic del sync nunca se ha diseñado
La sincronización de saves existe en el PC (rclone → nube), pero la Anbernic (Android) no tiene ninguna solución definida. El PC sube saves a Dropbox; ¿quién los descarga en la consola? Las opciones que se barajaron (FolderSync, Autosync, Termux + rclone) siguen sin evaluarse. Sin esto, el objetivo #2 del proyecto está a medias: los saves suben pero no bajan automáticamente a la consola.

**Opciones a decidir:**
- **FolderSync / Autosync for Dropbox** — app Android, el usuario configura carpeta local ↔ Dropbox. Sin código. El más fácil.
- **Termux + rclone** — mismo binario que en el PC, misma config. Más control, más fricción para el usuario.
- **USB desde el PC** — fallback: cuando la Anbernic está enchufada, el PC puede leer/escribir en ella con ADB o como dispositivo MTP.

#### 2. Metadatos y gamelist.xml para la Anbernic
EmulationStation (el frontend de la Anbernic) muestra portadas, descripciones y géneros a través de archivos `gamelist.xml` por sistema. Sin esos archivos, aunque los ROMs estén perfectamente organizados y renombrados, la consola muestra solo una lista de texto plano.

Tenemos CRC32, MD5 y SHA1 de todos los archivos. ScreenScraper acepta exactamente esos hashes. Solo falta:
1. Llamar a la API de ScreenScraper por cada ROM
2. Descargar portadas/metadatos
3. Generar `gamelist.xml` por sistema en el formato que espera EmulationStation

Esto es la diferencia entre una colección funcional y una colección con la que da gusto jugar en la Anbernic.

#### 3. Cómo llegan los ROMs a la Anbernic
Organizar la biblioteca en el PC está bien. Pero ¿cómo se copia a la Anbernic? No hay ninguna herramienta para:
- Copiar ROMs seleccionados por plataforma a la consola (USB/ADB/red)
- Sincronizar solo las novedades (nuevos ROMs) sin copiar todo
- Adaptar la estructura de carpetas al formato que espera RetroArch en Android

---

### 🟡 Importante — mejora significativa de la experiencia

#### 4. Configuración desde la UI
Para que el sync funcione, el usuario tiene que editar `config.toml` a mano para poner `saves_dir` y el remote de rclone. Hay que poder configurar esto desde la pestaña Settings (que no existe aún). Mínimo útil: un formulario con los campos críticos que escriba el TOML.

#### 5. Scan lento
Identificado en Día 3. El scanner hashea cada archivo completo (SHA1+MD5+CRC32). Para ISOs de PS2, Wii o GameCube (4–8 GB), esto tarda minutos por archivo. La caché por mtime ya evita rehashear en rescans, pero el scan inicial de una librería grande puede durar horas.

Solución: modo `--quick` que solo indexa nombre + tamaño + mtime sin hashear. Pierde matching por hash pero detecta plataforma y permite navegar la biblioteca de forma inmediata. El hash completo se puede lanzar en background o bajo demanda.

#### 6. Tests probablemente rotos
La memoria dice "200 tests passing" pero desde entonces:
- `MatchedGame` ganó un campo `sha1` (nuevo campo obligatorio en el dataclass)
- Se añadieron varios métodos a `LibraryRepository`
- `build_plan` cambió su firma

Cualquier test que construya un `MatchedGame` directamente falla ahora. Hay que verificar y actualizar.

---

### 🟢 Calidad de vida — menor prioridad

#### 7. Vista de saves en el frontend
El tab Sync muestra el log de operaciones pero no los saves en sí: qué archivos hay, cuándo se sincronizaron por última vez, si hay alguno sin subir.

#### 8. Historial de scans
La tabla `scan_runs` existe en la BD (con fecha, archivos vistos, ROMs detectados) pero no hay ninguna vista en el frontend. Útil para saber cuándo fue el último scan y qué encontró.

#### 9. Región parser muy limitado
`region_parser.py` se marcó como "muy limitado" en el Día 2 y nunca se mejoró. Muchos juegos probablemente tienen `region = null` aunque el nombre del archivo sí la incluye.

#### 10. App nativa vs servidor local
Decisión arquitectural pendiente. Mientras el servidor local funcione bien, no es urgente.

---

### Resumen de prioridades

| Prioridad | Qué | Por qué |
|-----------|-----|---------|
| 🔴 1 | Diseñar sync en la Anbernic (Android) | Sin esto el objetivo #2 no existe |
| 🔴 2 | Scraping + gamelist.xml | Sin esto la consola es una lista de texto |
| 🔴 3 | Cómo copiar ROMs a la Anbernic | Sin esto la colección solo vive en el PC |
| 🟡 4 | Config desde la UI | Necesario para que un usuario normal pueda configurar el sync |
| 🟡 5 | Quick scan | Usabilidad con librerías grandes |
| 🟡 6 | Pasar los tests | Deuda técnica acumulada |
