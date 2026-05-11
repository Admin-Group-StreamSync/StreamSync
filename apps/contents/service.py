import os
from concurrent.futures import ThreadPoolExecutor

import requests

from apps.external_apis import API_CONFIG

TMDB_API_KEY = os.getenv('TMDB_API_KEY')

# --- 4. STREAMSYNC API CALLS ---

def get_all_movies(query=None):
    results = []
    for base_url, key in API_CONFIG.items():
        headers = {'x-api-key': key}
        port = base_url.split(':')[-1]
        params = {'title': query} if query else {}
        try:
            response = requests.get(f"{base_url}/movies", headers=headers, params=params, timeout=2)
            if response.status_code == 200:
                for item in response.json():
                    obj = map_data(item, port)
                    obj['tipus'] = 'movie'
                    results.append(obj)
        except:
            pass
    return deduplicate_content(results)  # ✅ Deduplicació

def get_all_series(query=None):
    results = []
    for base_url, key in API_CONFIG.items():
        headers = {'x-api-key': key}
        port = base_url.split(':')[-1]
        params = {'title': query} if query else {}
        try:
            response = requests.get(f"{base_url}/series", headers=headers, params=params, timeout=2)
            if response.status_code == 200:
                for item in response.json():
                    obj = map_data(item, port)
                    obj['tipus'] = 'series'
                    results.append(obj)
        except:
            pass
    return deduplicate_content(results)  # ✅ Deduplicació


def map_data(item, port):
    platforms = {"8080": "CinePlus", "8081": "StreamHub", "8082": "PlayMax"}
    port_net = str(port).replace('/','')


    title = item.get('title') or item.get('titol') or "Sense títol"
    synopsis = item.get('synopsis') or "Sense sinopsi disponible."
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
        'plataforma': platforms.get(port, "Altres"),
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


# --- 2. TMDB FUNCTIONS ---

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
