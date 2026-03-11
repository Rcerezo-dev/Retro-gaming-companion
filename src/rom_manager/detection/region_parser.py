from __future__ import annotations

import re

# No-Intro canonical region names (appear in parentheses in filenames).
# The key is the lowercase version of what appears inside the parens.
_NOINTRO_REGIONS: dict[str, str] = {
    "usa": "USA",
    "europe": "Europe",
    "japan": "Japan",
    "world": "World",
    "spain": "Spain",
    "germany": "Germany",
    "france": "France",
    "italy": "Italy",
    "korea": "Korea",
    "china": "China",
    "brazil": "Brazil",
    "australia": "Australia",
    "netherlands": "Netherlands",
    "sweden": "Sweden",
    "norway": "Norway",
    "denmark": "Denmark",
    "finland": "Finland",
    "portugal": "Portugal",
    "russia": "Russia",
    "poland": "Poland",
    "greece": "Greece",
    "czech": "Czech",
    "hungary": "Hungary",
    "romania": "Romania",
    "canada": "Canada",
    "mexico": "Mexico",
    "taiwan": "Taiwan",
    "hong kong": "Hong Kong",
    "asia": "Asia",
    "scandinavia": "Scandinavia",
}

# GoodTools bracket codes: the key is the bracket content in lowercase, e.g. "u" for "[U]".
# Using content-only (without brackets) to avoid false positives when matching
# against the full bracket content extracted by _BRACKET_PATTERN.
_GOODTOOLS_CODES: dict[str, str] = {
    "u": "USA",
    "e": "Europe",
    "j": "Japan",
    "b": "Brazil",
    "c": "China",
    "a": "Australia",
    "f": "France",
    "g": "Germany",
    "s": "Spain",
    "i": "Italy",
    "k": "Korea",
    "nl": "Netherlands",
    "sw": "Sweden",
    "no": "Norway",
}

_PAREN_PATTERN = re.compile(r"\(([^)]+)\)")
_BRACKET_PATTERN = re.compile(r"\[([^\]]+)\]")


def parse_region_from_name(name: str) -> str:
    """Return the region detected from a ROM filename, or 'UNK' if none found."""
    # 1. No-Intro style: "(USA)", "(Europe)", "(USA, Europe)", …
    for match in _PAREN_PATTERN.finditer(name):
        for part in match.group(1).split(","):
            region = _NOINTRO_REGIONS.get(part.strip().casefold())
            if region:
                return region

    # 2. GoodTools bracket codes: "[U]", "[E]", "[NL]", …
    # Extract each bracket's full content and compare exactly to avoid
    # false positives like "[g]" matching inside "[Gauntlet]".
    for match in _BRACKET_PATTERN.finditer(name):
        region = _GOODTOOLS_CODES.get(match.group(1).casefold())
        if region:
            return region

    # 3. Plain-text fallbacks for common informal naming
    lowered = name.casefold()
    if bool(re.search(r'\bjapan\b', lowered)) or bool(re.search(r'\bjpn\b', lowered)):
        return "Japan"
    if bool(re.search(r'\bpal\b', lowered)):
        return "Europe"

    return "UNK"
