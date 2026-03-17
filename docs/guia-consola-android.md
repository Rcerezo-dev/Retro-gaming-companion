# Guía: sync de saves en la consola Android

*Retro Vault — guía para configurar la consola Android con sync automático de saves.*

Esta guía cubre todo lo que hay que hacer en la consola para que los saves se sincronicen solos con el PC vía Dropbox (u otro cloud).

---

## Requisitos previos

- Consola Android con RetroArch instalado
- Cuenta en Dropbox (o el proveedor configurado en el PC)
- Wi-Fi activo durante la configuración inicial
- Retro Vault ya configurado y funcionando en el PC

---

## Opción A — Termux + rclone (recomendado, gratis)

La opción más sólida: instalar Termux, rclone, y un script que se ejecuta en bucle cada hora. La consola sincroniza sola en background.

### Paso 1 — Instalar Termux

> ⚠️ **NO instales Termux desde Google Play.** La versión de Play Store está desactualizada. Usa F-Droid.

1. Abre el navegador en la consola → ve a **f-droid.org**
2. Descarga e instala F-Droid (permitir "orígenes desconocidos" en Ajustes → Seguridad)
3. Dentro de F-Droid, busca **Termux** e instálalo
4. Instala también **Termux:Boot** (en F-Droid, misma búsqueda) — hace que el script arranque al encender la consola

### Paso 2 — Dar permisos a Termux

- **Ajustes → Aplicaciones → Termux → Permisos** → activa **Almacenamiento**
- **Ajustes → Aplicaciones → Termux:Boot → Batería** → selecciona "Sin restricciones"

### Paso 3 — Instalar rclone dentro de Termux

Abre Termux y ejecuta:

```bash
pkg update && pkg upgrade -y
pkg install -y curl wget
curl https://rclone.org/install.sh | bash
```

Verifica:
```bash
rclone version
```

### Paso 4 — Dar acceso al almacenamiento

```bash
termux-setup-storage
```

Android mostrará un diálogo pidiendo acceso a archivos. Acepta.

Comprueba acceso:
```bash
ls ~/storage/shared/
```

Deberías ver las carpetas `psx/`, `gba/`, `snes/`, etc. (o las que tengas).

### Paso 5 — Configurar rclone con Dropbox

**Opción recomendada: copiar la config del PC.**

En el PC:
```bash
rclone config file   # muestra la ruta del archivo de config
```

Copia el contenido de ese archivo (habitualmente `C:\Users\<usuario>\AppData\Roaming\rclone\rclone.conf`).

En Termux:
```bash
mkdir -p ~/.config/rclone
nano ~/.config/rclone/rclone.conf
# pega el contenido, guarda con Ctrl+O, sal con Ctrl+X
```

Verifica:
```bash
rclone lsd dropbox:
# debe mostrar las carpetas de tu Dropbox
```

**Si no puedes copiar la config, configura desde cero:**
```bash
rclone config
# Sigue el asistente: nueva config, tipo Dropbox, nombre debe ser idéntico al del PC
# En el paso de autenticación: NO uses el navegador de la consola — elige "No" y abre la URL en el PC
```

### Paso 6 — Crear el script de sync

```bash
cat > ~/sync_saves.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash

# Rutas de RetroArch en Android (ajusta si usas rutas diferentes)
ANDROID_SAVES="/storage/emulated/0/RetroArch/saves"
ANDROID_STATES="/storage/emulated/0/RetroArch/states"

# Remote: debe coincidir con la config del PC en config.toml [sync]
REMOTE="dropbox:/RetroSync/saves"

LOG="$HOME/sync_log.txt"
echo "[$(date)] Iniciando sync..." >> "$LOG"

rclone sync "$ANDROID_SAVES"  "$REMOTE/saves"  --update --log-file="$LOG" --log-level INFO
rclone sync "$ANDROID_STATES" "$REMOTE/states" --update --log-file="$LOG" --log-level INFO

echo "[$(date)] Sync completado." >> "$LOG"
EOF
chmod +x ~/sync_saves.sh
```

Prueba manual:
```bash
~/sync_saves.sh && cat ~/sync_log.txt
```

### Paso 7 — Script de arranque automático (Termux:Boot)

```bash
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/start_sync.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash

# Esperar a que el sistema arranque
sleep 30

# Sync inmediato al arrancar
~/sync_saves.sh

# Bucle: sync cada hora
while true; do
  sleep 3600
  ~/sync_saves.sh
done
EOF
chmod +x ~/.termux/boot/start_sync.sh
```

A partir de ahora, cada vez que enciendas la consola el sync arrancará automáticamente.

### Paso 8 — Verificar

Reinicia la consola. Tras ~1 minuto, ejecuta en Termux:
```bash
cat ~/sync_log.txt
```
Si ves líneas con "Sync completado", funciona.

---

## Opción B — FolderSync (más fácil, sin terminal)

FolderSync es una app Android con interfaz gráfica. La versión gratuita es funcional.

1. Instala **FolderSync** desde Google Play
2. **Cuentas → + → Dropbox** → autoriza con OAuth
3. Crea dos pares de sincronización:

| Campo | Saves | States |
|-------|-------|--------|
| Carpeta local | `/storage/emulated/0/RetroArch/saves` | `/storage/emulated/0/RetroArch/states` |
| Carpeta remota | `Dropbox:/RetroSync/saves/saves` | `Dropbox:/RetroSync/saves/states` |
| Tipo de sync | **Bidireccional** | **Bidireccional** |
| Política de conflicto | **Ganador: más reciente** | **Ganador: más reciente** |
| Solo por WiFi | ✅ | ✅ |
| Intervalo | Cada 15-60 min | Cada 15-60 min |

4. Activa el interruptor de programación para cada par.

---

## Rutas importantes de referencia

| Ubicación | Ruta en Android |
|-----------|----------------|
| Saves de RetroArch | `/storage/emulated/0/RetroArch/saves/` |
| States de RetroArch | `/storage/emulated/0/RetroArch/states/` |
| Config de rclone (Termux) | `~/.config/rclone/rclone.conf` |
| Log de sync | `~/sync_log.txt` |
| Script de boot | `~/.termux/boot/start_sync.sh` |

---

## Checklist final

- [ ] Termux instalado desde F-Droid (NO Play Store)
- [ ] Termux:Boot instalado desde F-Droid
- [ ] Permisos de almacenamiento dados a Termux
- [ ] `termux-setup-storage` ejecutado
- [ ] rclone instalado (`rclone version` funciona)
- [ ] rclone configurado con las mismas credenciales que el PC
- [ ] `rclone lsd dropbox:` muestra los archivos correctamente
- [ ] `~/sync_saves.sh` ejecutado manualmente sin errores
- [ ] `~/.termux/boot/start_sync.sh` creado con permisos +x
- [ ] Consola reiniciada y log muestra "Sync completado"
- [ ] En Retro Vault PC: Overview muestra los saves actualizados

---

## Solución de problemas

| Problema | Causa | Solución |
|----------|-------|----------|
| `rclone: command not found` | rclone no instalado | `pkg install rclone -y` |
| `permission denied` en `/sdcard/` | Falta permiso | Ejecutar `termux-setup-storage` de nuevo |
| `OAuth token expired` | Token caducado | `rclone config reconnect dropbox:` |
| bisync falla la primera vez | Falta inicialización | Añadir `--resync` al primer comando |
| Script no arranca al encender | Termux:Boot sin permisos | Ajustes → Apps → Termux:Boot → Permisos → Inicio automático |
| Saves del PC no llegan a la consola | Sync unidireccional | Usar `rclone bisync` en lugar de `rclone sync` |
