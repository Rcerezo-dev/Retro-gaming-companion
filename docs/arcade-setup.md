# Arcade Setup — Anbernic RG556 + RetroArch

> Cubre ARCADE-SETUP-1/2/3. ARCADE-SETUP-4 (test ROM end-to-end) requiere hardware.

---

## 1. FBNeo vs MAME — Decisión para el RG556

### Hardware (RG556)

- SoC: Unisoc T618 (Cortex-A75 × 2 + A55 × 6 @ 2.0 GHz)
- RAM: 8 GB LPDDR4X
- OS: Android 13 + RetroArch

### Veredicto

| Core | ROM set | Recomendado para RG556 | Por qué |
|------|---------|------------------------|---------|
| **FBNeo** | FBNeo propio (curado) | **Sí — primera opción** | Ligero, alta compatibilidad con títulos populares (CPS1/2/3, Neo-Geo, Cave), set pequeño y bien mantenido |
| **MAME 2003 Plus** | MAME 0.78+ (merged) | Sí — segunda opción | Excelente rendimiento en el T618; cubre títulos que no están en FBNeo |
| MAME 2010 | MAME 0.139 | Ocasional | Mejor precisión que 2003 Plus; algo más pesado; para títulos específicos que 2003 Plus no emula bien |
| MAME current | MAME actual | No | Demasiado pesado; rendimiento inconsistente en el T618 |

**Regla práctica**: primero busca el ROM en FBNeo. Si no existe o falla, prueba MAME 2003 Plus. MAME 2010 solo para casos concretos.

---

## 2. Sistemas objetivo y cores

| Sistema | Core RetroArch | ROM set |
|---------|---------------|---------|
| CPS1 (Street Fighter, Final Fight…) | `fbalpha2012_cps1` o **FBNeo** | FBNeo |
| CPS2 (Marvel vs Capcom, DarkStalkers…) | **FBNeo** | FBNeo |
| CPS3 (Street Fighter III…) | **FBNeo** | FBNeo |
| Neo-Geo (KOF, Metal Slug…) | **FBNeo** | FBNeo (+ BIOS `neogeo.zip`) |
| Cave (DoDonPachi, ESP Ra.De…) | **FBNeo** | FBNeo |
| MAME general (golden era) | **MAME 2003 Plus** | MAME 0.78 merged |
| MAME 90s-2000s (más preciso) | MAME 2010 | MAME 0.139 merged |
| Konami (Simpsons, TMNT, X-Men…) | **FBNeo** | FBNeo |
| Data East, Taito, Jaleco… | **FBNeo** o MAME 2003 Plus | FBNeo / MAME 0.78 |

### BIOS necesarias (FBNeo)

| Archivo | Sistema |
|---------|---------|
| `neogeo.zip` | Neo-Geo (obligatorio) |
| `pgm.zip` | PolyGame Master (opcional, para juegos PGM en FBNeo) |

Colocar en la misma carpeta que las ROMs o en la carpeta `system/` de RetroArch.

---

## 3. Estructura de biblioteca

```
F:\Juegos Retro\
└── Arcade\
    ├── FBNeo\          # ROMs para el core FBNeo
    │   ├── neogeo.zip  # BIOS Neo-Geo
    │   └── *.zip
    └── MAME\           # ROMs para MAME 2003 Plus / 2010
        └── *.zip
```

En `config.toml`:

```toml
# Arcade — añadir a library_root o como ruta adicional
# El scanner detecta .zip en subcarpetas automáticamente
```

No se necesita config nueva en `config.toml`: el scanner ya recorre subcarpetas.
Si se quiere separar el match DAT, añadir las carpetas de DATs arcade a `dat_dirs`.

### DATs arcade

| Fuente | Formato | Dónde obtener |
|--------|---------|---------------|
| FBNeo DAT | Logiqx XML + clrmamepro | `libretro/libretro-database` → `metadat/fbneo/` |
| MAME 2003 Plus DAT | Logiqx XML | `libretro/libretro-database` → `metadat/mame/` |

Ambos compatibles con el auto-downloader (`DAT-DL-1/2/3`, ya implementado).
En Settings → Catálogos DAT → seleccionar plataforma `arcade_fbneo` / `arcade_mame`.

---

## 4. Pendiente (requiere hardware)

- **ARCADE-SETUP-4**: scan → rename → launch de una ROM de muestra en el RG556.
  Candidatos: `mslug.zip` (Metal Slug, Neo-Geo/FBNeo) y `sf2.zip` (CPS1/FBNeo).
