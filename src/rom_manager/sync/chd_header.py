"""Lectura de la cabecera de un ``.chd`` v5 (DUP-CHD-RAW-1a).

Un CHD v5 guarda en su cabecera de 124 bytes el SHA1 de los datos *sin comprimir*
(``rawsha1``): dos CHD del mismo disco comprimidos distinto tienen SHA1 de fichero
distinto pero el mismo ``rawsha1``. Leer 124 bytes basta para saberlo, sin descargar
el fichero ni ejecutar ``chdman``.
"""

from __future__ import annotations

from pathlib import Path

CHD_V5_HEADER_SIZE = 124
_CHD_TAG = b"MComprHD"
_RAWSHA1_OFFSET = 64
_RAWSHA1_LEN = 20


def chd_v5_raw_sha1(header: bytes) -> str | None:
    """``rawsha1`` (hex) de una cabecera CHD v5, o None si no es un CHD v5 válido.

    Solo v5 (el que escribe ``chdman`` actual): en v3/v4 los offsets difieren y un
    hash mal leído sería peor que no tener hash.
    """
    if len(header) < CHD_V5_HEADER_SIZE or header[:8] != _CHD_TAG:
        return None
    if int.from_bytes(header[8:12], "big") != CHD_V5_HEADER_SIZE:
        return None
    if int.from_bytes(header[12:16], "big") != 5:
        return None
    raw = header[_RAWSHA1_OFFSET : _RAWSHA1_OFFSET + _RAWSHA1_LEN]
    if raw == bytes(_RAWSHA1_LEN):  # campo vacío: el CHD no lo registra
        return None
    return raw.hex()


def chd_problem(header: bytes, size: int) -> str | None:
    """Motivo por el que un ``.chd`` es inservible, o None si la cabecera parece sana.

    Solo mira la cabecera (un v3/v4 no se juzga más allá de la firma): vacío, sin firma
    ``MComprHD`` (p. ej. en blanco) o con los offsets del mapa/metadatos fuera del fichero (truncado).
    """
    if size == 0:
        return "vacío (0 bytes)"
    if header[:8] != _CHD_TAG:
        return "cabecera inválida (no es un CHD)"
    if len(header) < CHD_V5_HEADER_SIZE or int.from_bytes(header[12:16], "big") != 5:
        return None
    if int.from_bytes(header[32:40], "big") == 0:
        return "sin datos (tamaño lógico 0)"
    if max(int.from_bytes(header[40:48], "big"), int.from_bytes(header[48:56], "big")) >= size:
        return "truncado (mapa o metadatos fuera del fichero)"
    return None


def read_chd_raw_sha1(path: Path) -> str | None:
    """Igual que :func:`chd_v5_raw_sha1` sobre un fichero local; None si no se puede leer."""
    try:
        with path.open("rb") as f:
            return chd_v5_raw_sha1(f.read(CHD_V5_HEADER_SIZE))
    except OSError:
        return None
