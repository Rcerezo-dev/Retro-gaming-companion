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

### Fase 3 — Documentación que no miente (≈ 2 h)

| Tarea | Qué se hace | Esfuerzo |
|-------|-------------|----------|
| ONB-3 | Regenerar `docs/architecture/architecture.md` desde el código actual: árbol de módulos real (`web/builders/`, `database/repositories/`, `services/`, `esde/`, `patch/`, `web/jobs/`, `router.py`, `auth.py`, `daemons.py`, `state.py`, `lan.py`, `wizard.py`, `static/js/` + `partials/`), nombres de BD reales (`library_pc.db` / android), sin rutas personales | 1.5 h |
| ONB-8 | Podar `backlog.md`: secciones 100% completadas (SRP, ARC-JM, ARC-CFG, SEC, UR-0421, COL-REVIEW, FLOW-WIZARD, CLOUD-RESEARCH, NLP-REC, ANBERNIC-TV) → `Tareas/diario/archivo/archivo.md` | 30 min |

**Resultado:** lo que un dev nuevo lee coincide con lo que ve en el código.

### Fase 4 — Orientación de dominio y de código (≈ 2 h)

| Tarea | Qué se hace | Esfuerzo |
|-------|-------------|----------|
| ONB-5 | `docs/onboarding.md` — "primeros 30 minutos": (1) mapa de lectura del código con el flujo request→handler→service→repository, (2) levantar el app con datos sintéticos (`scripts/e2e_integration_test.py`, `/test-pipeline`), (3) enlace al Debug Playbook, (4) dónde viven los tests y cómo se organizan | 1 h |
| ONB-6 | `docs/glossary.md` — jerga retro en 1-2 líneas por término, con el "por qué importa aquí" (ej.: *DAT — catálogo XML de hashes canónicos; el matcher casa tu ROM contra él por SHA1*). Términos: DAT, Logiqx, clrmamepro, No-Intro, Redump, CHD, cue/bin, m3u, save vs savestate, core, BIOS, ES-DE, RetroAchievements, scraping | 45 min |

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
