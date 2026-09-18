"""Windows-only ``creationflags`` for subprocess calls to external tools.

``subprocess.CREATE_NO_WINDOW`` doesn't exist outside Windows (AttributeError
on import/reference) — every call site that shells out to a bundled tool
(adb/rclone/chdman/...) needs this constant instead of the raw attribute so
the code (and its tests) still runs on non-Windows CI.
"""

from __future__ import annotations

import subprocess
import sys

NO_WINDOW: int = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
