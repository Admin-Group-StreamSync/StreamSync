"""
content_service.py — StreamSync API client.

Les APIs de Render Free es desperten en <1s un cop hi ha tràfic.
El problema anterior era que TIMEOUT_COLD=30 bloquejava el thread principal.

Estratègia actual:
  - Timeout sempre curt (6s): si l'API no respon en 6s, passa a la següent.
  - Les 3 APIs es criden EN PARAL·LEL (no seqüencialment), de manera que
    el temps total d'espera màxim és 6s, no 6s × 3 = 18s.
  - Caché en memòria de 5 minuts: la majoria de pàgines no fan cap crida a l'API.
  - Keep-alive cada 8 minuts en background per evitar que les APIs tornin a adormir-se.
"""

import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuració
# ---------------------------------------------------------------------------

urls_list = os.getenv('API_BASE_URLS', '').split(',')
keys_list = os.getenv('API_KEYS_DJANGO', '').split(',')
API_CONFIG = dict(zip(urls_list, keys_list))

TMDB_API_KEY = os.getenv('TMDB_API_KEY')

OPTIONS = {
    'plataformas': ['CinePlus', 'StreamHub', 'PlayMax'],
    'idiomas': ['Català', 'Castellano', 'English', 'Français']
}

# Timeout únic per a totes les crides (les APIs de Render desperten en <1s amb tràfic actiu)
API_TIMEOUT = int(os.getenv('API_TIMEOUT', '6'))
# Temps en segons que la caché és vàlida
CACHE_TTL_SECONDS = int(os.getenv('API_CACHE_TTL', '300'))  # 5 minuts
# Interval del keep-alive en background
KEEPALIVE_INTERVAL = int(os.getenv('API_KEEPALIVE_INTERVAL', '480'))  # 8 minuts

# ---------------------------------------------------------------------------
# Caché en memòria (thread-safe)
# ---------------------------------------------------------------------------

_cache: dict = {}
_cache_lock = threading.Lock()


def _cache_get(key: str):
    with _cache_lock:
        entry = _cache.get(key)
        if entry and (time.monotonic() - entry['ts']) < CACHE_TTL_SECONDS:
            return entry['data']
        return None


def _cache_set(key: str, data) -> None:
    with _cache_lock:
        _cache[key] = {'data': data, 'ts': time.monotonic()}


# ---------------------------------------------------------------------------
# Keep-alive en background
# ---------------------------------------------------------------------------

def _ping_all_apis() -> None:
    """Ping silenciós a totes les APIs per mantenir-les despiertes."""
    for base_url, key in API_CONFIG.items():
        try:
            requests.get(
                f"{base_url}/movies",
                headers={'x-api-key': key},
                timeout=API_TIMEOUT,
            )
        except requests.RequestException:
            pass  # Silenciós — és només un keep-alive


def _keepalive_loop() -> None:
    while True:
        time.sleep(KEEPALIVE_INTERVAL)
        _ping_all_apis()
        # Invalida la caché perquè la propera visita tingui dades fresques
        with _cache_lock:
            _cache.clear()


_keepalive_thread = threading.Thread(
    target=_keepalive_loop, daemon=True, name="api-keepalive"
)
_keepalive_thread.start()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_source_key(base_url: str) -> str:
    parsed = urlparse(base_url.strip())
    if parsed.port:
        return str(parsed.port)
    if parsed.netloc:
        return parsed.netloc
    return base_url.replace('://', '').strip('/').split('/')[0]


def get_tmdb_image(title: str) -> str:
    try:
        response = requests.get(
            "https://api.themoviedb.org/3/search/multi",
            params={"api_key": TMDB_API_KEY, "query": title, "language": "en"},
            timeout=3,
        )
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results and results[0].get("poster_path"):
                return f"https://image.tmdb.org/t/p/w500{results[0]['poster_path']}"
    except (requests.RequestException, ValueError) as exc:
        logger.debug("TMDB image failed for '%s': %s", title, exc)
    return 'https://via.placeholder.com/300x450'


def enrich_tmdb_images(items: list) -> list:
    def load_image(item):
        item['imatge'] = get_tmdb_image(item['titol'])
        return item

    with ThreadPoolExecutor(max_workers=10) as executor:
        items = list(executor.map(load_image, items))
    return items


# ---------------------------------------------------------------------------
# Mapeig de dades
# ---------------------------------------------------------------------------

def map_data(item: dict, port: str, base_url: str = "") -> dict:
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
        'plataforma': platform_name,
        'genre_id': item.get('genre_id'),
        'director_id': item.get('director_id'),
        'age_rating_id': item.get('age_rating_id'),
        'genere_nom': "General",
        'director_nom': "Desconegut",
        'edat_nom': "N/A",
    }


def deduplicate_content(llista: list) -> list:
    vistos: dict = {}
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
# Crida a una sola API
# ---------------------------------------------------------------------------

def _fetch_from_api(base_url: str, key: str, endpoint: str, params: dict | None = None) -> list:
    headers = {'x-api-key': key}
    url = f"{base_url}/{endpoint}"
    try:
        response = requests.get(url, headers=headers, params=params or {}, timeout=API_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        logger.warning("API %s va retornar status %s", url, response.status_code)
    except requests.Timeout:
        logger.warning("Timeout (%.0fs) a %s", API_TIMEOUT, url)
    except requests.RequestException as exc:
        logger.warning("Error de connexió a %s: %s", url, exc)
    return []


# ---------------------------------------------------------------------------
# Funcions públiques — crides en paral·lel + caché
# ---------------------------------------------------------------------------

def get_all_movies(query: str | None = None) -> list:
    cache_key = f"movies:{query or ''}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    results = []

    def fetch(args):
        base_url, key = args
        port = extract_source_key(base_url)
        items = _fetch_from_api(base_url, key, 'movies', {'title': query} if query else {})
        return [{**map_data(item, port, base_url=base_url), 'tipus': 'movie'} for item in items]

    with ThreadPoolExecutor(max_workers=len(API_CONFIG) or 3) as executor:
        for res in as_completed([executor.submit(fetch, pair) for pair in API_CONFIG.items()]):
            try:
                results.extend(res.result())
            except Exception as exc:
                logger.error("Error inesperat en fetch movies: %s", exc)

    deduped = deduplicate_content(results)
    if deduped:
        _cache_set(cache_key, deduped)
    return deduped


def get_all_series(query: str | None = None) -> list:
    cache_key = f"series:{query or ''}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    results = []

    def fetch(args):
        base_url, key = args
        port = extract_source_key(base_url)
        items = _fetch_from_api(base_url, key, 'series', {'title': query} if query else {})
        return [{**map_data(item, port, base_url=base_url), 'tipus': 'series'} for item in items]

    with ThreadPoolExecutor(max_workers=len(API_CONFIG) or 3) as executor:
        for res in as_completed([executor.submit(fetch, pair) for pair in API_CONFIG.items()]):
            try:
                results.extend(res.result())
            except Exception as exc:
                logger.error("Error inesperat en fetch series: %s", exc)

    deduped = deduplicate_content(results)
    if deduped:
        _cache_set(cache_key, deduped)
    return deduped


def enrich_api_data(content_list: list) -> list:
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


def get_genres_from_api() -> list:
    cached = _cache_get('genres')
    if cached is not None:
        return cached
    for base_url, key in API_CONFIG.items():
        data = _fetch_from_api(base_url, key, 'genres')
        if data:
            _cache_set('genres', data)
            return data
    return []


def get_directors_from_api() -> list:
    cached = _cache_get('directors')
    if cached is not None:
        return cached
    for base_url, key in API_CONFIG.items():
        data = _fetch_from_api(base_url, key, 'directors')
        if data:
            _cache_set('directors', data)
            return data
    return []


def get_age_ratings_from_api() -> list:
    cached = _cache_get('age_ratings')
    if cached is not None:
        return cached
    for base_url, key in API_CONFIG.items():
        data = _fetch_from_api(base_url, key, 'age-ratings')
        if data:
            _cache_set('age_ratings', data)
            return data
    return []