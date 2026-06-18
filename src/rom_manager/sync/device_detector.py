"""Android device connectivity detection (UX-1/2).

Extracted from ``AppConfig`` (ARC-CFG-3) so the check is a pure function of its
inputs (an ADB binary path and an SD-card root) instead of a method coupled to
the whole config object.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

_logger = logging.getLogger(__name__)


def is_device_connected(adb_path: str | None, android_root: str | None) -> tuple[bool, str]:
    """Check if an Android device is connected.

    Returns ``(connected, reason)`` where ``reason`` explains the status.
    Device is connected if EITHER:
    - ADB device is available (Android device plugged in via USB), OR
    - SD card is mounted at ``android_root``.

    Checks in order: ADB first (more reliable), then SD card.
    """
    # Check ADB device
    if adb_path:
        try:
            result = subprocess.run(
                [adb_path, "devices"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            # Parse output for connected devices (exclude "daemon started" and headers)
            lines = result.stdout.strip().split("\n")[1:]  # skip "List of attached devices"
            for line in lines:
                if "\t" in line:
                    device_id, status = line.split("\t", 1)
                    if status.strip() == "device":  # online device
                        return True, f"ADB device: {device_id}"
        except Exception:
            _logger.debug("ADB device check failed, falling back to SD card", exc_info=True)

    # Check SD card mount
    if android_root:
        try:
            root_path = Path(android_root).expanduser().resolve()
            if root_path.exists() and root_path.is_dir():
                # Check if path is accessible (can list it)
                list(root_path.iterdir())
                return True, f"SD card mounted: {android_root}"
        except (OSError, PermissionError):
            pass  # SD card path not accessible

    # Not connected
    if adb_path and android_root:
        reason = "Device not found (not plugged in via ADB, SD card not mounted)"
    elif adb_path:
        reason = "Android device not connected via ADB"
    elif android_root:
        reason = f"SD card not mounted at {android_root}"
    else:
        reason = "No device configured (anbernic_root or adb not set)"

    return False, reason
