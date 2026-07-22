"""LAN address detection — pure stdlib, no external dependencies."""

from __future__ import annotations

import socket
import subprocess
import sys
import time


def get_lan_ip() -> str | None:
    """Return the primary LAN IPv4 address of this machine, or None."""
    try:
        # Connect to an external address without actually sending anything;
        # the OS assigns the right source IP for the default route.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return None


def get_mdns_name() -> str | None:
    """Return hostname.local (ASCII or punycode-encoded) for mDNS access."""
    try:
        hostname = socket.gethostname()
        try:
            hostname.encode("ascii")
            label = hostname.lower()
        except UnicodeEncodeError:
            # Convert to IDNA/punycode so browsers can use it as a valid URL
            label = hostname.lower().encode("idna").decode("ascii")
        return f"{label}.local"
    except (OSError, UnicodeError):
        return None


def lan_urls(port: int) -> list[str]:
    """Return the LAN URL(s) where the server can be reached from other devices."""
    urls: list[str] = []
    ip = get_lan_ip()
    mdns = get_mdns_name()
    if mdns:
        urls.append(f"http://{mdns}:{port}/")
    if ip:
        urls.append(f"http://{ip}:{port}/")
    return urls


_FIREWALL_RULE_NAME = "Retro Vault (LAN)"

# ANBERNIC-UX-9: el estado del firewall no cambia entre refrescos de pestaña;
# cachear evita un subprocess (netsh, decenas de ms) en cada GET /api/local-url.
_FIREWALL_CACHE_TTL_S = 60.0
_firewall_cache: dict[int, tuple[bool, float]] = {}


def _check_firewall(port: int) -> bool:
    """Return True if the Retro Vault inbound firewall rule exists (Windows only).
    Returns True on non-Windows (no firewall to worry about)."""
    cached = _firewall_cache.get(port)
    now = time.time()
    if cached and now - cached[1] < _FIREWALL_CACHE_TTL_S:
        return cached[0]

    if sys.platform != "win32":
        result = True
    else:
        try:
            proc = subprocess.run(
                [
                    "netsh",
                    "advfirewall",
                    "firewall",
                    "show",
                    "rule",
                    f"name={_FIREWALL_RULE_NAME}",
                    "dir=in",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            out = proc.stdout
            result = ("Permitir" in out or "Allow" in out) and proc.returncode == 0
        except Exception:
            result = True  # can't check → don't warn

    _firewall_cache[port] = (result, now)
    return result
