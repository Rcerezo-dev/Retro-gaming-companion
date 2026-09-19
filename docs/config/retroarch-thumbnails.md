# RetroArch — Convención de thumbnails y su relación con el scraper de Retro Vault

Investigado y verificado en vivo 2026-09-19 (máquina "Ruben"/PC2) para responder
si el scraping de Retro Vault puede reutilizarse a la vez por ES-DE, RetroArch
y la propia app, sin repetir el trabajo de scraping para cada uno.

## Resumen

- **ES-DE**: ya funciona hoy sin nada nuevo — lee `media/images|screenshots|wheels/`
  junto al ROM vía el `gamelist.xml` que ya genera `scraper/gamelist_writer.py`
  (ver `docs/config/esde-themes.md`).
- **RetroArch**: usa una convención de carpetas y nombres completamente distinta
  (`thumbnails/<sistema>/Named_Boxarts|Named_Snaps|Named_Titles/<título>.png`),
  **solo acepta PNG**, y no lee la carpeta `media/` de ES-DE en absoluto. Hace
  falta un paso de publicación aparte — no es trivial pero tampoco requiere
  volver a scrapear nada, solo reformatear lo que ya existe.

## Estructura real de `RetroArch/thumbnails/`

Verificado contra un pack oficial real (descargado por RetroArch mismo, Online
Updater → Thumbnails Updater, sistema Game Boy Advance, 193 juegos):

```
RetroArch/thumbnails/
  Nintendo - Game Boy Advance/
    Named_Boxarts/
      007 - NightFire (USA, Europe) (En,Fr,De).png
      Alien Hominid (Europe) (En,Fr,De,Es,It).png
      ...
    Named_Snaps/          ← captura de gameplay
      (mismos nombres, mismo set de juegos)
    Named_Titles/         ← pantalla de título
      (mismos nombres, mismo set de juegos)
```

**Tres hechos confirmados empíricamente, no de memoria:**

1. **El nombre de carpeta de sistema es exactamente el mismo `db_name`** que ya
   usa `utils/lpl_generator.py::_platform_db_name()` para las playlists
   (`"Nintendo - Game Boy Advance"`, `"Sony - PlayStation"`, etc.) — no hace
   falta una tabla de mapeo nueva, ya existe.
2. **El nombre de archivo es el título completo estilo No-Intro/Redump**, con
   tags de región e idioma (`(USA, Europe) (En,Fr,De)`) — coincide con
   `canonical_title`, el mismo campo que `.lpl` ya usa como `label`. RetroArch
   busca el thumbnail de un juego por su `label` en la playlist, no por el
   nombre de archivo del ROM.
3. **Formato: 100% `.png`** en las 193 imágenes del pack oficial — cero `.jpg`.
   Confirma lo que decían los foros de RetroArch (histórico, nunca se probó en
   este proyecto hasta hoy): el visor de thumbnails no acepta JPG.

## El problema real: la biblioteca ya scrapeada es JPG

`web/handlers/scraper.py` descarga box art como `.jpg` o `.png` según lo que
sirva ScreenScraper (`_ext = ".png" if ".png" in url.lower() else ".jpg"`) —
en la práctica, casi siempre `.jpg`. Verificado contra la biblioteca real de
esta máquina: **934/934 carátulas ya scrapeadas son `.jpg`**, 0 en PNG.

## Conversión sin añadir una dependencia nueva

El proyecto no tiene ninguna librería de imágenes (regla: solo stdlib) y
Python puro no decodifica JPEG. La solución probada en vivo: **PowerShell +
`System.Drawing`** (parte de .NET, presente en cualquier Windows), mismo
patrón que ya usa `utils/notifier.py` para las notificaciones — no es pip, es
un `subprocess` más a un binario que ya viene con el sistema operativo.

```powershell
Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile($origenJpg)
$img.Save($destinoPng, [System.Drawing.Imaging.ImageFormat]::Png)
$img.Dispose()
```

Verificado en vivo: convertida la carátula de "Super Mario Bros. 3 (Europe)"
(NES), colocada en `Named_Boxarts/`, visible en la playlist de RetroArch tras
reiniciar la app (RetroArch solo lee `playlists/`/`thumbnails/` al arrancar,
no en caliente).

## Mapeo Retro Vault → RetroArch, por tipo de media

| Carpeta de Retro Vault (`media/`) | ScreenScraper media type | Carpeta RetroArch |
|---|---|---|
| `images/` (box art) | `box-3D`/`box-2D`/`box-2D-side` | `Named_Boxarts/` |
| `screenshots/` (gameplay) | `screenshot` | `Named_Snaps/` |
| — (no se scrapea hoy) | `sstitle` | `Named_Titles/` |
| `wheels/` (logo) | `wheel`/`wheel-hd`/`mixrbv*` | — (RetroArch no tiene categoría de wheel/logo) |

`screenshot_url` en `scraper/screenscraper.py:224` pide explícitamente el tipo
`"screenshot"` (gameplay), no `"sstitle"` (pantalla de título) — por eso el
mapeo a `Named_Snaps` es 1:1, pero `Named_Titles` se quedaría vacío salvo que
se añada ese tipo de media al scraper aparte.

## Implementado: `publish_retroarch_thumbnails()` (RETROARCH-THUMBS-1)

Construido como función real de la app (no pasos manuales), botón "Publicar
carátulas en RetroArch" en la pestaña Formatos/Tools:

- `utils/retroarch_thumbnails.py::publish_retroarch_thumbnails()` — recorre
  `games` JOIN `game_metadata`, agrupa por `(platform, canonical_title)` y
  publica `box_art_path`/`screenshot_path` en
  `<RetroArch>/thumbnails/<db_name>/Named_Boxarts|Named_Snaps/<canonical_title>.png`.
  Reutiliza `platform_db_name()` de `lpl_generator.py` (renombrada de privada
  a pública al pasar a usarse desde dos módulos — no se duplicó la tabla).
- **Sin duplicar bytes cuando el origen ya es PNG**: enlace duro
  (`os.link`, mismo inodo — 0 bytes extra, y un rescrape que sobreescribe el
  origen en el sitio mantiene el enlace sincronizado), con `shutil.copy2`
  como fallback solo si el enlace cruza de volumen.
- **JPG (RetroArch los rechaza) se convierte una vez** vía PowerShell +
  `System.Drawing` (mismo truco que `utils/notifier.py`, sin dependencia
  nueva) a una caché en `library_root/.rommgr/retroarch_thumbnails_cache/`
  keyed por mtime del origen — reruns no reconvierten lo ya convertido.
- Filas sin `canonical_title` (arcade sin match, hacks/parches — ver
  `CATALOG-MATCH-SUBSET-1`) se cuentan en `skipped_no_title` y se quedan sin
  carátula en RetroArch, comportamiento correcto (no inventar un nombre).
- Corre como **job en background** (`web/jobs/manager.py`, patrón
  `convert_chd`/`download_dats`) — a escala de biblioteca real, cientos de
  conversiones JPG→PNG (~1 proceso PowerShell cada una) tardan minutos;
  síncrono habría bloqueado el servidor HTTP, con riesgo de retrasar el
  watcher de sync (Pilar 3, nunca debe bloquearse). `POST
  /api/publish-retroarch-thumbnails` arranca el job, `GET
  /api/publish-retroarch-thumbnails-status` reporta progreso/resultado.
- 9 tests nuevos (`tests/test_retroarch_thumbnails.py`,
  `tests/test_publish_retroarch_thumbnails_job.py`), 1367 tests totales.

**Hallazgo real durante la verificación en vivo contra la biblioteca de esta
máquina**: el primer intento de conversión falló en masa
(`FileNotFoundError` resolviendo `powershell.exe`) porque se probó desde un
proceso lanzado con el `PATH` restringido de la sesión de herramientas de
Claude Code, no el `PATH` normal de Windows — no es un bug del código. Al
relanzar el servidor vía la tarea programada real (`RetroVault-AutoStart`,
que sí hereda el `PATH` completo del usuario) la conversión funcionó
correctamente.

**Pendiente, sin backlog ID todavía** (fuera de alcance de esta sesión): el
punto 4 original — ejecutar `generate_lpl_playlists()` y copiar el resultado
a `<RetroArch>/playlists/` (hoy solo escribe a
`library_root/.rommgr/playlists/`, staging sin desplegar).
