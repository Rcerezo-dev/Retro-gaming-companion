def test_identical_save_is_not_backed_up_twice(tmp_path, monkeypatch):
    from rom_manager.backup import save_backup
    from rom_manager.backup.save_backup import backup_save

    stamps = iter(["20260101T000001Z", "20260101T000002Z"])
    monkeypatch.setattr(save_backup, "_ts", lambda: next(stamps))

    save = tmp_path / "gba" / "Zelda.srm"
    save.parent.mkdir()
    save.write_bytes(b"A")
    first = backup_save(save, tmp_path / "bk")
    assert backup_save(save, tmp_path / "bk") == first
    save.write_bytes(b"B")
    assert backup_save(save, tmp_path / "bk") != first
