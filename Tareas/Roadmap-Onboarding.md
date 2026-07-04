# Roadmap — Onboarding & Developer Experience

> Origen: auditoría del 2026-07-04 desde la perspectiva de un desarrollador nuevo,
> sin contexto del proyecto y con poco conocimiento del dominio retro-gaming.
> Tareas registradas en `Tareas/backlog.md` §ONB.

---

## Diagnóstico

### Lo que ya funciona bien (no tocar)

- **README de usuario excelente**: motivación, flujo, features, instalación, config,
  tabla de pestañas, estructura de biblioteca. Un *usuario* nuevo se orienta solo.
- **`docs/` con índice** (`docs/README.md`) y separación arquitectura / config / sync
  / ideas / `_archive` con justificación de por qué cada doc está archivado.
- **Debug Playbook** en el backlog: tabla síntoma → dónde mirar. Oro para un dev nuevo.
- **CI real** (ruff format + lint, pytest 3.11/3.12), pre-commit, branch protection,
  CodeRabbit. ~30 archivos de tests con nombres descriptivos.
- **Skills/agents de Claude** (`/test-pipeline`, `/db-check`, `inbox-watchdog`…) que
  documentan implícitamente cómo se valida el sistema.

### El problema

Todo lo anterior está pensado para el **usuario final** o para **quien ya vive en el
proyecto** (o para Claude). El *desarrollador* nuevo se encuentra con:

1. **Sin licencia efectiva** — README dice MIT pero no hay `LICENSE`. Sin ese archivo
   nadie puede legalmente usar ni contribuir al código.
2. **Reglas de contribución invisibles** — la estrategia de ramas (PRs a `develop`,
   no a `main`), los check names de CI y los hooks están en `docs/ci-cd.md`…
   redactado como "notas para Claude". Un humano no sabe que existe ni que le aplica.
3. **El doc de arquitectura miente** — describe el código de hace varios refactors
   (pre SRP-1a/b/c, pre ARC): módulos que ya no existen, monolitos ya troceados,
   rutas de usuario de otra máquina. Un dev nuevo que lo siga se pierde *más* que
   sin él.
4. **Config con dos fuentes de verdad desincronizadas** — `config.toml.example` y el
   bloque TOML del README difieren entre sí y ambos van por detrás de `config.py`.
5. **Sin mapa de entrada al código** — nadie te dice que el flujo se lee
   `cli.py` → `web/server.py` → `router.py` → `web/handlers/` → `services/`, ni que
   existe un e2e sintético para trastear sin ROMs reales.
6. **Jerga de dominio sin explicar** — DAT, Logiqx, No-Intro/Redump, CHD, `.cue+.bin`,
   `.m3u`, saves vs states, cores… El código y los docs la asumen; un dev sin
   background retro no puede razonar sobre el pipeline de matching sin ella.

---

## Fases

### Fase 1 — Legal + quick wins ✅ COMPLETADA (2026-07-04, rama `chore/onb-phase1-license-docs-index`)

| Tarea | Qué se hace | Estado |
|-------|-------------|--------|
| ONB-1 | `LICENSE` con texto MIT estándar (copyright Rubén Cerezo, 2026) | ✅ |
| ONB-7 | Índice `docs/README.md`: sección "Desarrollo" (`ci-cd.md`, `SKILLS-QUICK-START.md`) + `arcade-setup.md`, `emulator-compat.md`, `sync-wifi-sftp.md`; README raíz: sección "Documentación" → `docs/README.md` y licencia enlazada a `LICENSE` | ✅ |

**Resultado:** el repo es legalmente usable y toda la documentación es descubrible.

### Fase 2 — Contribuir sin preguntar ✅ COMPLETADA (2026-07-04, rama `chore/onb-phase2-contributing-config`)

| Tarea | Qué se hace | Estado |
|-------|-------------|--------|
| ONB-2 | `CONTRIBUTING.md`: setup dev (conda/venv + `pip install -e ".[dev]"` + pre-commit hooks), estrategia de ramas, check names exactos de CI, verificación local, convenciones (stdlib-only, SOLID, reglas de seguridad de datos, UI en español), checklist de PR. Enlazado desde el README | ✅ |
| ONB-4 | `config.toml.example` regenerado desde `load_config()` con TODAS las secciones (sync/auto_sync, inbox, backup, launchers, notifications, session_ttl, emulator_paths…) comentadas; el README deja de duplicar el TOML (tenía el default de `host` obsoleto) y enlaza al example con un snippet mínimo | ✅ |

**Resultado:** un dev clona, configura y abre su primer PR correcto sin ayuda.

### Fase 3 — Documentación que no miente ✅ COMPLETADA (2026-07-04, rama `chore/onb-phase3-arch-backlog`)

| Tarea | Qué se hace | Estado |
|-------|-------------|--------|
| ONB-3 | `docs/architecture/architecture.md` regenerado desde el código: árbol de módulos real (builders, repositories con mixins, services, esde, patch, jobs, router/auth/state/lan/wizard, static/js + partials), 2 BDs (`library_pc.db`/`library_android.db`) con las 10 tablas, patrones actuales (JobManager, `web/state.py`, seguridad SEC), API → `openapi.json`, config → enlace único a `config.toml.example`, historial de refactors hasta Día37 | ✅ |
| ONB-8 | `backlog.md` podado: ~440 líneas de secciones 100% completadas (branching Día26/27, SRP, App Universal Ph1–5, COL-REVIEW, FLOW-WIZARD, CLOUD-RESEARCH, ANBERNIC-TV, NLP-REC, UR-0421, SEC, ARC, REPORT-FIX/DAT-DL, DESIGN, UX-FIX, PONT, NEW-FEAT, SYNC-SETUP, DB-FIX, DÍA35) → `Tareas/diario/archivo/archivo.md`; quedan solo pendientes + Debug Playbook | ✅ |

**Resultado:** lo que un dev nuevo lee coincide con lo que ve en el código.

### Fase 4 — Orientación de dominio y de código ✅ COMPLETADA (2026-07-04, rama `chore/onb-phase4-onboarding-glossary`)

| Tarea | Qué se hace | Estado |
|-------|-------------|--------|
| ONB-5 | `docs/onboarding.md` — "primeros 30 minutos": pipeline central en 6 líneas, mapa de lectura del código en 6 pasos, flujo request→handler→service→repository, e2e sintético (`scripts/e2e_integration_test.py`, `/test-pipeline`), Debug Playbook, tests como documentación, guía del primer cambio | ✅ |
| ONB-6 | `docs/glossary.md` — ~30 términos en 4 bloques (identificación de ROMs, formatos de disco/multidisco, saves y emulación, infraestructura), cada uno con el "por qué importa en este código". Enlazado desde README, `docs/README.md` y onboarding | ✅ |

**Resultado:** un dev sin background retro entiende *qué* hace el pipeline y *por qué*.

### Fase 5 — Opcional / decisión de producto

| Tarea | Qué se hace | Esfuerzo |
|-------|-------------|----------|
| ONB-9 | Decidir audiencia del README: si el repo es también portfolio internacional, añadir TL;DR en inglés al inicio (3-4 líneas + stack + screenshot). No traducir el resto | 20 min |

---

## Orden recomendado

```
ONB-1 → ONB-7          (quick wins, una sesión corta)
ONB-2 → ONB-4          (rama chore/onboarding-contributing)
ONB-3 → ONB-8          (rama docs/architecture-refresh)
ONB-5 + ONB-6          (rama docs/onboarding-glossary — se escriben juntos)
ONB-9                  (cuando se decida la audiencia)
```

Esfuerzo total estimado: **~6-7 h** repartibles en 3-4 sesiones. Ninguna tarea toca
código de producción → riesgo cero, sin necesidad de hardware ni de CI especial
(salvo el gate de formato de Markdown si algún hook aplica).

## Criterio de éxito

Un desarrollador que no conoce el proyecto debería poder, sin preguntar nada:

1. Saber que puede usar el código legalmente (LICENSE visible en GitHub).
2. Clonar, instalar y correr los tests en < 15 min (CONTRIBUTING).
3. Levantar la web con datos sintéticos y ver el pipeline completo (onboarding.md).
4. Entender qué es un DAT y por qué el matcher usa SHA1 (glossary.md).
5. Abrir un PR a la rama correcta que pase CI a la primera (CONTRIBUTING + ci-cd).
