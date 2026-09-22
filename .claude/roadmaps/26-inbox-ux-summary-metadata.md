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

### Paso 1 — ✅ Investigado (2026-09-22): `INBOX-METADATA-INLINE-1`

Confirmado contra el código real: `web/inbox_pipeline.py` (extract → scan →
match → plan → rename → organize, 6 pasos) no menciona `scraper` en ningún
sitio — el scraping siempre fue una acción manual aparte desde Colección.
Trazado también el resultado del job (`job_result`, final de
`_run_inbox_pipeline`): **ya** incluye `matched`, `organized`,
`duplicates_removed`, `conflicts_unresolved`, `ra_resolved`, listas de
errores — mucho más completo de lo asumido. Y en el frontend,
`_renderInboxResult()` (`inbox.js:274-316`) **ya** pinta un panel de resumen
completo con esos contadores + un toast — `INBOX-SESSION-SUMMARY-1` (Paso 3
original) resultó ya estar hecho casi del todo, salvo un hueco real: no
había una cifra de "sin match" (solo "Cotejados: N" de un total, sin
destacar cuántos quedaron sin catalogar).

### Paso 2 — ✅ Hecho (2026-09-22): scraping opt-in al organizar

- `config.py`: `InboxConfig.scrape_on_organize: bool = False` (TOML
  `[inbox] scrape_on_organize = true`), apagado por defecto.
- **Extraído** `web/handlers/scraper.py::_do_scrape_single` a
  `services/scrape_service.py::scrape_game_metadata()` — mismo lookup+apply
  (hash → nombre, ScreenScraper), ahora reutilizable sin `ctx` HTTP. El
  handler queda como wrapper fino sobre el servicio (cero cambio de
  comportamiento para Colección — mismos tests manuales que antes, sin
  tests previos que cubrieran el endpoint, así que no hay suite que romper
  pero sí se verificó el refactor con los tests nuevos del servicio).
- `scrape_game_metadata()` acepta un `client` opcional — necesario porque
  `ScreenScraperClient.min_interval` es un throttle **por instancia**; un
  cliente nuevo por juego en un lote lo saltaría entero. Un solo cliente
  para todo el lote resuelve el riesgo de rate-limit que el roadmap ya
  anticipaba.
- `inbox_pipeline.py`: nueva `_scrape_organized_games()` (testeable en
  aislado, sin necesitar la pipeline completa) — se llama tras el loop de
  organize con la lista de `game_id` recién organizados. No-op si el opt-in
  está apagado, no hay juegos, o faltan credenciales. Un fallo puntual
  nunca aborta el organize — los archivos ya se movieron, esto solo
  intenta enriquecerlos.

### Paso 3 — ✅ Hecho (2026-09-22): `INBOX-SESSION-SUMMARY-1`

Ya estaba hecho (ver Paso 1) salvo el hueco de "sin match". Añadido:
`unmatched` (juegos organizados cuya `platform` quedó vacía — cayeron en
`Unknown/`) y `scraped`/`scrape_errors` (resultado del Paso 2) al
`job_result`, y sus líneas correspondientes en `_renderInboxResult()`
(`inbox.js`) — "Sin match de catálogo" destacado igual que "Conflictos sin
resolver", "Metadata scrapeada" solo si > 0.

### Paso 4 — ✅ Tests (2026-09-22)

- `tests/test_scrape_service.py` (6 tests): sin credenciales, sin match,
  preview no escribe en BD, apply sí escribe y marca `metadata_scraped`,
  reutiliza el `client` pasado en vez de crear uno nuevo, una excepción del
  cliente nunca se propaga.
- `tests/test_inbox_scrape_hook.py` (6 tests): no-op con el opt-in apagado/
  sin juegos/sin credenciales, un solo cliente para todo el lote, un fallo
  puntual no detiene el resto del lote, el callback de progreso recibe
  índice/total correctos.

### Paso 5 — ✅ Verificación (2026-09-22)

```bash
python -m pytest tests/ -q     # 1452 pass, 0 fallos (sin ADB conectado esta sesión)
ruff check src/rom_manager/web/inbox_pipeline.py src/rom_manager/services/scrape_service.py src/rom_manager/web/handlers/scraper.py src/rom_manager/config.py   # limpio
ruff format --check ...                                                                                                                                          # limpio
```

---

## Fuera de alcance

- Cambiar qué cuenta como "conflicto" o "sin match" — ya está definido en el
  pipeline existente, esta rama solo lo reporta mejor.
- Scraping retroactivo de la biblioteca ya organizada (eso es `SAGE-1`, ya
  en el backlog bajo RA/Scraper).

---

## Checklist

- [x] Paso 1 — hallazgo documentado (archivo:línea) sobre si metadata ya se aplica (2026-09-22)
- [x] Paso 2 — integración de scraping al organize (2026-09-22)
- [x] Paso 3 — resumen de sesión, hueco de "sin match" cerrado (2026-09-22)
- [x] Paso 4 — tests nuevos (2026-09-22)
- [x] Paso 5 — suite completa + ruff limpios (2026-09-22)
- [ ] Commit en rama, PR a `develop` — pendiente, requiere confirmación explícita del usuario
