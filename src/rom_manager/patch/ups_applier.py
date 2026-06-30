"""UPS patch applier (stdlib only)."""

from __future__ import annotations

from pathlib import Path

from rom_manager.patch.ips_applier import PatchError


def _read_vlq(data: bytes, pos: int) -> tuple[int, int]:
    """UPS VLQ: terminal byte has bit-7 set; accumulates with shift multiplied."""
    value = 0
    shift = 1
    while True:
        byte = data[pos]
        pos += 1
        value += (byte & 0x7F) * shift
        if byte & 0x80:
            break
        shift <<= 7
        value += shift
    return value, pos


def apply_ups(rom_path: Path, patch_path: Path, output_path: Path) -> int:
    """Apply a UPS patch. Returns number of hunks written. Raises PatchError on format errors."""
    patch = patch_path.read_bytes()
    if patch[:4] != b"UPS1":
        raise PatchError(f"Cabecera UPS inválida: {patch[:4]!r}")

    pos = 4
    src_size, pos = _read_vlq(patch, pos)
    _tgt_size, pos = _read_vlq(patch, pos)

    source = bytearray(rom_path.read_bytes())
    if len(source) != src_size:
        raise PatchError(f"Tamaño ROM incorrecto: esperado {src_size}, obtenido {len(source)}")

    target = bytearray(source)
    if _tgt_size > len(target):
        target.extend(b"\x00" * (_tgt_size - len(target)))
    else:
        target = target[:_tgt_size]

    # Footer is last 12 bytes (3 × CRC32 LE); stop before it
    footer_start = len(patch) - 12
    write_pos = 0
    hunks = 0

    while pos < footer_start:
        offset, pos = _read_vlq(patch, pos)
        write_pos += offset
        # XOR bytes until null terminator
        while pos < footer_start:
            b = patch[pos]
            pos += 1
            if b == 0:
                write_pos += 1
                break
            if write_pos < len(target):
                target[write_pos] ^= b
            write_pos += 1
        hunks += 1

    output_path.write_bytes(bytes(target))
    return hunks
