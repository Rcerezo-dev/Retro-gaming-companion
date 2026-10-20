## Validación en hardware — → #211

Tareas que requieren consola real o SD card para verificarse — no ejecutables
solo con datos sintéticos.

### Hardware validation (requires console or SD card)
> **Estado (revisado 2026-10-20):** ⏳ abierta — V1–V5 y B1-hw son pasos de validación sin ejecutar o sin confirmar (requieren consola, tarjeta SD o API key de RA real); el estado individual de cada uno no está verificado. Corrección: en la revisión DOCS-AUDIT-3d se marcó por error como cerrada.

| ID | Task |
|----|------|
| V1 | SD card auto-sync — configure `anbernic_root`, insert SD, verify banner + log |
| V2 | Two-database migration — Settings → "Migrate DB" → verify separate PC/Android counts |
| V3 | Inbox end-to-end — configure `inbox_path`, drop ZIP, verify extraction + rename + move |
| V4 | RetroAchievements with real API key |
| V5 | Termux guide on console — prereq for WiFi sync |
| B1-hw | Android renamer doesn't reduce queue — test with SD inserted |

---

> ✅ Archivado en `Tareas/diario/archivo/archivo.md`: VAL-FIX-1..7 (hallazgos de la validación con consola real — completos, 2026-07-13/2026-07-20).

---
