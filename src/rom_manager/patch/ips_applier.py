"""IPS / IPS32 patch applier — stdlib only, no dependencies.

IPS format:
  Header: b'PATCH'
  Records: [3-byte BE offset][2-byte BE size][<size> bytes data]
    Special (RLE): [3-byte offset][0x0000][2-byte run-length][1-byte fill-byte]
  EOF marker: b'EOF'

IPS32 (for ROMs > 16 MiB): offsets are 4 bytes instead of 3.
Detection: header b'IPS32' instead of b'PATCH'; EOF marker b'EEOF'.
"""

from __future__ import annotations

import struct
from pathlib import Path


class PatchError(ValueError):
    """Raised for malformed or incompatible patch data."""


def apply_ips(rom_path: Path, patch_path: Path, output_path: Path) -> int:
    """Apply *patch_path* to *rom_path*, writing result to *output_path*.

    Returns the number of patch records applied.
    Supports IPS and IPS32 (auto-detected from header).
    """
    patch_data = patch_path.read_bytes()

    if patch_data[:5] == b"IPS32":
        offset_size = 4
        eof_marker = b"EEOF"
        pos = 5
    elif patch_data[:5] == b"PATCH":
        offset_size = 3
        eof_marker = b"EOF"
        pos = 5
    else:
        raise PatchError(f"No es un archivo IPS/IPS32 válido: {patch_path.name}")

    rom = bytearray(rom_path.read_bytes())
    records = 0

    while pos < len(patch_data):
        marker_candidate = patch_data[pos : pos + len(eof_marker)]
        if marker_candidate == eof_marker:
            break

        if pos + offset_size + 2 > len(patch_data):
            raise PatchError("Patch truncado: offset/size incompletos")

        if offset_size == 4:
            offset = struct.unpack_from(">I", patch_data, pos)[0]
        else:
            b = patch_data[pos : pos + 3]
            offset = (b[0] << 16) | (b[1] << 8) | b[2]
        pos += offset_size

        size = struct.unpack_from(">H", patch_data, pos)[0]
        pos += 2

        if size == 0:
            # RLE record
            if pos + 3 > len(patch_data):
                raise PatchError("Patch truncado: RLE incompleto")
            run_len = struct.unpack_from(">H", patch_data, pos)[0]
            fill = patch_data[pos + 2]
            pos += 3
            end = offset + run_len
            if end > len(rom):
                rom.extend(b"\x00" * (end - len(rom)))
            rom[offset:end] = bytes([fill]) * run_len
        else:
            if pos + size > len(patch_data):
                raise PatchError("Patch truncado: data incompleta")
            chunk = patch_data[pos : pos + size]
            pos += size
            end = offset + size
            if end > len(rom):
                rom.extend(b"\x00" * (end - len(rom)))
            rom[offset:end] = chunk

        records += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(bytes(rom))
    return records
