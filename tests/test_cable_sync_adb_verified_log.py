"""VAL-FIX-7: ADB cable sync must record whether the MD5 post-transfer check
(AUD-2/REV43-1) actually ran and passed in save_sync_log.verified — before
this fix ADB syncs wrote a row but always left ``verified`` NULL, so the
"último sync por juego" view of Sync Doctor couldn't tell a verified save
apart from a non-save file that skipped verification entirely.
"""

from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace

import rom_manager.web.state as _state
from rom_manager.database.repository import LibraryRepository
from rom_manager.sync import adb_transport as at
from rom_manager.web.handlers.sync_cable import _do_cable_sync


class _FakeCtx:
    def __init__(self, post_data: dict) -> None:
        self._post_data = post_data
        self.out = None

    def _send_json(self, obj) -> None:
        self.out = obj


class _FakeDevice:
    """Minimal in-memory ADB device: push + md5 + mv, no real subprocess."""

    def __init__(self):
        self.files: dict[str, bytes] = {}

    def run(self, cmd, capture_output=True, timeout=None):
        import subprocess

        rest = cmd[3:]  # strip [adb, -s, serial]
        out, rc = b"", 0
        if rest[0] == "push":
            src, dst = rest[1], rest[2]
            self.files[dst] = Path(src).read_bytes()
        elif rest[0] == "shell":
            import shlex
            from hashlib import md5

            args = shlex.split(rest[1])
            if args[0] == "mkdir":
                pass
            elif args[0] == "md5sum":
                path = args[-1]
                out = f"{md5(self.files[path]).hexdigest()}  {path}\n".encode()
            elif args[0] == "mv":
                src, dst = args[-2], args[-1]
                self.files[dst] = self.files.pop(src)
            elif args[0] == "rm":
                self.files.pop(args[-1], None)
        return subprocess.CompletedProcess(cmd, rc, stdout=out, stderr=b"")


def _config(tmp_path: Path):
    return SimpleNamespace(
        adb="adb",
        project_root=tmp_path,
        library_root=str(tmp_path / "pc"),
        anbernic_root=None,
        save_extensions=(".sav",),
        backup=SimpleNamespace(saves_enabled=False),
        data_dir=tmp_path / "data",
        notify_desktop=False,
        sync=SimpleNamespace(auto_sync_direction="pc_to_anbernic"),
    )


def _wait_done() -> dict:
    for _ in range(50):
        status = _state._job_manager.get_status()
        if not status["cable_sync_running"]:
            return status["cable_sync_result"]
        time.sleep(0.05)
    raise AssertionError("cable_sync job never finished")


def test_adb_push_logs_verified_true_for_saves(tmp_path: Path, monkeypatch) -> None:
    pc = tmp_path / "pc"
    (pc / "gba").mkdir(parents=True)
    (pc / "gba" / "mario.sav").write_bytes(b"SAVEDATA")

    device = _FakeDevice()
    monkeypatch.setattr(at.subprocess, "run", device.run)
    monkeypatch.setattr(at.AdbTransport, "ls_recursive", lambda self, *a, **kw: [])

    _state._job_manager.finish("cable_sync", None)
    repo = LibraryRepository(tmp_path / "lib.sqlite")
    config = _config(tmp_path)

    ctx = _FakeCtx(
        {
            "pc_path": str(pc),
            "use_adb": True,
            "adb_serial": "SERIAL",
            "android_path": "/storage/emulated/0",
            "what": ["saves"],
            "direction": "pc_to_anbernic",
            "dry_run": False,
            "safe_mode": False,
        }
    )
    _do_cable_sync(ctx, ctx._post_data, config, repo, _state._job_manager)
    result = _wait_done()

    assert result["copied"] == 1
    assert result["errors"] == 0

    with repo.connect() as conn:
        row = conn.execute("SELECT result, verified FROM save_sync_log").fetchone()
    assert row["result"] == "ok"
    assert row["verified"] == 1
