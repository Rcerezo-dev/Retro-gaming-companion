"""CABLE-UX-9e — should_verify() es la unica fuente de la politica "MD5 solo
en saves", compartida entre sync manual y el daemon de auto-sync.
"""

from __future__ import annotations

from rom_manager.sync.adb_transport import should_verify

_SAVE_EXTS = frozenset({".sav", ".srm"})


def test_should_verify_true_for_save_extension() -> None:
    assert should_verify("game.sav", _SAVE_EXTS) is True


def test_should_verify_false_for_rom_extension() -> None:
    assert should_verify("game.zip", _SAVE_EXTS) is False


def test_should_verify_case_insensitive() -> None:
    assert should_verify("GAME.SAV", _SAVE_EXTS) is True
