import re
import requests

TMDB_API_KEY = "TU_API_KEY_AQUI"
TMDB_URL = "https://api.themoviedb.org/3/search/tv"


def clean_text(text):
    """Limpia tags como HD, 720p, etc."""
    if not text:
        return ""

    # elimina cosas típicas de calidad
    text = re.sub(r'\b(HD|720p|1080p|WEB|BluRay)\b', '', text, flags=re.IGNORECASE)
    return text.strip()


def parse_filename(filename):
    """
    Extrae:
    - título
    - temporada
    - episodio
    - subtítulo (nombre del capítulo)
    """

    # ejemplo: HC 08x25 - La Profeta HD
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
        "subtitle": subtitle
    }


def search_tmdb(query):
    """Busca en TMDB"""
    try:
        response = requests.get(
            TMDB_URL,
            params={
                "api_key": TMDB_API_KEY,
                "query": query,
                "language": "es-ES"
            },
            timeout=5
        )

        data = response.json()

        if data.get("results"):
            return data["results"][0]

    except Exception as e:
        print("TMDB error:", e)

    return None


def enrich_entry(parsed):
    """
    Enriquece con TMDB sin romper si falla
    """

    if not parsed:
        return None

    title = parsed["title"]
    subtitle = parsed.get("subtitle", "")

    tmdb_data = None

    # 🔴 CASO 1: título muy corto → NO buscar directamente
    if len(title) < 3:
        # intentar SOLO con subtítulo si existe
        if subtitle:
            tmdb_data = search_tmdb(subtitle)

    # 🟡 CASO 2: título corto pero usable
    elif len(title) <= 4:
        if subtitle:
            # mejor usar subtítulo solo (más preciso)
            tmdb_data = search_tmdb(subtitle)

        # fallback
        if not tmdb_data:
            tmdb_data = search_tmdb(title)

    # 🟢 CASO NORMAL
    else:
        tmdb_data = search_tmdb(title)

    # ⚠️ IMPORTANTE: NUNCA eliminar el episodio
    return {
        "title": title,
        "season": parsed["season"],
        "episode": parsed["episode"],
        "subtitle": subtitle,
        "tmdb": tmdb_data  # puede ser None y NO pasa nada
    }
