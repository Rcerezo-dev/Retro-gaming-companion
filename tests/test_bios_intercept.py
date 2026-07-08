"""INBOX-FIX-3: BIOS interception is shared between the Inbox pipeline and the
first-time setup wizard, and covers the arcade system BIOS found loose in
Unknown\\ during JUNK-REVIEW-1."""

from __future__ import annotations

import logging
from pathlib import Path

from rom_manager.web.inbox_pipeline import _KNOWN_BIOS_MAP, _intercept_bios_files

_logger = logging.getLogger(__name__)


def test_arcade_bios_entries_present() -> None:
    """Systems found loose in Unknown\\ (JUNK-REVIEW-1) must resolve to a slug."""
    for name in (
        "naomi.zip",
        "chihiro.zip",
        "triforce.zip",
        "hikaru.zip",
        "aristmk5.zip",
        "aristmk6.zip",
        "hod2bios.zip",
        "lindbios.zip",
        "f355bios.zip",
        "galgbios.zip",
        "airlbios.zip",
        "ar_bios.zip",
        "cdibios.zip",
        "macsbios.zip",
        "alg_bios.zip",
        "crysbios.zip",
        "v4bios.zip",
    ):
        assert name in _KNOWN_BIOS_MAP, f"{name} missing from _KNOWN_BIOS_MAP"


def test_intercept_moves_known_bios_and_leaves_unknown_files(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "naomi.zip").write_bytes(b"bios")
    (inbox / "Sonic (USA).zip").write_bytes(b"game")  # not a known BIOS — must stay

    moved = _intercept_bios_files(inbox, inbox, _logger)

    assert moved == 1
    assert not (inbox / "naomi.zip").exists()
    assert (inbox / "bios" / "naomi" / "naomi.zip").read_bytes() == b"bios"
    assert (inbox / "Sonic (USA).zip").exists()


def test_intercept_exact_duplicate_in_dest_deletes_source(tmp_path: Path) -> None:
    """Same name AND same content (SHA1 match) -> genuinely a duplicate, safe to delete."""
    inbox = tmp_path / "inbox"
    dest_dir = inbox / "bios" / "naomi"
    dest_dir.mkdir(parents=True)
    (dest_dir / "naomi.zip").write_bytes(b"identical bios bytes")
    (inbox / "naomi.zip").write_bytes(b"identical bios bytes")

    moved = _intercept_bios_files(inbox, inbox, _logger)

    assert moved == 1
    assert not (inbox / "naomi.zip").exists()
    assert (dest_dir / "naomi.zip").read_bytes() == b"identical bios bytes"  # untouched


def test_intercept_same_name_different_content_touches_neither(tmp_path: Path) -> None:
    """INBOX-FIX-5: same filename but different bytes must NOT be deleted as a duplicate."""
    inbox = tmp_path / "inbox"
    dest_dir = inbox / "bios" / "naomi"
    dest_dir.mkdir(parents=True)
    (dest_dir / "naomi.zip").write_bytes(b"already there")
    (inbox / "naomi.zip").write_bytes(b"different bios revision")

    moved = _intercept_bios_files(inbox, inbox, _logger)

    assert moved == 0
    assert (
        inbox / "naomi.zip"
    ).read_bytes() == b"different bios revision"  # untouched, not deleted
    assert (dest_dir / "naomi.zip").read_bytes() == b"already there"  # untouched


def test_intercept_skips_internal_underscore_folders(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    processed = inbox / "_processed"
    processed.mkdir(parents=True)
    (processed / "naomi.zip").write_bytes(b"bios")

    moved = _intercept_bios_files(inbox, inbox, _logger)

    assert moved == 0
    assert (processed / "naomi.zip").exists()
