import os
import requests
from concurrent.futures import ThreadPoolExecutor
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import update_session_auth_hash, login
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from dotenv import load_dotenv
from rest_framework.decorators import api_view
from thefuzz import process, fuzz

from .models import Pelicula, LlistaPersonal, Carpeta, Profile, Ressenya, Views, Feedback
from .forms import RegistroUsuarioForm, UserUpdateForm

# 1. LOAD CONFIGURATION
load_dotenv()

urls_list = os.getenv('API_BASE_URLS', '').split(',')
keys_list = os.getenv('API_KEYS_DJANGO', '').split(',')
API_CONFIG = dict(zip(urls_list, keys_list))

TMDB_API_KEY = os.getenv('TMDB_API_KEY')

OPTIONS = {
    'plataformas': ['CinePlus', 'StreamHub', 'PlayMax'],
    'idiomas': ['Català', 'Castellano', 'English', 'Français']
}


class StreamSyncLoginView(LoginView):
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Benvingut/da de nou, {form.get_user().username}!")
        return response


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


# --- 3. DATA MAPPING ---

def map_data(item, port):
    platforms = {"8080": "CinePlus", "8081": "StreamHub", "8082": "PlayMax"}

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
    return results


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
    return results


def get_genres_from_api():
    for base_url, key in API_CONFIG.items():
        try:
            return requests.get(f"{base_url}/genres", headers={'x-api-key': key}, timeout=1).json()
        except:
            continue
    return []


def get_directors_from_api():
    for base_url, key in API_CONFIG.items():
        try:
            return requests.get(f"{base_url}/directors", headers={'x-api-key': key}, timeout=1).json()
        except:
            continue
    return []


def get_age_ratings_from_api():
    for base_url, key in API_CONFIG.items():
        try:
            return requests.get(f"{base_url}/age-ratings", headers={'x-api-key': key}, timeout=1).json()
        except:
            continue
    return []


# --- 4. MAIN VIEWS ---

def home_page(request):
    # 1. Fetch and label the data
    movies = get_all_movies()
    for m in movies: m['tipus'] = 'movie'

    series = get_all_series()
    for s in series: s['tipus'] = 'series'

    all_content = movies + series

    # 2. Load translation dictionaries from the API (display only)
    genres_api = get_genres_from_api()
    ratings_api = get_age_ratings_from_api()

    genre_map = {str(g['id']): g['name'] for g in genres_api}
    rating_map = {str(r['id']): r.get('description', 'N/A') for r in ratings_api}

    def enrich(items):
        for item in items:
            gid = str(item.get('genre_id'))
            eid = str(item.get('age_rating_id'))
            item['genere_nom'] = genre_map.get(gid, "General")
            item['edat_nom'] = rating_map.get(eid, "N/A")
        return items

    profile_recommendations = []
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            filtered = all_content

            if profile.tipus:
                filtered = [x for x in filtered if x['tipus'] in profile.tipus]
            if profile.plataformes:
                filtered = [x for x in filtered if x.get('plataforma') in profile.plataformes]
            if profile.generes:
                filtered = [x for x in filtered if str(x.get('genre_id')) in profile.generes]
            if profile.edat_rating:
                filtered = [x for x in filtered if str(x.get('age_rating_id')) in profile.edat_rating]

            top4 = sorted(filtered, key=lambda x: float(x.get('rating', 0)), reverse=True)[:4]
            profile_recommendations = enrich_tmdb_images(enrich(top4))  # ✅ TMDB in parallel

        except Exception as e:
            print(f"Error filtering preferences: {e}")
            profile_recommendations = []

    tendencies = enrich_tmdb_images(enrich(all_content[:4]))  # ✅ TMDB in parallel
    top_rated = enrich_tmdb_images(
        enrich(sorted(all_content, key=lambda x: float(x.get('rating', 0)), reverse=True)[:4])
    )

    return render(request, 'pages/pagina_principal.html', {
        'tendencies': tendencies,
        'millor_valorades': top_rated,
        'recomanacions_perfil': profile_recommendations,
        'genres_api': genres_api,
        'ratings': ratings_api
    })


def content_detail(request, tipus, content_id):
    all_content = get_all_series() if tipus == 'series' else get_all_movies()
    item = next((p for p in all_content if str(p['id']) == str(content_id)), None)

    if not item:
        return render(request, '404.html', status=404)

    genres = get_genres_from_api()
    item['genere_nom'] = next((g['name'] for g in genres if str(g['id']) == str(item['genre_id'])), "General")

    directors = get_directors_from_api()
    item['director_nom'] = next((d['name'] for d in directors if str(d['id']) == str(item['director_id'])), "Desconegut")

    ratings = get_age_ratings_from_api()
    item['edat_nom'] = next((r.get('title') or r.get('name') or r.get('description')
                             for r in ratings if str(r['id']) == str(item['age_rating_id'])), "N/A")

    item['imatge'] = get_tmdb_image(item['titol'])

    movie_db, _ = Pelicula.objects.update_or_create(
        id=item['id'],
        defaults={
            "titol": item['titol'],
            "any": item['any'],
            "valoracio": float(item.get('rating', 0)),
            "imatge": item.get('imatge'),
            "tipus": tipus
        }
    )

    raw_recommendations = [p for p in all_content if str(p['id']) != str(content_id)][:5]
    recommendations = enrich_tmdb_images(raw_recommendations)

    return render(request, 'pagina_contingut.html', {
        'item': item,
        'tipus': tipus,
        'ja_guardada': LlistaPersonal.objects.filter(usuari=request.user,
                                                     pelicula=movie_db).exists() if request.user.is_authenticated else False,
        'carpetes': request.user.les_meves_carpetes.all() if request.user.is_authenticated else [],
        'ressenyes': Ressenya.objects.filter(pelicula=movie_db).order_by('-data_publicacio'),
        'recomanacions': recommendations,
    })


def catalogo(request, tipus=None):
    if tipus == 'movie':
        all_content = get_all_movies()
    elif tipus == 'series':
        all_content = get_all_series()
    else:
        all_content = get_all_movies() + get_all_series()

    genres_api = get_genres_from_api()
    ratings_api = get_age_ratings_from_api()
    directors_api = get_directors_from_api()

    genre_map = {str(g['id']): g['name'] for g in genres_api}
    rating_map = {str(r['id']): r.get('description', 'N/A') for r in ratings_api}
    director_map = {str(d['id']): d['name'] for d in directors_api}

    filters = {
        'p': request.GET.get('plataforma', ''),
        'g': request.GET.get('genere', ''),
        'e': request.GET.get('edat', ''),
        'v': request.GET.get('valoracio', '0'),
        'd': request.GET.get('director', '').strip().lower()
    }

    results = []
    for item in all_content:
        gid = str(item.get('genre_id'))
        eid = str(item.get('age_rating_id'))
        did = str(item.get('director_id'))

        item['genere_nom'] = genre_map.get(gid, "General")
        item['edat_nom'] = rating_map.get(eid, "N/A")
        item['director_nom'] = director_map.get(did, "Desconegut")

        if filters['p'] and item.get('plataforma') != filters['p']: continue
        if filters['g'] and gid != filters['g']: continue
        if filters['e'] and eid != filters['e']: continue
        if filters['d'] and filters['d'] not in item['director_nom'].lower(): continue

        try:
            if float(item.get('rating', 0)) < float(filters['v']): continue
        except:
            pass

        results.append(item)

    paginator = Paginator(results, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    enrich_tmdb_images(list(page_obj.object_list))

    filters_url = f"&plataforma={filters['p']}&genere={filters['g']}&edat={filters['e']}&valoracio={filters['v']}&director={filters['d']}"

    return render(request, 'cataleg.html', {
        'contenidos': page_obj.object_list,
        'page_obj': page_obj,
        'filtres_url': filters_url,
        'tipus_actual': tipus,
        'opcions': OPTIONS,
        'genres_api': genres_api,
        'ratings': ratings_api,
        'filtros_sel': filters
    })

def feedback_view(request):
    if request.method == "POST":
        tipus = request.POST.get("tipus")
        title = request.POST.get("titol")
        description = request.POST.get("descripcio")
        rating = request.POST.get("rating")

        Feedback.objects.create(
            tipus=tipus,
            titol=title,
            descripcio=description,
            rating=rating if rating else None
        )

        messages.success(request, "Gràcies per la teva opinió!")

        return redirect("feedback")

    return render(request, "pages/feedback.html")

# --- 5. USER MANAGEMENT AND LISTS ---

@login_required
def publish_review(request, tipus, content_id):
    if request.method == "POST":
        movie_db = get_object_or_404(Pelicula, id=content_id)
        Ressenya.objects.update_or_create(
            usuari=request.user, pelicula=movie_db,
            defaults={'puntuacio': request.POST.get('puntuacio'), 'comentari': request.POST.get('comentari')}
        )
        messages.success(request, "Ressenya publicada!")
    return redirect('pagina_contingut', tipus=tipus, content_id=content_id)


@login_required
def add_to_list(request, tipus, content_id):
    movie = get_object_or_404(Pelicula, id=content_id)
    folder_id = request.POST.get('carpeta_id')
    folder = get_object_or_404(Carpeta, id=folder_id, usuari=request.user) if folder_id else None
    LlistaPersonal.objects.get_or_create(usuari=request.user, pelicula=movie, carpeta=folder)
    messages.success(request, "Afegit a la llista!")
    return redirect('pagina_contingut', tipus=tipus, content_id=content_id)


@login_required
def delete_review(request, ressenya_id):
    review = get_object_or_404(Ressenya, id=ressenya_id, usuari=request.user)
    content_id_value, content_type = review.pelicula.id, review.pelicula.tipus
    review.delete()
    return redirect('pagina_contingut', tipus=content_type, content_id=content_id_value)


@login_required
def lists(request):
    return render(request, 'llistes.html', {
        'carpetes': request.user.les_meves_carpetes.all(),
        'elements_solts': LlistaPersonal.objects.filter(usuari=request.user, carpeta__isnull=True)
    })


@login_required
def folder_detail(request, carpeta_id):
    folder = get_object_or_404(Carpeta, id=carpeta_id, usuari=request.user)
    return render(request, 'detall_carpeta.html', {
        'carpeta': folder,
        'elements': LlistaPersonal.objects.filter(carpeta=folder)
    })


@login_required
def create_list(request):
    if request.method == "POST":
        Carpeta.objects.create(
            usuari=request.user, nom=request.POST.get('nom'),
            icona=request.POST.get('icona'), color=request.POST.get('color')
        )
        return redirect('llistes')
    return render(request, 'crear_llista.html', {'opcions': OPTIONS})


@login_required
def edit_list(request, carpeta_id):
    folder = get_object_or_404(Carpeta, id=carpeta_id, usuari=request.user)
    if request.method == "POST":
        folder.nom, folder.icona, folder.color = request.POST.get('nom'), request.POST.get('icona'), request.POST.get('color')
        folder.save()
        return redirect('llistes')
    return render(request, 'editar_llista.html', {'carpeta': folder, 'opcions': OPTIONS})


@login_required
def delete_folder(request, carpeta_id):
    get_object_or_404(Carpeta, id=carpeta_id, usuari=request.user).delete()
    return redirect('llistes')


@login_required
def remove_from_list(request, tipus, content_id):
    LlistaPersonal.objects.filter(usuari=request.user, pelicula_id=content_id).delete()
    messages.success(request, "Element eliminat de la llista.")
    return redirect('llistes')


# --- 7. REGISTRATION AND PROFILE ---

def crear_cuenta(request):
    genres_api = get_genres_from_api()
    ratings_api = get_age_ratings_from_api()
    platforms_api = OPTIONS.get('plataformas', [])

    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()

            profile = user.profile
            profile.tipus = request.POST.getlist('tipus')
            profile.plataformes = request.POST.getlist('plataformes')
            profile.generes = request.POST.getlist('generos')
            profile.edat_rating = request.POST.getlist('edats')
            profile.save()

            login(request, user)
            messages.success(request, f"Benvingut/da, {user.username}!")
            return redirect('pagina_principal')
        else:
            print("Form errors:", form.errors)
            messages.error(request, "Error in the form.")
    else:
        form = RegistroUsuarioForm()

    context = {
        'form': form,
        'opcions': {
            'tipus': [('movie', 'Pel·lícules'), ('series', 'Sèries')],
            'plataformas': platforms_api,
            'genres_api': genres_api,
            'ratings_api': ratings_api
        }
    }
    return render(request, 'registration/registre.html', context)


@login_required
def profile_page1(request):
    form = UserUpdateForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Perfil actualitzat!")
    return render(request, 'registration/pagina_perfil1.html', {'form': form})


@login_required
def profile2(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        profile.tipus = request.POST.getlist('tipus')
        profile.plataformes = request.POST.getlist('plataformes')
        profile.generes = request.POST.getlist('generos')
        profile.edat_rating = request.POST.getlist('edats')
        profile.save()

        messages.success(request, "Preferències actualitzades!")
        return redirect('profile2')

    genres = get_genres_from_api()
    ratings = get_age_ratings_from_api()

    context = {
        'perfil': profile,
        'genres_api': genres,
        'ratings_api': ratings,
        'opcions': {
            'tipus': [('movie', 'Pel·lícules'), ('series', 'Sèries')],
            'plataformas': OPTIONS.get('plataformas', []),
        }
    }
    return render(request, 'profile2.html', context)


@login_required
def cambiar_password(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        return redirect('pagina_perfil1')
    return render(request, 'registration/cambiar_password.html', {'form': form})


@login_required
def delete_account(request):
    if request.method == 'POST':
        request.user.delete()
        return redirect('pagina_principal')
    return render(request, 'registration/esborrar_compte.html')


def search_content(request):
    query = request.GET.get('q', '').strip()

    movies = get_all_movies()
    for m in movies: m['tipus'] = 'movie'
    series = get_all_series()
    for s in series: s['tipus'] = 'series'

    all_content = movies + series
    main_result = None
    recommendations = []

    if query:
        titles = [p['titol'] for p in all_content]
        matches = process.extract(query, titles, scorer=fuzz.token_set_ratio, limit=1)

        if matches and matches[0][1] > 65:
            main_result = next(p for p in all_content if p['titol'] == matches[0][0])

            main_result['imatge'] = get_tmdb_image(main_result['titol'])

            others = [p for p in all_content if p['id'] != main_result['id']]

            def calculate_score(item):
                score = 0
                if item.get('director_id') == main_result.get('director_id'):
                    score += 10
                if item.get('genre_id') == main_result.get('genre_id'):
                    score += 5
                if item.get('age_rating_id') == main_result.get('age_rating_id'):
                    score += 2
                return score

            recommendations = sorted(others, key=calculate_score, reverse=True)
            recommendations = [p for p in recommendations if calculate_score(p) > 0][:5]

            enrich_tmdb_images(recommendations)

    return render(request, 'cerca_contingut.html', {
        'query': query,
        'resultat': main_result,
        'resultats': recommendations
    })

@login_required
@api_view(['POST'])
def register_view(request):
    film_id = request.data.get("film")

    # Check that film_id is present
    if not film_id:
        return HttpResponse({"error": "film_id required"}, status=400)#

    # Fetch movie
    film = get_object_or_404(Pelicula, id=film_id)

    # Create or update view
    view_reg, created = Views.objects.get_or_create(
        usuari=request.user,
        pelicula=film,
        defaults={"count": 0}
    )

    view_reg.count += 1
    view_reg.save()

    return HttpResponse({"ok": True, "count": view_reg.count})
