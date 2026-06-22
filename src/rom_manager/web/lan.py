"""LAN address detection — pure stdlib, no external dependencies."""

from __future__ import annotations

import socket


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
