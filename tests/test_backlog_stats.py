import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "backlog_stats", Path(__file__).resolve().parent.parent / "scripts" / "backlog_stats.py"
)
bs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bs)

MD = """intro
### A — hecha
| ID | Estado |
|----|--------|
| A1 | ✅ ok |
### B — abierta
| ID | Estado |
|----|--------|
| B1 | ✅ ok |
| B2 | ⬜ |
### C — prosa
```
### no es sección
```
texto
"""


def test_classify():
    got = {t: bs.classify(l) for t, l in bs.sections(MD)}
    assert got == {"A — hecha": ("hecho", 1, 0), "B — abierta": ("pendiente", 1, 1), "C — prosa": ("revisar", 0, 0)}
