# DEVPROFILE-5/6 — Botones de restauración (PC / Android)

> Diseñado 2026-09-01. Ver `Tareas/backlog.md` sección `DEVPROFILE` para el
> estado de cada tarea — este documento es el detalle de diseño, no se edita
> tarea a tarea. Continúa `Tareas/Roadmap-DEVPROFILE-1-4.md` (1-4, ✅) — este
> documento asume que `services/device_profile.py`
> (`detect_tier_a_sources`/`export_profile_sources`/`import_profile_sources`)
> y la pantalla "Perfil del dispositivo" en Settings ya existen (PR #272).

## Contexto

Pilar 1 ("Primera vez") ya cubre "biblioteca caótica → organizada" en un PC
que ya tiene RetroVault funcionando. Lo que falta es el otro extremo: **un
PC nuevo** (o el mismo PC reinstalado) donde el usuario ya tiene su
biblioteca de ROMs en un disco externo, pero RetroArch/config/BIOS/
`config.toml` no existen todavía. Hoy eso se resuelve a mano o con
`rommgr init-config` (wizard interactivo, pregunta todo desde cero).
DEVPROFILE-5 sustituye la parte de sync de ese wizard por un restore
automático desde el perfil ya guardado en la nube.

---

## 1. Hallazgo — hay un hueco real antes de poder implementar 5/6

`DEVPROFILE-4` está ✅ en el backlog, pero solo cubre la mitad del título
("Manifiesto Tier A **+ backup del perfil al remoto**"):

- `detect_tier_a_sources()` / `export_profile_sources()` /
  `import_profile_sources()` (`services/device_profile.py`) son **funciones
  puras** — construyen y leen la estructura del manifiesto en memoria, pero
  ninguna lo escribe a un archivo ni lo sube a la nube.
- Verificado con `grep -rln "export_profile_sources\|import_profile_sources" src/`
  → solo aparecen en `device_profile.py` mismo y en los tests. **Cero
  llamadores en producción.**

Así que antes de que `rommgr restore` pueda descargar un perfil, tiene que
existir algo que lo suba. Eso es el primer sub-paso de este diseño (§3, 5a)
— no reabre DEVPROFILE-4 (ya cerrada), simplemente el trabajo que faltaba
vive aquí.

---

## 2. Estado real del código reutilizable (verificado)

**El motor de sync bidireccional ya existe y hace exactamente lo que
"restaurar Tier A" necesita** — no hace falta descarga especializada:

```python
# cli.py:832 `rommgr sync --apply` y web/handlers/sync_cloud.py:280 _do_sync
sources = build_cloud_sync_sources(config)   # incluye config.sync.sync_sources
for source in sources:
    sync_saves(Path(source.local_dir), saves_remote=source.remote, ...)
```

`sync_saves()` ya es bidireccional (sube lo que falta en la nube, baja lo
que falta en local) — una vez `config.toml` tiene los `sync_sources`
correctos apuntando a las carpetas Tier A de este PC, `rommgr sync --apply`
descarga sus contenidos sin código nuevo.

**Gotcha verificado** (`cli.py:855`, mismo patrón en `_do_sync`):
```python
if not saves_dir.exists():
    print(f"[ERROR] {source.name}: directorio no encontrado...")
    continue  # ese source se salta entero, no se crea
```
En un PC nuevo, carpetas como `system/` (BIOS) casi seguro no existen
todavía — **`rommgr restore` tiene que crear cada `local_dir` con
`mkdir(parents=True)` antes de llamar a sync**, o esos sources se saltan en
silencio.

**Tier B — verificado, no es uniforme:**
| Generador | Necesita DB (`repository`) | Necesita solo `cores/` |
|---|---|---|
| `esde/systems_generator.py::generate_es_systems_xml(cores_dir, output_path)` | No | Sí — ya usado en `/api/generate-es-systems` |
| `utils/lpl_generator.py::generate_lpl_playlists(library_root, repository, ...)` | **Sí** (`SELECT ... FROM games`) | — |

`generate_lpl_playlists` depende de la tabla `games`, que solo existe tras
un `scan` (pilar 1, ya un flujo separado) — **no es parte de "Tier B tras
restaurar"**, es posterior a que el usuario re-escanee su biblioteca (o a
DEVPROFILE-8 si se restaura la BD en vez de rehashear). Este ticket solo
regenera `es_systems.xml` — lo demás sale gratis cuando el usuario haga su
primer scan.

**BIOS checker — ya devuelve justo lo necesario para "reportar lo que
falta":**
```python
# detection/bios_checker.py:66 check_bios(search_dirs) -> list[dict]
# ya usado en GET /api/bios-status con los 3 search_dirs correctos
# (library_root, library_root/bios, retroarch_path/../system)
```

**`download-tools.ps1`** ya existe (`scripts/download-tools.ps1`) y
descarga `rclone`/`adb`/`chdman` a `tools/` si faltan — es un script
externo, `rommgr restore` solo necesita decirle al usuario que lo corra
antes (o comprobar que los binarios existen y avisar si no).

---

## 3. Desglose propuesto

- **5a — Exportar el perfil al remoto** — ✅ 2026-09-01 (cierra el hueco de
  §1). `save_profile_manifest(sources, roms_dir, saves_dir, system_dir,
  transport, remote_base)` en `device_profile.py`: serializa con
  `export_profile_sources()` (ya existía) a JSON temporal y sube con
  `RcloneTransport.upload()` — **no hizo falta un método nuevo**: pasando
  extensiones vacías + `fallback_remote=remote_base`, `upload()` ya
  enruta cualquier archivo directo al fallback (`_resolve_remote()`,
  camino ya cubierto por `test_upload_unknown_ext_falls_back_to_fallback_remote`).
  Escribe en `<remote_base>/device-profile.json`. Handler
  `_handle_save_device_profile_manifest()` (`web/handlers/system.py`) +
  ruta `POST /api/device-profile-save-manifest`
  (`web/handlers/esde/system.py`) + botón manual "Guardar copia del perfil
  en la nube" en el panel de Settings de DEVPROFILE-4a (PR #272),
  `saveDeviceProfileManifest()` en `js/tabs/esde.js`. Sube
  `config.sync.sync_sources` (lo ya confirmado, no los candidatos sin
  guardar). 6 tests nuevos (`tests/test_device_profile.py`) — sin mocks
  para el camino de error real (rclone binario inexistente → `RcloneError`
  capturado limpio). **No probado contra el remoto real** (Dropbox) —
  deliberado, ver `feedback_config_toml_manual_testing` en memoria: un
  test end-to-end habría escrito de verdad en la nube del usuario sin que
  lo pidiera.
- **5b — `rommgr restore` (nuevo comando CLI)**: descarga el manifiesto
  (`RcloneTransport.download`, ya existe) → pide `roms_dir`/`saves_dir`/
  `system_dir` de este PC (puede reusar los `_ask()` de `wizard.py`, o
  detectar `library_root` como ya hace el wizard) → `import_profile_sources()`
  (ya existe) resuelve los tokens contra esas rutas → escribe `config.toml`
  reusando `write_config_toml()` (ya genérico, ya soporta `[[sync.sources]]`
  como en DEVPROFILE-4a).
- **5c — Crear directorios + `rommgr sync --apply`**: `mkdir(parents=True)`
  de cada `local_dir` resuelto (ver el gotcha de §2) y then invocar el
  mismo camino que `rommgr sync --apply` (llamada directa a la función, no
  un subproceso) para bajar el contenido real de Tier A.
- **5d — Regenerar Tier B**: llamar a `generate_es_systems_xml()` si ES-DE
  está instalado (mismo detector que `_handle_esde_status`). No incluye
  `generate_lpl_playlists` (ver §2, depende de DB/scan).
- **5e — `bios_checker` + reporte final**: `check_bios()` con los 3
  `search_dirs` ya usados por `/api/bios-status`, imprimir/loggear lo que
  falta (BIOS requerido no encontrado) como resumen final de `rommgr
  restore`.
- **5f — Disparador**: comando CLI (`rommgr restore`) es el mínimo viable
  (headless, scripteable) — decidido en §5. Un botón en Settings puede
  esperar a que el CLI funcione y esté probado.

DEVPROFILE-6 (botón Android) es más pequeño porque no puede tocar
`retroarch.cfg` (DEVPROFILE-0): solo core options/remaps/BIOS vía el mismo
`sync_sources` una vez el usuario hace login en Dropbox en la consola — se
diseña después de que 5 esté probado en PC, para reusar lo aprendido.

---

## 4. Riesgos / cosas a no automatizar sin confirmar

- **Sobrescribir un `config.toml` existente** — igual que `wizard.py` ya
  pregunta "¿Sobreescribir?" antes de tocar uno existente, `rommgr restore`
  debe hacer lo mismo (CLAUDE.md: "Nunca eliminar ni sobreescribir sin
  política de conflictos documentada").
- **Credenciales en el manifiesto** — si el perfil llega a incluir
  ScreenScraper/RA (§5, pregunta abierta), viajarían en texto plano dentro
  de un JSON en la nube. Necesita decisión explícita del usuario, no un
  default silencioso.
- **`rommgr sync --apply` sin dry-run previo** — el patrón ya establecido
  en el resto del proyecto es dry-run por defecto (`--apply` para
  confirmar). `rommgr restore` debería mostrar qué va a bajar antes de
  escribir, mismo espíritu.

---

## 5. Preguntas para el usuario — resueltas 2026-09-01

1. **¿Dónde vive el manifiesto en el remoto?** ✅ `<remote_base>/device-profile.json`
   (mismo `remote_base` que ya deriva `_handle_device_profile_detect`, p. ej.
   `dropbox:RetroSync/device-profile.json`).
2. **¿Qué lleva el manifiesto además de `sync_sources`?** ✅ Solo rutas
   tokenizadas — sin secretos. ScreenScraper/RA se piden de nuevo en el
   `rommgr restore` interactivo, como ya hace `wizard.py`.
3. **¿Cuándo se sube el manifiesto?** ✅ Botón manual en Settings (mismo
   patrón que DEVPROFILE-2d) — en el mismo panel "Perfil del dispositivo"
   de DEVPROFILE-4a (PR #272), junto a `saveDeviceProfileSources()`.
4. **¿CLI primero o botón en Settings primero?** ✅ CLI (`rommgr restore`,
   §5b-5e) primero — un botón en Settings puede envolverlo más adelante.

---

## Orden recomendado

`5a` (cierra el hueco de export) → `5b` (comando `restore`, config.toml) →
`5c` (mkdir + sync Tier A) → `5d` (Tier B: es_systems) → `5e` (bios_checker
+ reporte) → `5f` ya incluido en 5b como CLI. Probar todo el flujo en un
directorio de prueba (`tmp_path`-style, **nunca contra el `config.toml`
real** — ver `feedback_config_toml_manual_testing` en memoria) antes de
tocar el PC real. DEVPROFILE-6 después, reusando lo aprendido de 5.

**5b-5f implementados 2026-09-01** (`rommgr restore` en `cli.py`, ver
`Tareas/backlog.md` DEVPROFILE-5) — probado contra un `tmp_path` con
`RcloneTransport._run` fake (`tests/test_cli_restore.py`), nunca contra
rclone/Dropbox real. **Pendiente de validar en un PC realmente nuevo/vacío**
antes de darlo por probado en condiciones reales.
