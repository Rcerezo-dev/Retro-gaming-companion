# Contribuir a Retro Vault

Guía para poner el entorno a punto y abrir tu primer PR sin sorpresas.
Documentación técnica completa: [`docs/README.md`](docs/README.md) ·
Detalle del pipeline CI/CD: [`docs/ci-cd.md`](docs/ci-cd.md).

---

## Setup del entorno

**Requisitos:** Python 3.11+ (recomendado 3.12). Sin dependencias externas de
runtime — el proyecto es 100% stdlib; las dev-deps son solo `pytest`, `ruff` y
`pre-commit`.

```bash
git clone https://github.com/Rcerezo-dev/Retro-gaming-companion.git
cd Retro-gaming-companion

# Con Conda (recomendado en Windows) …
conda create -n rom_manager python=3.12
conda activate rom_manager
# … o con venv:
# python -m venv .venv && .venv\Scripts\activate

pip install -e ".[dev]"

# Hooks locales (una sola vez):
pre-commit install                       # ruff check+format en cada commit
pre-commit install --hook-type pre-push  # pytest completo antes de cada push
```

> El hook de push ejecuta `conda run -n rom_manager python -m pytest` —
> necesita `conda` en el PATH. Si no usas conda, edita la entry del hook en
> `.pre-commit-config.yaml` o lanza los tests a mano antes de pushear.

**Binarios externos** (opcionales, según qué toques): `chdman` y `adb` en
`tools/` (ver README §Instalación); `rclone` para cloud sync.

## Verificar en local (lo mismo que corre CI)

```bash
ruff format --check src tests   # gate de formato
ruff check src tests            # gate de lint
pytest -q                       # suite completa
```

Para auto-arreglar: `ruff format src tests && ruff check src tests --fix`.

## Estrategia de ramas y PRs

- **`develop`** — rama de integración y **rama por defecto**. Todos los PRs apuntan aquí.
- **`main`** — estable/release. Solo se mergea `develop` → `main` tras probar.
- Flujo: rama por tarea (`feature/x`, `fix/x`, `chore/x`, `refactor/x`) → PR a
  `develop` → pasan los checks → merge.
- Ambas ramas tienen **branch protection**: el PR no se puede mergear si no
  pasan los 3 checks — `Lint (ruff)`, `Tests (pytest) (3.11)` y
  `Tests (pytest) (3.12)` — y las conversaciones deben estar resueltas.
- **CodeRabbit** revisa cada PR automáticamente (comentarios en español).
  Para forzar re-review: comentar `@coderabbitai review`.

## Convenciones del proyecto

- **Solo stdlib en runtime** — no añadas dependencias a `[project.dependencies]`.
  Los binarios externos (chdman, adb, rclone) se invocan como subprocesos.
- **Principios SOLID** — módulos pequeños con una responsabilidad; la lógica de
  negocio vive en `services/`, los handlers web son routers finos.
- **Lint**: reglas `E, F, I, UP, S110, S112`. `E501` está ignorado a propósito
  (el largo de línea lo gestiona el formatter — no lo reactives). Nada de
  `except: pass` silencioso: como mínimo `logger.debug(..., exc_info=True)`.
- **UI en español** — textos de la interfaz y mensajes al usuario en español;
  los términos técnicos (SHA1, ROM, CHD, DAT…) se conservan.
- **Reglas de seguridad de datos** (no negociables):
  - `rommgr plan` siempre antes de `rommgr apply`; nunca sobreescribir sin
    política de conflictos documentada.
  - PSX se maneja por sets: nunca renombrar un `.bin` sin reescribir su `.cue`.
  - BIOS, assets y carpetas Android no se tratan como ROMs.
  - Toda operación sobre archivos se registra en SQLite.
  - En sync, ante la duda no se sobreescribe: backup primero.
- **Tests**: cada fix/feature lleva su test en `tests/` (pytest, sin plugins).

## Checklist antes de abrir el PR

1. `ruff format --check` + `ruff check` + `pytest -q` en verde en local.
2. Rama creada desde `develop` actualizado; título de commit estilo
   `tipo(ámbito): descripción` (p. ej. `fix(sync): …`).
3. Si la tarea viene del backlog, referencia su ID (p. ej. `ONB-4`) en el
   commit/PR y actualiza su estado en `Tareas/backlog.md`.
4. PR con base `develop`, descripción de qué/por qué, y riesgo señalado si toca
   renombrado, sync o base de datos.
