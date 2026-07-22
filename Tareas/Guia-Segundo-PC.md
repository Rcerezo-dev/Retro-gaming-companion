# Guía — Añadir un segundo PC al sync de saves (vía nube)

Objetivo: que las partidas y savestates aparezcan solas en el otro PC (otra
ciudad), usando el sync en la nube ya existente (rclone). **No hay que tocar
código ni sincronizar las bases de datos** — la arquitectura es hub-and-spoke:
cada máquina sincroniza contra el remoto y la nube es la fuente de verdad.

## Por qué NO se sincronizan las bases de datos

- El SQLite de cada PC es un índice local de SU biblioteca (rutas, escaneos).
  Se reconstruye con un scan; no hay nada que compartir.
- El `save_sync_log` (con `last_sync_at` por archivo) es **por máquina**:
  registra lo que ESA máquina vio del remoto la última vez. Compartirlo
  rompería la detección de conflictos (`sync/conflict_resolver.py`).
- Sincronizar un SQLite vivo por Dropbox corrompe la BD (WAL, escrituras
  parciales). Nunca.

## Pasos en el PC nuevo

1. **Instalar Retro Vault** (`RetroVault-Setup.exe` o clonar repo + conda).
2. **Instalar rclone** y conectar Dropbox desde la propia app: pestaña
   **Sync → Conectar Dropbox**. El asistente abre el navegador, inicias sesión
   en Dropbox, autorizas, y la app guarda el remoto sola (no hace falta API
   key propia: rclone usa su propia app OAuth registrada en Dropbox).
   - Alternativa por terminal: `rclone config` (el remoto debe llamarse igual
     que en el PC principal, p. ej. `dropbox:`).
   - Verificar: `rclone lsd dropbox:` debe listar las carpetas de saves.
3. **Configurar `config.toml`** con las mismas rutas remotas de saves/states
   que el PC principal (`saves_remote`, `states_remote`). El `local_dir`
   apunta a la carpeta de saves LOCAL de ese PC (donde escribe RetroArch).
4. **Configurar RetroArch** en ese PC: Savefile/Savestate Directory → la
   carpeta local del paso 3.
5. **Organizar la biblioteca con la herramienta** (scan + rename canónico).
   Requisito real: los ROMs deben llamarse igual en ambos PCs para que las
   rutas relativas de los saves coincidan — el renombrado No-Intro/Redump ya
   lo garantiza.
6. **Primer sync**: lanzar `rommgr` web → pestaña Sync → sync manual y revisar
   el plan antes de aplicar. Después, activar auto-sync si se quiere.

## Requisitos para que funcione bien

- **Relojes en hora** en ambos PCs (la detección de conflictos es por mtime,
  tolerancia 2 s). El NTP por defecto de Windows basta.
- **Ante conflicto** (ambos lados cambiaron desde el último sync): la
  herramienta NO sobreescribe — resolver a mano desde la UI. Regla de oro del
  proyecto: ante duda, backup primero.

## La Anbernic no cambia

Sigue sincronizando por ADB/SD contra el PC que tenga cerca; ese PC hace de
pasarela hacia la nube. Cualquier número de dispositivos puede colgar del
mismo remoto — no hay límite de 3 ni de ningún otro número.
