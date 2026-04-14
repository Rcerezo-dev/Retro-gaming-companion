from __future__ import annotations

import pathlib
import re

_STATIC_DIR = pathlib.Path(__file__).parent / "static"


def _assemble(index_path: pathlib.Path) -> str:
    """Read index.html and resolve <!--INCLUDE:partials/xxx.html--> directives."""
    text = index_path.read_text(encoding="utf-8")

    def _replace(m: re.Match) -> str:
        partial = index_path.parent / m.group(1)
        return partial.read_text(encoding="utf-8")

    return re.sub(r"<!--INCLUDE:([^>]+)-->", _replace, text)


# HTML is assembled at import time so that existing code (`from frontend import HTML`)
# keeps working without any changes to server.py.
HTML: str = _assemble(_STATIC_DIR / "index.html")
