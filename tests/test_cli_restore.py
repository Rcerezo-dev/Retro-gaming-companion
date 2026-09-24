"""Self-check for `rommgr restore` (DEVPROFILE-5b-5e)."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from rom_manager.cli import main
from rom_manager.sync.rclone_transport import RcloneTransport


def test_restore_downloads_manifest_and_writes_config(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "builtins.input", lambda *a, **k: ""
    )  # accept every default (skip RetroArch)

    manifest = [
        {
            "name": "RetroArch Shaders",
            "local_dir": "{SYSTEM}/../shaders",
            "remote": "dropbox:RetroSync/shaders",
            "sync_all": True,
        }
    ]

    def _fake_run(args: list[str]) -> str:
        if args[0] == "copyto" and args[1] == "dropbox:RetroSync/device-profile.json":
            Path(args[2]).write_text(json.dumps(manifest), encoding="utf-8")
            return ""
        if args[0] == "lsjson":
            return "[]"  # no remote files → nothing to download in the Tier A pass
        raise AssertionError(f"unexpected rclone invocation: {args}")

    monkeypatch.setattr(RcloneTransport, "_run", lambda self, args: _fake_run(args))

    library_dir = tmp_path / "library"
    rc = main(
        [
            "restore",
            "--remote",
            "dropbox:RetroSync",
            "--rclone",
            "fake-rclone",
            "--library-dir",
            str(library_dir),
        ]
    )

    assert rc == 0
    toml_path = tmp_path / "config.toml"
    assert toml_path.exists()
    written = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    assert written["library"]["library_root"] == str(library_dir.resolve())
    assert written["sync"]["sources"][0]["name"] == "RetroArch Shaders"
    # Tier A source's local_dir must be resolved against *this* device's roots, not a token.
    assert "{SYSTEM}" not in written["sync"]["sources"][0]["local_dir"]
