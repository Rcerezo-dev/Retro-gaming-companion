"""Characterization tests for RcloneTransport routing (REV43-34).

diagnose_routing/upload/download shared the same state→saves→fallback
decision, copy-pasted 3 times. These tests lock in the exact current
behavior (including routing_reason text) before/after deduplicating the
decision into one shared helper.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from rom_manager.sync.rclone_transport import RcloneTransport

SAVE_EXTS = (".sav", ".srm")
STATE_EXTS = (".state", ".state0")


# ── diagnose_routing ──────────────────────────────────────────────────────────


class TestDiagnoseRouting:
    def _diag(self, filename: str, **kwargs) -> dict:
        t = RcloneTransport()
        return t.diagnose_routing(
            filename,
            saves_remote=kwargs.get("saves_remote"),
            states_remote=kwargs.get("states_remote"),
            save_extensions=kwargs.get("save_extensions", SAVE_EXTS),
            state_extensions=kwargs.get("state_extensions", STATE_EXTS),
            fallback_remote=kwargs.get("fallback_remote"),
        )

    def test_state_ext_routes_to_states_remote(self):
        d = self._diag("game.state", saves_remote="s:/saves", states_remote="s:/states")
        assert d["routing_decision"] == "s:/states"
        assert d["routing_reason"] == "state extension (.state)"

    def test_save_ext_routes_to_saves_remote(self):
        d = self._diag("game.sav", saves_remote="s:/saves", states_remote="s:/states")
        assert d["routing_decision"] == "s:/saves"
        assert d["routing_reason"] == "save extension (.sav)"

    def test_state_ext_without_states_remote_falls_back_to_explicit_fallback(self):
        d = self._diag("game.state", saves_remote="s:/saves", fallback_remote="s:/fallback")
        assert d["routing_decision"] == "s:/fallback"
        assert d["routing_reason"] == (
            "matches state ext (.state) but states_remote not configured "
            "→ using fallback_remote"
        )

    def test_state_ext_without_states_remote_defaults_to_saves_remote(self):
        d = self._diag("game.state", saves_remote="s:/saves")
        assert d["routing_decision"] == "s:/saves"
        assert d["routing_reason"] == (
            "matches state ext (.state) but states_remote not configured "
            "→ using saves_remote (default)"
        )

    def test_save_ext_without_saves_remote_defaults_to_states_remote(self):
        d = self._diag("game.sav", states_remote="s:/states")
        assert d["routing_decision"] == "s:/states"
        assert d["routing_reason"] == (
            "matches save ext (.sav) but saves_remote not configured "
            "→ using states_remote (default)"
        )

    def test_unknown_ext_uses_fallback(self):
        d = self._diag("readme.txt", saves_remote="s:/saves", fallback_remote="s:/fallback")
        assert d["routing_decision"] == "s:/fallback"
        assert d["routing_reason"] == "unknown extension (.txt) → using fallback_remote"

    def test_unknown_ext_defaults_to_saves_remote(self):
        d = self._diag("readme.txt", saves_remote="s:/saves")
        assert d["routing_decision"] == "s:/saves"
        assert d["routing_reason"] == "unknown extension (.txt) → using saves_remote (default)"

    def test_unknown_ext_defaults_to_states_remote_when_no_saves_remote(self):
        d = self._diag("readme.txt", states_remote="s:/states")
        assert d["routing_decision"] == "s:/states"
        assert d["routing_reason"] == "unknown extension (.txt) → using states_remote (default)"

    def test_no_remote_configured_is_an_error(self):
        d = self._diag("readme.txt")
        assert d["routing_decision"] == "(ERROR: no remote)"
        assert d["routing_reason"] == "unknown extension (.txt) → NO REMOTE CONFIGURED (ERROR)"

    def test_config_summary_reports_extension_overlap(self):
        d = self._diag(
            "game.sav",
            saves_remote="s:/saves",
            save_extensions=(".sav", ".srm"),
            state_extensions=(".srm", ".state"),
        )
        assert d["config_summary"]["extension_overlap"] == 1


# ── upload / download routing (which remote gets the copyto) ─────────────────


class TestUploadDownloadRouting:
    def _transport_capturing_run(self):
        t = RcloneTransport()
        t._run = MagicMock(return_value="")
        return t

    def test_upload_state_ext_goes_to_states_remote(self, tmp_path: Path):
        local = tmp_path / "game.state"
        local.write_bytes(b"x")
        t = self._transport_capturing_run()
        t.upload(
            local,
            "Genesis/game.state",
            saves_remote="s:/saves",
            states_remote="s:/states",
            save_extensions=SAVE_EXTS,
            state_extensions=STATE_EXTS,
        )
        args = t._run.call_args[0][0]
        assert args == ["copyto", str(local), "s:/states/Genesis/game.state"]

    def test_upload_save_ext_goes_to_saves_remote(self, tmp_path: Path):
        local = tmp_path / "game.sav"
        local.write_bytes(b"x")
        t = self._transport_capturing_run()
        t.upload(
            local,
            "Genesis/game.sav",
            saves_remote="s:/saves",
            states_remote="s:/states",
            save_extensions=SAVE_EXTS,
            state_extensions=STATE_EXTS,
        )
        args = t._run.call_args[0][0]
        assert args == ["copyto", str(local), "s:/saves/Genesis/game.sav"]

    def test_upload_unknown_ext_falls_back_to_fallback_remote(self, tmp_path: Path):
        local = tmp_path / "game.bin"
        local.write_bytes(b"x")
        t = self._transport_capturing_run()
        t.upload(
            local,
            "Genesis/game.bin",
            saves_remote="s:/saves",
            states_remote="s:/states",
            save_extensions=SAVE_EXTS,
            state_extensions=STATE_EXTS,
            fallback_remote="s:/fallback",
        )
        args = t._run.call_args[0][0]
        assert args == ["copyto", str(local), "s:/fallback/Genesis/game.bin"]

    def test_upload_no_remote_configured_raises(self, tmp_path: Path):
        local = tmp_path / "game.bin"
        local.write_bytes(b"x")
        t = self._transport_capturing_run()
        with pytest.raises(ValueError, match="no suitable remote configured"):
            t.upload(local, "Genesis/game.bin")

    def test_download_state_ext_reads_from_states_remote(self, tmp_path: Path):
        local = tmp_path / "out" / "game.state"
        t = self._transport_capturing_run()
        t.download(
            "Genesis/game.state",
            local,
            saves_remote="s:/saves",
            states_remote="s:/states",
            save_extensions=SAVE_EXTS,
            state_extensions=STATE_EXTS,
        )
        args = t._run.call_args[0][0]
        assert args == ["copyto", "s:/states/Genesis/game.state", str(local)]

    def test_download_save_ext_reads_from_saves_remote(self, tmp_path: Path):
        local = tmp_path / "out" / "game.sav"
        t = self._transport_capturing_run()
        t.download(
            "Genesis/game.sav",
            local,
            saves_remote="s:/saves",
            states_remote="s:/states",
            save_extensions=SAVE_EXTS,
            state_extensions=STATE_EXTS,
        )
        args = t._run.call_args[0][0]
        assert args == ["copyto", "s:/saves/Genesis/game.sav", str(local)]

    def test_download_no_remote_configured_raises(self, tmp_path: Path):
        t = self._transport_capturing_run()
        with pytest.raises(ValueError, match="no suitable remote configured"):
            t.download("Genesis/game.bin", tmp_path / "game.bin")
