import re
import aiohttp
import asyncio

TMDB_API_KEY = "TU_API_KEY_AQUI"

SEARCH_TV = "https://api.themoviedb.org/3/search/tv"
SEARCH_MOVIE = "https://api.themoviedb.org/3/search/movie"

# Cache simple en memoria (evita llamadas repetidas)
_tmdb_cache = {}


# -------------------------
# UTILIDADES
# -------------------------
def clean_text(text):
    if not text:
        return ""

    return re.sub(
        r"\b(HD|720p|1080p|WEB|BluRay)\b",
        "",
        text,
        flags=re.IGNORECASE
    ).strip()


# -------------------------
# PARSER
# -------------------------
def parse_filename(filename):
    """
    Extrae:
    - title
    - season
    - episode
    - subtitle
    """

    if not filename:
        return None

    pattern = r'^(.*?)\s+(\d{1,2})x(\d{1,2})(?:\s*-\s*(.*))?'
    match = re.search(pattern, filename)

    if not match:
        return None

    title = match.group(1).strip()
    season = int(match.group(2))
    episode = int(match.group(3))
    subtitle = clean_text(match.group(4)) if match.group(4) else ""

    return {
        "title": title,
        "season": season,
        "episode": episode,
        "subtitle": subtitle,
        "is_series": True
    }


# -------------------------
# NORMALIZAR RESPUESTA TMDB
# -------------------------
def normalize_tmdb(item):
    """
    Asegura que SIEMPRE tenga las claves que usa tu frontend
    """

    if not item:
        return {
            "name": "",
            "title": "",
            "poster_path": None,
            "backdrop_path": None,
            "overview": ""
        }

    return {
        "name": item.get("name") or item.get("title") or "",
        "title": item.get("title") or item.get("name") or "",
        "poster_path": item.get("poster_path"),
        "backdrop_path": item.get("backdrop_path"),
        "overview": item.get("overview", "")
    }


# -------------------------
# FETCH TMDB
# -------------------------
async def fetch_tmdb(session, url, query):
    try:
        async with session.get(
            url,
            params={
                "api_key": TMDB_API_KEY,
                "query": query,
                "language": "es-ES"
            },
            timeout=aiohttp.ClientTimeout(total=5)
        ) as resp:

            if resp.status != 200:
                return None

            data = await resp.json()

            if data.get("results"):
                return data["results"][0]

    except Exception as e:
        print("TMDB fetch error:", e)

    return None


# -------------------------
# SEARCH TMDB (CON CACHE)
# -------------------------
async def search_tmdb(title, is_series=True, subtitle=None):
    if not title:
        return None

    title = title.strip()

    # cache key
    cache_key = f"{title}_{subtitle}_{is_series}"
    if cache_key in _tmdb_cache:
        return _tmdb_cache[cache_key]

    url = SEARCH_TV if is_series else SEARCH_MOVIE

    result = None

    try:
        async with aiohttp.ClientSession() as session:

            # 🔴 título muy corto
            if len(title) < 3:
                if subtitle:
                    result = await fetch_tmdb(session, url, subtitle)

            # 🟡 título corto
            elif len(title) <= 4:
                if subtitle:
                    result = await fetch_tmdb(session, url, subtitle)

                if not result:
                    result = await fetch_tmdb(session, url, title)

            # 🟢 normal
            else:
                result = await fetch_tmdb(session, url, title)

    except Exception as e:
        print("TMDB search error:", e)

    # guardar en cache (aunque sea None)
    _tmdb_cache[cache_key] = result

    return result


# -------------------------
# ENRICH ENTRY (FIX REAL)
# -------------------------
async def enrich_entry(entry):
    """
    NO rompe nada:
    - siempre mantiene estructura
    - nunca elimina episodios
    - nunca deja tmdb undefined
    """

    try:
        if not isinstance(entry, dict):
            return entry

        if not entry.get("media"):
            return entry

        filename = entry.get("insight", "")

        parsed = parse_filename(filename)

        if parsed:
            entry["parsed"] = parsed
        else:
            # evitar romper templates
            entry["parsed"] = {
                "title": "",
                "season": None,
                "episode": None,
                "subtitle": ""
            }
            return entry

        meta_raw = await search_tmdb(
            parsed["title"],
            parsed.get("is_series", True),
            parsed.get("subtitle")
        )

        entry["tmdb"] = normalize_tmdb(meta_raw)

    except Exception as e:
        print("enrich_entry error:", e)

        # 🔥 fallback TOTAL (evita 500)
        entry["tmdb"] = {
            "name": entry.get("parsed", {}).get("title", ""),
            "title": entry.get("parsed", {}).get("title", ""),
            "poster_path": None,
            "backdrop_path": None,
            "overview": ""
        }

    return entry
