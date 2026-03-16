# Cable Sync — Transferencia directa por USB

El Cable Sync copia ROMs y saves entre el PC y la consola Android **sin necesidad de WiFi ni de la nube**. Ideal para transferir una tanda grande de ROMs nuevos o para hacer una copia de seguridad completa de los saves.

---

## Requisitos

- La consola Android conectada al PC por USB
- El almacenamiento de la consola accesible como **letra de unidad** en Windows

> El modo **MTP estándar** ("Transferencia de archivos") *no* expone una letra de unidad y *no* es compatible con Retro Vault. Usa una de las opciones siguientes.

---

## Opción 1: Tarjeta SD en lector (recomendada)

La opción más rápida y sin configuración:

1. Apaga la consola
2. Saca la tarjeta microSD
3. Conéctala al PC con un lector de tarjetas
4. Windows la asigna como unidad (ej. `H:\`)
5. Configura esa letra en **Ajustes → Ruta consola Android**
6. Vuelve a insertar la SD cuando termines

**Velocidades típicas**: 20-40 MB/s con una tarjeta UHS-I.

---

## Opción 2: Termux + SFTP (WiFi o USB tethering)

Monta el almacenamiento de la consola como unidad de red en Windows.

### En la consola (Termux)

```bash
pkg update && pkg install openssh

# Generar clave SSH
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""

# Añadir la clave pública del PC a authorized_keys
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Arrancar SFTP server en puerto 8022
sshd
```

### En el PC (Windows)

**Opción A — WinFsp + SSHFS-Win** (montar como unidad):

1. Instala [WinFsp](https://winfsp.dev/rel/) y [SSHFS-Win](https://github.com/winfsp/sshfs-win/releases)
2. En el Explorador de Windows → Conectar unidad de red:
   ```
   \\sshfs\user@192.168.1.X!8022\storage\emulated\0
   ```
3. Asigna una letra de unidad (ej. `Z:`)

**Opción B — rclone mount** (alternativa):

```powershell
rclone mount sftp:/ Z: --sftp-host 192.168.1.X --sftp-port 8022 --sftp-user u0_a123 --vfs-cache-mode full
```

Para conocer tu usuario en Termux: `whoami`

---

## Opción 3: ADB directo

Retro Vault incluye soporte experimental para transferencias vía `adb` sin montar unidad. Requiere el binario `adb.exe` en `tools/` o en el PATH.

```toml
[tools]
adb = "tools\\adb.exe"
```

Activa **Depuración USB** en la consola (Ajustes → Opciones de desarrollador) y conecta el cable. El Cable Sync detectará la consola automáticamente.

> Esta opción es más lenta que las anteriores (~5-8 MB/s) pero no requiere instalar nada extra en la consola.

---

## Cómo usar Cable Sync en Retro Vault

1. Abre la interfaz web: `http://127.0.0.1:7777`
2. Ve a la pestaña **Cable Sync**
3. Configura:
   - **Ruta PC**: carpeta raíz de la biblioteca en el PC
   - **Ruta consola**: letra de unidad de la SD o punto de montaje SFTP
   - **Dirección**: PC→Consola, Consola→PC, o el más reciente gana
   - **Qué sincronizar**: solo saves, solo ROMs, o ambos
4. Pulsa **Solo previsualizar** para ver qué se copiaría
5. Pulsa **Sincronizar** para ejecutar

---

## Estructura esperada en la consola Android

Retro Vault espera la misma estructura de carpetas que en el PC:

```
/storage/emulated/0/       ← o el root de la SD
  ROMs/
    psx/
    gba/
    snes/
    ...
  RetroArch/
    saves/       ← saves de RetroArch (flat)
    states/
  BIOS/
```

Si usas EmulationStation / Pegasus en la consola, configura las rutas de ROMs apuntando a `/storage/emulated/0/ROMs/<plataforma>/`.

---

## Notas

- **Deduplicación**: si un ROM ya existe en el destino con el mismo SHA1, no se copia de nuevo aunque el nombre sea diferente.
- **Conflictos de saves**: en modo "el más reciente gana", el archivo con `mtime` más reciente sobreescribe al otro. En caso de empate, se conserva el del PC.
- **ROMs grandes**: los ISOs y CHDs pueden ocupar varios GB. Para transferencias de ROM masivas, la opción de tarjeta SD es muy superior en velocidad.
