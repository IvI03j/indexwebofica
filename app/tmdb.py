import re
import aiohttp

TMDB_API_KEY = "TU_API_KEY_AQUI"

SEARCH_TV = "https://api.themoviedb.org/3/search/tv"
SEARCH_MOVIE = "https://api.themoviedb.org/3/search/movie"


# -------------------------
# UTIL
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
    pattern = r'^(.*?)\s+(\d{1,2})x(\d{1,2})(?:\s*-\s*(.*))?'
    match = re.search(pattern, filename)

    if not match:
        return None

    return {
        "title": match.group(1).strip(),
        "season": int(match.group(2)),
        "episode": int(match.group(3)),
        "subtitle": clean_text(match.group(4)) if match.group(4) else "",
        "is_series": True
    }


# -------------------------
# TMDB SEARCH
# -------------------------
async def fetch_tmdb(session, url, query):
    try:
        async with session.get(
            url,
            params={
                "api_key": TMDB_API_KEY,
                "query": query,
                "language": "es-ES"
            }
        ) as resp:

            data = await resp.json()

            if data.get("results"):
                return data["results"][0]

    except Exception as e:
        print("TMDB error:", e)

    return None


async def search_tmdb(title, is_series=True, subtitle=None):
    if not title:
        return None

    title = title.strip()
    url = SEARCH_TV if is_series else SEARCH_MOVIE

    async with aiohttp.ClientSession() as session:

        # 🔴 TÍTULO MUY CORTO
        if len(title) < 3:
            if subtitle:
                return await fetch_tmdb(session, url, subtitle)
            return None

        # 🟡 TÍTULO CORTO
        if len(title) <= 4:
            if subtitle:
                result = await fetch_tmdb(session, url, subtitle)
                if result:
                    return result

            return await fetch_tmdb(session, url, title)

        # 🟢 NORMAL
        return await fetch_tmdb(session, url, title)


# -------------------------
# ENRICH (CLAVE)
# -------------------------
async def enrich_entry(entry):
    if not entry.get("media"):
        return entry

    filename = entry.get("insight", "")
    parsed = parse_filename(filename)

    if not parsed:
        return entry

    # 🔥 SIEMPRE GUARDAR PARSED
    entry["parsed"] = parsed

    meta = await search_tmdb(
        parsed["title"],
        parsed["is_series"],
        parsed.get("subtitle")
    )

    # 🔥 SI FALLA TMDB → NO BORRAR DATOS ANTIGUOS
    if meta:
        entry["tmdb"] = meta
    else:
        # 👇 CLAVE: mantener estructura para que el frontend no muera
        entry["tmdb"] = entry.get("tmdb", {
            "name": parsed["title"],
            "title": parsed["title"],
            "poster_path": None,
            "backdrop_path": None,
            "overview": ""
        })

    return entry
