"""N64 ROM format converter (byte-swap).

N64 ROMs come in three byte-order variants:
  .z64  — Big-endian (native N64 order)  — magic: 0x80 0x37 0x12 0x40
  .v64  — Byte-swapped (Doctor V64)      — magic: 0x37 0x80 0x40 0x12
  .n64  — Little-endian (Word-swapped)   — magic: 0x40 0x12 0x37 0x80

Converting to .z64 is done entirely in Python — no external tools needed.
"""

from __future__ import annotations

import array
from dataclasses import dataclass
from pathlib import Path

# First 4 bytes identify byte order
_MAGIC_Z64 = b"\x80\x37\x12\x40"
_MAGIC_V64 = b"\x37\x80\x40\x12"
_MAGIC_N64 = b"\x40\x12\x37\x80"

_CHUNK = 4 * 1024 * 1024  # 4 MB per chunk


@dataclass(slots=True)
class N64ConvertResult:
    success: bool
    source_path: str
    target_path: str
    source_format: str  # "z64" | "v64" | "n64" | "unknown"
    size_bytes: int
    error: str = ""


def detect_n64_format(path: Path) -> str:
    """Return 'z64', 'v64', 'n64', or 'unknown' based on magic bytes."""
    try:
        header = path.read_bytes()[:4]
    except OSError:
        return "unknown"
    if header == _MAGIC_Z64:
        return "z64"
    if header == _MAGIC_V64:
        return "v64"
    if header == _MAGIC_N64:
        return "n64"
    return "unknown"


def convert_to_z64(source: Path, target: Path | None = None) -> N64ConvertResult:
    """Convert a .v64 or .n64 ROM to .z64 (big-endian).

    If *target* is None, the output file is placed alongside *source* with
    extension ``.z64``.  Already-z64 files are copied as-is if target differs
    from source; if same, nothing is done.
    """
    if target is None:
        target = source.with_suffix(".z64")

    fmt = detect_n64_format(source)
    size = 0
    try:
        size = source.stat().st_size
    except OSError:
        pass

    result = N64ConvertResult(
        success=False,
        source_path=str(source),
        target_path=str(target),
        source_format=fmt,
        size_bytes=size,
    )

    if fmt == "unknown":
        result.error = "Formato no reconocido (magic bytes desconocidos)"
        return result

    if fmt == "z64" and source == target:
        result.success = True
        result.error = "Ya está en formato .z64"
        return result

    if target.exists():
        result.error = f"El destino ya existe: {target.name} — no se sobrescribe."
        return result

    try:
        with open(source, "rb") as fin, open(target, "wb") as fout:
            while True:
                chunk = fin.read(_CHUNK)
                if not chunk:
                    break
                # Pad to multiple of 2 (v64) or 4 (n64) if needed
                if fmt == "v64":
                    if len(chunk) % 2:
                        chunk += b"\x00"
                    # Swap every pair of bytes
                    arr = bytearray(chunk)
                    arr[0::2], arr[1::2] = arr[1::2].copy(), arr[0::2].copy()
                    fout.write(bytes(arr))
                elif fmt == "n64":
                    if len(chunk) % 4:
                        chunk += b"\x00" * (4 - len(chunk) % 4)
                    a = array.array("I", chunk)
                    a.byteswap()
                    fout.write(a.tobytes())
                else:  # z64 → just copy
                    fout.write(chunk)
        result.success = True
    except OSError as exc:
        result.error = str(exc)
        # Clean up partial output
        try:
            if target.exists() and target != source:
                target.unlink()
        except OSError:
            pass

    return result


def scan_n64_roms(directory: Path) -> list[dict]:
    """Return a list of N64 ROM files with their detected format."""
    results = []
    for ext in (".z64", ".v64", ".n64"):
        for path in directory.rglob("*" + ext):
            fmt = detect_n64_format(path)
            results.append(
                {
                    "path": str(path),
                    "filename": path.name,
                    "format": fmt,
                    "needs_conversion": fmt not in ("z64", "unknown"),
                    "size_bytes": path.stat().st_size if path.exists() else 0,
                }
            )
    return results
