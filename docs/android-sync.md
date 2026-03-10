# Sincronización de saves en la Anbernic RG 556

Guía para sincronizar saves y save states entre el PC y la Anbernic RG 556 (Android nativo).

> **Cable Sync (transferencia directa por USB):** Si quieres copiar ROMs o saves por cable sin
> WiFi, usa la pestaña **Cable Sync** de la interfaz web (`rommgr serve`). Requiere que la Anbernic
> sea accesible como ruta del sistema de archivos (SD card en el PC, Termux SFTP, o WinFsp+SSHFS).
> El MTP estándar de Android **no** es compatible.
>
> Esta guía cubre el sync automático por WiFi vía rclone o FolderSync.

## Rutas de RetroArch en Android

| Tipo | Ruta |
|------|------|
| Saves de batería (`.sav`, `.srm`) | `/storage/emulated/0/RetroArch/saves/` |
| Save states (`.state`, `.state0`–`.state9`) | `/storage/emulated/0/RetroArch/states/` |
| Configuración | `/storage/emulated/0/RetroArch/retroarch.cfg` |

> **Nota:** Si usas un núcleo que guarda en subcarpetas por plataforma, las rutas serán
> `/storage/emulated/0/RetroArch/saves/<plataforma>/`.  Ajusta los pares de sync
> en FolderSync o en el script de rclone para cubrir todas las subcarpetas.

---

## Opción A — Termux + rclone (más control)

Requiere instalar Termux desde **F-Droid** (no la versión de Play Store, que está abandonada).

### 1. Instalar Termux

Descarga el APK desde <https://f-droid.org/packages/com.termux/> e instálalo.

### 2. Instalar rclone en Termux

```bash
pkg update && pkg install rclone
```

### 3. Configurar el mismo remote que el PC

```bash
rclone config
```

Crea un remote con el mismo nombre y tipo que el configurado en el PC
(por ejemplo `dropbox` apuntando a tu cuenta Dropbox).

Para Dropbox, rclone abrirá un enlace de autorización — ábrelo en el navegador
del móvil y autoriza el acceso.

### 4. Script de sync

Crea `~/sync-saves.sh`:

```bash
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REMOTE="dropbox:RetroArch"    # Ajusta al nombre de tu remote
LOCAL_SAVES="/storage/emulated/0/RetroArch/saves"
LOCAL_STATES="/storage/emulated/0/RetroArch/states"

echo "[$(date -u +%FT%TZ)] Iniciando sync de saves..."

# Política: el archivo con mtime más reciente gana (--update)
rclone sync "$LOCAL_SAVES"  "$REMOTE/saves"  --update --verbose
rclone sync "$LOCAL_STATES" "$REMOTE/states" --update --verbose

echo "[$(date -u +%FT%TZ)] Sync completado."
```

Dale permisos de ejecución:

```bash
chmod +x ~/sync-saves.sh
```

Ejecuta manualmente:

```bash
~/sync-saves.sh
```

### 5. Automatizar con Termux:Boot

1. Instala **Termux:Boot** desde F-Droid.
2. Crea el script de arranque:

```bash
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/sync-on-boot.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
# Espera a que la red esté disponible antes de sincronizar
sleep 30
~/sync-saves.sh >> ~/sync-saves.log 2>&1
EOF
chmod +x ~/.termux/boot/sync-on-boot.sh
```

> **Aviso:** No sincronices mientras RetroArch está abierto y usando el save.
> Los archivos podrían quedar en estado inconsistente.  Cierra RetroArch antes
> de ejecutar el sync manual.

---

## Opción B — FolderSync Pro (más fácil)

FolderSync es una app Android con interfaz gráfica.  La versión gratuita es
funcional; la Pro elimina los anuncios.

### 1. Instalar FolderSync

Busca **FolderSync** en Google Play Store o usa la APK desde su web oficial.

### 2. Configurar la cuenta Dropbox

Dentro de FolderSync → **Cuentas** → **+** → Dropbox → sigue el proceso de
autorización OAuth.

### 3. Crear pares de sincronización

Crea dos pares (uno para saves, otro para states):

| Campo | Saves | States |
|-------|-------|--------|
| Carpeta local | `/storage/emulated/0/RetroArch/saves` | `/storage/emulated/0/RetroArch/states` |
| Carpeta remota | `Dropbox:/RetroArch/saves` | `Dropbox:/RetroArch/states` |
| Tipo de sync | **Bidireccional** | **Bidireccional** |
| Política de conflicto | **Ganador: más reciente** | **Ganador: más reciente** |
| Sync solo por WiFi | ✅ Activado | ✅ Activado |
| Intervalo automático | Cada 15 minutos | Cada 15 minutos |

### 4. Activar sync automático

En la pestaña de **Pares de sincronización**, activa el interruptor de
programación para cada par.  FolderSync sincronizará en segundo plano cuando
haya WiFi disponible.

---

## Política de conflictos

Tanto en el PC (rclone) como en la Anbernic (Termux o FolderSync) se usa la
misma regla: **el archivo con fecha de modificación más reciente gana**.

Si se detecta un conflicto real (ambos lados modificados desde el último sync),
el PC guardará ambas versiones con sufijo de timestamp y notificará al usuario.
En FolderSync esto equivale a la opción "Conservar ambos".

---

## Sincronización solo desde el PC (fallback)

Si no quieres instalar nada en la Anbernic, puedes sincronizar cuando la
consola está conectada por USB en modo MTP o ADB:

```bash
# Con adb (requiere activar Depuración USB en la Anbernic)
adb pull /storage/emulated/0/RetroArch/saves/ C:/Users/rammu/saves/anbernic/
adb push C:/Users/rammu/saves/pc/ /storage/emulated/0/RetroArch/saves/
```

Esta opción es más manual pero no requiere WiFi ni instalaciones en la consola.
