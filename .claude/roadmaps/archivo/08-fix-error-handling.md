# Roadmap 08 — `fix/error-handling`

**Rama:** `fix/error-handling`
**Base:** `develop`
**Prioridad:** 🟠 P2 (subida desde 🟡 P3 del plan original — el hallazgo 1 toca
el job más sensible del Pilar 3, no es limpieza cosmética)
**Esfuerzo estimado:** ~1-1.5 h (los pasos 1-4 son cambios de una línea cada
uno; el paso 5 es solo documentar una decisión pendiente, no implementarla)
**Riesgo:** Muy bajo — todos los fixes de código son aditivos (añaden logging,
no cambian ningún flujo de control ni el `job_result` que ya ve el usuario)

---

## Origen

`.claude/mejoras-por-rama.md` (sección 8) describía el problema en términos
genéricos y con referencias ya desactualizadas (`cable_sync_daemon.py` línea
322 — no existe esa línea con ese contenido hoy; `handlers/sync.py` línea 174
sí sigue existiendo, coincidencia). Siguiendo la regla del proyecto
"investigar antes de arreglar" (`CLAUDE.md`) — y el precedente del roadmap 07
(`fix/remove-debug-prints`), cuyo problema original ya no existía — se releyó
uno a uno **todo** bloque `except Exception` real de los 4 archivos
mencionados (33 bloques en total) antes de escribir este roadmap, en vez de
confiar en la descripción vieja.

**Resultado de la relectura:** a diferencia del roadmap 07, aquí sí hay
hallazgos reales — 5, de severidad baja a alta — mezclados con un conjunto
mayor (24 bloques) que ya está bien manejado y no se toca. El criterio usado
para separarlos no fue "¿es `except Exception`?" (amplio no es
automáticamente un bug) sino: **¿puede el usuario/operador enterarse de que
algo falló cuando de verdad importa?** — con el Pilar 3 (sync de saves,
"cualquier bug aquí es prioridad absoluta" según `CLAUDE.md`) como el listón
más alto.

El punto 3 del documento viejo ("`inbox_pipeline.py`: varios `.get()` sin
validación de claves") se descarta — **ya no aplica**. Los 17 `.get()` del
archivo o bien tienen default seguro (`options.get("scan", True)`, todos los
toggles de `_run_inbox_pipeline`) o están seguidos de un guard explícito
(`folder_name = _ES_PLATFORM_FOLDERS.get(...); if not folder_name: continue`,
línea 86-88). Ninguno puede producir un fallo silencioso.

### Hallazgos reales (por severidad)

**1. 🔴 Alto — `sync_cable.py:1413-1414`, el job runner de Cable Sync (Pilar 3) no deja rastro en el log del servidor**

```python
        except Exception as exc:
            job_result = {"error": str(exc)}
        finally:
            ...
            job_manager.finish("cable_sync", job_result)
```

Es el catch-all de más alto nivel de `_do_cable_sync.run()` — el job que
mueve saves/ROMs de verdad entre PC y Anbernic, tanto por ADB como por
filesystem/SD. Si algo revienta ahí que no sea uno de los `OSError`
puntuales ya capturados más abajo (esos sí están bien: cuentan en `errors`,
quedan en `_log`/`details`), el usuario ve `{"error": "..."}` en la UI pero
**el servidor no guarda ningún traceback** — nada que buscar en los logs si
el mensaje de `str(exc)` no basta para diagnosticar. Contraste directo con
el mismo patrón en `inbox_pipeline.py` (líneas 939 y 1305, ver más abajo),
que sí llama `logger.exception(...)` en el catch-all equivalente.

**2. 🔴 Alto — `cable_sync_daemon.py:100-106`, el pre-flight de reloj del auto-sync falla "hacia lo inseguro" en vez de fail-safe**

```python
            if config.sync.auto_sync_direction == "newest":
                from rom_manager.web.handlers.sync_cable import _build_sync_doctor

                try:
                    _doc = _build_sync_doctor(
                        config, None, serial, config.sync.auto_sync_android_path, "", quick=True
                    )
                except Exception:
                    _logger.debug("Pre-flight de reloj de auto-sync falló", exc_info=True)
                    _doc = {"skew_exceeded": False}
                if _doc.get("skew_exceeded"):
                    ...  # aborta el auto-sync, avisa en _auto_sync_status
                    continue
```

Si `_build_sync_doctor` (que hace una llamada ADB real,
`transport.device_epoch()`) falla por cualquier motivo — timeout, ADB
inestable, lo que sea — el código **asume que no hay desfase de reloj**
(`skew_exceeded: False`) y sigue adelante con el sync `"newest"` sin avisar a
nadie. Esto anula justo la protección que existe para evitar que un reloj
desincronizado (redondeo de FAT32/exFAT, hora mal puesta en la consola) haga
que `"newest"` sobrescriba en silencio una partida más nueva por el otro
lado. Comparar con el path MANUAL del mismo chequeo, que sí falla seguro:

```python
# sync_cable.py:314-321 (sync manual, mismo _build_sync_doctor)
    if use_adb and direction == "newest" and not dry_run:
        try:
            _doc = _build_sync_doctor(
                config, repository, adb_serial, android_path, pc_path_str, quick=True
            )
        except Exception as exc:
            ctx._send_json({"error": f"No se pudo comprobar el reloj de la consola: {exc}"})
            return
```

Mismo chequeo, mismo tipo de fallo, comportamiento opuesto: el manual aborta
con un error visible; el automático (que corre sin nadie mirando, disparado
solo por conectar el cable) sigue adelante como si todo estuviera bien. El
auto-sync es exactamente el caso donde el fail-safe importa más, no menos.

**3. 🟡 Medio-alto — `inbox_pipeline.py:1233-1249`, mover el archivo y actualizar la fila de BD no son atómicos**

```python
            try:
                _shutil.move(str(source_file), str(dest_file))
                # Update DB path. ZIP-ROUTE-FIX-2: ...
                dest_path_str = str(dest_file.resolve())
                with repository.batch() as conn:
                    cascade_delete_games_by_source_path(conn, dest_path_str, exclude_id=game_id)
                    conn.execute(
                        "UPDATE games SET source_path=?, original_filename=? WHERE id=?",
                        (dest_path_str, dest_file.name, game_id),
                    )
                organized += 1
            except Exception as exc:
                organize_errors.append(f"{source_file.name}: {exc}")
```

Si `_shutil.move` tiene éxito pero el `UPDATE`/`cascade_delete` que sigue
falla (SQLite bloqueada, disco lleno, lo que sea), el archivo físico ya está
en `dest_file` pero la fila de `games` **sigue apuntando al `source_path`
viejo dentro del Inbox, que ya no existe**. Viola "toda operación sobre
archivos se registra en SQLite" (`CLAUDE.md`) de forma silenciosa: el
usuario solo ve `"nombre.zip: <mensaje de excepción sqlite>"` en
`organize_errors` — nada le dice que el archivo SÍ se movió y que ahora hay
un descuadre real entre disco y BD para ese juego concreto. No es un caso de
"excepción tragada" (el error llega a la UI), es un **hueco de atomicidad**
con un mensaje de error que no transmite el riesgo real.

**4. 🟡 Medio — dos bucles del daemon de auto-sync registran su propio
catch-all con `debug()` plano, sin traceback**

```python
# cable_sync_daemon.py:418-420 (bucle ADB, envuelve TODO el ciclo de sondeo)
        except Exception as exc:
            # Never crash the daemon
            _logger.debug("Auto-sync daemon exception: %s", exc)

# cable_sync_daemon.py:650-651 (bucle SD, mismo patrón)
        except Exception as exc:
            _logger.debug("SD sync daemon exception: %s", exc)
```

Ambos son el `except` más externo de un `while True` que corre para
siempre en background. Si algo no previsto revienta ahí en cada ciclo de
sondeo (no el caso ya cubierto explícitamente en la línea 52, "adb no
disponible", que sí tiene su propio comentario y `continue`), el auto-sync
puede quedarse mudo indefinidamente — sin logging visible a nivel normal
(DEBUG suele estar apagado por defecto) y sin traceback ni con `exc_info`.
El "watchdog" del hilo sigue vivo (nunca se cae, por diseño — "Never crash
the daemon"), pero nada le dice al operador que dejó de funcionar de verdad.

**5. 🟢 Bajo — dos job runners de solo-lectura tienen el mismo hueco que el
hallazgo 1, pero sin riesgo de datos**

- `handlers/sync.py:174` (`_do_ra_check.run()`, job `"ra_check"`)
- `sync_cable.py:1499` (`_do_tree_diff.run()`, job `"tree_diff"`)

Mismo patrón (`except Exception as exc: job_result = {"error": str(exc)}`
sin `logger.exception`) que el hallazgo 1, pero ambos son herramientas de
diagnóstico de solo lectura (comprobar logros RA, comparar árboles PC vs
consola) — ningún archivo ni fila de BD está en juego si fallan. Se incluyen
por consistencia, no por urgencia.

### Confirmado correcto tal cual (no se toca)

El resto de los 33 bloques — `_sql_log`/actualización de barra de
progreso/cierre de fichero de log/limpieza de carpeta temporal en
`cable_sync_daemon.py` (líneas 52, 207, 409, 423, 504, 588, 620, 654),
`sync_cable.py` (75, 95, 224, 405, 713, 845, 1231, 1377, 1385, 1419) e
`inbox_pipeline.py` (743, 1270, 1278) — ya son correctos: son operaciones
genuinamente best-effort (una segunda copia del evento en SQLite que no es
la fuente de verdad, refrescar una barra de progreso, cerrar un fichero,
borrar una carpeta temporal ya vacía) y casi todos ya pasan `exc_info=True`
o cuentan el fallo en `errors`/`details`, visibles al usuario. `sync_cable.py:75,95`
son handlers HTTP síncronos que devuelven el error directamente en la
respuesta — el llamador lo ve al instante, no hace falta más.
`inbox_pipeline.py:1270` incluso ya usa `.warning(exc_info=True)`, mejor que
el resto. `sync_cable.py:845` cuenta el error en `errors`+`_log`, correcto.
Ampliar excepciones específicas aquí (`OSError` en vez de `Exception`) no
aporta nada real — no hay ningún caso real de un `except Exception` amplio
que esté ocultando un bug de programación en vez de un fallo esperado de
I/O/red.

---

## Objetivo

Cerrar los 4 huecos de logging/atomicidad reales (hallazgos 1, 2, 4, 5) con
cambios mínimos y aditivos — añadir logging con traceback donde falta, y en
el caso 2 hacer que el auto-sync falle tan seguro como ya falla el sync
manual. El hallazgo 3 (atomicidad archivo+BD) se **documenta pero no se
implementa** en esta rama — cambiar el comportamiento ahí (¿reintentar el
UPDATE? ¿revertir el `move`? ¿solo mejorar el mensaje?) es una decisión de
diseño que toca el Pilar 2 de lleno y merece su propia conversación, no un
efecto colateral de una rama de "logging".

No tocar: ningún `except Exception: pass`/`.debug()` de la lista "confirmado
correcto" de arriba — no hay ninguno realmente roto ahí, cambiarlos sería
ruido sin beneficio.

---

## Pasos

### Paso 1 — `sync_cable.py:1413`, loggear el catch-all de Cable Sync

```python
# Antes:
        except Exception as exc:
            job_result = {"error": str(exc)}
        finally:

# Después:
        except Exception as exc:
            _logger.exception("Cable Sync error: %s", exc)
            job_result = {"error": str(exc)}
        finally:
```

Mismo patrón exacto que ya usa `inbox_pipeline.py:939`/`:1305` para su propio
catch-all de nivel de job — no es un patrón nuevo, es alinear este job con
el que ya existe en el resto del proyecto.

### Paso 2 — `cable_sync_daemon.py:100-106`, el pre-flight de reloj del auto-sync falla seguro

```python
# Antes:
                try:
                    _doc = _build_sync_doctor(
                        config, None, serial, config.sync.auto_sync_android_path, "", quick=True
                    )
                except Exception:
                    _logger.debug("Pre-flight de reloj de auto-sync falló", exc_info=True)
                    _doc = {"skew_exceeded": False}
                if _doc.get("skew_exceeded"):

# Después:
                try:
                    _doc = _build_sync_doctor(
                        config, None, serial, config.sync.auto_sync_android_path, "", quick=True
                    )
                except Exception as exc:
                    _logger.warning(
                        "Auto-sync: no se pudo comprobar el reloj de la consola — "
                        "abortando este ciclo (%s)",
                        exc,
                        exc_info=True,
                    )
                    _state._auto_sync_status = {
                        "state": "idle",
                        "last_device": serial,
                        "last_sync_at": _state._auto_sync_status.get("last_sync_at"),
                        "last_error": f"No se pudo comprobar el reloj de la consola: {exc}",
                    }
                    continue
                if _doc.get("skew_exceeded"):
```

Mismo criterio de "fail-safe" que el path manual (`sync_cable.py:319-321`):
si no se puede confirmar que el reloj está bien, no se asume que sí — se
salta este ciclo de auto-sync y se deja constancia visible en
`_auto_sync_status["last_error"]` (mismo campo que ya lee la UI para el caso
de skew real detectado, línea 118 más abajo). El siguiente ciclo de sondeo
(8s después, `_POLL_INTERVAL`) lo reintentará solo.

**Nota de alcance**: este `if` solo se ejecuta cuando
`config.sync.auto_sync_direction == "newest"` — las direcciones
`pc_to_anbernic`/`anbernic_to_pc` fijas no dependen de comparar mtimes entre
ambos lados, así que no les afecta este pre-flight ni este fix.

### Paso 3 — `cable_sync_daemon.py:418-420` y `:650-651`, traceback real en los catch-all de los daemons

```python
# Antes (bucle ADB, línea 418-420):
        except Exception as exc:
            # Never crash the daemon
            _logger.debug("Auto-sync daemon exception: %s", exc)

# Después:
        except Exception as exc:
            # Never crash the daemon — pero sí dejar rastro con traceback,
            # o un fallo repetido en cada ciclo de sondeo queda invisible.
            _logger.warning("Auto-sync daemon exception: %s", exc, exc_info=True)
```

```python
# Antes (bucle SD, línea 650-651):
        except Exception as exc:
            _logger.debug("SD sync daemon exception: %s", exc)

# Después:
        except Exception as exc:
            _logger.warning("SD sync daemon exception: %s", exc, exc_info=True)
```

Se sube a `.warning()` (visible con la config de logging por defecto,
a diferencia de `.debug()`) y se añade `exc_info=True` en ambos — el hilo
sigue sin caerse nunca (mismo `while True` de siempre, ningún cambio de
control de flujo), solo deja de ser indetectable si algo falla de verdad.

### Paso 4 — `handlers/sync.py:174` y `sync_cable.py:1499`, alinear con el patrón de `inbox_pipeline.py`

```python
# handlers/sync.py — antes:
        except Exception as exc:
            job_result = {"error": str(exc)}
        finally:
            job_manager.finish("ra_check", job_result)

# Después:
        except Exception as exc:
            logger.exception("RA check error: %s", exc)
            job_result = {"error": str(exc)}
        finally:
            job_manager.finish("ra_check", job_result)
```

`handlers/sync.py` no tiene todavía un `logger`/`_logger` de módulo — añadir
`import logging` + `logger = logging.getLogger(__name__)` a nivel de módulo
(mismo patrón que el resto de `handlers/*.py`).

```python
# sync_cable.py:1499 — antes:
        except Exception as exc:
            job_result = {"error": str(exc)}
        finally:
            job_manager.finish("tree_diff", job_result)

# Después:
        except Exception as exc:
            _logger.exception("Tree diff error: %s", exc)
            job_result = {"error": str(exc)}
        finally:
            job_manager.finish("tree_diff", job_result)
```

`sync_cable.py` ya tiene `_logger` de módulo (línea 21) — solo añadir la
línea.

### Paso 5 — Documentar el hallazgo 3, sin implementarlo

Añadir una entrada al backlog (`Tareas/backlog.md`, sección Pilar 2 o una
nueva si no encaja en ninguna existente) citando
`inbox_pipeline.py:1233-1249` con el escenario exacto de arriba, para que se
decida aparte si el fix es "reintentar el UPDATE en un `finally` separado",
"revertir el `_shutil.move` si el UPDATE falla" o "solo mejorar el mensaje
de `organize_errors` para que nombre explícitamente el riesgo (`archivo
movido a {dest_file} pero la base de datos no se pudo actualizar — revisar
a mano`)". No tocar código en este paso.

### Paso 6 — Tests

- `tests/test_cable_sync_*.py` (o uno nuevo,
  `test_cable_sync_error_logging.py`): monkeypatch algo dentro del `try` de
  `_do_cable_sync.run()` para forzar una excepción no capturada más abajo
  (p.ej. hacer que `transport.ls_recursive` lance `RuntimeError`) y
  confirmar con `caplog`/`monkeypatch` sobre `_logger.exception` que se
  llama — no solo que `job_result["error"]` queda poblado (eso ya lo cubren
  tests existentes).
- Test equivalente para `_do_ra_check` y `_do_tree_diff` (mismo patrón,
  forzar una excepción y confirmar `logger.exception`/`_logger.exception`).
- `tests/test_cable_sync_clock_guard.py` (ya existe, cubre el guard de
  reloj del path manual — usarlo de plantilla): nuevo caso para el daemon
  de auto-sync (`cable_sync_daemon.py`) donde `_build_sync_doctor` lanza —
  confirmar que el ciclo se salta (`continue`, no sigue con el sync) y que
  `_state._auto_sync_status["last_error"]` queda con un mensaje, en vez de
  proceder con `skew_exceeded=False`.
- Para el Paso 3 (daemons): más difícil de testear de forma aislada porque
  viven dentro de un `while True` con `sleep` real — si no hay ya un patrón
  de test para estos bucles, verificar manualmente con `caplog` invocando
  un solo ciclo del cuerpo del bucle extraído a una función testeable, o
  aceptar cobertura solo por inspección si extraerlo es demasiado invasivo
  para el alcance de esta rama.

### Paso 7 — Verificación

```bash
python -m pytest tests/ -q
ruff check src/rom_manager/web/handlers/sync.py src/rom_manager/web/handlers/sync_cable.py src/rom_manager/web/cable_sync_daemon.py
ruff format --check src/rom_manager/web/handlers/sync.py src/rom_manager/web/handlers/sync_cable.py src/rom_manager/web/cable_sync_daemon.py
```

---

## Fuera de alcance (documentado aparte, no entra en esta rama)

- Hallazgo 3 (atomicidad `_shutil.move` + `UPDATE` en `inbox_pipeline.py`) —
  decisión de diseño pendiente, ver Paso 5.
- Los 24 bloques de la lista "confirmado correcto tal cual" — no son bugs,
  cambiarlos es ruido.
- Cualquier refactor de `JobManager` para centralizar el logging de
  excepciones (p.ej. que `start()` envuelva `fn` automáticamente) — no es
  viable sin cambiar la firma de cada `run()` para que deje de capturar
  `Exception` él mismo (si el caller ya la captura, el wrapper del manager
  nunca ve la excepción) — cambio estructural mayor, no encaja en una rama
  de "1-1.5 h, riesgo muy bajo".

---

## Checklist

- [ ] Paso 1 — `sync_cable.py:1413` loggea con `_logger.exception`
- [ ] Paso 2 — pre-flight de reloj del auto-sync falla seguro (aborta el ciclo, no asume `skew_exceeded=False`)
- [ ] Paso 3 — ambos catch-all de los daemons suben a `.warning(exc_info=True)`
- [ ] Paso 4 — `handlers/sync.py:174` y `sync_cable.py:1499` loggean con traceback
- [ ] Paso 5 — hallazgo 3 documentado en `Tareas/backlog.md`, sin implementar
- [ ] Paso 6 — tests nuevos, suite completa en verde
- [ ] Paso 7 — ruff + format limpios
- [ ] Commit en rama, PR a `develop`
