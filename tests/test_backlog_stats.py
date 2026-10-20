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
    assert got == {
        "A — hecha": ("hecho", 1, 0),
        "B — abierta": ("pendiente", 1, 1),
        "C — prosa": ("revisar", 0, 0),
    }


def test_marker_line():
    assert bs.classify(["> **Estado (revisado 2026-10-20):** ✅ cerrada"]) == ("hecho", 1, 0)
    assert bs.classify(["> **Estado:** ⏳ abierta"]) == ("pendiente", 0, 1)
