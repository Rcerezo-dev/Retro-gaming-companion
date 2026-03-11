from __future__ import annotations

import time
import urllib.error
import urllib.parse
import urllib.request
import json
from dataclasses import dataclass, field
from pathlib import Path


_API_BASE = "https://www.screenscraper.fr/api2"
_SOFT_NAME = "rommgr"


@dataclass(slots=True)
class ScraperResult:
    ss_game_id: str
    title: str
    year: str
    genre: str
    publisher: str
    developer: str
    description: str
    rating: str
    box_art_url: str


@dataclass
class ScreenScraperClient:
    user: str
    password: str
    dev_id: str = ""
    dev_password: str = ""
    # Rate limiting: free tier allows ~1 req/s
    min_interval: float = 1.2

    _last_call: float = field(default=0.0, init=False, repr=False)

    def search(
        self,
        *,
        crc32: str = "",
        md5: str = "",
        sha1: str = "",
        filename: str = "",
        size_bytes: int = 0,
        system_id: int | None = None,
        lang: str = "en",
    ) -> ScraperResult | None:
        """Query ScreenScraper for one ROM. Returns None if not found."""
        self._rate_limit()

        params: dict[str, str] = {
            "ssid": self.user,
            "sspassword": self.password,
            "softname": _SOFT_NAME,
            "output": "json",
        }
        # Only include dev credentials if provided (empty values cause 403)
        if self.dev_id:
            params["devid"] = self.dev_id
        if self.dev_password:
            params["devpassword"] = self.dev_password
        if crc32:
            params["crc"] = crc32
        if md5:
            params["md5"] = md5
        if sha1:
            params["sha1"] = sha1
        if filename:
            params["romnom"] = filename
        if size_bytes:
            params["romtaille"] = str(size_bytes)
        if system_id is not None:
            params["systemeid"] = str(system_id)

        url = f"{_API_BASE}/jeuInfos.php?{urllib.parse.urlencode(params)}"

        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 426):
                # 404 = not found
                return None
            if exc.code == 430:
                # 430 = rate limited / daily quota exceeded
                return None
            if exc.code == 403:
                raise PermissionError(
                    "ScreenScraper returned HTTP 403 — credenciales incorrectas o cuenta bloqueada. "
                    "Verifica usuario y contraseña en Settings."
                ) from exc
            raise
        except (urllib.error.URLError, OSError):
            return None

        game = data.get("response", {}).get("jeu")
        if not game:
            return None

        return self._parse(game, lang=lang)

    def search_by_name(
        self,
        name: str,
        system_id: int | None = None,
        lang: str = "en",
    ) -> ScraperResult | None:
        """Fallback search using only the game name (no hash).

        Strips region/revision tags from *name* before sending to ScreenScraper.
        Uses jeuInfos.php with romnom only; slower than hash search.
        """
        import re
        clean = re.sub(r"\s*[\(\[][^\)\]]*[\)\]]", "", name)  # strip (USA), [Rev A], etc.
        clean = clean.strip().removesuffix(Path(clean).suffix)  # remove extension
        if not clean:
            return None

        self._rate_limit()
        params: dict[str, str] = {
            "ssid": self.user,
            "sspassword": self.password,
            "softname": _SOFT_NAME,
            "output": "json",
            "romnom": clean,
        }
        if self.dev_id:
            params["devid"] = self.dev_id
        if self.dev_password:
            params["devpassword"] = self.dev_password
        if system_id is not None:
            params["systemeid"] = str(system_id)

        url = f"{_API_BASE}/jeuInfos.php?{urllib.parse.urlencode(params)}"
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 426, 430):
                return None
            raise
        except (urllib.error.URLError, OSError):
            return None

        game = data.get("response", {}).get("jeu")
        if not game:
            return None
        return self._parse(game, lang=lang)

    # ------------------------------------------------------------------

    def _rate_limit(self) -> None:
        now = time.monotonic()
        wait = self.min_interval - (now - self._last_call)
        if wait > 0:
            time.sleep(wait)
        self._last_call = time.monotonic()

    @staticmethod
    def _parse(game: dict, lang: str = "en") -> ScraperResult:
        ss_id = str(game.get("id", ""))
        title = _pick_regional(game.get("noms", []), lang) or game.get("nom", "")
        year = _pick_date(game.get("dates", []))
        genres = game.get("genres", [])
        genre = _pick_regional(genres[0].get("noms", []) if genres else [], lang) if genres else ""
        publisher = game.get("editeur", {}).get("text", "")
        developer = game.get("developpeur", {}).get("text", "")
        description = _pick_regional(game.get("synopsis", []), lang)
        rating = str(game.get("note", {}).get("text", ""))
        box_art_url = _pick_media(game.get("medias", []), ("box-2D", "box-2D-side", "screenshot"))

        return ScraperResult(
            ss_game_id=ss_id,
            title=title,
            year=year,
            genre=genre,
            publisher=publisher,
            developer=developer,
            description=description,
            rating=rating,
            box_art_url=box_art_url,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pick_regional(items: list[dict], lang: str) -> str:
    """Return the text for *lang*, falling back to 'en', then first item."""
    if not items:
        return ""
    for item in items:
        if item.get("langue") == lang:
            return item.get("text", "")
    for item in items:
        if item.get("langue") == "en":
            return item.get("text", "")
    return items[0].get("text", "")


def _pick_date(dates: list[dict]) -> str:
    """Return the first date text available, prefer 'wor' (world) region."""
    if not dates:
        return ""
    for d in dates:
        if d.get("region") == "wor":
            return d.get("text", "")[:4]
    return dates[0].get("text", "")[:4]


def _pick_media(medias: list[dict], types: tuple[str, ...]) -> str:
    """Return the URL of the first matching media type."""
    for wanted in types:
        for m in medias:
            if m.get("type") == wanted:
                return m.get("url", "")
    return ""


def download_image(url: str, dest: Path) -> bool:
    """Download *url* to *dest*. Returns True on success."""
    if not url:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            dest.write_bytes(resp.read())
        return True
    except (urllib.error.URLError, OSError):
        return False
