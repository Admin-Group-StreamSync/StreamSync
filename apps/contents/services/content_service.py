import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
# logger = logging.getLogger(__name__)

urls_list = os.getenv('API_BASE_URLS', '').split(',')
keys_list = os.getenv('API_KEYS_DJANGO', '').split(',')
API_CONFIG = dict(zip(urls_list, keys_list))

# LOG TEMPORAL DE DIAGNÒSTIC
logging.basicConfig(level=logging.INFO)
logging.info("=== DIAGNOSI API_CONFIG: %s entrades ===", len(API_CONFIG))
for _u in API_CONFIG:
    logging.info("  URL: %s", _u)

TMDB_API_KEY = os.getenv('TMDB_API_KEY')

OPTIONS = {
    'plataformas': ['CinePlus', 'StreamHub', 'PlayMax'],
    'idiomas': ['Català', 'Castellano', 'English', 'Français']
}

# ---------------------------------------------------------------------------
# Caché en memòria — únic afegit respecte al codi original
# ---------------------------------------------------------------------------

_cache: dict = {}
_cache_lock = threading.Lock()
CACHE_TTL = int(os.getenv('API_CACHE_TTL', '300'))  # 5 minuts


def _cache_get(key: str):
    with _cache_lock:
        entry = _cache.get(key)
        if entry and (time.monotonic() - entry['ts']) < CACHE_TTL:
            return entry['data']
        return None


def _cache_set(key: str, data) -> None:
    with _cache_lock:
        _cache[key] = {'data': data, 'ts': time.monotonic()}

# ---------------------------------------------------------------------------


def extract_source_key(base_url):
    parsed = urlparse(base_url.strip())
    if parsed.port:
        return str(parsed.port)
    if parsed.netloc:
        return parsed.netloc
    return base_url.replace('://', '').strip('/').split('/')[0]

def get_tmdb_image(title):
    try:
        response = requests.get(
            "https://api.themoviedb.org/3/search/multi",
            params={
                "api_key": TMDB_API_KEY,
                "query": title,
                "language": "en"
            },
            timeout=2
        )
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results and results[0].get("poster_path"):
                return f"https://image.tmdb.org/t/p/w500{results[0]['poster_path']}"
    except (requests.RequestException, ValueError) as exc:
        logging.debug("Failed to fetch TMDB image for title '%s': %s", title, exc)
    return 'https://via.placeholder.com/300x450'


def enrich_tmdb_images(items):
    def load_image(item):
        item['imatge'] = get_tmdb_image(item['titol'])
        return item

    with ThreadPoolExecutor(max_workers=10) as executor:
        items = list(executor.map(load_image, items))
    return items


# --- 3. DATA MAPPING ---

def map_data(item, port, base_url=""):
    # Mapeig basat en el text de la URL de Render o en els ports antics (per si de cas)
    url_str = str(base_url).lower()
    port_str = str(port).lower()

    if "movies-api-1" in url_str or "8080" in port_str:
        platform_name = "CinePlus"
    elif "movies-api-2" in url_str or "8081" in port_str:
        platform_name = "StreamHub"
    elif "movies-api-3" in url_str or "8082" in port_str:
        platform_name = "PlayMax"
    else:
        platform_name = "Altres"

    title = item.get('title') or item.get('titol') or "No title"
    synopsis = item.get('synopsis') or "No synopsis available."
    content_year = item.get('year') or item.get('start_year') or 0

    return {
        'id': f"{port}_{item.get('id')}",
        'titol': title,
        'sinopsi': synopsis,
        'any': content_year,
        'any_fi': item.get('end_year'),
        'total_seasons': item.get('total_seasons'),
        'rating': item.get('rating', '0.0'),
        'imatge': item.get('imatge') or 'https://via.placeholder.com/300x450',
        'plataforma': platform_name,  # Assigna correctament CinePlus, StreamHub o PlayMax
        'genre_id': item.get('genre_id'),
        'director_id': item.get('director_id'),
        'age_rating_id': item.get('age_rating_id'),
        'genere_nom': "General",
        'director_nom': "Desconegut",
        'edat_nom': "N/A"
    }

def deduplicate_content(llista):
    vistos = {}
    for item in llista:
        titol = item['titol'].strip().lower()
        if titol not in vistos:
            item['plataformes_disponibles'] = [item['plataforma']]
            vistos[titol] = item
        else:
            if item['plataforma'] not in vistos[titol]['plataformes_disponibles']:
                vistos[titol]['plataformes_disponibles'].append(item['plataforma'])
    return list(vistos.values())

# --- 4. STREAMSYNC API CALLS ---

def get_all_movies(query=None):
    cache_key = f"movies:{query or ''}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    results = []
    for base_url, key in API_CONFIG.items():
        headers = {'x-api-key': key}
        port = extract_source_key(base_url)
        params = {'title': query} if query else {}
        try:
            response = requests.get(f"{base_url}/movies", headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                for item in response.json():
                    obj = map_data(item, port, base_url=base_url)
                    obj['tipus'] = 'movie'
                    results.append(obj)
        except Exception as exc:
            logging.warning(
                "Failed to fetch movies from %s with query=%r: %s",
                base_url,
                query,
                exc,
                exc_info=True,
            )
    deduped = deduplicate_content(results)
    if deduped:
        _cache_set(cache_key, deduped)
    return deduped


def enrich_api_data(content_list):
    genres_api = get_genres_from_api()
    ratings_api = get_age_ratings_from_api()

    genre_map = {str(g['id']): g['name'] for g in genres_api}
    rating_map = {str(r['id']): r.get('description', 'N/A') for r in ratings_api}

    for item in content_list:
        gid = str(item.get('genre_id'))
        eid = str(item.get('age_rating_id'))
        item['genere_nom'] = genre_map.get(gid, "General")
        item['edat_nom'] = rating_map.get(eid, "N/A")
        if 'tipus' not in item:
            item['tipus'] = item.get('media_type', 'movie')

    return content_list


def get_all_series(query=None):
    cache_key = f"series:{query or ''}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    results = []
    for base_url, key in API_CONFIG.items():
        headers = {'x-api-key': key}
        port = extract_source_key(base_url)
        params = {'title': query} if query else {}
        try:
            response = requests.get(f"{base_url}/series", headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                for item in response.json():
                    obj = map_data(item, port, base_url=base_url)
                    obj['tipus'] = 'series'
                    results.append(obj)
        except requests.RequestException as exc:
            logging.warning("Failed to fetch series from %s: %s", base_url, exc)
    deduped = deduplicate_content(results)
    if deduped:
        _cache_set(cache_key, deduped)
    return deduped


def get_genres_from_api():
    cached = _cache_get('genres')
    if cached is not None:
        return cached
    for base_url, key in API_CONFIG.items():
        try:
            data = requests.get(f"{base_url}/genres", headers={'x-api-key': key}, timeout=10).json()
            if data:
                _cache_set('genres', data)
                return data
        except requests.RequestException:
            continue
    return []


def get_directors_from_api():
    cached = _cache_get('directors')
    if cached is not None:
        return cached
    for base_url, key in API_CONFIG.items():
        try:
            data = requests.get(f"{base_url}/directors", headers={'x-api-key': key}, timeout=10).json()
            if data:
                _cache_set('directors', data)
                return data
        except (requests.RequestException, ValueError, TypeError):
            continue
    return []


def get_age_ratings_from_api():
    cached = _cache_get('age_ratings')
    if cached is not None:
        return cached
    for base_url, key in API_CONFIG.items():
        try:
            data = requests.get(f"{base_url}/age-ratings", headers={'x-api-key': key}, timeout=10).json()
            if data:
                _cache_set('age_ratings', data)
                return data
        except requests.RequestException:
            continue
    return []