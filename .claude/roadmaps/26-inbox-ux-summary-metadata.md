# Roadmap 26 — `feature/inbox-ux-summary-metadata`

**Rama:** `feature/inbox-ux-summary-metadata`
**Base:** `develop`
**Prioridad:** 🟡 P3 — Pilar 2, mejora de cierre/feedback sobre un pipeline que ya funciona, no un fix
**Esfuerzo estimado:** S-M (~3-4 h, más tiempo de investigación en el Paso 1)
**Riesgo:** Bajo — no cambia la lógica de organización, solo qué se reporta al terminar

---

## Origen

`INBOX-SESSION-SUMMARY-1`, `INBOX-METADATA-INLINE-1` (`Tareas/backlog.md`,
Pilar 2 → #203, idea usuario 2026-09-22). Objetivo: que "soltar y listo" se
sienta completo — cierre visible de qué pasó, y confirmar si falta portada/
metadata al llegar el juego a su carpeta final.

---

## Objetivo

1. Resumen visible al terminar un job de Inbox/organize (organizados /
   conflictos / sin match) en vez de tener que revisar logs.
2. Confirmar si portada/metadata ya se aplican automáticamente al organizar
   desde el Inbox; si no, integrarlo.

---

## Pasos

### Paso 1 — `INBOX-METADATA-INLINE-1`: investigar antes de tocar código

Regla del proyecto ("Investigar antes de arreglar"): verificar contra el
código real, no contra suposiciones. Trazar `web/inbox_pipeline.py` paso a
paso — ¿alguno de sus pasos dispara `web/handlers/scraper.py` (o el servicio
que usa) para el juego recién organizado, o el scraping siempre es una
acción manual aparte desde Colección? Documentar el hallazgo (archivo:línea
exactos) antes de decidir si hace falta código nuevo.

### Paso 2 — Si falta integrarlo

Enganchar el scraping puntual (reutilizar el mismo mecanismo que ya usa un
juego individual en Colección, no una implementación nueva) al final del
paso "Move to platform folders" del job de organize. Opt-in vía config
(`config.toml`) para no ralentizar organizaciones masivas sin red o con
rate-limit de la fuente.

### Paso 3 — `INBOX-SESSION-SUMMARY-1`: resumen de job

- `web/inbox_pipeline.py` ya reporta progreso vía
  `job_manager.update_progress` (mismo patrón que `scan_progress`/
  `match_progress`) — añadir contadores finales al resultado del job:
  organizados, con conflicto, sin match.
- Frontend (`web/static/js/jobs.js`): panel/toast con el resumen al
  completar, con el mismo guard `result_ts`/`_shownResultTs` que ya usan
  otros jobs para no repetir el toast en cada poll.

### Paso 4 — Tests

- El resultado del job expone los tres contadores y suman al total de
  archivos procesados.
- Si `INBOX-METADATA-INLINE-1` requiere código nuevo: test de que el
  scraping se dispara solo cuando el opt-in está activo, y que un fallo de
  red no rompe el organize en sí (el archivo se mueve igual).

### Paso 5 — Verificación

```bash
python -m pytest tests/ -q
ruff check src/rom_manager/web/inbox_pipeline.py
```

---

## Fuera de alcance

- Cambiar qué cuenta como "conflicto" o "sin match" — ya está definido en el
  pipeline existente, esta rama solo lo reporta mejor.
- Scraping retroactivo de la biblioteca ya organizada (eso es `SAGE-1`, ya
  en el backlog bajo RA/Scraper).

---

## Checklist

- [ ] Paso 1 — hallazgo documentado (archivo:línea) sobre si metadata ya se aplica
- [ ] Paso 2 — integración de scraping al organize (solo si el Paso 1 confirma que falta)
- [ ] Paso 3 — resumen de sesión (backend + frontend)
- [ ] Paso 4 — tests nuevos
- [ ] Paso 5 — suite completa + ruff limpios
- [ ] Commit en rama, PR a `develop` — pendiente, requiere confirmación explícita del usuario
