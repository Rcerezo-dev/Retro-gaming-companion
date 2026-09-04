from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class CatalogEntry:
    title: str
    sha1: str
    md5: str
    crc32: str
    size_bytes: int
    serial: str = ""  # CATALOG-MATCH-REGION-1: disc serial (Redump clrmamepro DATs only, e.g. "SLUS-00402")


def _detect_dat_format(path: Path) -> str:
    """Return 'xml' or 'clrmamepro' by sniffing the first non-empty line."""
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                return "xml" if stripped.startswith("<") else "clrmamepro"
    return "xml"


def _iter_clrmamepro_blocks(text: str) -> Iterator[tuple[str, str]]:
    """Yield (keyword, body) for each top-level block in clrmamepro text."""
    pos = 0
    length = len(text)
    kw_re = re.compile(r"([A-Za-z]\w*)\s*\(")
    while pos < length:
        m = kw_re.search(text, pos)
        if not m:
            break
        keyword = m.group(1).lower()
        i = m.end()
        depth = 1
        while i < length and depth:
            c = text[i]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            i += 1
        yield keyword, text[m.end() : i - 1]
        pos = i


_ATTR_RE = re.compile(r'(\w+)\s+(?:"([^"]*)"|([\w.\-]+))')


def _parse_clrmamepro_attrs(body: str) -> dict[str, str]:
    return {
        m.group(1).lower(): (m.group(2) if m.group(2) is not None else m.group(3))
        for m in _ATTR_RE.finditer(body)
    }


def _top_level_text(body: str) -> str:
    """Return only the text outside nested (...) blocks, respecting quoted strings."""
    out: list[str] = []
    depth, in_quote = 0, False
    for ch in body:
        if in_quote:
            out.append(ch)
            if ch == '"':
                in_quote = False
        elif ch == '"':
            in_quote = True
            if depth == 0:
                out.append(ch)
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def load_clrmamepro_dat(path: Path) -> dict[str, CatalogEntry]:
    """Parse a clrmamepro-format DAT and return sha1→CatalogEntry."""
    text = path.read_text(encoding="utf-8", errors="replace")
    entries: dict[str, CatalogEntry] = {}
    for keyword, body in _iter_clrmamepro_blocks(text):
        if keyword != "game":
            continue
        game_attrs = _parse_clrmamepro_attrs(_top_level_text(body))
        title = game_attrs.get("name", "").strip()
        serial = game_attrs.get("serial", "").strip()
        for rom_kw, rom_body in _iter_clrmamepro_blocks(body):
            if rom_kw != "rom":
                continue
            r = _parse_clrmamepro_attrs(rom_body)
            sha1 = r.get("sha1", "").strip().upper()
            if not sha1:
                continue
            entries[sha1] = CatalogEntry(
                title=title,
                sha1=sha1,
                md5=r.get("md5", "").strip().upper(),
                crc32=r.get("crc", "").strip().upper(),
                size_bytes=int(r.get("size", 0) or 0),
                serial=serial,
            )
    return entries


def load_nointro_dat(path: Path) -> dict[str, CatalogEntry]:
    """Parse a No-Intro DAT file (Logiqx XML) and return a sha1→CatalogEntry mapping.

    The DAT format looks like:
        <game name="Tetris (World) (Rev 1)">
            <rom name="..." size="32768" crc="46df91ad" md5="..." sha1="..."/>
        </game>

    SHA1 keys are stored in uppercase to match the output of hash_calculator.
    """
    tree = ET.parse(path)
    root = tree.getroot()

    entries: dict[str, CatalogEntry] = {}
    for game in root.iter("game"):
        title = game.get("name", "").strip()
        for rom in game.findall("rom"):
            sha1 = rom.get("sha1", "").strip().upper()
            if not sha1:
                continue
            entries[sha1] = CatalogEntry(
                title=title,
                sha1=sha1,
                md5=rom.get("md5", "").strip().upper(),
                crc32=rom.get("crc", "").strip().upper(),
                # INICIO-FIX-1: size="" en DATs reales — or 0 como sus gemelos
                size_bytes=int(rom.get("size", 0) or 0),
            )
    return entries


def load_dat_file(path: Path) -> dict[str, CatalogEntry]:
    """Load a single DAT file, auto-detecting XML vs clrmamepro format."""
    if _detect_dat_format(path) == "clrmamepro":
        return load_clrmamepro_dat(path)
    return load_nointro_dat(path)


def load_dat_directory(directory: Path) -> dict[str, CatalogEntry]:
    """Load all .dat files from a directory and merge them into a single mapping.

    Later files overwrite earlier ones on SHA1 collision (last file wins).
    """
    merged: dict[str, CatalogEntry] = {}
    for dat_file in sorted(directory.glob("*.dat")):
        merged.update(load_dat_file(dat_file))
    return merged


def load_nointro_dat_with_header(path: Path) -> tuple[str, dict[str, CatalogEntry]]:
    """Parse a No-Intro/Redump DAT file and return (platform_label, sha1→CatalogEntry).

    platform_label is extracted from <header><name>, with the "No-Intro: " or "Redump - "
    prefix stripped.  Falls back to the file stem if the header element is absent.
    """
    tree = ET.parse(path)
    root = tree.getroot()

    platform_label = path.stem
    header_el = root.find("header")
    if header_el is not None:
        name_el = header_el.find("name")
        if name_el is not None and name_el.text:
            platform_label = name_el.text.strip()
            # Strip "No-Intro: " / "Redump - " prefix
            platform_label = re.sub(
                r"^(No-Intro|Redump)[:\s\-]+", "", platform_label, flags=re.IGNORECASE
            ).strip()

    entries: dict[str, CatalogEntry] = {}
    for game in root.iter("game"):
        title = game.get("name", "").strip()
        for rom in game.findall("rom"):
            sha1 = rom.get("sha1", "").strip().upper()
            if not sha1:
                continue
            entries[sha1] = CatalogEntry(
                title=title,
                sha1=sha1,
                md5=rom.get("md5", "").strip().upper(),
                crc32=rom.get("crc", "").strip().upper(),
                size_bytes=int(rom.get("size", 0) or 0),
            )
    return platform_label, entries


def load_dat_files_by_platform(
    *directories: Path,
) -> list[tuple[str, dict[str, CatalogEntry]]]:
    """Load each .dat file in the given directories separately.

    Returns a list of (platform_label, sha1→CatalogEntry) tuples, one per file.
    Non-existent directories are silently skipped.
    """
    results: list[tuple[str, dict[str, CatalogEntry]]] = []
    for directory in directories:
        if not directory.exists():
            continue
        for dat_file in sorted(directory.glob("*.dat")):
            try:
                if _detect_dat_format(dat_file) == "clrmamepro":
                    entries = load_clrmamepro_dat(dat_file)
                    platform_label = dat_file.stem
                else:
                    platform_label, entries = load_nointro_dat_with_header(dat_file)
                if entries:
                    results.append((platform_label, entries))
            except ET.ParseError:
                continue
    return results
