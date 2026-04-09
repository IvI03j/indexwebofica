import re
import os
import logging
import aiohttp

log = logging.getLogger(__name__)

TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")
BASE_URL = "https://api.themoviedb.org/3"
POSTER_BASE = "https://image.tmdb.org/t/p/w500"
BACKDROP_BASE = "https://image.tmdb.org/t/p/w1280"

_metadata_cache = {}
_genre_cache = {}

# Palabras de calidad/tags que no forman parte del título ni del subtítulo
_QUALITY_TAGS = re.compile(
    r'\b(HD|SD|4K|UHD|720p?|1080p?|2160p?|BluRay|BDRip|WEB[-\s]?DL|WEBRip|HDTV|DVDRip|x264|x265|HEVC|AAC|AC3|DTS|Remux)\b',
    flags=re.IGNORECASE
)


def parse_filename(filename):
    name = re.sub(r'\.[a-zA-Z0-9]{2,4}$', '', filename)

    series_match = re.search(
        r'[Ss](\d{1,2})[Ee](\d{1,2})|(\d{1,2})x(\d{2})', name
    )

    episode_subtitle = None

    if series_match:
        is_series = True
        if series_match.group(1):
            season = int(series_match.group(1))
            episode = int(series_match.group(2))
        else:
            season = int(series_match.group(3))
            episode = int(series_match.group(4))
        before = name[:series_match.start()].strip()
        after = name[series_match.end():].strip()
        raw_title = before if len(re.sub(r'[\._\-\s]+', '', before)) >= 2 else after

        # Extraer subtítulo del episodio: lo que hay DESPUÉS del código SxEE
        # limpiando tags de calidad
        after_clean = _QUALITY_TAGS.sub('', after)
        after_clean = re.sub(r'[\._\-]+', ' ', after_clean).strip()
        after_clean = re.sub(r'\s+', ' ', after_clean).strip()
        after_clean = re.sub(r'^[\s\-]+', '', after_clean).strip()
        if len(after_clean) >= 3:
            episode_subtitle = after_clean
    else:
        is_series = False
        season = None
        episode = None
        year_match = re.search(r'\b(19|20)\d{2}\b', name)
        raw_title = name[:year_match.start()] if year_match else name

    title = re.sub(r'[\._\-]+', ' ', raw_title).strip()
    title = re.sub(r'\s+', ' ', title).strip()

    return {
        'title': title,
        'is_series': is_series,
        'season': season,
        'episode': episode,
        'episode_subtitle': episode_subtitle,
    }


async def _fetch_genres(session):
    global _genre_cache
    if _genre_cache:
        return
    for media_type in ["movie", "tv"]:
        try:
            url = f"{BASE_URL}/genre/{media_type}/list"
            async with session.get(url, params={"api_key": TMDB_API_KEY, "language": "es-ES"}) as r:
                data = await r.json()
                for g in data.get("genres", []):
                    _genre_cache[g["id"]] = g["name"]
        except Exception as e:
            log.debug(f"Genre fetch error: {e}")


async def _fetch_trailer_url(session, tmdb_id, is_series=False):
    try:
        media_type = "tv" if is_series else "movie"
        url = f"{BASE_URL}/{media_type}/{tmdb_id}/videos"
        async with session.get(url, params={"api_key": TMDB_API_KEY, "language": "es-ES"}) as r:
            data = await r.json()
            results = data.get("results", [])

            for video in results:
                if (
                    video.get("site") == "YouTube" and
                    video.get("type") == "Trailer" and
                    video.get("key")
                ):
                    return f"https://www.youtube.com/watch?v={video['key']}"

            for video in results:
                if video.get("site") == "YouTube" and video.get("key"):
                    return f"https://www.youtube.com/watch?v={video['key']}"

    except Exception as e:
        log.debug(f"Trailer fetch error: {e}")

    return None


async def search_tmdb(title, is_series=False, subtitle=None):
    if not TMDB_API_KEY or not title.strip():
        return None

    title_clean = re.sub(r'\s+', '', title)

    # Título muy corto (abreviatura como "HC"): buscar directamente con el subtítulo si está disponible
    if len(title_clean) < 3:
        if subtitle and len(subtitle.strip()) >= 5:
            search_query = subtitle
            log.debug(f"Título '{title}' muy corto, buscando con subtítulo: '{search_query}'")
        else:
            log.debug(f"Título '{title}' demasiado corto y sin subtítulo, se omite.")
            return None
    # Título corto (3-4 chars): combinar título + subtítulo para mayor precisión
    elif len(title_clean) <= 4 and subtitle:
        search_query = f"{title} {subtitle}"
        log.debug(f"Título corto '{title}', usando búsqueda ampliada: '{search_query}'")
    else:
        search_query = title

    cache_key = f"{search_query.lower()}_{is_series}"
    if cache_key in _metadata_cache:
        return _metadata_cache[cache_key]

    params = {"api_key": TMDB_API_KEY, "query": search_query, "language": "es-ES"}

    async with aiohttp.ClientSession() as session:
        await _fetch_genres(session)

        result = None
        for endpoint in (
            "search/tv" if is_series else "search/movie",
            "search/movie" if is_series else "search/tv",
            "search/multi",
        ):
            try:
                async with session.get(f"{BASE_URL}/{endpoint}", params=params) as r:
                    data = await r.json()
                    results = data.get("results", [])
                    if results:
                        result = results[0]
                        if endpoint == "search/tv" or result.get("media_type") == "tv":
                            is_series = True
                        elif endpoint == "search/movie" or result.get("media_type") == "movie":
                            is_series = False
                        break
            except Exception as e:
                log.debug(f"TMDB search error ({endpoint}): {e}")

        if not result:
            _metadata_cache[cache_key] = None
            return None

        poster_path = result.get("poster_path")
        backdrop_path = result.get("backdrop_path")
        genre_ids = result.get("genre_ids", [])
        genres = [_genre_cache.get(gid) for gid in genre_ids if gid in _genre_cache]
        tmdb_id = result.get("id")

        trailer_url = None
        if tmdb_id:
            trailer_url = await _fetch_trailer_url(session, tmdb_id, is_series=is_series)

        metadata = {
            "title": result.get("title") or result.get("name", title),
            "overview": result.get("overview", ""),
            "poster": f"{POSTER_BASE}{poster_path}" if poster_path else None,
            "backdrop": f"{BACKDROP_BASE}{backdrop_path}" if backdrop_path else None,
            "year": (result.get("release_date") or result.get("first_air_date", ""))[:4],
            "rating": round(result.get("vote_average", 0), 1),
            "is_series": is_series,
            "genres": genres,
            "tmdb_id": tmdb_id,
            "trailer_url": trailer_url,
        }

        _metadata_cache[cache_key] = metadata
        return metadata


async def enrich_entry(entry):
    if not entry.get("media"):
        return entry
    filename = entry.get("insight", "")
    parsed = parse_filename(filename)
    if not parsed["title"]:
        return entry
    meta = await search_tmdb(
        parsed["title"],
        parsed["is_series"],
        subtitle=parsed.get("episode_subtitle"),
    )
    if meta:
        entry["tmdb"] = meta
        entry["parsed"] = parsed
    return entry
