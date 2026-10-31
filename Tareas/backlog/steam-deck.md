## Steam Deck — sync de saves por SSH — → #489

Idea 2026-10-30: la Deck no tiene ADB (SteamOS = Linux). Retro Vault se queda en el PC y hace sync por SSH/rsync hacia las rutas de EmuDeck. Caso de uso que lo motivó: Prince of Persia Warrior Within en PC pide teclado para el nombre; emulado (GameCube/Dolphin o PS2/PCSX2) se escribe con el mando y además da RetroAchievements.

| ID | Task | Estado |
|----|------|--------|
| DECK-SSH-1 | Backend de transporte SSH (`ssh`/`scp`/`rsync`, solo stdlib + binarios del sistema) paralelo al de ADB; detrás de la misma interfaz de transporte que usa Cable Sync (SOLID: no duplicar el flujo de sync) | pendiente |
| DECK-PATHS-1 | Perfil de dispositivo Steam Deck: rutas de EmuDeck (`~/Emulation/saves`, `~/Emulation/roms`) y de RetroArch Flatpak (`~/.var/app/org.libretro.RetroArch/`) | pendiente |
| DECK-SYNC-1 | Sync de saves PC ↔ Deck con la política de siempre: ante duda no sobreescribir, backup primero, conflictos a carpeta aparte | pendiente |
| DECK-HW-1 | Validación en la Deck real: activar `sshd` (`passwd` + `systemctl enable --now sshd`), misma red; probar Dolphin/PCSX2 con RA (usuario + token) y comprobar si Warrior Within tiene set de logros en GC y PS2 | pendiente |
| DECK-PORT-1 | (Opcional) Retro Vault corriendo en la propia Deck: rutas de `chdman`/`adb` hoy asumen `tools/*.exe` de Windows. Sin probar | pendiente |
| DECK-UI-1 | **Pestaña «Dispositivos» para pasar juegos a un dispositivo.** Un selector de destino (Steam Deck por SSH; Anbernic por ADB/SD, que ya existe) + elegir plataforma/juegos + comprobar espacio libre (`df`) + copia **reanudable y con md5 verificado**, sin sobrescribir + informe. Transporte abstraído (SOLID: la pestaña no sabe si es SSH o ADB). La selección fina de juegos es la de #246 — no duplicar, esto es la UI y el transporte. Decidir si la Anbernic entra en la misma pestaña o se queda en Sync | pendiente |
| DECK-BIOS-1 | Mandar las BIOS de la biblioteca al dispositivo, descomprimiendo si vienen en zip (`ROMS/BIOS/ps2-bios-all-bios.zip`; `BIOS/ps2/` estaba vacía y `SCPH1001.BIN` es de PS1, no de PS2). Destino EmuDeck: `~/Emulation/bios` **plano** (ver hallazgos) | pendiente |
| DECK-LAUNCH-1 | Dejar los juegos en la biblioteca de Steam sin Steam ROM Manager: añadir a `shortcuts.vdf` + portadas en `grid/` (miniaturas libretro). Requiere Steam y PCSX2 cerrados | pendiente |
| DECK-CARD-1 | Memory card PS2 al dispositivo (la fusionada de 22 partidas, ver ANDROID-EMU-SAVES-ACCESS-1j) con backup de la que hubiera y emulador cerrado | pendiente |

### Hecho a mano 2026-10-30 (base del diseño de DECK-UI-1…)

Sesión real con una Deck por SSH (`deck@192.168.1.226`, clave `~/.ssh/id_deck`). Se copiaron a mano 3 ISOs de PS2, las BIOS y la memory card fusionada, todo verificado por md5. Hallazgos que la pestaña debe respetar:

- **El Wi-Fi se cae si la Deck se duerme** (`Connection reset by peer`, ISO de 4 GB a medias). La copia tiene que ser **reanudable**: se reanudó truncando al último MiB completo y haciendo `tail -c +N | ssh … "cat >>"`; `rsync` está en la Deck pero no en el PC con Windows.
- **Verificar siempre por md5 en ambos lados** y no confiar en el tamaño.
- **EmuDeck reinicia ajustes al abrir un emulador** (`emulatorInit` en `~/Emulation/tools/launchers/pcsx2-qt.sh`): devolvió `Bios` a `~/Emulation/bios` aunque se hubiera cambiado a `bios/ps2`. Solución usada: ficheros reales en `bios/ps2` y **enlaces simbólicos** en `bios/`.
- PCSX2 en la Deck es un **AppImage** (`~/Applications/pcsx2-Qt.AppImage`, config en `~/.config/PCSX2/inis/PCSX2.ini`), no un Flatpak: `flatpak list` no lo ve.
- **No tocar el `.ini`, la card ni `shortcuts.vdf` con el emulador/Steam abiertos**: los sobrescriben al cerrar. Cuidado con `pgrep -f`: se detecta a sí mismo si la orden contiene el patrón (usar `[p]csx2-Qt`).
- Steam ROM Manager **por CLI se cae** (coredump) y tenía el parser de PS2 desactivado y 80 activados; se añadieron los accesos escribiendo `shortcuts.vdf` (binario; `appid = crc32(exe+nombre) | 0x80000000`; portada = `grid/<appid>p.png`). `shortcuts.vdf` se respalda antes.
- Las portadas salen de `thumbnails.libretro.com/Sony - PlayStation 2/Named_Boxarts/<nombre Redump>.png` (200 OK con los nombres de las ISOs).
- `sudo` en la Deck pide contraseña: nada que requiera instalar paquetes del sistema.
- Rendimiento aplicado (sin medir): Vulkan, 2x, parches de pantalla ancha y sin entrelazado, FPS en pantalla.
- Juegos nativos (p. ej. Dark Cloud 2 con `DC2Launcher`): `Saves/` vacía, formato desconocido y no intercambiable con la card PS2; sincronizarlos solo cuando se hayan jugado una vez en el PC.

### Diseño de DECK-SYNC-1 (2026-10-31, sobre el sync real leído con /sync-design)

**Topología:** el PC es el centro (`gdrive:/RetroSync/saves/…` por rclone; Anbernic por ADB). La Deck es un cliente más por SSH; no hay sync directa entre dispositivos y solo propaga cuando el PC está encendido y la Deck responde.

1. **Un protocolo de transporte común.** `sync_saves()` está atado a `RcloneTransport` (`sync/save_syncer.py:77-93`, `_resolve_remote` en `:11-16`). Extraer un protocolo mínimo (`list_remote`, `upload`, `download`) que implementen rclone y un nuevo `SshTransport` — así la Deck reutiliza `decide()` (`sync/conflict_resolver.py:25-64`), la marca de `save_sync_log` (`sync/sync_log.py:100-135`), la guarda de 0 bytes (`save_syncer.py:189-196`) y los conflictos manuales, en vez de copiar el «gana el mtime» de Cable Sync. Es el cambio más grande y toca código que funciona: rama propia y tests con BD real.
2. **Rutas de la Deck en configuración** (como `[[emulator_paths]]`): `~/Emulation/saves/pcsx2/saves`, Dolphin, DuckStation y RetroArch de EmuDeck (DECK-PATHS-1).
3. **Seguridad:** reutilizar pre-flight de desvío de reloj (`sync_cable.py:352-370`), backup versionado previo (`saves_keep_n`), verificación por md5, y comprobar por SSH que el emulador no está abierto antes de escribir (en la sesión real PCSX2 sobrescribe su `.ini` y la card al cerrar). Tolerar que la Deck desaparezca a mitad de sync (se duerme y el Wi-Fi cae: ver «Hecho a mano 2026-10-30»).
4. **Disparo:** manual primero; luego sondeo del puerto 22 al estilo del daemon ADB (`web/cable_sync_daemon.py:85-176`: 10 s de sondeo, 30 s de enfriamiento).
5. **Memory cards PS2: nunca se resuelven solas.** Son un único archivo de 8 MB (`Mcd001.ps2`); «gana el más nuevo» pierde los saves del otro lado. La fusión real necesita `mymcplus`, dependencia externa que choca con la regla «solo stdlib» de `CLAUDE.md`. Primera versión: un conflicto de card guarda ambas versiones y avisa; la fusión queda como paso posterior fuera del runtime (como ANDROID-EMU-SAVES-ACCESS-1j).

**Prerrequisitos** (en la rama `docs/sync-pcsx2-dir-1`, aún sin PR): `SYNC-PCSX2-DIR-1` y `CABLE-NEWEST-NO-CONFLICT-1` (con tres dispositivos los conflictos dejan de ser raros y la ruta cable hoy no los detecta).
