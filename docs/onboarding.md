# Onboarding — tus primeros 30 minutos en el código

Guía de orientación para desarrolladores nuevos. Prerrequisitos: haber hecho el
setup de [`CONTRIBUTING.md`](../CONTRIBUTING.md). Si algún término retro te suena
a chino (DAT, CHD, `.cue`…), tenlo abierto al lado: [`glossary.md`](glossary.md).

---

## 1. Qué es esto en una frase

Una app local (Python stdlib + SPA vanilla JS) que convierte una carpeta caótica
de ROMs en una biblioteca identificada por hash, con metadatos y carátulas, y que
mantiene las partidas guardadas sincronizadas entre el PC y una consola Android.

## 2. El pipeline central (el corazón del dominio)

Casi todo el código sirve a este flujo; entiéndelo y el resto encaja:

```
scan    → hashea cada archivo (SHA1+MD5+CRC32) y lo inventaría en SQLite
match   → cruza los hashes contra catálogos DAT (No-Intro/Redump) → título canónico
plan    → calcula qué renombrados harían falta (sin tocar nada)
apply   → ejecuta los renombrados de forma atómica, con rollback y saves incluidos
scrape  → descarga metadatos y carátulas (ScreenScraper) → gamelist.xml
sync    → saves ↔ nube (rclone) o ↔ consola por USB (adb)
```

Regla de oro del proyecto: **`plan` siempre antes de `apply`**, y ninguna
operación destructiva sin backup ni registro en SQLite (`file_operations`).

Dos variantes empaquetan ese mismo flujo: el **Inbox**
(`web/inbox_pipeline.py`) lo encadena entero para una carpeta de entrada
(extract → scan → match → rename → organize → cleanup), y el **zip_router**
(`web/zip_router.py`) coloca en un solo paso los ZIPs sueltos que el junk-scan
identifica por el CRC32 del header del ZIP, sin descomprimir (término
"ZIP-ROUTE" en el [glosario](glossary.md)); los ZIPs arcade van directos a
`arcade\` porque extraerlos los rompería — el ZIP es el ROM.

## 3. Mapa de lectura del código (en este orden)

| Paso | Archivo | Qué aprendes |
|------|---------|--------------|
| 1 | `src/rom_manager/cli.py` | Todos los comandos (scan, plan, apply, serve…) y qué módulo invoca cada uno. Índice ejecutable del proyecto |
| 2 | `src/rom_manager/config.py` | `AppConfig` y sus sub-configs; todo recibe config por parámetro (no hay singleton) |
| 3 | `src/rom_manager/scanner/rom_scanner.py` → `hashing/` → `database/repository.py` | La mitad "inventario": cómo un archivo acaba siendo una fila en `games` |
| 4 | `src/rom_manager/catalog/matcher.py` → `planner/operation_planner.py` → `renamer/file_renamer.py` | La mitad "identificar y renombrar": match por SHA1 → plan → apply atómico |
| 5 | `src/rom_manager/web/server.py` → `router.py` → `handlers/scan.py` | Cómo una request HTTP llega a un handler y cómo se lanza un job en background (`web/jobs/manager.py`) |
| 6 | `src/rom_manager/web/static/js/main.js` + `js/tabs/scan.js` | El otro lado del cable: polling de `/api/job-status` cada 2s y pintado de progreso |

Flujo de una request web, de punta a punta:

```
navegador → server.py (ThreadingHTTPServer) → router.dispatch()
          → web/handlers/<dominio>.py        (router fino: parsea y responde)
          → services/ o builders/            (lógica de negocio / respuesta pura)
          → database/repository.py           (SQLite)
Los jobs largos van a un thread registrado en web/jobs/manager.py (JobManager);
el frontend los sigue con GET /api/job-status.
```

La referencia completa de módulos está en
[`architecture/architecture.md`](architecture/architecture.md).

## 4. Ver el sistema funcionando sin ROMs reales

No necesitas una biblioteca real para desarrollar:

```bash
# E2E sintético: crea ROMs falsas en un tmp dir y ejecuta
# setup → scan → integridad BD → plan → prune → schema → config roundtrip
python scripts/e2e_integration_test.py

# Suite de tests (usa BD real en tmp_path, sin mocks)
pytest -q
```

Con Claude Code hay atajos equivalentes: `/test-pipeline` (scan → match → plan
sintético) e `inbox-watchdog` (valida el pipeline del Inbox).

Para la UI: `rommgr serve` (o `scripts\rommgr.cmd serve`) → `http://127.0.0.1:7777`.
El primer arranque sin `config.toml` te lleva por un wizard; apunta `library_root`
a una carpeta de prueba con 2-3 archivos con extensión de ROM (p. ej. `.gba`).

## 5. Cuando algo falla

El **Debug Playbook** de [`Tareas/backlog.md`](../Tareas/backlog.md) es la tabla
"síntoma → dónde mirar" mantenida por el proyecto (DBG-1…DBG-7). Empieza siempre
por ahí. Resumen de los dos trucos más usados:

- Logs en vivo: lanzar `serve` desde terminal — stdout muestra requests, errores y jobs.
- Jobs "colgados": DevTools → Network → `/api/job-status`; si falta `result_ts`
  en la respuesta, el bug está en el cierre del job, no en el frontend.

## 6. Los tests como documentación

`tests/` es la especificación viva. Los más didácticos para empezar:

| Test | Qué documenta |
|------|---------------|
| `test_operation_planner.py` | Qué renombrados se planifican y qué cuenta como conflicto |
| `test_cue_validator.py` | La regla PSX: el `.cue` referencia los `.bin` por nombre — el set viaja junto e intacto |
| `test_catalog_matcher.py` | Niveles de confianza del match (high/medium/low) |
| `test_conflict_resolver.py` | Política de conflictos del sync (newest/keep_pc/…) |
| `tests/web/` | Handlers HTTP con servidor real |

## 7. Tu primer cambio

1. Elige una tarea de `Tareas/backlog.md` (las MEJ-* suelen ser autocontenidas).
2. Rama desde `develop`, código + test, `ruff` + `pytest` en verde.
3. PR a `develop` con el ID de la tarea — checklist completo en `CONTRIBUTING.md`.
