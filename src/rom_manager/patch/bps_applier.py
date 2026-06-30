"""BPS (Beat Patch System) applier — stdlib only.

Format spec: https://www.romhacking.net/documents/746/
  Header:  magic b"BPS1"
  VLQ fields: source_size, target_size, metadata_length
  Metadata: UTF-8 string (ignored)
  Actions: sequence of (action << 2 | length_VLQ) records
    0 = SourceRead  — copy N+1 bytes from source at output position
    1 = TargetRead  — read N+1 literal bytes from patch
    2 = SourceCopy  — copy N+1 bytes from source at relative offset
    3 = TargetCopy  — copy N+1 bytes from output at relative offset
  Footer: source_crc32 (4 LE), target_crc32 (4 LE), patch_crc32 (4 LE)
"""
from __future__ import annotations

import struct
from pathlib import Path

from rom_manager.patch.ips_applier import PatchError


def _read_vlq(data: bytes, pos: int) -> tuple[int, int]:
    """Decode a BPS variable-length quantity starting at *pos*.

    BPS VLQ: terminal byte has bit-7 SET; non-terminal bytes accumulate with
    an extra +shift each iteration (distinct from standard VLQ).
    """
    value = 0
    shift = 1
    while True:
        if pos >= len(data):
            raise PatchError("BPS patch truncated in VLQ")
        byte = data[pos]
        pos += 1
        value += (byte & 0x7F) * shift
        if byte & 0x80:
            break
        shift <<= 7
        value += shift
    return value, pos


def apply_bps(rom_path: Path, patch_path: Path, output_path: Path) -> int:
    """Apply a BPS patch to *rom_path* and write result to *output_path*.

    Returns the number of actions processed.
    """
    patch = patch_path.read_bytes()
    if patch[:4] != b"BPS1":
        raise PatchError(f"Invalid BPS header in {patch_path.name!r}")

    pos = 4
    source_size, pos = _read_vlq(patch, pos)
    target_size, pos = _read_vlq(patch, pos)
    meta_length, pos = _read_vlq(patch, pos)
    pos += meta_length  # skip metadata string

    source = bytearray(rom_path.read_bytes())
    if len(source) != source_size:
        raise PatchError(
            f"Source size mismatch: patch expects {source_size}, got {len(source)}"
        )

    target = bytearray(target_size)
    out_pos = 0
    src_rel = 0  # relative offset for SourceCopy
    tgt_rel = 0  # relative offset for TargetCopy
    footer_start = len(patch) - 12  # last 12 bytes = 3 × CRC32
    actions = 0

    while pos < footer_start:
        data_raw, pos = _read_vlq(patch, pos)
        action = data_raw & 3
        length = (data_raw >> 2) + 1
        actions += 1

        if action == 0:  # SourceRead
            end = out_pos + length
            target[out_pos:end] = source[out_pos:end]
            out_pos = end

        elif action == 1:  # TargetRead
            if pos + length > len(patch):
                raise PatchError("BPS TargetRead overflows patch data")
            target[out_pos : out_pos + length] = patch[pos : pos + length]
            pos += length
            out_pos += length

        elif action == 2:  # SourceCopy
            offset_raw, pos = _read_vlq(patch, pos)
            sign = -1 if offset_raw & 1 else 1
            src_rel += sign * (offset_raw >> 1)
            for _ in range(length):
                target[out_pos] = source[src_rel]
                out_pos += 1
                src_rel += 1

        else:  # TargetCopy
            offset_raw, pos = _read_vlq(patch, pos)
            sign = -1 if offset_raw & 1 else 1
            tgt_rel += sign * (offset_raw >> 1)
            for _ in range(length):
                target[out_pos] = target[tgt_rel]
                out_pos += 1
                tgt_rel += 1

    output_path.write_bytes(bytes(target))
    return actions
