# Roadmap 24 — Seguimiento de la auditoría de documentación (2026-09-20)

**Rama:** ninguna por defecto — son dos limpiezas pequeñas de documentación/
comentarios, sin lógica de producto. Si al ejecutar aparece algo que sí
merece rama propia, se corta en ese momento.
**Base:** `develop`
**Prioridad:** 🟡 P3 — cosmético, no bloquea ningún pilar.
**Esfuerzo estimado:** XS (~15-20 min combinado).
**Riesgo:** ninguno — no toca comportamiento, solo texto.

---

## Contexto

Surgido de una auditoría completa de documentación (2026-09-20, ver sesión
de ese día): se corrigieron los hallazgos de "rompe confianza" y
"desactualizado" (roadmap 23, `docs/ci-cd.md`, `Roadmap-212-Ideas-Futuras.md`,
`Validacion-STORAGE-MGR.md`) y se archivaron `Día56`/`Día57`,
`Roadmap-DEVPROFILE-1-4/5-6.md` y `docs/Feedback/29/8.md`. Quedaron dos
puntos "cosméticos" sin resolver porque requerían una decisión de convención,
no solo corregir un dato:

## Tarea 1 — Convención de archivo para informes puntuales en `Tareas/`

`Tareas/zip-route-identificacion.md` (2026-07-10) y
`Tareas/psx-cue-rotos-2026-08-30.md` (2026-08-30) son informes de una
investigación puntual ya cerrada (identificación de ZIPs sueltos, `.cue`
rotos de PSX). A diferencia de los diarios (`Tareas/diario/archivo/`) o los
roadmaps de feature (`Tareas/diario/archivo/*-completado.md`), no existe
carpeta de archivo para este tipo de informe suelto en `Tareas/`.

**Decisión pendiente del usuario:** ¿crear `Tareas/archivo/` para este tipo
de documento, o dejarlos donde están con solo una nota de cierre en la
cabecera (mismo patrón que se usó en `Validacion-STORAGE-MGR.md`)? Una vez
decidido, aplicar el mismo criterio retroactivamente a los dos archivos
existentes y documentarlo en la regla 5 de `.claude/roadmaps/INDEX.md`
("Cómo usar este roadmap") para que sea consistente en el futuro.

## Tarea 2 — Actualizar referencias de código a los roadmaps DEVPROFILE movidos

`Tareas/Roadmap-DEVPROFILE-1-4.md` y `Tareas/Roadmap-DEVPROFILE-5-6.md` se
renombraron y movieron a `Tareas/diario/archivo/*-completado.md` el
2026-09-20. `Tareas/backlog.md` y `.claude/roadmaps/19-device-profile-loose-data.md`
ya se actualizaron, pero quedan 8 comentarios de código con la ruta vieja:

- `src/rom_manager/esde/systems_generator.py:28`
- `src/rom_manager/detection/platform_detector.py:70`
- `src/rom_manager/detection/platforms.toml:242`
- `src/rom_manager/web/handlers/system.py:493`
- `src/rom_manager/web/handlers/system.py:583`
- `src/rom_manager/services/device_profile.py:137`
- `src/rom_manager/services/path_tokenizer.py:8`
- `src/rom_manager/services/retroarch_cfg_writer.py:5`

Cambio mecánico: reemplazar `Roadmap-DEVPROFILE-1-4.md`/`Roadmap-DEVPROFILE-5-6.md`
por `diario/archivo/Roadmap-DEVPROFILE-1-4-completado.md`/
`diario/archivo/Roadmap-DEVPROFILE-5-6-completado.md` (o ruta relativa
equivalente) en cada comentario. Sin cambio de comportamiento — no necesita
tests nuevos, solo verificar que ningún test hace snapshot literal de esos
docstrings/comentarios antes de tocarlos.

---

## Checklist

- [ ] Tarea 1 — decisión de convención tomada con el usuario y aplicada a los 2 archivos existentes
- [ ] Tarea 1 — regla 5 de `.claude/roadmaps/INDEX.md` actualizada si la convención implica una carpeta nueva
- [ ] Tarea 2 — 8 comentarios de código actualizados a la ruta real
