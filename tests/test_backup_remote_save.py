"""SYNC-SAFE-2: el save de la consola se respalda antes de sobrescribirlo por ADB."""

from pathlib import Path

import pytest

from rom_manager.backup.save_backup import backup_remote_save


class _FakeTransport:
    def __init__(self, exists: bool = True, fail: bool = False):
        self.exists, self.fail = exists, fail

    def file_exists(self, android_path: str) -> bool:
        return self.exists

    def pull(self, android_src: str, local_dst: Path, *, dry_run=False, verify=False) -> int:
        if self.fail:
            raise OSError("adb pull falló")
        local_dst.parent.mkdir(parents=True, exist_ok=True)
        local_dst.write_bytes(b"SRAM-consola")
        return 12


def test_backs_up_existing_remote_save(tmp_path):
    bk = backup_remote_save(_FakeTransport(), "/sdcard/RetroArch/gba/Zelda.srm", tmp_path)
    assert bk is not None and bk.read_bytes() == b"SRAM-consola"
    assert bk.parent == tmp_path / "saves-backup" / "gba" / "Zelda"


def test_absent_remote_is_not_an_error(tmp_path):
    assert backup_remote_save(_FakeTransport(exists=False), "/x/gba/Z.srm", tmp_path) is None


def test_failed_backup_raises_so_caller_skips_push(tmp_path):
    with pytest.raises(OSError):
        backup_remote_save(_FakeTransport(fail=True), "/x/gba/Z.srm", tmp_path)
