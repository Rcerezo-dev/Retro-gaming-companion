"""GET /api/detect-android-ra-config-dir (B0-3c): end-to-end via the full app."""

from __future__ import annotations


def test_no_device_connected_reports_message(client):
    # tests/web/conftest.py's `config` fixture points config.adb at a
    # project-relative "tools/adb.exe" that doesn't exist under tmp_path, so
    # this deterministically exercises the "no device" path without needing
    # a real ADB binary in CI.
    data = client.get_json("/api/detect-android-ra-config-dir")

    assert data == {
        "found": False,
        "ra_config_dir": None,
        "error": "conecta el dispositivo Android por ADB primero",
    }
