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
