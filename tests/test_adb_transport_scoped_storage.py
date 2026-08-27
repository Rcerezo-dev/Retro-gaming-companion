"""SYNC-FIX-2 — Android/data/<pkg> es scoped storage (Android 11+): adb puede
escribir el contenido de un push pero fallar al hacer fchown a la UID de la
app sin root, y adb devuelve un exit code != 0 aunque el archivo llegó bien.
push() debía tratar ese caso como fallo total y borrar el .part recién escrito
— aquí se verifica que ahora cae al chequeo MD5 en vez de descartarlo a ciegas.
pull() no tiene ese margen (si no puede ni abrir el archivo para leer, no hay
nada que verificar) pero su mensaje de error ahora explica que es una
restricción de permisos del dispositivo, no un fallo transitorio genérico.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import pytest

from rom_manager.sync.adb_transport import AdbTransport


@dataclass
class _FakeResult:
    returncode: int
    stdout: bytes = b""
    stderr: bytes = b""


def _md5_of(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def test_push_survives_benign_fchown_failure_when_content_matches(
    tmp_path: Path, monkeypatch
) -> None:
    local_src = tmp_path / "game.p2s"
    content = b"savestate-bytes"
    local_src.write_bytes(content)
    remote_md5 = _md5_of(content)

    transport = AdbTransport("adb", "SERIAL")
    calls: list[tuple] = []

    def fake_run(*args, timeout=None):
        calls.append(args)
        if args[0] == "push":
            return _FakeResult(
                returncode=1,
                stderr=(
                    b"adb: error: failed to copy '...' to '....part': "
                    b"remote fchown failed: Operation not permitted"
                ),
            )
        raise AssertionError(f"unexpected _run call: {args}")

    def fake_shell(*args, timeout=None):
        calls.append(("shell",) + args)
        cmd = args[0]
        if cmd.startswith("md5sum"):
            return f"{remote_md5}  target\n"
        return ""

    monkeypatch.setattr(transport, "_run", fake_run)
    monkeypatch.setattr(transport, "_shell", fake_shell)

    size = transport.push(local_src, "/storage/emulated/0/Android/data/pkg/files/game.p2s", verify=True)

    assert size == len(content)
    assert any(c[0] == "shell" and c[1].startswith("mv -f") for c in calls), (
        "esperaba que se finalizara con mv -f tras verificar el MD5"
    )
    assert not any(c[0] == "shell" and c[1].startswith("rm -f") for c in calls), (
        "no debería borrar el .part si el contenido llegó bien"
    )


def test_push_still_fails_if_fchown_error_but_content_corrupt(
    tmp_path: Path, monkeypatch
) -> None:
    local_src = tmp_path / "game.p2s"
    local_src.write_bytes(b"savestate-bytes")

    transport = AdbTransport("adb", "SERIAL")

    def fake_run(*args, timeout=None):
        if args[0] == "push":
            return _FakeResult(
                returncode=1,
                stderr=b"remote fchown failed: Operation not permitted",
            )
        raise AssertionError(f"unexpected _run call: {args}")

    def fake_shell(*args, timeout=None):
        cmd = args[0]
        if cmd.startswith("md5sum"):
            return "0" * 32 + "  target\n"  # no coincide con el local
        return ""

    monkeypatch.setattr(transport, "_run", fake_run)
    monkeypatch.setattr(transport, "_shell", fake_shell)

    with pytest.raises(OSError, match="verificación MD5"):
        transport.push(local_src, "/storage/emulated/0/Android/data/pkg/files/game.p2s", verify=True)


def test_push_still_raises_for_unrelated_errors(tmp_path: Path, monkeypatch) -> None:
    local_src = tmp_path / "game.p2s"
    local_src.write_bytes(b"x")

    transport = AdbTransport("adb", "SERIAL")

    def fake_run(*args, timeout=None):
        return _FakeResult(returncode=1, stderr=b"no devices/emulators found")

    monkeypatch.setattr(transport, "_run", fake_run)
    monkeypatch.setattr(transport, "_shell", lambda *a, timeout=None: "")

    with pytest.raises(OSError, match="adb push falló"):
        transport.push(local_src, "/sdcard/game.p2s", verify=True)


def test_pull_permission_denied_gets_clear_message(tmp_path: Path, monkeypatch) -> None:
    transport = AdbTransport("adb", "SERIAL")

    def fake_run(*args, timeout=None):
        return _FakeResult(
            returncode=1,
            stderr=b"adb: error: failed to copy '...': remote open failed: Permission denied",
        )

    monkeypatch.setattr(transport, "_run", fake_run)

    with pytest.raises(OSError, match="scoped storage"):
        transport.pull(
            "/storage/emulated/0/Android/data/pkg/files/game.p2s",
            tmp_path / "game.p2s",
        )
