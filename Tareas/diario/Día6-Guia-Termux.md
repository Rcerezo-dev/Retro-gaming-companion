# Guía: Sync de saves con Termux + rclone en la Anbernic RG 556

Esta guía configura la Anbernic para que sincronice automáticamente los saves con Dropbox
usando Termux y rclone — el mismo binario que usa la herramienta en el PC.

---

## Requisitos previos

- Anbernic RG 556 con Android
- Cuenta en Dropbox (o el proveedor que hayas configurado en el PC)
- Wi-Fi activo durante la configuración inicial
- La herramienta ya configurada y funcionando en el PC (`rommgr sync-saves`)

---

## Paso 1: Instalar Termux

1. Abre el navegador en la Anbernic y descarga **Termux** desde F-Droid:
   - URL: `https://f-droid.org/packages/com.termux/`
   - **No uses la versión de Google Play** — está desactualizada y tiene restricciones de almacenamiento.

2. Instala el APK descargado. Si Android pide permiso para instalar apps de fuentes desconocidas, acéptalo.

3. Abre Termux. Verás una terminal de texto.

---

## Paso 2: Actualizar paquetes e instalar rclone

En la terminal de Termux:

```bash
# Actualizar repositorios (puede tardar unos minutos)
pkg update && pkg upgrade -y

# Instalar rclone
pkg install rclone -y
```

Verifica que funciona:

```bash
rclone version
```

---

## Paso 3: Dar acceso al almacenamiento

Termux necesita permiso para leer y escribir en la tarjeta SD:

```bash
termux-setup-storage
```

Android mostrará un diálogo pidiendo permiso de acceso a archivos. Acepta.

Tras aceptar, tendrás acceso a:
- Almacenamiento interno: `~/storage/shared/` → equivale a `/sdcard/`
- Tarjeta SD externa (si existe): `~/storage/external-1/`

Comprueba que puedes ver tus ROMs:

```bash
ls ~/storage/shared/
```

Deberías ver las carpetas `psx/`, `gba/`, `snes/`, etc.

---

## Paso 4: Configurar rclone con Dropbox

Necesitas copiar la configuración de rclone desde el PC a la Anbernic. Es más fácil que
hacerlo desde cero en la consola.

### Opción A: Copiar el archivo de config desde el PC (recomendado)

En el PC, abre un terminal y ejecuta:

```bash
# Windows — muestra la ruta del config de rclone
rclone config file
```

Copia el contenido de ese archivo (suele estar en `C:\Users\<usuario>\AppData\Roaming\rclone\rclone.conf`).

Luego en Termux:

```bash
mkdir -p ~/.config/rclone
# Pega el contenido del archivo de config
nano ~/.config/rclone/rclone.conf
```

Pega el contenido (en Termux, mantén pulsado para pegar), guarda con `Ctrl+O`, sale con `Ctrl+X`.

Verifica que funciona:

```bash
rclone lsd dropbox:
```

Deberías ver las carpetas de tu Dropbox.

### Opción B: Configurar desde cero en la Anbernic

Si no puedes copiar el archivo, ejecuta el asistente interactivo:

```bash
rclone config
```

Sigue los pasos para añadir un nuevo remote `dropbox`. En algún punto pedirá abrir un
navegador para autenticar — desde la Anbernic puedes usar el navegador integrado de Android.

---

## Paso 5: Hacer el primer sync manual

Con rclone configurado, prueba el sync:

```bash
# Dry run: muestra qué haría sin transferir nada
rclone sync ~/storage/shared/ dropbox:/RetroSync/saves/ \
  --include "*.sav" \
  --include "*.srm" \
  --include "*.state" \
  --include "*.state1" \
  --include "*.state2" \
  --include "*.sgm" \
  --include "*.brm" \
  --include "*.brmc" \
  --include "*.nv" \
  --include "*.hi" \
  --include "*.fs" \
  --include "*.ml1" \
  --dry-run \
  --progress
```

Si el resultado tiene sentido, quita `--dry-run` para ejecutarlo de verdad:

```bash
rclone sync ~/storage/shared/ dropbox:/RetroSync/saves/ \
  --include "*.sav" \
  --include "*.srm" \
  --include "*.state" \
  --include "*.state1" \
  --include "*.state2" \
  --include "*.sgm" \
  --include "*.brm" \
  --include "*.brmc" \
  --include "*.nv" \
  --include "*.hi" \
  --include "*.fs" \
  --include "*.ml1" \
  --progress
```

---

## Paso 6: Crear un script de sync

Para no escribir el comando completo cada vez, crea un script:

```bash
nano ~/sync-saves.sh
```

Contenido del script:

```bash
#!/data/data/com.termux/files/usr/bin/bash

LIBRARY="$HOME/storage/shared"
REMOTE="dropbox:/RetroSync/saves"
FILTERS=(
  --include "*.sav"
  --include "*.srm"
  --include "*.state"
  --include "*.state1"
  --include "*.state2"
  --include "*.sgm"
  --include "*.brm"
  --include "*.brmc"
  --include "*.nv"
  --include "*.hi"
  --include "*.fs"
  --include "*.ml1"
  --exclude "*"
)

echo "=== Sync saves: Anbernic → Dropbox ==="
rclone bisync "$LIBRARY" "$REMOTE" "${FILTERS[@]}" --progress --log-level INFO

echo "=== Hecho ==="
```

Guarda y dale permisos de ejecución:

```bash
chmod +x ~/sync-saves.sh
```

Ejecútalo cuando quieras sincronizar:

```bash
~/sync-saves.sh
```

> **Nota sobre `bisync`**: a diferencia de `sync` (que solo va en una dirección),
> `bisync` sincroniza en ambas direcciones: sube lo nuevo de la Anbernic y descarga
> lo nuevo del cloud. Perfecto para alternar entre PC y Anbernic.
> La primera vez hay que inicializarlo con `--resync`:
> `rclone bisync ... --resync`

---

## Paso 7: Automatizar con Termux:Boot (opcional)

Si quieres que el sync ocurra automáticamente al arrancar la Anbernic:

1. Instala **Termux:Boot** desde F-Droid.
2. Crea el script de arranque:

```bash
mkdir -p ~/.termux/boot
nano ~/.termux/boot/sync-on-boot.sh
```

Contenido:

```bash
#!/data/data/com.termux/files/usr/bin/bash
# Espera a que haya Wi-Fi (máximo 60 segundos)
for i in $(seq 1 12); do
  ping -c1 -W2 1.1.1.1 &>/dev/null && break
  sleep 5
done

# Sync
~/sync-saves.sh >> ~/sync.log 2>&1
```

```bash
chmod +x ~/.termux/boot/sync-on-boot.sh
```

---

## Workflow completo

```
[Anbernic] Juega → save se crea/modifica en /sdcard/gba/Game.sav
     ↓
[Anbernic] Abre Termux → ejecuta ~/sync-saves.sh
     ↓
[Dropbox]  dropbox:/RetroSync/saves/gba/Game.sav actualizado
     ↓
[PC]       rommgr sync-saves --apply → descarga Game.sav a C:\ROMs\gba\Game.sav
```

Y al revés cuando juegas en el PC.

---

## Solución de problemas

| Problema | Causa probable | Solución |
|----------|---------------|----------|
| `rclone: command not found` | pkg no instaló rclone | `pkg install rclone -y` |
| `permission denied` en `/sdcard/` | No se ejecutó `termux-setup-storage` | Ejecutarlo de nuevo |
| `Failed to sync: ...token expired` | Token de Dropbox expirado | `rclone config reconnect dropbox:` |
| bisync falla la primera vez | Falta `--resync` inicial | Añadir `--resync` al primer comando |
| No detecta Wi-Fi en el boot script | El servicio de red tarda en arrancar | Aumentar los intentos de ping en el loop |
