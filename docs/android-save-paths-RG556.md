# Android Save Paths — Anbernic RG556

Verified live on device `RG556006101273` (model: RG556, Android scoped storage).
All paths are under `/storage/emulated/0/` unless noted as scoped storage.
Scoped storage paths (`Android/data/<package>/files/`) require ADB to access — they are not visible via a file manager without root.

---

## RetroArch (`com.retroarch.aarch64`)

RetroArch stores everything on the **SD card** (not scoped storage), configured in `retroarch.cfg`:

| Type | Path |
|------|------|
| Save files (.srm, .sav, etc.) | `/storage/emulated/0/RetroArch/saves/<CoreName>/` |
| Save states | `/storage/emulated/0/RetroArch/states/<CoreName>/` |

Save and state subfolders confirmed on device (core name = display name):

**Saves:**
- `Beetle PSX/` — PS1
- `LRPS2/` — PS2 (LRPS2 core)
- `FCEUmm/` — NES
- `mGBA/` — GB / GBC / GBA
- `VBA Next/` — GBA
- `Snes9x/`, `Snes9x 2010/`, `Snes9x 2005 Plus/`, `bsnes2014/` — SNES
- `Genesis Plus GX/`, `Genesis Plus GX Wide/` — Mega Drive / Genesis
- `Flycast/` — Dreamcast
- `PPSSPP/PSP/`, `PSP/SAVEDATA/` — PSP (mirrors `/storage/emulated/0/PSP/SAVEDATA/`)
- `User/GC/` — GameCube (Dolphin core)
- `Citra/Citra/` — 3DS (Citra core)
- `fbneo/` — FBNeo arcade
- `mame2003/` — MAME 2003

**States:**
- `Beetle PSX/`, `LRPS2/`, `FCEUmm/`, `mGBA/`, `VBA Next/`
- `Snes9x/`, `Snes9x 2010/`, `Snes9x 2005 Plus/`, `bsnes2014/`
- `Flycast/`

---

## DuckStation — PS1 (`com.github.stenzek.duckstation`)

Scoped storage — requires ADB.

| Type | Path | Extensions |
|------|------|-----------|
| Memory cards | `/storage/emulated/0/Android/data/com.github.stenzek.duckstation/files/memcards/` | `.mcd`, `.mcr`, `.srm` |
| Save states | `/storage/emulated/0/Android/data/com.github.stenzek.duckstation/files/savestates/` | `.sav` |

Save state naming: `<SERIAL>_<slot>.sav` and `<SERIAL>_resume.sav`

---

## AetherSX2 — PS2 (`xyz.aethersx2.android`)

Scoped storage — requires ADB.

| Type | Path | Extensions |
|------|------|-----------|
| Memory cards | `/storage/emulated/0/Android/data/xyz.aethersx2.android/files/memcards/` | `.ps2` |
| Save states | `/storage/emulated/0/Android/data/xyz.aethersx2.android/files/sstates/` | `.p2s`, `.p2s.backup` |

Save state naming: `<SERIAL> (<HASH>).<slot>.p2s`

---

## PPSSPP — PSP (`org.ppsspp.ppsspp`)

PPSSPP stores saves on the **SD card** (accessible without ADB):

| Type | Path |
|------|------|
| Save data | `/storage/emulated/0/PSP/SAVEDATA/` |
| Save states | `/storage/emulated/0/PSP/PPSSPP_STATE/` |

Note: RetroArch's PPSSPP core mirrors to `/storage/emulated/0/RetroArch/saves/PSP/SAVEDATA/`.

---

## Dolphin — GameCube / Wii (`org.dolphinemu.dolphinemu`)

Scoped storage — **Permission denied via ADB shell** (requires `run-as` or root).
Paths exist at:

| Type | Path (inaccessible via ADB) |
|------|------------------------------|
| GC memory cards | `/storage/emulated/0/Android/data/org.dolphinemu.dolphinemu/files/GC/` |
| Wii saves | `/storage/emulated/0/Android/data/org.dolphinemu.dolphinemu/files/Wii/` |
| Save states | `/storage/emulated/0/Android/data/org.dolphinemu.dolphinemu/files/StateSaves/` |

⚠️ **Sync not possible via ADB pull/push without root.** Use the Dolphin in-app backup feature or grant ADB special permissions.

---

## Dolphin MMJ (`org.dolphinemu.mmjr`)

Same situation as Dolphin — scoped storage, ADB permission denied.
Files directory: `/storage/emulated/0/Android/data/org.dolphinemu.mmjr/files/`

---

## Citra — 3DS (`org.citra.emu`)

Scoped storage — requires ADB. Save data is buried inside a Nintendo-style directory tree:

| Type | Path |
|------|------|
| Game saves | `/storage/emulated/0/Android/data/org.citra.emu/files/citra-emu/sdmc/Nintendo 3DS/<uid>/<uid>/title/<titleid>/data/` |
| Extra data | `/storage/emulated/0/Android/data/org.citra.emu/files/citra-emu/nand/data/<uid>/extdata/` |

The `<uid>` folders are all-zeros (`00000000000000000000000000000000`) on this device.

---

## Lime3DS — 3DS (`io.github.lime3ds.android`)

Installed but no save data found yet. Expected paths (by analogy with Citra):
`/storage/emulated/0/Android/data/io.github.lime3ds.android/files/`

---

## melonDS — Nintendo DS (`me.magnum.melonds`)

Installed but no save data found. Files dir:
`/storage/emulated/0/Android/data/me.magnum.melonds/files/`
melonDS typically stores `.sav` files next to ROMs or in a configurable directory.

---

## Mupen64Plus FZ — N64 (`org.mupen64plusae.v3.fzurita.pro`)

Installed but no save data found in scoped storage. Files dir is empty.
Saves may be written alongside ROMs or in a user-configured sdcard path.

---

## Redream — Dreamcast (`io.recompiled.redream`)

Scoped storage — requires ADB.

| Type | Path | Notes |
|------|------|-------|
| Save states | `/storage/emulated/0/Android/data/io.recompiled.redream/files/states/` | `.sav` + `.png` screenshot per state |
| VMU saves | `/storage/emulated/0/Android/data/io.recompiled.redream/files/` | `vmu0.bin`–`vmu3.bin` |

---

## Flycast — Dreamcast (`com.flycast.emulator`)

Scoped storage files dir is empty — save data not yet created, or stored in a different location.
RetroArch Flycast core saves at `/storage/emulated/0/RetroArch/saves/Flycast/`.

---

## Yaba Sanshiro 2 — Saturn (`org.devmiyax.yabasanshioro2.pro`)

Scoped storage — requires ADB.

| Type | Path | Notes |
|------|------|-------|
| Internal RAM (saves) | `/storage/emulated/0/Android/data/org.devmiyax.yabasanshioro2.pro/files/yabause/memory/` | `memory.ram` |
| Save states | `/storage/emulated/0/Android/data/org.devmiyax.yabasanshioro2.pro/files/yabause/state/` | Empty on device |

---

## EX+ Emulators (Robert Broglia)

All EX+ emulators use the same structure. The `EmuEx/` folder is created after the first time a game is saved.

| Emulator | Package | Saves path |
|----------|---------|-----------|
| GBA.emu | `com.explusalpha.GbaEmu` | `.../files/EmuEx/<SystemFolder>/saves/` *(not yet created)* |
| GBC.emu | `com.explusalpha.GbcEmu` | `.../files/EmuEx/<SystemFolder>/saves/` *(not yet created)* |
| NES.emu | `com.explusalpha.NesEmu` | `.../files/EmuEx/<SystemFolder>/saves/` *(not yet created)* |
| Snes9x EX+ | `com.explusalpha.Snes9xPlus` | `/storage/emulated/0/Android/data/com.explusalpha.Snes9xPlus/files/EmuEx/SFC-SNES/saves/` ✅ |
| MD.emu | `com.explusalpha.MdEmu` | `.../files/EmuEx/<SystemFolder>/saves/` *(not yet created)* |
| NEO.emu | `com.explusalpha.NeoEmu` | `.../files/EmuEx/<SystemFolder>/saves/` *(not yet created)* |

Save file format: `.frz` (freeze state), named `<GameTitle>.<slot>.frz`.
All scoped storage — requires ADB.

---

## Summary — Access method by emulator

| Emulator | Saves location | ADB needed? |
|----------|---------------|-------------|
| RetroArch | SD card `/storage/emulated/0/RetroArch/saves/` | ❌ No |
| PPSSPP | SD card `/storage/emulated/0/PSP/` | ❌ No |
| DuckStation | Scoped storage | ✅ Yes |
| AetherSX2 | Scoped storage | ✅ Yes |
| Citra | Scoped storage | ✅ Yes |
| Redream | Scoped storage | ✅ Yes |
| Yaba Sanshiro 2 | Scoped storage | ✅ Yes |
| EX+ (Snes9x EX+) | Scoped storage | ✅ Yes |
| Dolphin / MMJ | Scoped storage + **permission denied** | ⚠️ Root/special grant needed |
| Flycast | Scoped storage (empty) | ✅ Yes |
| melonDS | Scoped storage (empty) | ✅ Yes |
| Mupen64Plus FZ | Unknown / alongside ROMs | TBD |
| Lime3DS | Scoped storage (empty) | ✅ Yes |

---

*Verified: 2026-04-05 · Device: Anbernic RG556 · ADB serial: RG556006101273*
