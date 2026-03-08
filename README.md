# ROM Manager Local

Base de la Fase 1 para escanear bibliotecas mixtas de ROMs, clasificar archivos y registrar el inventario en SQLite.

## Uso

```bat
.\scripts\rommgr.cmd status
.\scripts\rommgr.cmd scan <ruta>
```

## Entorno

Actualmente el proyecto no tiene dependencias externas de runtime; la instalación base se resuelve con el propio paquete.

`requirements.txt`:

```text
-e .
```

Si tienes Conda disponible, el entorno recomendado es:

```bash
conda env create -f environment.yml
conda activate rom_manager
```

En esta máquina ya quedó creado como:

```text
C:\Users\rammu\anaconda3\envs\rom_manager
```

Ejecución directa con ese entorno:

```bat
C:\Users\rammu\anaconda3\envs\rom_manager\python.exe -m rom_manager status
```

Si no tienes Conda en `PATH`, puedes seguir usando el lanzador:

```bat
.\scripts\rommgr.cmd status
```

Alternativa sin script:

```powershell
$env:PYTHONPATH = "src"
& "C:\Users\rammu\AppData\Local\Programs\Python\Python312\python.exe" -m rom_manager status
```

## Estado actual

La implementación actual hace esto:

- escaneo recursivo de una carpeta origen
- clasificación inicial en `rom`, `save`, `frontend_asset`, `system_support`, `unknown`
- exclusión lógica de carpetas típicas del dispositivo como `Android`, `BIOS` o `Movies`
- cálculo de `SHA1`, `MD5` y `CRC32` para archivos clasificados como ROM
- detección básica de plataforma por extensión
- persistencia en `.rommgr/library.sqlite`
- resumen de biblioteca con `status`

## Limitaciones actuales

- todavía no hay matching con catálogos No-Intro o Redump
- todavía no existe `plan` o `apply`
- PSX aún no se trata con lógica específica por set
- el comando `python` del sistema puede resolver al alias de Windows Store
- PowerShell puede bloquear scripts `.ps1` por política de ejecución
- por eso el proyecto incluye `scripts\rommgr.cmd`, que usa Python 3.12 directamente y funciona sin cambiar la configuración global
- `conda` no estaba en `PATH`, pero la instalación real de Anaconda está en `C:\Users\rammu\anaconda3`
