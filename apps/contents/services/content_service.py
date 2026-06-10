import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

urls_list = os.getenv('API_BASE_URLS', '').split(',')
keys_list = os.getenv('API_KEYS_DJANGO', '').split(',')
API_CONFIG = dict(zip(urls_list, keys_list))

TMDB_API_KEY = os.getenv('TMDB_API_KEY')

OPTIONS = {
    'plataformas': ['CinePlus', 'StreamHub', 'PlayMax'],
    'idiomas': ['Català', 'Castellano', 'English', 'Français']
}

# ---------------------------------------------------------------------------
# Caché en memòria
# ---------------------------------------------------------------------------
_cache: dict = {}
_cache_lock = threading.Lock()
CACHE_TTL = int(os.getenv('API_CACHE_TTL', '300'))


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
# Helpers
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
            params={"api_key": TMDB_API_KEY, "query": title, "language": "en"},
            timeout=2
        )
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results and results[0].get("poster_path"):
                return f"https://image.tmdb.org/t/p/w500{results[0]['poster_path']}"
    except (requests.RequestException, ValueError):
        pass
    return 'https://via.placeholder.com/300x450'


def enrich_tmdb_images(items):
    def load_image(item):
        item['imatge'] = get_tmdb_image(item['titol'])
        return item
    with ThreadPoolExecutor(max_workers=10) as executor:
        items = list(executor.map(load_image, items))
    return items


def map_data(item, port, base_url=""):
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

    return {
        'id': f"{port}_{item.get('id')}",
        'titol': item.get('title') or item.get('titol') or "No title",
        'sinopsi': item.get('synopsis') or "No synopsis available.",
        'any': item.get('year') or item.get('start_year') or 0,
        'any_fi': item.get('end_year'),
        'total_seasons': item.get('total_seasons'),
        'rating': item.get('rating', '0.0'),
        'imatge': item.get('imatge') or 'https://via.placeholder.com/300x450',
        'plataforma': platform_name,
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


# ---------------------------------------------------------------------------
# Crida única a una API
# ---------------------------------------------------------------------------

def _fetch_one(base_url, key, endpoint, params=None):
    port = extract_source_key(base_url)
    try:
        r = requests.get(
            f"{base_url}/{endpoint}",
            headers={'x-api-key': key},
            params=params or {},
            timeout=10,
        )
        if r.status_code == 200:
            return port, base_url, r.json()
    except requests.RequestException as exc:
        logging.warning("Failed %s from %s: %s", endpoint, base_url, exc)
    return port, base_url, []


# ---------------------------------------------------------------------------
# Fetch paral·lel de les 3 APIs
# ---------------------------------------------------------------------------

def _fetch_all_parallel(endpoint, tipus, query=None):
    results = []
    params = {'title': query} if query else {}
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(_fetch_one, url, key, endpoint, params): url
                   for url, key in API_CONFIG.items()}
        for future in as_completed(futures, timeout=15):
            try:
                port, base_url, items = future.result()
                for item in items:
                    obj = map_data(item, port, base_url=base_url)
                    obj['tipus'] = tipus
                    results.append(obj)
            except Exception as exc:
                logging.warning("Parallel fetch error: %s", exc)
    return deduplicate_content(results)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def get_all_movies(query=None):
    cache_key = f"movies:{query or ''}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    result = _fetch_all_parallel('movies', 'movie', query)
    if result:
        _cache_set(cache_key, result)
    return result


def get_all_series(query=None):
    cache_key = f"series:{query or ''}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    result = _fetch_all_parallel('series', 'series', query)
    if result:
        _cache_set(cache_key, result)
    return result


def enrich_api_data(content_list):
    genres_api = get_genres_from_api()
    ratings_api = get_age_ratings_from_api()
    genre_map = {str(g['id']): g['name'] for g in genres_api}
    rating_map = {str(r['id']): r.get('description', 'N/A') for r in ratings_api}
    for item in content_list:
        item['genere_nom'] = genre_map.get(str(item.get('genre_id')), "General")
        item['edat_nom'] = rating_map.get(str(item.get('age_rating_id')), "N/A")
        if 'tipus' not in item:
            item['tipus'] = item.get('media_type', 'movie')
    return content_list


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