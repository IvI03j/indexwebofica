import re
import aiohttp

TMDB_API_KEY = "TU_API_KEY_AQUI"
TMDB_URL = "https://api.themoviedb.org/3/search/tv"


# -------------------------
# PARSER
# -------------------------
def clean_text(text):
    if not text:
        return ""

    text = re.sub(r'\b(HD|720p|1080p|WEB|BluRay)\b', '', text, flags=re.IGNORECASE)
    return text.strip()


def parse_filename(filename):
    """
    Extrae:
    - título
    - temporada
    - episodio
    - subtítulo
    """

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
# TMDB SEARCH (ASYNC)
# -------------------------
async def search_tmdb(title, is_series=True, subtitle=None):
    """
    Busca en TMDB de forma segura
    """

    if not title:
        return None

    title_clean = title.strip()

    # 🔴 Título muy corto → evitar basura
    if len(title_clean) < 3:
        if subtitle:
            query = subtitle
        else:
            return None

    # 🟡 Título corto
    elif len(title_clean) <= 4:
        if subtitle:
            query = subtitle  # 🔥 mejor que combinar
        else:
            query = title_clean

    # 🟢 Normal
    else:
        query = title_clean

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                TMDB_URL,
                params={
                    "api_key": TMDB_API_KEY,
                    "query": query,
                    "language": "es-ES"
                },
                timeout=5
            ) as resp:

                data = await resp.json()

                if data.get("results"):
                    return data["results"][0]

    except Exception as e:
        print("TMDB error:", e)

    return None


# -------------------------
# ENRICH (FIX DEFINITIVO)
# -------------------------
async def enrich_entry(entry):
    """
    Enriquece sin romper la app
    """

    if not entry.get("media"):
        return entry

    filename = entry.get("insight", "")
    parsed = parse_filename(filename)

    if not parsed:
        return entry

    # 🔥 CLAVE: SIEMPRE guardar parsed
    entry["parsed"] = parsed

    meta = await search_tmdb(
        parsed["title"],
        parsed.get("is_series", True),
        subtitle=parsed.get("subtitle"),
    )

    # 🔥 TMDB opcional (NUNCA rompe)
    entry["tmdb"] = meta if meta else None

    return entry
