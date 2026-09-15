# Roadmap 19 — `feature/device-profile-loose-data`

**Rama:** `feature/device-profile-loose-data`
**Base:** `develop`
**Prioridad:** 🟡 P3 — cola pequeña de una feature ya mayormente completa (Perfil de dispositivo, epic → #238)
**Esfuerzo estimado:** S (~2 h — una decisión de diseño + un tipo de fuente nuevo, reutilizando infraestructura ya existente)
**Riesgo:** Bajo — es sync de archivos de configuración/datos de usuario, no de saves de partida (Pilar 3)

---

## Origen

`DEVPROFILE-8b`/`DEVPROFILE-9` (`Tareas/backlog.md`, epic "Perfil de
dispositivo — provisioning con un botón" → #238). El diseño completo de la
feature ya está hecho y en su mayoría implementado — ver
`Tareas/Roadmap-DEVPROFILE-1-4.md` y `Tareas/Roadmap-DEVPROFILE-5-6.md`
(convención de roadmap distinta a `.claude/roadmaps/`, específica de esta
feature, con su propio detalle de diseño ya verificado contra el código
real). Este roadmap NO repite ese diseño — cubre solo el hueco pequeño que
quedó suelto.

**El hueco**: `SyncSource`/`sync_saves()` (`sync/`) solo sincroniza
**directorios completos**, nunca un archivo suelto (ver nota en
`_TIER_A_SUBDIRS`, `services/device_profile.py:29-31`). Dos grupos de datos
de usuario son archivos sueltos, no carpetas:

- **`DEVPROFILE-8b`**: `library_pc.db`/`library_android.db` — las BDs SQLite
  en sí.
- **`DEVPROFILE-9`**: `content_history.lpl` (recientes), `content_favorites.lpl`,
  `.lrtl` (playtime, ver `MEJ-1`), credenciales RA (`cheevos_*`, en
  almacenamiento cifrado).

Ambos bloqueados por la misma decisión de diseño pendiente: **single-file
source kind nuevo** vs. **apuntar `SyncSource` a la carpeta contenedora
(`.rommgr`) con un filtro de extensión** (reutilizando `sync_saves`, que trae
lógica de conflictos pensada para saves de partida — merge/resolución por
mtime —, no para un blob de BD o un `.lpl` de lista de recientes, donde esa
lógica probablemente no aplica igual).

---

## Objetivo

Decidir el mecanismo y sincronizar los dos grupos de archivos sueltos como
parte del Perfil de dispositivo, sin reimplementar la lógica de conflictos
de saves para un caso que no es un save.

---

## Pasos

### Paso 1 — Decisión de diseño (bloqueante)

Presentar al usuario los dos caminos:
- **(a) Single-file source kind nuevo**: `SyncSource` gana un modo
  "archivo único" además de "carpeta completa" — más limpio conceptualmente
  (una BD SQLite o un `.lpl` no necesitan resolución de conflictos por
  archivo individual dentro de un directorio, solo "¿cuál es más reciente,
  cuál gano?"), pero es código nuevo en el motor de sync compartido.
- **(b) Reutilizar `sync_saves` apuntando a `.rommgr` con filtro de
  extensión**: cero código nuevo en el motor de sync, pero hereda lógica de
  conflictos pensada para saves de partida (probablemente over-engineered
  para este caso, y puede comportarse de forma no obvia si el usuario espera
  "restaurar" en vez de "mergear").

Recomendación implícita en el propio hallazgo original (ver
`DEVPROFILE-8`, ya parcialmente implementado): el proyecto ya trata
`SyncSource` de carpeta completa como el patrón por defecto para todo lo que
no es un save de partida (los DATs de catálogo ya se sincronizan así,
`detect_data_sources()`) — la opción (a) es más consistente con "perfil =
restore, no merge" (diferencia ya documentada entre Perfil de dispositivo y
saves en la cabecera de la sección del backlog), pero la decisión final es
del usuario.

### Paso 2 — Implementar el mecanismo decidido

Si (a): nuevo tipo de fuente en `services/device_profile.py`
(`_TIER_A_SUBDIRS` o equivalente), con su propio manejo simple de
"¿cuál es más reciente, restaurar esa versión?" (no merge) — consistente con
que el Perfil de dispositivo ya es direccional (restore), no bidireccional
como los saves.

Si (b): extender `SyncSource`/`sync_saves()` para aceptar un filtro de
extensión sobre `.rommgr` como raíz, verificando que el comportamiento de
"ganador más reciente" sigue siendo razonable para una BD SQLite completa
(un archivo, no fragmentos comparables como los saves).

### Paso 3 — Tokenización de rutas para los archivos nuevos

Reutilizar el tokenizador ya existente (`services/path_tokenizer.py`,
`DEVPROFILE-3`, ya implementado) para que `library_pc.db`/`content_history.lpl`
etc. se guarden con rutas portables (`{PROJECT_ROOT}`, ya usado para los
DATs en `DEVPROFILE-8`) en vez de una ruta absoluta fija.

### Paso 4 — Wiring en `rommgr restore` / detección de perfil

`_handle_device_profile_detect()` y `rommgr restore` (`DEVPROFILE-5`, ya
implementado) deben incluir los nuevos archivos en el manifiesto/backup
automáticamente una vez añadidos como fuente — verificar que no hace falta
tocar esos comandos si el mecanismo elegido en el Paso 1 encaja en el mismo
patrón que ya usan los DATs.

### Paso 5 — Tests

- Fuente nueva (BD o `.lpl`) detectada correctamente por
  `detect_data_sources()`/`_handle_device_profile_detect()`.
- Restauración real (mock) en un PC nuevo: el archivo aparece en la ruta
  correcta tras `rommgr restore`.

### Paso 6 — Verificación

```bash
python -m pytest tests/ -q
ruff check src/rom_manager/services/device_profile.py src/rom_manager/sync/
```

---

## Fuera de alcance

- Rediseñar el motor de sync de saves en sí — este roadmap solo añade
  cobertura para 2 grupos de archivos sueltos, no toca `sync_saves()` para
  el caso de saves de partida real (Pilar 3, fuera de alcance por diseño).
- Credenciales RA cifradas de Android (`cheevos_*`) — mencionadas en
  `DEVPROFILE-9` pero su viabilidad depende de que sean legibles sin root
  (mismo límite ya documentado en `DEVPROFILE-0`); confirmar accesibilidad
  antes de comprometerse a sincronizarlas.

---

## Checklist

- [ ] Paso 1 — decisión de diseño confirmada por el usuario
- [ ] Paso 2 — mecanismo implementado
- [ ] Paso 3 — tokenización de rutas para los archivos nuevos
- [ ] Paso 4 — wiring en detección/restore
- [ ] Paso 5 — tests nuevos
- [ ] Paso 6 — suite completa + ruff limpios
- [ ] Commit en rama, PR a `develop` — pendiente, requiere confirmación explícita del usuario
