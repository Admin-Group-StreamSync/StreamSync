"""
content_service.py — StreamSync API client amb suport per a Render Free Tier.

Render Free dorm les instàncies després de 15 min d'inactivitat i tarda ~30s
a despertar. Solució: caché en memòria + timeout adaptatiu + warm-up en background.

Flux:
  1. Primera crida → timeout llarg (25s) per permetre el "cold start" de Render.
  2. Crides posteriors → timeout curt (5s), les dades venen de caché si estan fresques.
  3. La caché s'invalida cada CACHE_TTL_SECONDS (5 min per defecte).
  4. Un thread de warm-up fa un ping silenciós cada 10 min per evitar que les APIs
     tornin a adormir-se mentre la web està activa.
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

# Timeout per al primer intent (Render cold start pot tardar fins a 30s)
TIMEOUT_COLD = int(os.getenv('API_TIMEOUT_COLD', '30'))
# Timeout per a crides normals un cop l'API està desperta
TIMEOUT_WARM = int(os.getenv('API_TIMEOUT_WARM', '8'))
# Temps en segons que la caché és vàlida
CACHE_TTL_SECONDS = int(os.getenv('API_CACHE_TTL', '300'))   # 5 minuts
# Interval del keep-alive en background (en segons)
KEEPALIVE_INTERVAL = int(os.getenv('API_KEEPALIVE_INTERVAL', '600'))  # 10 minuts

# ---------------------------------------------------------------------------
# Estat de les APIs (dormides o despiertes)
# ---------------------------------------------------------------------------

_api_state: dict[str, dict] = {
    url: {'awake': False, 'last_success': 0.0}
    for url in API_CONFIG
}
_state_lock = threading.Lock()


def _mark_awake(base_url: str) -> None:
    with _state_lock:
        _api_state[base_url]['awake'] = True
        _api_state[base_url]['last_success'] = time.monotonic()


def _mark_asleep(base_url: str) -> None:
    with _state_lock:
        _api_state[base_url]['awake'] = False


def _is_awake(base_url: str) -> bool:
    with _state_lock:
        state = _api_state.get(base_url, {})
        # Si han passat més de 16 min sense èxit, considerem que pot haver tornat a dormir
        elapsed = time.monotonic() - state.get('last_success', 0.0)
        if elapsed > 960:  # 16 minuts
            _api_state[base_url]['awake'] = False
        return _api_state[base_url]['awake']


def _get_timeout(base_url: str) -> int:
    """Retorna el timeout adequat segons si l'API sembla desperta o no."""
    return TIMEOUT_WARM if _is_awake(base_url) else TIMEOUT_COLD


# ---------------------------------------------------------------------------
# Caché en memòria
# ---------------------------------------------------------------------------

_cache: dict[str, dict] = {}
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


def _cache_invalidate(key: str) -> None:
    with _cache_lock:
        _cache.pop(key, None)


# ---------------------------------------------------------------------------
# Warm-up keep-alive en background
# ---------------------------------------------------------------------------

def _ping_all_apis() -> None:
    """Fa un ping a totes les APIs per mantenir-les despiertes."""
    for base_url, key in API_CONFIG.items():
        try:
            r = requests.get(
                f"{base_url}/movies",
                headers={'x-api-key': key},
                timeout=TIMEOUT_COLD,
                params={'limit': '1'},
            )
            if r.status_code == 200:
                _mark_awake(base_url)
                logger.debug("Keep-alive OK: %s", base_url)
            else:
                _mark_asleep(base_url)
        except requests.RequestException as exc:
            _mark_asleep(base_url)
            logger.debug("Keep-alive failed for %s: %s", base_url, exc)
    # Invalida la caché perquè la propera crida tingui dades fresques
    _cache_invalidate('movies')
    _cache_invalidate('series')


def _keepalive_loop() -> None:
    """Thread en background que fa warm-up periòdic."""
    # Primer ping immediat en arrencar (per despertar les APIs al deploy)
    logger.info("API warm-up inicial en background...")
    _ping_all_apis()
    while True:
        time.sleep(KEEPALIVE_INTERVAL)
        logger.info("API keep-alive ping...")
        _ping_all_apis()


# Arrenquem el thread de keep-alive una sola vegada
_keepalive_thread = threading.Thread(target=_keepalive_loop, daemon=True, name="api-keepalive")
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
# Crida a una sola API (amb timeout adaptatiu)
# ---------------------------------------------------------------------------

def _fetch_from_api(base_url: str, key: str, endpoint: str, params: dict | None = None) -> list:
    """
    Fa una petició GET a base_url/endpoint.
    Usa timeout llarg si l'API sembla dormida, curt si sembla desperta.
    """
    timeout = _get_timeout(base_url)
    headers = {'x-api-key': key}
    url = f"{base_url}/{endpoint}"
    try:
        response = requests.get(url, headers=headers, params=params or {}, timeout=timeout)
        if response.status_code == 200:
            _mark_awake(base_url)
            return response.json()
        logger.warning("API %s retornat status %s", url, response.status_code)
    except requests.Timeout:
        _mark_asleep(base_url)
        logger.warning(
            "Timeout (%.0fs) a %s — l'API pot estar dormida (Render Free cold start).",
            timeout, url
        )
    except requests.RequestException as exc:
        _mark_asleep(base_url)
        logger.warning("Error de connexió a %s: %s", url, exc)
    return []


# ---------------------------------------------------------------------------
# Funcions públiques de dades
# ---------------------------------------------------------------------------

def get_all_movies(query: str | None = None) -> list:
    cache_key = f"movies:{query or ''}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    results = []

    def fetch_movies(base_url_key):
        base_url, key = base_url_key
        port = extract_source_key(base_url)
        params = {'title': query} if query else {}
        items = _fetch_from_api(base_url, key, 'movies', params)
        return [
            {**map_data(item, port, base_url=base_url), 'tipus': 'movie'}
            for item in items
        ]

    # Fem les 3 crides en paral·lel per reduir el temps d'espera total
    with ThreadPoolExecutor(max_workers=len(API_CONFIG)) as executor:
        futures = {executor.submit(fetch_movies, item): item for item in API_CONFIG.items()}
        for future in as_completed(futures):
            try:
                results.extend(future.result())
            except Exception as exc:
                logger.error("Error inesperat en fetch_movies: %s", exc)

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

    def fetch_series(base_url_key):
        base_url, key = base_url_key
        port = extract_source_key(base_url)
        params = {'title': query} if query else {}
        items = _fetch_from_api(base_url, key, 'series', params)
        return [
            {**map_data(item, port, base_url=base_url), 'tipus': 'series'}
            for item in items
        ]

    with ThreadPoolExecutor(max_workers=len(API_CONFIG)) as executor:
        futures = {executor.submit(fetch_series, item): item for item in API_CONFIG.items()}
        for future in as_completed(futures):
            try:
                results.extend(future.result())
            except Exception as exc:
                logger.error("Error inesperat en fetch_series: %s", exc)

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
        gid = str(item.get('genre_id'))
        eid = str(item.get('age_rating_id'))
        item['genere_nom'] = genre_map.get(gid, "General")
        item['edat_nom'] = rating_map.get(eid, "N/A")
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
