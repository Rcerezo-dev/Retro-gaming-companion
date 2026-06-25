# Sync de saves por WiFi directo (SFTP) — PC ↔ Anbernic

Alternativa a `Guia-Termux-Anbernic.md` (que sincroniza vía Dropbox/cloud): esta guía
conecta el PC directamente con la Anbernic **por la red local**, sin pasar por ningún
proveedor de la nube. Usa un servidor SSH en Termux + un remote `sftp` de rclone — el
mismo `rclone` que ya usa la herramienta, así que **no hace falta código nuevo**: una vez
configurado el remote, el sync normal de la app (`Sync ahora` / `POST /api/sync`) lo usa
sin cambios.

---

## ¿WiFi/SFTP o Cloud?

| | WiFi/SFTP (esta guía) | Cloud — `Guia-Termux-Anbernic.md` |
|---|---|---|
| Requiere internet | ❌ No (solo LAN) | ✅ Sí |
| Velocidad | Más rápido (red local) | Limitado por la subida/bajada a internet |
| Disponible fuera de casa | ❌ No | ✅ Sí |
| Cuenta en proveedor externo | ❌ No | ✅ Sí (Dropbox, etc.) |
| Configuración | IP fija/reservada recomendada | Funciona con cualquier IP |

Usa WiFi/SFTP si el PC y la Anbernic están casi siempre en la misma red doméstica. Si
sincronizas también fuera de casa, mantén el remote cloud y usa este como complemento.

---

## Investigación — servidor SSH en Termux: `openssh` vs `dropbear`

**Recomendado: `openssh`.**

- Termux empaqueta `openssh` como la opción estándar y mejor documentada; trae el
  subsistema `sftp-server` necesario para que `rclone` (backend `sftp`) funcione sin pasos
  extra.
- Soporta autenticación por contraseña y por clave pública sin configuración adicional.
- `sshd` de Termux escucha por defecto en el **puerto 8022** (no en el 22 — Termux corre
  sin root y no puede usar puertos privilegiados).

`dropbear` es más ligero en memoria, pero en Termux no trae el `sftp-server` integrado de
forma tan directa y hay menos guías/soporte de la comunidad para este caso de uso. Queda
documentado como alternativa avanzada, no como ruta recomendada.

---

## Paso 1 — Servidor SSH en la Anbernic (Termux)

Si ya tienes Termux instalado siguiendo `Guia-Termux-Anbernic.md`, parte del Paso 1 de esa
guía. Si no, instala Termux desde F-Droid primero (no la versión de Google Play).

```bash
pkg update && pkg upgrade -y
pkg install openssh -y
```

### Autenticación — elige una opción

**Opción A: contraseña (más simple)**

```bash
passwd
```

Introduce una contraseña. Se usará para conectar desde el PC.

**Opción B: clave pública (más segura, recomendada si vas a automatizar)**

En el PC, genera un par de claves si no tienes uno:

```powershell
ssh-keygen -t ed25519 -f $HOME\.ssh\anbernic_sftp
```

Copia el contenido de `anbernic_sftp.pub` y, en Termux:

```bash
mkdir -p ~/.ssh
echo "<contenido de anbernic_sftp.pub>" >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### Arrancar el servidor

```bash
sshd
```

No imprime nada si arranca bien. Comprueba que está escuchando:

```bash
pgrep sshd
```

### Obtener la IP de la Anbernic

```bash
ifconfig wlan0 | grep "inet "
```

O en Android: Ajustes → WiFi → (red conectada) → Detalles → dirección IP.

> **Recomendación:** reserva esa IP en el router (DHCP reservation) para que no cambie.
> Si tu router soporta mDNS y el hostname de la Anbernic resuelve a `<nombre>.local`, puedes
> usar ese nombre en vez de la IP.

### Arranque automático (opcional)

Igual que en `Guia-Termux-Anbernic.md` (Paso 7), usando Termux:Boot:

```bash
mkdir -p ~/.termux/boot
nano ~/.termux/boot/start-sshd.sh
```

```bash
#!/data/data/com.termux/files/usr/bin/bash
sshd
```

```bash
chmod +x ~/.termux/boot/start-sshd.sh
```

---

## Paso 2 — Remote SFTP en el PC (rclone)

Necesitas `rclone` instalado en el PC (ver `docs/sync/sync-cloud.md` §1) — el mismo binario
que usa la herramienta (`config.rclone_binary`, por defecto `rclone` en el PATH; si no está
en el PATH, indica la ruta en `config.toml` → `sync.rclone`). Crea el remote sin pasar por
el asistente interactivo:

**Con contraseña:**

```powershell
$pass = rclone obscure "tu_password_de_termux"
rclone config create anbernic sftp host=<IP_ANBERNIC> port=8022 user=<usuario_termux> pass=$pass
```

> El usuario de Termux es el que aparece en el prompt (`whoami` en Termux).

**Con clave pública:**

```powershell
rclone config create anbernic sftp host=<IP_ANBERNIC> port=8022 user=<usuario_termux> key_file=$HOME\.ssh\anbernic_sftp
```

### Verificar el remote

```powershell
rclone lsd anbernic:
```

Deberías ver las carpetas de la raíz de almacenamiento de la Anbernic (`RetroArch`, etc.).

También puedes usar el botón **"Probar remote"** que ya existe en la app
(`GET /api/rclone-test-remote`, en Ajustes → Catálogos/Sync), introduciendo `anbernic`
como nombre de remote.

---

## Paso 3 — Configurar la app para usar el remote WiFi

En **Ajustes**, apunta `saves_remote` (y `states_remote` si aplica) al nuevo remote, usando
las rutas de saves de RetroArch en el dispositivo (ver
`docs/sync/android-save-paths-RG556.md`):

```
saves_remote  = anbernic:/storage/emulated/0/RetroArch/saves
states_remote = anbernic:/storage/emulated/0/RetroArch/states
```

Guarda la configuración y pulsa **"Sync ahora"**. A partir de aquí el flujo es idéntico al
sync por cloud — misma política de conflictos, mismo backup automático antes de
sobreescribir, mismo delta cache para saltar archivos sin cambios. No hace falta ninguna
opción nueva en el código: para `rclone` y para `sync_saves()`, `anbernic:` es un remote
como cualquier otro.

> Nota: si usas también un remote cloud (Dropbox), puedes alternar el valor de
> `saves_remote`/`states_remote` entre el remote cloud y `anbernic:` según estés en casa o
> fuera. Un selector de UI dedicado ("Sync por WiFi" vs "Sync por Cloud") queda pendiente
> como mejora futura (PHASE3-1c).

---

## Seguridad

- `sshd` solo debe escuchar en la red local — no expongas el puerto 8022 al router/internet
  (port forwarding). Esta guía asume uso estrictamente dentro de la LAN doméstica.
- Prefiere autenticación por clave sobre contraseña si vas a dejar `sshd` arrancando
  automáticamente con Termux:Boot.
- Si no vas a sincronizar por un tiempo largo, puedes detener el servidor con
  `pkill sshd` en Termux.
- La IP del dispositivo puede cambiar si no reservaste la IP en el router; si el remote deja
  de responder, repite el Paso 1 (obtener IP) y actualiza el remote con
  `rclone config update anbernic host=<nueva_IP>`.

---

## Solución de problemas

| Problema | Causa probable | Solución |
|----------|---------------|----------|
| `connection refused` al hacer `rclone lsd anbernic:` | `sshd` no está arrancado en Termux, o el puerto no es 8022 | Ejecuta `sshd` en Termux; confirma el puerto con `pgrep sshd` y revisando `port=8022` en el remote |
| `permission denied (publickey,password)` | Contraseña incorrecta, o clave no añadida a `authorized_keys` | Repite `passwd` en Termux, o revisa que la clave pública esté en `~/.ssh/authorized_keys` con permisos `600` |
| `rclone` no encuentra `sftp-server` / falla al listar | Paquete `openssh` incompleto o desactualizado | `pkg reinstall openssh` en Termux |
| El remote deja de conectar tras un tiempo | La IP de la Anbernic cambió | Reserva la IP en el router (DHCP) o actualiza el remote con `rclone config update anbernic host=<IP>` |
| Sync no encuentra los saves | Ruta incorrecta en `saves_remote`/`states_remote` | Verifica la ruta exacta en `docs/sync/android-save-paths-RG556.md` (varía según el core/emulador) |
| `sshd` no arranca tras reiniciar la Anbernic | Termux:Boot no instalado o script sin permisos de ejecución | Instala **Termux:Boot** desde F-Droid; `chmod +x ~/.termux/boot/start-sshd.sh` |

---

## Validación en hardware real

Esta guía está escrita pero **no verificada en la consola física** — el paso final
(probar `sshd` + el remote rclone end-to-end desde el RG556) está trackeado como **V5** en
la tabla de validación de hardware del backlog (`Tareas/backlog.md`).
