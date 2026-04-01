# Estructura de saves en Anbernic — Guía para RetroArch Android

> Documento de referencia para la estructura correcta de carpetas de saves en dispositivos Anbernic (y otros Android con RetroArch).

---

## 📂 Estructura general

RetroArch en Android almacena saves en:

```
/storage/emulated/0/RetroArch/
├── saves/                           # Saves de batería (.sav, .srm)
│   ├── NES/
│   ├── SNES/
│   ├── Game Boy Advance/
│   ├── PlayStation/
│   ├── Sega Mega Drive/
│   └── ... (una subcarpeta por plataforma)
│
├── states/                          # Save states (.state0–.state9, .state)
│   ├── NES/
│   ├── SNES/
│   └── ... (misma estructura que saves)
│
└── retroarch.cfg                   # Configuración principal
```

---

## 🎮 Mapeo de plataformas → carpetas de saves

| Plataforma | Carpeta en saves | Nombre en config | Extensión típica |
|------------|------------------|------------------|------------------|
| **Nintendo** | | | |
| NES / Famicom | `NES/` | `NES` | `.sav` |
| SNES / Super Famicom | `SNES/` | `SNES` | `.sav`, `.srm` |
| Nintendo 64 | `Nintendo 64/` | `Nintendo 64` | `.srm` |
| Game Boy | `Game Boy/` | `Game Boy` | `.sav` |
| Game Boy Color | `Game Boy Color/` | `Game Boy Color` | `.sav` |
| Game Boy Advance | `Game Boy Advance/` | `Game Boy Advance` | `.sav` |
| Nintendo DS | `Nintendo DS/` | `Nintendo DS` | `.sav` |
| Nintendo 3DS | `Nintendo 3DS/` | `Nintendo 3DS` | `.sav` |
| GameCube | `GameCube/` | `GameCube` | `.sav` |
| Wii | `Wii/` | `Wii` | `.sav` |
| Wii U | `Wii U/` | `Wii U` | `.sav` |
| | | | |
| **Sony** | | | |
| PlayStation 1 (PSX) | `PlayStation/` | `PlayStation` | `.srm`, `.sav` |
| PlayStation 2 | `PlayStation 2/` | `PlayStation 2` | `.srm`, `.sav` |
| PSP | `PSP/` | `PSP` | `.srm`, `.sav` |
| | | | |
| **Sega** | | | |
| Master System | `Master System/` | `Master System` | `.sav`, `.srm` |
| Game Gear | `Game Gear/` | `Game Gear` | `.sav`, `.srm` |
| Sega Mega Drive | `Sega Mega Drive/` | `Sega Mega Drive` | `.sav`, `.srm` |
| Sega Saturn | `Sega Saturn/` | `Sega Saturn` | `.sav` |
| Dreamcast | `Dreamcast/` | `Dreamcast` | `.sav` |
| | | | |
| **Otros** | | | |
| PC Engine | `PC Engine/` | `PC Engine` | `.sav` |
| Neo Geo | `Neo Geo/` | `Neo Geo` | `.sav` |
| Atari 2600 | `Atari 2600/` | `Atari 2600` | `.sav` |

---

## ⚙️ Configuración en RetroArch

Para que RetroArch use subcarpetas por plataforma, configura en `retroarch.cfg`:

```ini
# Ruta base de saves
savefile_directory = "/storage/emulated/0/RetroArch/saves"

# Usar subcarpetas por plataforma (cada núcleo crea su propia subcarpeta)
# Esta opción depende del núcleo — muchos la respetan automáticamente
# Si no funciona, crea las carpetas manualmente
```

### Núcleos que respetan subcarpetas por plataforma:

- ✅ Nestopia (NES)
- ✅ Snes9x (SNES)
- ✅ Mupen64 (N64)
- ✅ Mgba (GBA)
- ✅ DeSmuME (NDS)
- ✅ Genesis Plus GX (Mega Drive, Master System)
- ✅ Mednafen (PSX, Saturn, PC Engine)
- ✅ PCSX2 (PS2)

**Recomendación:** Prueba con un juego y verifica dónde se guarda el save. Si no crea carpetas automáticamente, créalas tú manualmente en el Android.

---

## 📁 Crear carpetas manualmente (con ADB)

Si tu Anbernic no crea las carpetas automáticamente, usa ADB:

```bash
# Conectar por USB y activar Depuración USB en la Anbernic

# Crear estructura de carpetas
adb shell mkdir -p /storage/emulated/0/RetroArch/saves/NES
adb shell mkdir -p /storage/emulated/0/RetroArch/saves/SNES
adb shell mkdir -p /storage/emulated/0/RetroArch/saves/"Game Boy"
adb shell mkdir -p /storage/emulated/0/RetroArch/saves/"Game Boy Advance"
adb shell mkdir -p /storage/emulated/0/RetroArch/saves/PlayStation
adb shell mkdir -p /storage/emulated/0/RetroArch/saves/"Sega Mega Drive"
adb shell mkdir -p /storage/emulated/0/RetroArch/saves/"Nintendo 64"

# Lo mismo para states/
adb shell mkdir -p /storage/emulated/0/RetroArch/states/NES
adb shell mkdir -p /storage/emulated/0/RetroArch/states/SNES
# ... etc
```

---

## 🔄 Sincronización con PC (Retro Vault)

Cuando sincronices saves desde **Retro Vault**, asegúrate de que coincidan las rutas:

### Opción A: Sync automático (recomendado)

En la pestaña **Cable Sync** de Retro Vault:

- **Ruta local PC:** `C:\Mis Documentos\RetroArch\saves`
- **Ruta Anbernic:** `/storage/emulated/0/RetroArch/saves`
- **Dirección:** Bidireccional (más reciente gana)
- **Incluir subcarpetas:** ✅ Sí

Esto copiará automáticamente:
```
C:\...\saves\NES\         → /storage/emulated/0/RetroArch/saves/NES/
C:\...\saves\SNES\        → /storage/emulated/0/RetroArch/saves/SNES/
C:\...\saves\PlayStation/ → /storage/emulated/0/RetroArch/saves/PlayStation/
```

### Opción B: Sincronización vía WiFi (rclone/FolderSync)

Ver: `docs/android-sync.md`

---

## ⚠️ Notas y solución de problemas

### "Mi save no aparece"

1. ✅ Verifica que la carpeta de plataforma existe en la Anbernic
2. ✅ Comprueba el nombre del archivo — debe coincidir con el ROM (ej. `Mario Bros.sav`)
3. ✅ Cierra RetroArch antes de copiar saves manualmente
4. ✅ Espera 5 segundos y reabre RetroArch

### "Los saves se pierden después de sincronizar"

- ❌ **NO** sincronices mientras RetroArch esté abierto
- ❌ **NO** tengas dos sincronizaciones corriendo a la vez (PC + Anbernic)
- ✅ Usa siempre la regla de conflicto "más reciente gana"
- ✅ Haz un backup de tus saves antes de experimentar

### "Quiero usar una carpeta diferente para cada usuario"

RetroArch soporta múltiples configuraciones — crea archivos de config separados:

```
/storage/emulated/0/RetroArch/
├── retroarch.cfg                 (config por defecto)
├── retroarch-player2.cfg         (config alterno)
└── saves/                        (carpeta compartida o separada)
```

---

## 📋 Checklist de configuración

- [ ] Carpeta `/storage/emulated/0/RetroArch/` existe
- [ ] Subcarpetas de saves `/storage/emulated/0/RetroArch/saves/<Plataforma>/` creadas
- [ ] Subcarpetas de states `/storage/emulated/0/RetroArch/states/<Plataforma>/` creadas
- [ ] RetroArch configurado para usar estas rutas (ver config)
- [ ] Permisos correctos: RetroArch tiene permisos de lectura/escritura
- [ ] Primer sync completado sin errores
- [ ] Saves de prueba sincronizados correctamente

---

## 📚 Referencias

- Documentación de sincronización: `docs/android-sync.md`
- RetroArch oficial: https://www.retroarch.com/
- Guía de configuración: https://docs.libretro.com/
