from __future__ import annotations

INVALID_WINDOWS_CHARS = '<>:"/\\|?*'


def sanitize_filename(value: str) -> str:
    sanitized = value
    for char in INVALID_WINDOWS_CHARS:
        sanitized = sanitized.replace(char, "_")
    sanitized = sanitized.strip().rstrip(".")
    return " ".join(sanitized.split())
