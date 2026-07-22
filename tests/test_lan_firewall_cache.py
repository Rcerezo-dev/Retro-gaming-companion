"""ANBERNIC-UX-9: _check_firewall cachea su resultado — no un subprocess por llamada."""

from __future__ import annotations

from unittest.mock import patch

from rom_manager.web import lan


def test_check_firewall_caches_result_within_ttl() -> None:
    lan._firewall_cache.clear()
    with patch.object(lan, "sys") as mock_sys, patch.object(lan.subprocess, "run") as mock_run:
        mock_sys.platform = "win32"
        mock_run.return_value.stdout = "Permitir  Allow  Enabled"
        mock_run.return_value.returncode = 0

        assert lan._check_firewall(7777) is True
        assert lan._check_firewall(7777) is True
        assert mock_run.call_count == 1  # segunda llamada sirvió de la caché


def test_check_firewall_recomputes_after_ttl_expires() -> None:
    lan._firewall_cache.clear()
    with (
        patch.object(lan, "sys") as mock_sys,
        patch.object(lan.subprocess, "run") as mock_run,
        patch.object(lan, "time") as mock_time,
    ):
        mock_sys.platform = "win32"
        mock_run.return_value.stdout = "Permitir"
        mock_run.return_value.returncode = 0

        mock_time.time.return_value = 1000.0
        assert lan._check_firewall(7777) is True
        mock_time.time.return_value = 1000.0 + lan._FIREWALL_CACHE_TTL_S + 1
        assert lan._check_firewall(7777) is True

        assert mock_run.call_count == 2
