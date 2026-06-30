"""RetroArch save-state thumbnail extractor.

Two strategies, tried in order:
  1. Sidecar .png  — RetroArch writes <game>.state0.png next to <game>.state0
                     when "Save State Thumbnail" is ON in settings.
  2. Embedded PNG  — Some cores store a raw PNG inside the .state binary
                     (may or may not be zlib-compressed).

Usage:
    from rom_manager.utils.state_reader import find_state_thumbnails
    shots = find_state_thumbnails(rom_stem, search_dirs)
    # shots: list of (state_index: int, png_bytes: bytes)
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

_PNG_SIG = b"\x89PNG\r\n\x1a\n"
_IEND = b"IEND"


def _extract_png_from_data(data: bytes) -> bytes | None:
    """Find and return the first valid PNG block in *data* (raw or zlib-compressed)."""
    for blob in _iter_candidates(data):
        png = _parse_png(blob)
        if png:
            return png
    return None


def _iter_candidates(data: bytes):
    """Yield the raw data and any zlib-decompressed block found within it."""
    yield data
    # Try zlib decompression at small offsets (RetroArch header ≤ 32 bytes)
    for start in range(min(32, len(data))):
        try:
            yield zlib.decompress(data[start:])
            return  # first successful decompression is sufficient
        except zlib.error:
            continue


def _parse_png(data: bytes) -> bytes | None:
    """Return the first complete PNG block from *data*, or None."""
    idx = data.find(_PNG_SIG)
    if idx < 0:
        return None
    pos = idx + 8  # skip signature
    end = pos
    while pos + 8 <= len(data):
        try:
            length = struct.unpack_from(">I", data, pos)[0]
        except struct.error:
            break
        chunk_type = data[pos + 4 : pos + 8]
        chunk_end = pos + 12 + length  # 4 len + 4 type + data + 4 crc
        if chunk_end > len(data):
            break
        end = chunk_end
        if chunk_type == _IEND:
            return data[idx:end]
        pos = chunk_end
    return None


def _state_index(path: Path) -> int:
    """Extract numeric slot from filename like game.state2(.png) → 2, game.state → 0."""
    name = path.name
    if name.lower().endswith(".png"):
        name = name[:-4]
    parts = name.rsplit(".state", 1)
    if len(parts) < 2:
        return 0
    part = parts[-1].lstrip("0") or "0"
    try:
        return int(part)
    except ValueError:
        return 0


def find_state_thumbnails(
    rom_stem: str,
    search_dirs: list[Path],
    *,
    max_results: int = 8,
) -> list[tuple[int, bytes]]:
    """Return up to *max_results* (slot_index, png_bytes) pairs, sorted by slot.

    Strategy 1 — sidecar .png files:
      Search each directory for `<rom_stem>.state*.png`.

    Strategy 2 — embedded PNG in .state files:
      For any slot without a sidecar, try to extract a PNG from the binary .state file.
    """
    # Collect all state files (sidecar .png and binary .state) per slot
    sidecars: dict[int, Path] = {}
    state_files: dict[int, Path] = {}

    for d in search_dirs:
        if not d.is_dir():
            continue
        for f in d.rglob(rom_stem + ".state*"):
            if f.suffix.lower() == ".png":
                slot = _state_index(f)
                sidecars.setdefault(slot, f)
            elif ".state" in f.name and f.suffix.lower() != ".png":
                slot = _state_index(f)
                state_files.setdefault(slot, f)

    results: list[tuple[int, bytes]] = []
    seen_slots = set(sidecars) | set(state_files)

    for slot in sorted(seen_slots)[:max_results]:
        if slot in sidecars:
            try:
                png = sidecars[slot].read_bytes()
                if png.startswith(_PNG_SIG):
                    results.append((slot, png))
                    continue
            except OSError:
                pass
        if slot in state_files:
            try:
                png = _extract_png_from_data(state_files[slot].read_bytes())
                if png:
                    results.append((slot, png))
            except OSError:
                pass

    return results
