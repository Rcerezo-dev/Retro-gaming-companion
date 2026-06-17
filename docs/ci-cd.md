# CI/CD & GitHub Actions — Notas para Claude

> Instrucciones para mí mismo (Claude) sobre el pipeline de CI/CD de Retro Vault.
> Describe **qué existe, cómo funciona, cómo interactuar con ello y los gotchas**.
> Configurado el 2026-06-17. Repo: `Rcerezo-dev/Retro-gaming-companion`.

---

## 1. Estrategia de ramas

- **`develop`** — rama de integración y **rama por defecto en GitHub**. Todos los PRs apuntan aquí.
- **`main`** — rama estable/release. Solo se mergea `develop` → `main` tras probar.
- Flujo normal: feature branch → PR a `develop` → (CI + CodeRabbit) → merge → cuando estable, PR `develop` → `main`.

---

## 2. Workflow de GitHub Actions

Archivo: **`.github/workflows/ci.yml`**

- **Triggers**: `pull_request` y `push` a `develop` y `main`.
- **Concurrency**: cancela runs antiguos del mismo ref (`cancel-in-progress: true`).
- **Dos jobs** (corren en `ubuntu-latest`):

### Job `lint` → check name **`Lint (ruff)`**
```
pip install ruff
ruff format --check src tests     # gate de formato (falla si algo no está formateado)
ruff check src tests              # gate de lint
```

### Job `tests` → check names **`Tests (pytest) (3.11)`** y **`Tests (pytest) (3.12)`**
```
matrix: python-version [3.11, 3.12]   (fail-fast: false)
pip install -e ".[dev]"
pytest -q
```

> **Los 3 check names exactos** (importan para branch protection):
> `Lint (ruff)`, `Tests (pytest) (3.11)`, `Tests (pytest) (3.12)`

---

## 3. Configuración de ruff

En **`pyproject.toml`**:
```toml
[tool.ruff]
target-version = "py311"
src = ["src", "tests"]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]
ignore = ["E501"]            # el largo de línea lo gestiona el FORMATTER, no el linter

[tool.ruff.lint.isort]
known-first-party = ["rom_manager"]
```

- **`E501` está deliberadamente ignorado en el linter**: el formatter (`ruff format`) controla el largo de línea; las líneas que deja largas son intencionales (strings/comentarios no rompibles) y no deben re-marcarse. NO quitar este ignore.
- Reglas activas: `E` (pycodestyle), `F` (pyflakes), `I` (isort), `UP` (pyupgrade).

---

## 4. Branch protection

Aplicada en **ambas** ramas `develop` y `main` vía API. Para verla/editarla:
```
gh api repos/Rcerezo-dev/Retro-gaming-companion/branches/develop/protection
```
Reglas:
- **Required status checks** (strict = deben estar actualizados): los 3 checks de arriba.
- **Required PR** antes de merge (`required_pull_request_reviews` presente, `required_approving_review_count: 0`).
- **`required_conversation_resolution: true`**, sin force-push, sin borrado.
- **`enforce_admins: false`** → el owner (solo colaborador: `Rcerezo-dev`) PUEDE saltarse las reglas en pushes directos.

### Por qué `required_approving_review_count: 0`
Es un repo de un solo dev. GitHub no cuenta tu propia aprobación, y CodeRabbit no envía aprobaciones formales por defecto → exigir 1 review bloquearía TODOS los merges. Si algún día hay un segundo colaborador o CodeRabbit aprueba formalmente, subir a 1.

### Push directo a `develop`/`main` (como owner)
Funciona porque `enforce_admins=false`. GitHub responde con
`remote: Bypassed rule violations…` — **es informativo, el push tiene éxito**.
Para trabajo normal usar PRs (es lo que ejecuta los checks de verdad).

---

## 5. CodeRabbit

- Config: **`.coderabbit.yaml`** (raíz). Auto-review de PRs a `develop`/`main`, salida en **español**, perfil `chill`, integración ruff activada, filtros de ruido (`*.lock`, `*.min.*`, `library.db`, `Tareas/**`).
- **El GitHub App debe estar instalado** en el repo (https://github.com/apps/coderabbitai) o el YAML no hace nada. **Ya está instalado** (confirmado 2026-06-17).
- Solo actúa en **PRs**, no en pushes directos.
- Forzar re-review: comentar **`@coderabbitai review`** en el PR.

---

## 6. Hooks locales (framework `pre-commit`)

Config: **`.pre-commit-config.yaml`**. `pre-commit` es dev-dep en `pyproject.toml`.

### Hook de commit (`pre-commit` stage)
Repo `astral-sh/ruff-pre-commit` (rev `v0.15.17`), restringido a `^(src|tests)/` (espeja el gate de CI):
- `ruff-check --fix`
- `ruff-format`

### Hook de push (`pre-push` stage)
Hook `local`, `language: system`:
```
conda run -n rom_manager --no-capture-output python -m pytest -q
```
- Corre **toda** la suite antes de cada push.
- `conda run -n rom_manager` apunta siempre al env del proyecto **sin necesidad de `conda activate`** — solo necesita `conda` en el PATH.

### Activación (tras clonar en limpio)
```
pre-commit install                       # hook de commit
pre-commit install --hook-type pre-push  # hook de push
```

---

## 7. Cómo trabajo yo (Claude) con este pipeline — recetas

### Entorno
- **Python del proyecto**: `C:\Users\Ruben\anaconda3\envs\rom_manager\python.exe`
  (OJO: el CLAUDE.md dice `rammu` pero la ruta real es `Ruben`).
- `python` "a secas" en una shell limpia resuelve a un Python 3.10 sin `rom_manager` → NO usarlo para tests.
- **conda** no está en el PATH en shell limpia; está en `C:\Users\Ruben\anaconda3\condabin\conda.bat`.

### Verificar lint/format/tests localmente (igual que CI)
```powershell
$py = "C:\Users\Ruben\anaconda3\envs\rom_manager\python.exe"
& $py -m ruff format --check src tests
& $py -m ruff check src tests
& $py -m pytest -q
```
Auto-arreglar antes de commitear:
```powershell
& $py -m ruff format src tests
& $py -m ruff check src tests --fix
```

### Pushear a `develop` (el pre-push corre pytest vía conda run)
El hook necesita `conda` en el PATH. En el tool de PowerShell el `$env:PATH` NO persiste entre llamadas, así que hay que ponerlo inline en el MISMO comando:
```powershell
$env:PATH = "C:\Users\Ruben\anaconda3\condabin;" + $env:PATH
git push origin develop
```
Si `conda` no está accesible y el push falla con `Executable conda not found`, alternativa: `git push --no-verify` (solo si ya verifiqué que los tests pasan).

### gh CLI
- **NO está en el PATH**. Ruta completa: `C:\Program Files\GitHub CLI\gh.exe`.
- En bash: `"/c/Program Files/GitHub CLI/gh.exe"`.

### Ver estado de CI
```powershell
$gh = "C:\Program Files\GitHub CLI\gh.exe"
& $gh run list --branch develop --limit 1
$id = (& $gh run list --branch develop --limit 1 --json databaseId --jq ".[0].databaseId")
& $gh run view $id --json jobs --jq ".jobs[] | {name: .name, conclusion: .conclusion}"
& $gh run watch $id --exit-status   # esperar a que termine
```

### Ver checks de un PR
```powershell
& $gh pr checks <PR#>
```

---

## 8. Cómo modificar el pipeline

- **Subir versión de ruff**: cambiar `rev` en `.pre-commit-config.yaml` (o `pre-commit autoupdate`). La versión de CI no está pinada (`pip install ruff` instala la última) — si divergen, pinar en `ci.yml`.
- **Añadir/quitar reglas de lint**: editar `[tool.ruff.lint] select`/`ignore` en `pyproject.toml`. Afecta a CI y a los hooks por igual (misma config).
- **Cambiar versiones de Python testeadas**: editar `matrix.python-version` en `ci.yml`. **Si cambian, los check names cambian** (`Tests (pytest) (3.x)`) → hay que actualizar los `contexts` de branch protection.
- **Editar branch protection**: `gh api -X PUT .../branches/<rama>/protection --input <json>`.

---

## 9. Gotchas (resumen)

1. **E501 ignorado a propósito** — no re-activar; el formatter manda en el largo de línea.
2. **Check names = contexts de branch protection** — cambiar la matrix de Python rompe la protección si no se actualizan los contexts.
3. **pre-push necesita `conda` en PATH** — en shell limpia de Claude hay que añadir `condabin` inline.
4. **`python` a secas ≠ env del proyecto** — usar siempre la ruta del env conda.
5. **gh y conda NO están en PATH** — usar rutas completas.
6. **Push directo como owner = "Bypassed rule violations"** — es normal, no es error.
7. **CodeRabbit solo en PRs** — un push directo a `develop` no dispara review.
8. **Borrar rama remota deja ref local** — `git fetch --prune` lo limpia (ya hay `fetch.prune=true` global).
9. **`.git-blame-ignore-revs`** — contiene el commit del reformat masivo de ruff; GitHub lo respeta en blame automáticamente.
```
git config blame.ignoreRevsFile .git-blame-ignore-revs   # para que git local también lo respete
```
