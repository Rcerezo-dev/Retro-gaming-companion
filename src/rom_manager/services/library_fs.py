"""Acceso mínimo a una biblioteca de ROMs, local o en la consola por ADB.

Interfaz estrecha (listar, leer texto, descartar) para que la lógica de análisis no sepa dónde
vive la biblioteca (ISP/DIP): ``incomplete_sets_service`` solo depende de ``LibraryFS``.
Las rutas son relativas a la raíz y usan ``/``.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Protocol

from rom_manager.sync.adb_transport import AdbTransport
from rom_manager.utils.trash import TRASH_DIR_NAME, discard_to_trash


class LibraryFS(Protocol):
    def list_files(self) -> dict[str, int]: ...

    def read_text(self, rel: str) -> str: ...

    def discard(self, rel: str) -> None: ...

    def read_head(self, rel: str, n: int) -> bytes: ...

    def write_text(self, rel: str, text: str) -> None: ...

    def move(self, src: str, dst: str) -> None: ...


class LocalLibraryFS:
    def __init__(self, root: Path):
        self.root = root

    def list_files(self) -> dict[str, int]:
        files: dict[str, int] = {}
        for p in self.root.rglob("*"):
            rel = p.relative_to(self.root)
            if p.is_file() and TRASH_DIR_NAME not in rel.parts and not rel.parts[0].startswith("."):
                files[rel.as_posix()] = p.stat().st_size
        return files

    def read_text(self, rel: str) -> str:
        return (self.root / rel).read_text(encoding="utf-8", errors="replace")

    def discard(self, rel: str) -> None:
        discard_to_trash(self.root / rel)

    def read_head(self, rel: str, n: int) -> bytes:
        with (self.root / rel).open("rb") as f:
            return f.read(n)

    def write_text(self, rel: str, text: str) -> None:
        with (self.root / rel).open("x", encoding="utf-8", newline="\n") as f:  # "x": no pisa
            f.write(text)

    def move(self, src: str, dst: str) -> None:
        if (self.root / dst).exists():
            raise FileExistsError(dst)
        (self.root / src).rename(self.root / dst)


class AdbLibraryFS:
    def __init__(self, transport: AdbTransport, root: str, *, list_timeout: int = 240):
        self.transport = transport
        self.root = root.rstrip("/")
        self.list_timeout = list_timeout

    def _abs(self, rel: str) -> str:
        return f"{self.root}/{rel}"

    def list_files(self) -> dict[str, int]:
        prefix = self.root + "/"
        infos = self.transport.ls_recursive(self.root, timeout=self.list_timeout)
        return {
            str(PurePosixPath(i.android_path))[len(prefix) :]: i.size
            for i in infos
            if i.android_path.startswith(prefix)
        }

    def read_text(self, rel: str) -> str:
        return self.transport.read_text(self._abs(rel))

    def discard(self, rel: str) -> None:
        self.transport.discard(self._abs(rel))

    def read_head(self, rel: str, n: int) -> bytes:
        return self.transport.read_head(self._abs(rel), n) or b""

    def write_text(self, rel: str, text: str) -> None:
        self.transport.write_text(self._abs(rel), text)

    def move(self, src: str, dst: str) -> None:
        self.transport.move(self._abs(src), self._abs(dst))
