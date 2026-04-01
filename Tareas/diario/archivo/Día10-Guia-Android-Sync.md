# Guía completa: sync automático en la consola Android

*Fecha: 2026-03-16 — Retro Vault / Retro Companion*

Esta guía cubre todo lo que tienes que hacer físicamente en la consola para que el sync de saves funcione de forma autónoma. Hay dos enfoques según lo que quieras instalar.

---

## Opción A — Termux + script de bucle (recomendado, gratis, sin programar)

Es la opción más sencilla. Instalar Termux, rclone y un script que se ejecuta en bucle cada hora. La consola sincroniza sola aunque no abras ninguna app.

### Paso 1 — Instalar Termux

> ⚠️ **IMPORTANTE:** NO instales Termux desde Google Play. La versión de Play Store está desactualizada y rota. Usa F-Droid.

1. Abre el navegador en la consola y ve a **f-droid.org**
2. Descarga e instala F-Droid (tendrás que permitir "orígenes desconocidos" en Ajustes → Seguridad)
3. Dentro de F-Droid, busca **Termux** e instálalo
4. Instala también **Termux:Boot** (en F-Droid, misma búsqueda) — esto hace que el script arranque al encender la consola

### Paso 2 — Dar permisos a Termux

En la consola: **Ajustes → Aplicaciones → Termux → Permisos** → activa **Almacenamiento**.

También, para que Termux:Boot funcione: **Ajustes → Aplicaciones → Termux:Boot → Batería** → selecciona "Sin restricciones" o "Optimización desactivada".

### Paso 3 — Instalar rclone dentro de Termux

Abre Termux y ejecuta estos comandos uno a uno:

```bash
pkg update && pkg upgrade -y
pkg install -y curl wget
curl https://rclone.org/install.sh | bash
```

Verifica que funciona:
```bash
rclone version
```

### Paso 4 — Configurar rclone con Dropbox (o el cloud que uses)

```bash
rclone config
```

Sigue el asistente:
- Elige `n` (nueva config)
- Nombre: `dropbox` (o el que usas en el PC — debe ser EXACTAMENTE el mismo nombre)
- Tipo: elige Dropbox (número correspondiente)
- Acepta todos los defaults hasta que te pida autenticación
- En el paso de autenticación **NO uses el navegador de la consola** — elige "No" al auto-open y copia la URL en tu PC para autenticarte allí
- Copia el token de vuelta en la consola

Verifica que funciona:
```bash
rclone ls dropbox:/RetroSync/saves
```

Si ves la lista de saves, está configurado correctamente.

### Paso 5 — Crear el script de sync

```bash
mkdir -p ~/.termux/boot
```

Crea el script de sincronización:
```bash
cat > ~/sync_saves.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash

# Ruta donde RetroArch guarda los saves en Android
ANDROID_SAVES="/storage/emulated/0/RetroArch/saves"
ANDROID_STATES="/storage/emulated/0/RetroArch/states"

# Ruta en el cloud (debe coincidir con la config del PC)
REMOTE="dropbox:/RetroSync/saves"

LOG="$HOME/sync_log.txt"
echo "[$(date)] Iniciando sync..." >> "$LOG"

# Sync saves
rclone sync "$ANDROID_SAVES" "$REMOTE/saves" \
  --update \
  --log-file="$LOG" \
  --log-level INFO 2>&1

# Sync states
rclone sync "$ANDROID_STATES" "$REMOTE/states" \
  --update \
  --log-file="$LOG" \
  --log-level INFO 2>&1

echo "[$(date)] Sync completado." >> "$LOG"
EOF
chmod +x ~/sync_saves.sh
```

Prueba que funciona:
```bash
~/sync_saves.sh
```

### Paso 6 — Script de arranque automático (Termux:Boot)

```bash
cat > ~/.termux/boot/start_sync.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash

# Esperar a que el sistema arranque completamente
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

A partir de ahora, cada vez que enciendas la consola, el sync arrancará automáticamente en background.

### Paso 7 — Probar el arranque automático

Reinicia la consola. Después de ~1 minuto, ejecuta en Termux:
```bash
cat ~/sync_log.txt
```
Si ves líneas con "Sync completado", funciona.

---

## Opción B — App Android simple (sin Termux, sin programación)

Si prefieres una app con icono en el lanzador en lugar de Termux, hay dos opciones sin programar:

### Opción B1 — MacroDroid (recomendada, gratis)

1. Instala **MacroDroid** desde la Play Store (gratuita para funciones básicas)
2. Crea una nueva macro:
   - **Trigger (Disparador):** "Temporizador periódico" → cada 60 minutos
   - **Action (Acción):** "Shell Script" → introduce el comando rclone del Paso 5
3. Activa la macro
4. En ajustes de MacroDroid: activa "Arrancar al inicio del sistema"

### Opción B2 — Tasker (de pago, ~3€)

Similar a MacroDroid pero más potente. Si ya lo tienes:
- Tarea nueva → "Código Shell" → comando rclone
- Perfil → Tiempo → cada hora → ejecutar tarea
- Activar "Arrancar con dispositivo"

---

## Opción C — App Android nativa (sin saber Java/Kotlin)

> Esto es para el futuro — mencionado porque el usuario preguntó.

Se puede crear una APK sencilla usando **Python + BeeWare (Briefcase)**. La app tendría una sola pantalla con un botón "Sincronizar ahora" y un texto con el estado del último sync. En background usaría `WorkManager` de Android (o simplemente un `Service`).

**¿Cuánto cuesta aprenderlo?** Con Python ya conocido, BeeWare/Briefcase se aprende en 1-2 días. El resultado es una APK real que funciona como cualquier app Android.

**Recursos:**
- briefcase.readthedocs.io — tutorial oficial en Python
- La lógica de sync ya está escrita en `src/rom_manager/sync/` — solo habría que llamarla

Por ahora, **la Opción A (Termux) es suficiente** y más fiable. La app nativa quedaría para cuando se quiera distribuir la herramienta a otros usuarios.

---

## Resumen de rutas importantes

| Ubicación | Ruta en Android |
|-----------|----------------|
| Saves de RetroArch | `/storage/emulated/0/RetroArch/saves/` |
| States de RetroArch | `/storage/emulated/0/RetroArch/states/` |
| Config de rclone | `~/.config/rclone/rclone.conf` (en Termux) |
| Log de sync | `~/sync_log.txt` (en Termux home) |
| Script de boot | `~/.termux/boot/start_sync.sh` |

---

## Checklist final

- [ ] Termux instalado desde F-Droid (NO Play Store)
- [ ] Termux:Boot instalado desde F-Droid
- [ ] Permisos de almacenamiento dados a Termux
- [ ] rclone instalado y probado (`rclone version`)
- [ ] rclone configurado con las mismas credenciales que el PC
- [ ] `rclone ls dropbox:/RetroSync/saves` muestra archivos correctamente
- [ ] `~/sync_saves.sh` ejecutado manualmente y sin errores
- [ ] `~/.termux/boot/start_sync.sh` creado y con permisos +x
- [ ] Consola reiniciada y log muestra "Sync completado"
- [ ] En la app del PC: verificar que los saves aparecen en Overview tras el sync

---

## Solución de problemas frecuentes

**"rclone: command not found"**
→ El PATH de Termux:Boot es distinto al de Termux interactivo. Cambia `rclone` por la ruta completa: `/data/data/com.termux/files/usr/bin/rclone`

**"Error: directory not found: /storage/emulated/0/RetroArch/saves"**
→ RetroArch no ha generado esa carpeta todavía. Lanza RetroArch una vez y crea un save state de cualquier juego. La carpeta se creará automáticamente.

**"OAuth token expired"**
→ Hay que reautenticar rclone. Ejecuta `rclone config reconnect dropbox:` en Termux.

**El script no arranca al encender la consola**
→ Verifica que Termux:Boot tiene permisos de "inicio automático" (en Ajustes → Aplicaciones → Termux:Boot → Permisos especiales → Inicio automático).

**El sync funciona pero los saves del PC no llegan a la consola**
→ Revisa la dirección del sync. `rclone sync A B` copia A→B. Para sync bidireccional usa `rclone bisync A B --resync` (primera vez con `--resync`, después sin él).
