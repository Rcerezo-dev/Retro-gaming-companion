# Retro Vault — Guía de pruebas en un PC nuevo

Esta guía cubre la instalación desde cero y la verificación de cada función principal. Sigue los pasos en orden: cada sección depende de la anterior.

---

## 1. Requisitos previos

| Herramienta | Versión mínima | Dónde conseguirla |
|---|---|---|
| Python | 3.11+ (recomendado 3.12) | python.org o Anaconda |
| rclone | cualquiera reciente | rclone.org |
| chdman | v0.286+ | mamedev.org/tools |
| adb | cualquiera | developer.android.com/tools (solo para Cable Sync) |
| Git | cualquiera | git-scm.com |

---

## 2. Instalación

### 2a. Clonar el repositorio

```bash
git clone https://github.com/Rcerezo-dev/Retro-gaming-companion.git
cd Retro-gaming-companion
```

### 2b. Crear entorno e instalar (Windows + Conda — recomendado)

```bash
conda create -n rom_manager python=3.12
conda activate rom_manager
pip install -e .
```

Sin Conda:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

### 2c. Binarios externos (descarga automática)

Ejecuta el script incluido. Descarga rclone, adb y chdman directamente en `tools/`:

```powershell
.\scripts\download-tools.ps1
```

Al terminar verifica:

```bash
tools\rclone.exe --version
tools\adb.exe version
tools\chdman.exe --version
```

> **chdman manual (fallback):** Si el script no pudo descargarlo (MAME solo publica instaladores grandes sin 7-Zip instalado), ve a **mamedev.org/tools**, descarga el paquete y extrae `chdman.exe` en `tools/`. Esto solo es necesario para convertir ROMs a CHD — el resto de funciones no lo requieren.

---

## 3. Configuración mínima

Crea `config.toml` en la raíz del proyecto. Ajusta las rutas a las de tu PC:

```toml
[library]
library_root = "D:\\ROMs"   # carpeta donde tienes o pondrás las ROMs

[tools]
chdman = "tools\\chdman.exe"
adb    = "tools\\adb.exe"

[web]
host = "127.0.0.1"
port = 7777

[screenscraper]
user = ""   # opcional; déjalo vacío para saltar el scraping
pass = ""

[retroachievements]
api_key  = ""   # opcional; déjalo vacío para saltar los logros
username = ""
```

Para cloud sync, añade las fuentes cuando llegues a esa sección.

---

## 4. Arrancar la aplicación

```bash
# Con Conda activado:
python -m rom_manager serve

# Con el lanzador Windows (no requiere activar el entorno):
scripts\rommgr.cmd serve
```

Abre **http://127.0.0.1:7777** en el navegador.

**Resultado esperado:** el dashboard carga, muestra "0 juegos" y no hay errores en la consola.

---

## 5. Pruebas funcionales

### 5.1 Escaneo de biblioteca

**Qué hace:** recorre `library_root`, hashea cada ROM (SHA1 + MD5 + CRC32) y guarda el inventario en SQLite.

**Pasos:**
1. Pon algunas ROMs en `library_root` (5-10 son suficientes para probar).
2. En la pestaña **Inicio** → pulsa **Escanear**.
3. Observa la barra de progreso en tiempo real.

**Resultado esperado:** al terminar, el contador de juegos sube. El archivo `.rommgr/library_pc.db` existe y pesa más de 0 bytes.

**Escaneo rápido (sin hashing):**

```bash
python -m rom_manager scan "D:\ROMs" --quick
```

---

### 5.2 Estructura de biblioteca

**Qué hace:** crea las carpetas estándar ES-DE (`psx/`, `gba/`, `snes/`, etc.) bajo `library_root`.

**Pasos:**
1. Pestaña **Herramientas** → sección **Estructura de biblioteca** → **Crear estructura**.

**Resultado esperado:** aparecen las carpetas de plataforma en `library_root`. Las existentes no se modifican.

---

### 5.3 Descarga de catálogos DAT

**Qué hace:** descarga los DATs de No-Intro y Redump desde libretro-database para poder identificar ROMs.

**Pasos:**
1. Pestaña **Ajustes** → sección **Catálogos DAT** → **Descarga automática**.
2. Selecciona las plataformas que quieras (o **Descargar todos**).
3. Espera a que la barra de progreso termine.

**Resultado esperado:** archivos `.dat` en `.rommgr/catalogs/nointro/` y/o `.rommgr/catalogs/redump/`.

También puedes colocar DATs manualmente en esas carpetas si ya los tienes.

---

### 5.4 Matching con catálogos

**Qué hace:** cruza el SHA1 de cada ROM escaneada con los DATs para identificar título canónico, región y plataforma.

**Pasos:**
1. Asegúrate de haber escaneado (5.1) y descargado DATs (5.3).
2. Pestaña **Juegos** → botón **Match** (o desde CLI: `python -m rom_manager match`).

**Resultado esperado:** en la columna "Match" aparece "✓ Matched" para las ROMs reconocidas. Las no reconocidas muestran "Sin match" — normal si son ROMs modificadas o regiones poco comunes.

---

### 5.5 Renombrado (Plan → Apply)

**Qué hace:** propone renombrar las ROMs al nombre canónico del catálogo. Atómico: si algo falla, revierte.

**Pasos:**
1. Pestaña **Organizar** → **Ver plan** (o CLI: `python -m rom_manager plan`).
2. Revisa la lista: columna "Actual" vs "Propuesto".
3. Pulsa **Aplicar** (o CLI: `python -m rom_manager apply`).

**Resultado esperado:** los archivos se renombran. Si hay saves con el mismo nombre base, se renombran junto a la ROM. Un segundo "Apply" no hace nada (idempotente).

> **Ojo PSX:** si tienes sets `.cue + .bin`, el renombrado reescribe el `.cue` automáticamente para mantener la referencia correcta.

---

### 5.6 Duplicados

**Qué hace:** detecta ROMs con el mismo SHA1 (copias exactas) para liberar espacio.

**Pasos:**
1. Pestaña **Duplicados**.
2. Revisa los grupos. La primera entrada de cada grupo es el "canónico" (el que se conserva).
3. Pulsa **Eliminar sobrantes** si quieres borrar las copias.

**Resultado esperado:** cada grupo muestra N entradas con el mismo hash. Eliminar sobrantes deja solo una copia por grupo.

---

### 5.7 Inbox (procesado automático de ZIPs)

**Qué hace:** procesa archivos nuevos en `library_root/inbox/`: identifica la plataforma, descomprime, renombra y mueve a la carpeta correcta.

**Pasos:**
1. Copia 1-2 ROMs en ZIP dentro de `library_root/inbox/`.
2. Pestaña **Inbox** → **Procesar inbox**.

**Resultado esperado:** los ZIPs desaparecen del inbox y los archivos extraídos aparecen en su carpeta de plataforma (`psx/`, `snes/`, etc.).

---

### 5.8 Scraper (metadatos y carátulas)

Requiere cuenta en ScreenScraper (gratuita). Añade usuario y contraseña en `config.toml` o en **Ajustes**.

**Pasos:**
1. Pestaña **Scraper** → selecciona las plataformas → **Scrapear**.
2. Espera a que descargue títulos, años, géneros y portadas.

**Resultado esperado:** aparecen imágenes en `library_root/<plataforma>/media/images/`. Se genera `gamelist.xml` en cada carpeta de plataforma, listo para ES-DE.

---

### 5.9 RetroAchievements

Requiere API key de retroachievements.org (Settings → Web API Key).

**Pasos:**
1. Añade `api_key` y `username` en `config.toml` o en **Ajustes**.
2. Pestaña **RetroAchievements** → **Comprobar compatibilidad**.

**Resultado esperado:** la tabla muestra qué ROMs tienen soporte de logros y qué versión es la compatible. El progreso personal aparece si el `username` es correcto.

---

### 5.10 Conversión a CHD

Para sets PSX, Saturn o Dreamcast en formato `.cue + .bin`.

**Pasos:**
1. Pestaña **Herramientas** → sección **Conversión CHD**.
2. Selecciona la carpeta con los sets → **Convertir**.

**Resultado esperado:** cada set `nombre.cue + nombre.bin` se convierte en `nombre.chd`. Los archivos originales se eliminan solo si la conversión fue exitosa (comprueba el log).

---

### 5.11 Cloud Sync (saves ↔ nube)

Requiere rclone configurado (`rclone config`) con al menos un remoto (Dropbox, OneDrive, Google Drive, etc.).

**Configuración en `config.toml`:**

```toml
[sync]
rclone = "rclone"   # o ruta completa si no está en PATH

[[sync.sources]]
name      = "RetroArch"
local_dir = "D:\\ROMs\\saves"
remote    = "dropbox:/RetroSync/saves/retroarch"

[[sync.sources]]
name      = "DuckStation (PSX)"
local_dir = "C:\\Users\\TU_USUARIO\\Documents\\DuckStation\\memcards"
remote    = "dropbox:/RetroSync/saves/duckstation"
```

**Pasos:**
1. Pestaña **Sync** → verifica que aparecen las fuentes configuradas.
2. Pulsa **Sincronizar**.

**Resultado esperado:** el log muestra qué archivos se subieron/bajaron. Conflictos (mismo archivo modificado en ambos lados) quedan como `nombre_TIMESTAMP.ext`.

---

### 5.12 Cable Sync (USB directo, sin WiFi)

Requiere consola Android conectada por USB con depuración ADB activada.

**Pasos:**
1. Conecta la consola por USB.
2. En la consola: activa **Opciones de desarrollador** → **Depuración USB**.
3. Acepta el aviso "¿Permitir depuración USB?" en la consola.
4. Pestaña **Cable Sync** → selecciona modo (PC→Consola / Consola→PC / Más reciente gana) → **Sincronizar**.

**Verificar que ADB detecta el dispositivo:**

```bash
tools\adb.exe devices
```

Debe mostrar el número de serie de la consola, no "unauthorized".

**Resultado esperado:** el log muestra los archivos copiados. Solo se transfieren archivos con SHA1 distinto (deduplicación automática).

---

## 6. Verificación de base de datos

```bash
# Ver resumen desde CLI
python -m rom_manager status

# Inspeccionar SQLite directamente (opcional)
# Usa DB Browser for SQLite o cualquier cliente SQLite
# Archivo: .rommgr/library_pc.db
```

---

## 7. Tests automáticos

```bash
# Con entorno activado:
pytest tests/ -v

# Con el lanzador Windows:
scripts\rommgr.cmd pytest tests/ -v
```

**Resultado esperado:** todos los tests pasan. Si alguno falla, el mensaje de error indica el módulo afectado.

---

## 8. Problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| La web no carga | Puerto 7777 ocupado | Cambia `port` en `config.toml` o cierra el proceso que usa ese puerto |
| "chdman not found" | Ruta incorrecta | Verifica `tools.chdman` en `config.toml` y que el archivo existe |
| Matching da 0 resultados | Sin DATs descargados | Sección 5.3 — descarga catálogos primero |
| ADB dice "unauthorized" | No aceptaste el aviso en la consola | Desconecta y reconecta el USB; acepta el aviso en la pantalla de la consola |
| Scraper sin resultados | Credenciales vacías o erróneas | Revisa usuario/contraseña en ScreenScraper (cuenta gratuita necesaria) |
| Los cambios de config no aplican | El servidor estaba corriendo | Reinicia `rommgr serve` tras guardar `config.toml` |
| `.rommgr/` no existe | Primer arranque | Se crea automáticamente al ejecutar cualquier comando o al iniciar el servidor |

---

## 9. Estructura mínima para probar sin ROMs reales

Si no tienes ROMs a mano, puedes probar el flujo de escaneo e inbox con archivos vacíos:

```bash
# Crea archivos de prueba (PowerShell)
New-Item "D:\ROMs\psx\test_game.cue" -ItemType File
New-Item "D:\ROMs\inbox\test.zip" -ItemType File
```

El escaneo los registrará en la BD (sin hash válido). El matching no los identificará (SHA1 no coincide), pero puedes verificar que la UI, la BD y los logs funcionan correctamente.
