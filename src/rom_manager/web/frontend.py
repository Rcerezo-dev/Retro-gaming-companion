from __future__ import annotations

import pathlib

_STATIC_DIR = pathlib.Path(__file__).parent / "static"

# HTML is read at import time so that existing code (`from frontend import HTML`)
# keeps working without any changes to server.py.
HTML: str = (_STATIC_DIR / "index.html").read_text(encoding="utf-8")
