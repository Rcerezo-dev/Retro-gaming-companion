# Sincronización en la nube — Guía completa

Retro Vault sincroniza los saves de cada emulador con la nube (Dropbox, OneDrive, Google Drive…) vía **rclone**. Cada emulador tiene su propia carpeta local y su propio path remoto — así los saves de PSX no se mezclan con los de GBA y el sync de una consola no interfiere con el de otra.

---

## 1. Instalar y configurar rclone

### Instalación

- **Windows**: descarga el `.exe` de [rclone.org/downloads](https://rclone.org/downloads/) y añádelo al PATH, o indica la ruta en `config.toml` → `sync.rclone`.
- **Android (Termux)**: `pkg install rclone`

### Configurar Dropbox (ejemplo)

```bash
rclone config
# → n (nueva configuración)
# → nombre: dropbox
# → tipo: dropbox
# → sigue las instrucciones del navegador para autorizarlo
```

Repite en **la Anbernic** (Termux) con las mismas credenciales o genera un token de acceso compartido.

---

## 2. Estructura remota recomendada

```
dropbox:/RetroSync/
  saves/
    retroarch/     ← saves de RetroArch (PC + Android)
    duckstation/   ← memory cards de DuckStation (PSX)
    pcsx2/         ← memory cards de PCSX2 (PS2)
    ppsspp/        ← SAVEDATA/ de PPSSPP (PSP)
    melon/         ← saves de MelonDS (NDS)
    dolphin/       ← saves de Dolphin (GC/Wii)
```

Cada carpeta es independiente: puedes añadir o quitar emuladores sin afectar a los demás.

---

## 3. Configuración en `config.toml`

```toml
[sync]
rclone = "rclone"   # o "C:\\rclone\\rclone.exe" si no está en PATH

[[sync.sources]]
name      = "RetroArch"
local_dir = "E:\\ROMs\\saves"   # carpeta centralizada de saves de RetroArch
remote    = "dropbox:/RetroSync/saves/retroarch"

[[sync.sources]]
name      = "DuckStation (PSX)"
local_dir = "C:\\Users\\TU_USUARIO\\Documents\\DuckStation\\memcards"
remote    = "dropbox:/RetroSync/saves/duckstation"

[[sync.sources]]
name      = "PCSX2 (PS2)"
local_dir = "C:\\Users\\TU_USUARIO\\Documents\\PCSX2\\memcards"
remote    = "dropbox:/RetroSync/saves/pcsx2"

[[sync.sources]]
name      = "PPSSPP (PSP)"
local_dir = "C:\\Users\\TU_USUARIO\\Documents\\PPSSPP\\PSP\\SAVEDATA"
remote    = "dropbox:/RetroSync/saves/ppsspp"
sync_all  = true   # PPSSPP usa subcarpetas por juego sin extensión estándar

[[sync.sources]]
name      = "MelonDS (NDS)"
local_dir = "C:\\Users\\TU_USUARIO\\Documents\\melonDS"
remote    = "dropbox:/RetroSync/saves/melon"

[[sync.sources]]
name      = "Dolphin (GC/Wii)"
local_dir = "C:\\Users\\TU_USUARIO\\Documents\\Dolphin Emulator"
remote    = "dropbox:/RetroSync/saves/dolphin"
sync_all  = true
```

> **`sync_all = true`**: sincroniza todos los archivos de la carpeta sin filtrar por extensión. Necesario para PPSSPP (estructura compleja de subcarpetas) y Dolphin (NAND + `.gci`).

---

## 4. Centralizar los saves de RetroArch (paso único)

RetroArch puede guardar saves junto a los ROMs o en una carpeta única. Para que el sync funcione limpiamente, usa una **carpeta centralizada**:

1. En RetroArch PC: **Settings → Saving → Savefile Directory** → pon `E:\ROMs\saves\`
2. Mueve los saves existentes (dispersos junto a los ROMs) a esa nueva carpeta. Puedes hacerlo manualmente o con el botón **Organizar biblioteca** en Herramientas (mueve ROMs pero no saves — los saves muévelos manualmente la primera vez).
3. Actualiza `config.toml`: cambia `local_dir` de la fuente RetroArch a la nueva carpeta.

En la Anbernic, RetroArch ya guarda los saves en `/storage/emulated/0/RetroArch/saves/` (plano). No hay que cambiar nada.

---

## 5. Configurar rclone en la Anbernic (Termux)

```bash
# Instalar Termux desde F-Droid (no desde Play Store)
pkg update && pkg install rclone

# Copiar la config de rclone desde el PC (o volver a hacer rclone config)
# Opción 1: copiar el archivo de config directamente
scp ~/.config/rclone/rclone.conf usuario@anbernic:/data/data/com.termux/files/home/.config/rclone/

# Opción 2: configurar desde cero en Termux
rclone config
```

**Script de sync en Termux** (`~/sync-saves.sh`):

```bash
#!/data/data/com.termux/files/usr/bin/bash
set -e

# RetroArch
rclone sync /storage/emulated/0/RetroArch/saves/ dropbox:/RetroSync/saves/retroarch/ \
  --update --use-mtime

# PPSSPP
rclone sync /storage/emulated/0/PSP/SAVEDATA/ dropbox:/RetroSync/saves/ppsspp/ \
  --update --use-mtime

echo "Sync completado: $(date)"
```

```bash
chmod +x ~/sync-saves.sh
~/sync-saves.sh
```

---

## 6. Política de conflictos

Cuando el mismo archivo fue modificado en PC y en la consola desde el último sync:

- **El más reciente gana** (comparación por `mtime`)
- La versión perdedora se guarda con sufijo `.conflict-YYYYMMDDTHHMMSS` junto al archivo — nunca se pierde nada
- El log de operaciones queda en la pestaña **Sync** de la interfaz web

---

## 7. Extensiones de save sincronizadas

Por defecto Retro Vault sincroniza estas extensiones (fuentes con `sync_all = false`):

| Extensión | Emulador / Sistema |
|---|---|
| `.sav` `.srm` | RetroArch (saves) |
| `.state` `.st0`…`.st5` `.state1` `.state2` | RetroArch (save states) |
| `.mcd` | DuckStation (PSX memory card) |
| `.ps2` | PCSX2 (PS2 memory card) |
| `.gci` | Dolphin (GameCube memory card slot) |
| `.ppst` | PPSSPP (save states) |
| `.dsv` `.nv` `.fcs` | Varios emuladores de NDS, N64 |
| `.eep` `.fla` `.sra` | N64 (EEPROM, Flash, SRAM) |

Las fuentes con `sync_all = true` sincronizan todos los archivos de la carpeta sin filtrar.
