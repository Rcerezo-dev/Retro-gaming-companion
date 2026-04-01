# ES-DE — Temas recomendados y configuración de medias

## Medias generadas por Retro Vault

El scraper descarga tres tipos de imagen por juego y los exporta al `gamelist.xml`:

| Tag XML       | Carpeta en disco          | Uso en ES-DE                     |
|---------------|---------------------------|----------------------------------|
| `<image>`     | `media/images/`           | Portada (box art 3D o 2D)        |
| `<thumbnail>` | `media/wheels/`           | Logo/wheel en la lista lateral   |
| `<marquee>`   | `media/wheels/`           | Marquee en algunos temas         |
| `<screenshot>`| `media/screenshots/`      | Captura de pantalla en detalle   |

Todos los archivos tienen el mismo nombre base que el ROM (ej. `Donkey Kong Country.png`).

---

## Temas recomendados para ES-DE (PC)

### 1. **Art Book Next** ⭐ (favorito para colecciones con portadas)
- Muestra box art grande + metadatos a la derecha
- Requiere: `<image>` (portada) — lo tenemos
- Descarga: ES-DE → Themes → Art Book Next
- Ideal para: colecciones completas con scraping hecho

### 2. **Slate**
- Diseño sobrio, dark, fácil de leer
- Usa `<image>` + `<thumbnail>` (wheel) si están disponibles
- Buena opción si la biblioteca tiene pocas portadas

### 3. **Rbsimple-DE** (incluido por defecto)
- Tema por defecto de ES-DE
- Funciona bien sin medias adicionales
- Usa `<image>` y `<thumbnail>`

### 4. **Modern** / **Modern-DE**
- Interfaz de cuadrícula con portadas grandes
- Requiere `<image>` para verse bien
- Descargar desde el gestor de temas integrado

---

## Instalar temas en ES-DE (PC)

1. Abre ES-DE → **Main Menu** (`Start`) → **UI Settings** → **Theme Set**
2. Pulsa **Download themes** para acceder al repositorio oficial
3. Selecciona el tema y pulsa **Install**
4. Reinicia ES-DE para aplicar

---

## Estructura de medias esperada por ES-DE

ES-DE busca las medias en la carpeta del ROM con esta estructura:

```
E:\Carpetas anbernic\
  Game Boy Advance\
    gamelist.xml
    Donkey Kong Country.gba
    media\
      images\
        Donkey Kong Country.png     ← <image>
      wheels\
        Donkey Kong Country.png     ← <thumbnail> / <marquee>
      screenshots\
        Donkey Kong Country.png     ← <screenshot>
```

Esta estructura es exactamente la que genera Retro Vault al hacer scraping con **Descargar imágenes** activado.

---

## ES-DE en la Anbernic RG556

ES-DE tiene versión para Android. En la Anbernic:

- Instalar: descargar el APK desde [es-de.org](https://es-de.org)
- ROMs: `storage/emulated/0/ROMs/<plataforma>/`
- Medias: `storage/emulated/0/ROMs/<plataforma>/media/images/`
- El `gamelist.xml` de cada plataforma debe estar en la carpeta de ROMs

Retro Vault puede copiar los `gamelist.xml` y las carpetas `media/` a la Anbernic mediante **Cable Sync** (activar los checkboxes "Assets/imágenes" y "Gamelists").

---

## Consejos de rendimiento

- En PC: los temas con vídeos (`.mp4`) consumen más recursos; desactívalos en **UI Settings → Scraper → Scrape videos** si el PC va justo
- Los wheels (logos) mejoran mucho la legibilidad en listas largas
- Art Book Next + portadas 3D es la combinación más vistosa con la biblioteca scrapeada

---

## 34d-2: Conversión CSO/ZSO → ISO (PSP)

**Estado:** Documentación para implementar en Retro Vault

### ¿Qué es CSO/ZSO?

- **CSO** (Compressed ISO) — formato comprimido para PSP, creado por `maxcso`
- **ZSO** — versión alternativa del mismo formato
- Ventaja: ocupan 40-60% menos espacio que `.iso`
- Desventaja: algunos emuladores (especialmente en PC con RetroArch) prefieren `.iso`

### Cuándo convertir

✅ **Usa CSO/ZSO si:**
- Juegas principalmente en la Anbernic
- RetroArch Android soporta CSO
- Quieres ahorrar espacio

❌ **Convierte a ISO si:**
- Quieres máxima compatibilidad en PC
- Tienes espacio suficiente
- Planeas cambiar entre dispositivos

### Herramienta: maxcso

**maxcso.exe** — compresor/descompresor de ISO ↔ CSO

```bash
# Descomprimir CSO a ISO
maxcso.exe --decompress input.cso output.iso

# Comprimir ISO a CSO
maxcso.exe input.iso output.cso

# Nivel de compresión (por defecto: 9)
maxcso.exe -l 9 input.iso output.cso
```

### Implementación esperada en Retro Vault (34d-2)

Cuando se implemente, habrá una sección en **Tools → Formatos de archivo** con:

```
╔════════════════════════════════════════╗
║  Conversión CSO/ZSO ↔ ISO (PSP)       ║
╠════════════════════════════════════════╣
║                                        ║
║  📁 Carpeta de ROMs: [__________]     ║
║     [library_root]                     ║
║                                        ║
║  ☐ CSO → ISO (descomprimir)           ║
║  ☐ ISO → CSO (comprimir)              ║
║                                        ║
║  Nivel compresión: [9 ▓▓▓▓▓▓▓] (máx) ║
║                                        ║
║  [🔧 Convertir] [━━━━━━] 45%          ║
║                                        ║
║  ✓ 5 archivos convertidos              ║
║  ✗ 1 fallo (archivo corrupto)          ║
║                                        ║
╚════════════════════════════════════════╝
```

**Características:**
- Detección automática de archivos `.cso`/`.zso` en la carpeta
- Opción para comprimir (ISO → CSO) o descomprimir (CSO → ISO)
- Barra de progreso por archivo
- Aviso si `maxcso.exe` no se encuentra (debe estar en `tools/maxcso.exe`)
- Rollback si hay error (archivo original se conserva)
- Resumen al final (X convertidos, Y fallidos)

### Descargando maxcso

1. Descarga desde: https://github.com/unknownbrackets/maxcso/releases
2. Busca `maxcso.exe` (build para Windows)
3. Coloca en: `Retro Vault/tools/maxcso.exe`
4. Retro Vault lo detectará automáticamente

### Configuración actual

En tu `config.toml`:

```toml
[tools]
maxcso_path = "tools/maxcso.exe"  # Ruta donde buscar maxcso
psp_default_format = "iso"         # Formato preferido: "iso" o "cso"
```

---

**Nota para otros PC:** Esta documentación sirve de referencia. La implementación se añadirá en una próxima sesión cuando sea prioritaria en el roadmap.
