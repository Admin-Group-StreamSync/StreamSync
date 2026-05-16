import os
from concurrent.futures import ThreadPoolExecutor

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TMDB_API_KEY = os.getenv('TMDB_API_KEY')

OPTIONS = {
    'plataformas': ['CinePlus', 'StreamHub', 'PlayMax'],
    'idiomas': ['Català', 'Castellano', 'English', 'Français']
}

# ─────────────────────────────────────────────────────────────────────────────
# CORRECCIÓ 1: API_CONFIG era una variable global que es construïa UNA SOLA
# VEGADA en importar el mòdul. Si el .env no existia en aquell moment, quedava
# com {'': ''} per sempre i calia reiniciar Django per actualitzar-lo.
# Ara és una funció que es crida cada vegada, llegint les variables en directe.
# ─────────────────────────────────────────────────────────────────────────────

def get_api_config():
    urls = [u.strip() for u in os.getenv('API_BASE_URLS', '').split(',') if u.strip()]
    keys = [k.strip() for k in os.getenv('API_KEYS_DJANGO', '').split(',') if k.strip()]
    return dict(zip(urls, keys))

def get_platform_names():
    return [n.strip() for n in os.getenv('API_PLATFORM_NAMES', 'CinePlus,StreamHub,PlayMax').split(',') if n.strip()]


# --- TMDB ---

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


# --- DATA MAPPING ---

# ─────────────────────────────────────────────────────────────────────────────
# CORRECCIÓ 2: map_data rebia 'port' i feia platforms.get(port, "Altres").
# Això funcionava en local (http://localhost:8080 → port '8080') però no a
# Render (https://movies-api-1.onrender.com → extreu 'onrender.com').
# Ara usa la posició de la URL dins get_api_config() per obtenir el nom.
# ─────────────────────────────────────────────────────────────────────────────

def map_data(item, base_url):
    api_config     = get_api_config()
    platform_names = get_platform_names()
    urls           = list(api_config.keys())

    try:
        idx      = urls.index(base_url)
        platform = platform_names[idx] if idx < len(platform_names) else "Altres"
    except ValueError:
        idx      = 0
        platform = "Altres"

    title        = item.get('title') or item.get('titol') or "Sense títol"
    synopsis     = item.get('synopsis') or "Sense sinopsi disponible."
    content_year = item.get('year') or item.get('start_year') or 0

    return {
        'id':            f"{idx + 1}_{item.get('id')}",
        'titol':         title,
        'sinopsi':       synopsis,
        'any':           content_year,
        'any_fi':        item.get('end_year'),
        'total_seasons': item.get('total_seasons'),
        'rating':        item.get('rating', '0.0'),
        'imatge':        item.get('imatge') or 'https://via.placeholder.com/300x450',
        'plataforma':    platform,
        'genre_id':      item.get('genre_id'),
        'director_id':   item.get('director_id'),
        'age_rating_id': item.get('age_rating_id'),
        'genere_nom':    "General",
        'director_nom':  "Desconegut",
        'edat_nom':      "N/A"
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


# --- STREAMSYNC API CALLS ---

# ─────────────────────────────────────────────────────────────────────────────
# CORRECCIÓ 3: totes les funcions ara criden get_api_config() en lloc de la
# variable global API_CONFIG. També es valida que la resposta sigui una llista
# per evitar el TypeError si l'API retorna un string d'error com "Unauthorized".
# ─────────────────────────────────────────────────────────────────────────────

def get_all_movies(query=None):
    results = []
    for base_url, key in get_api_config().items():
        headers = {'x-api-key': key}
        params = {'title': query} if query else {}
        try:
            response = requests.get(f"{base_url}/movies", headers=headers, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    for item in data:
                        obj = map_data(item, base_url)
                        obj['tipus'] = 'movie'
                        results.append(obj)
        except Exception as e:
            print(f"[API] Error movies {base_url}: {e}")
    return deduplicate_content(results)


def get_all_series(query=None):
    results = []
    for base_url, key in get_api_config().items():
        headers = {'x-api-key': key}
        params = {'title': query} if query else {}
        try:
            response = requests.get(f"{base_url}/series", headers=headers, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    for item in data:
                        obj = map_data(item, base_url)
                        obj['tipus'] = 'series'
                        results.append(obj)
        except Exception as e:
            print(f"[API] Error series {base_url}: {e}")
    return deduplicate_content(results)


def enrich_api_data(content_list):
    genres_api  = get_genres_from_api()
    ratings_api = get_age_ratings_from_api()

    genre_map  = {str(g['id']): g['name'] for g in genres_api}
    rating_map = {str(r['id']): r.get('description', 'N/A') for r in ratings_api}

    for item in content_list:
        gid = str(item.get('genre_id'))
        eid = str(item.get('age_rating_id'))
        item['genere_nom'] = genre_map.get(gid, "General")
        item['edat_nom']   = rating_map.get(eid, "N/A")
        if 'tipus' not in item:
            item['tipus'] = item.get('media_type', 'movie')

    return content_list


def get_genres_from_api():
    for base_url, key in get_api_config().items():
        try:
            data = requests.get(f"{base_url}/genres", headers={'x-api-key': key}, timeout=3).json()
            if isinstance(data, list):
                return data
        except Exception as e:
            print(f"[API] Error genres {base_url}: {e}")
            continue
    return []


def get_directors_from_api():
    for base_url, key in get_api_config().items():
        try:
            data = requests.get(f"{base_url}/directors", headers={'x-api-key': key}, timeout=3).json()
            if isinstance(data, list):
                return data
        except Exception as e:
            print(f"[API] Error directors {base_url}: {e}")
            continue
    return []


def get_age_ratings_from_api():
    for base_url, key in get_api_config().items():
        try:
            data = requests.get(f"{base_url}/age-ratings", headers={'x-api-key': key}, timeout=3).json()
            if isinstance(data, list):
                return data
        except Exception as e:
            print(f"[API] Error age-ratings {base_url}: {e}")
            continue
    return []