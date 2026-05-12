import os
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import update_session_auth_hash, login
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from dotenv import load_dotenv
from rest_framework.decorators import api_view
from thefuzz import process, fuzz
from django.db.models import Count, Avg, Sum
from django.utils import timezone

from .models import Pelicula, LlistaPersonal, Carpeta, Profile, Ressenya, Views, Feedback
from .forms import UserRegistrationForm, UserUpdateForm

# 1. LOAD CONFIGURATION
from functools import wraps
from django.shortcuts import redirect
import json
# 1. CARREGUEM CONFIGURACIÓ
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
    def get_success_url(self):
        user = self.request.user

        if hasattr(user, 'profile') and user.profile.manager_de:
            return f'/dashboard/{user.profile.manager_de}/'


        return '/perfil/'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Benvingut/da de nou, {form.get_user().username}!")
        return response

# --- decorador usuari SPM---

def cap_manager_permes(view_func):

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            plataforma = request.user.profile.manager_de
            if plataforma:
                # Es un SPM. Lo mandamos a su panel.
                messages.info(request, "Ets un Manager. Aquesta és la teva àrea de treball.")
                return redirect('dashboard_manager', plataforma_nom=plataforma)
        return view_func(request, *args, **kwargs)
    return _wrapped_view
# --- 2. FUNCIONS AUXILIARS I MAPEIG ---

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
    return deduplicate_content(results)  # ✅ Deduplicació


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

@cap_manager_permes
def home_page(request):
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


@cap_manager_permes
def content_detail(request, tipus, content_id):
    all_content = get_all_series() if tipus == 'series' else get_all_movies()
    item = next((p for p in all_content if str(p['id']) == str(content_id)), None)

    if not item:
        return render(request, '404.html', status=404)

    if 'plataformes_disponibles' not in item:
        item['plataformes_disponibles'] = [item.get('plataforma', 'N/A')]

    # ✅ Carreguem traduccions una sola vegada
    genres = get_genres_from_api()
    directors = get_directors_from_api()
    ratings = get_age_ratings_from_api()

    mapa_genres = {str(g['id']): g['name'] for g in genres}
    mapa_ratings = {str(r['id']): r.get('description') or r.get('title') or r.get('name') or 'N/A' for r in ratings}
    mapa_directors = {str(d['id']): d['name'] for d in directors}

    # ✅ Enriquim l'item principal
    item['genere_nom'] = mapa_genres.get(str(item.get('genre_id')), 'General')
    item['director_nom'] = mapa_directors.get(str(item.get('director_id')), 'Desconegut')
    item['edat_nom'] = mapa_ratings.get(str(item.get('age_rating_id')), 'N/A')
    item['imatge'] = get_tmdb_image(item['titol'])

    movie_db, _ = Pelicula.objects.update_or_create(
        id=item['id'],
        defaults={
            "titol": item['titol'],
            "any": item['any'],
            "valoracio": float(item.get('rating', 0)),
            "imatge": item.get('imatge'),
            "tipus": tipus,
            "plataforma": item.get('plataforma')
        }
    )

    # ✅ Enriquim les recomanacions amb gènere i edat
    raw_recommendations = [p for p in all_content if str(p['id']) != str(content_id)][:5]
    for r in raw_recommendations:
        r['genere_nom'] = mapa_genres.get(str(r.get('genre_id')), 'General')
        r['edat_nom'] = mapa_ratings.get(str(r.get('age_rating_id')), 'N/A')

    recommendations = enrich_tmdb_images(raw_recommendations)

    # CHECK IF THERE'S ALREADY A REVIEW
    ressenya_usuari = None

    if request.user.is_authenticated:
        ressenya_usuari = Ressenya.objects.filter(
            usuari=request.user,
            pelicula=movie_db
        ).first()

    return render(request, 'pagina_contingut.html', {
        'item': item,
        'tipus': tipus,
        'ja_guardada': LlistaPersonal.objects.filter(usuari=request.user,
                                                     pelicula=movie_db).exists() if request.user.is_authenticated else False,
        'carpetes': request.user.les_meves_carpetes.all() if request.user.is_authenticated else [],
        'ressenyes': Ressenya.objects.filter(pelicula=movie_db).order_by('-data_publicacio'),
        'recomanacions': recommendations,
        'ressenya_usuari': ressenya_usuari,
    })

@cap_manager_permes
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

        if filters['p'] and filters['p'] not in item.get('plataformes_disponibles', [item.get('plataforma', '')]): continue
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

# Legal pages
def termsofuse_view(request):
    return render(request, "legal/terms.html")
def privacy_view(request):
    return render(request, "legal/privacy.html")
def cookies_view(request):
    return render(request, "legal/cookies.html")
def content_disclaimer_view(request):
    return render(request, "legal/content_disclaimer.html")


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
    pass


@cap_manager_permes
def llistes(request):
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
        form = UserRegistrationForm(request.POST)
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
        form = UserRegistrationForm()

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
@cap_manager_permes
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

    # ✅ Carreguem traduccions una sola vegada
    genres_api = get_genres_from_api()
    ratings_api = get_age_ratings_from_api()
    mapa_genres = {str(g['id']): g['name'] for g in genres_api}
    mapa_ratings = {str(r['id']): r.get('description', 'N/A') for r in ratings_api}

    if query:
        titles = [p['titol'] for p in all_content]
        matches = process.extract(query, titles, scorer=fuzz.token_set_ratio, limit=1)

        if matches and matches[0][1] > 65:
            main_result = next(p for p in all_content if p['titol'] == matches[0][0])

            # ✅ Enriquim el resultat principal
            main_result['genere_nom'] = mapa_genres.get(str(main_result.get('genre_id')), 'General')
            main_result['edat_nom'] = mapa_ratings.get(str(main_result.get('age_rating_id')), 'N/A')
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



            # ✅ Només continguts del mateix gènere
            recommendations = [
                p for p in others
                if p.get('genre_id') == main_result.get('genre_id')
            ][:5]

            # ✅ Enriquim gènere i edat de les recomanacions
            for item in recommendations:
                item['genere_nom'] = mapa_genres.get(str(item.get('genre_id')), 'General')
                item['edat_nom'] = mapa_ratings.get(str(item.get('age_rating_id')), 'N/A')


            enrich_tmdb_images(recommendations)

    return render(request, 'cerca_contingut.html', {
        'query': query,
        'resultat': main_result,
        'resultats': recommendations
    })


@login_required
def dashboard_manager(request, plataforma_nom):
    if request.user.profile.manager_de != plataforma_nom:
        messages.error(request, "No tens permís per gestionar aquesta plataforma.")
        return redirect('pagina_principal')

    contingut = Pelicula.objects.filter(plataforma=plataforma_nom)

    # Consultes globals segures
    estadisticas_ressenyes = Ressenya.objects.filter(pelicula__in=contingut).aggregate(
        mitjana=Avg('puntuacio'), total=Count('id')
    )
    total_guardados = LlistaPersonal.objects.filter(pelicula__in=contingut).count()
    usuaris_interessats = sum(1 for p in Profile.objects.all() if plataforma_nom in p.plataformes)

    # Temps per a les tendencies
    ara = timezone.now()
    fa_30_dies = ara - timedelta(days=30)
    fa_60_dies = ara - timedelta(days=60)

    def calcular_percentatge(actual, anterior):
        if anterior == 0:
            return 100.0 if actual > 0 else 0.0
        return round(((actual - anterior) / anterior) * 100, 1)

    try:
        # --- TENDENCIES ---
        vistes_actuals = \
        Views.objects.filter(pelicula__in=contingut, visualization_date__gte=fa_30_dies).aggregate(t=Sum('count'))[
            't'] or 0
        vistes_anteriors = Views.objects.filter(pelicula__in=contingut, visualization_date__gte=fa_60_dies,
                                                visualization_date__lt=fa_30_dies).aggregate(t=Sum('count'))['t'] or 0
        trend_views = calcular_percentatge(vistes_actuals, vistes_anteriors)

        ress_actuals = Ressenya.objects.filter(pelicula__in=contingut, data_publicacio__gte=fa_30_dies).count()
        ress_anteriors = Ressenya.objects.filter(pelicula__in=contingut, data_publicacio__gte=fa_60_dies,
                                                 data_publicacio__lt=fa_30_dies).count()
        trend_ress = calcular_percentatge(ress_actuals, ress_anteriors)

        guardats_actuals = LlistaPersonal.objects.filter(pelicula__in=contingut, data_afegida__gte=fa_30_dies).count()
        guardats_anteriors = LlistaPersonal.objects.filter(pelicula__in=contingut, data_afegida__gte=fa_60_dies,
                                                           data_afegida__lt=fa_30_dies).count()
        trend_guardats = calcular_percentatge(guardats_actuals, guardats_anteriors)

        nota_actual = \
        Ressenya.objects.filter(pelicula__in=contingut, data_publicacio__gte=fa_30_dies).aggregate(m=Avg('puntuacio'))[
            'm'] or 0
        nota_anterior = Ressenya.objects.filter(pelicula__in=contingut, data_publicacio__gte=fa_60_dies,
                                                data_publicacio__lt=fa_30_dies).aggregate(m=Avg('puntuacio'))['m'] or 0
        trend_nota = round(nota_actual - nota_anterior, 1) if nota_anterior else round(nota_actual, 1)

        usuaris_actuals = sum(
            1 for p in Profile.objects.filter(user__date_joined__gte=fa_30_dies) if plataforma_nom in p.plataformes)
        usuaris_anteriors = sum(
            1 for p in Profile.objects.filter(user__date_joined__gte=fa_60_dies, user__date_joined__lt=fa_30_dies) if
            plataforma_nom in p.plataformes)
        trend_usuaris = calcular_percentatge(usuaris_actuals, usuaris_anteriors)

        # --- DADES GENERALS ---
        total_views = Views.objects.filter(pelicula__in=contingut).aggregate(total=Sum('count'))['total'] or 0
        top_contingut_db = contingut.annotate(vistes_totals=Sum('views__count')).order_by('-vistes_totals')[:5]
        top_contingut = []
        for p in top_contingut_db:
            top_contingut.append({
                'id': p.id,
                'titol': p.titol,
                'imatge': p.imatge,
                'any': p.any,
                'tipus': p.tipus,
                'rating': p.valoracio,
                'vistes_totals': p.vistes_totals,
                'genre_id': '',  # Enganyem al HTML perquè no doni error
                'age_rating_id': '',  # AÑADIMOS ESTO
                'genere_nom': '',
                'edat_nom': '',
                'director_nom': ''
            })

        # --- GRAFIC 1 i 2 (Donut i Barres) ---
        vistes_pelis = \
        Views.objects.filter(pelicula__in=contingut, pelicula__tipus='movie').aggregate(t=Sum('count'))['t'] or 0
        vistes_series = \
        Views.objects.filter(pelicula__in=contingut, pelicula__tipus='series').aggregate(t=Sum('count'))['t'] or 0

            # 1. Descarreguem l'API en segon pla per saber els gèneres reals
        totes_api = get_all_movies() + get_all_series()
        genres_api = get_genres_from_api()
        mapa_genres = {str(g['id']): g['name'] for g in genres_api}

            # 2. Creem un diccionari per agrupar i sumar les visites manualment
        visites_per_genere = {}
        vistes_cineplus = Views.objects.filter(pelicula__in=contingut)

        for v in vistes_cineplus:
                # Creuem la visita local amb la peli de l'API per l'ID
            item_api = next((x for x in totes_api if x['id'] == v.pelicula.id), None)

            if item_api:
                gid = str(item_api.get('genre_id'))
                nom_genere = mapa_genres.get(gid, "Altres")
            else:
                nom_genere = "Altres"

                # Sumem les visites (v.count) al gènere corresponent
            visites_per_genere[nom_genere] = visites_per_genere.get(nom_genere, 0) + v.count

            # 3. Ordenem els gèneres de més a menys visites i agafem els 6 primers
        generes_ordenats = sorted(visites_per_genere.items(), key=lambda x: x[1], reverse=True)[:6]

        noms_generes = [g[0] for g in generes_ordenats] if generes_ordenats else ["Altres"]
        valors_generes = [g[1] for g in generes_ordenats] if generes_ordenats else [0]

        # --- GRAFIC 3 (Evolucio Línies - Ultims 4 mesos) ---
        mesos_cat = ['Gen', 'Feb', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Oct', 'Nov', 'Des']
        evolucio_labels = []
        evolucio_vistes = []
        evolucio_usuaris = []

        for i in range(3, -1, -1):
            data_inici = ara - timedelta(days=30 * (i + 1))
            data_fi = ara - timedelta(days=30 * i)
            mes_nom = mesos_cat[data_fi.month - 1]
            evolucio_labels.append(mes_nom)

            v = Views.objects.filter(pelicula__in=contingut, visualization_date__gte=data_inici,
                                     visualization_date__lt=data_fi).aggregate(t=Sum('count'))['t'] or 0
            u = sum(
                1 for p in Profile.objects.filter(user__date_joined__gte=data_inici, user__date_joined__lt=data_fi) if
                plataforma_nom in p.plataformes)
            evolucio_vistes.append(v)
            evolucio_usuaris.append(u)

            # --- GRAFIC 4 (Classificacio Edat - Progress Bars) ---
            # 1. Obtenim les definicions d'edat de l'API
            ratings_api = get_age_ratings_from_api()
            # Creem un mapa d'IDs a noms (ex: {"1": "18+", "2": "Tots"})
            mapa_edats = {str(r['id']): (r.get('name') or r.get('title') or r.get('description') or "Tots") for r in
                          ratings_api}

            # 2. Inicialitzem el comptador per a les categories del teu HTML
            edats_dist = {'Tots': 0, '7+': 0, '13+': 0, '16+': 0, '18+': 0}
            total_vistes_calculades = 0

            # 3. Recuperem totes les visualitzacions de la plataforma
            vistes_plataforma = Views.objects.filter(pelicula__in=contingut)

            for v in vistes_plataforma:
                # Busquem la peli a l'API per saber el seu age_rating_id real
                # (Ja que a la DB local potser no el tens actualitzat)
                item_api = next((x for x in totes_api if x['id'] == v.pelicula.id), None)

                if item_api:
                    eid = str(item_api.get('age_rating_id'))
                    nom_edat = mapa_edats.get(eid, "Tots").upper()
                else:
                    nom_edat = "TOTS"

                # Sumem les visites a la categoria corresponent
                if "18" in nom_edat:
                    edats_dist['18+'] += v.count
                elif "16" in nom_edat:
                    edats_dist['16+'] += v.count
                elif "13" in nom_edat:
                    edats_dist['13+'] += v.count
                elif "7" in nom_edat:
                    edats_dist['7+'] += v.count
                else:
                    edats_dist['Tots'] += v.count

                total_vistes_calculades += v.count

            # 4. Calculem els percentatges reals per a l'HTML
            divisor = total_vistes_calculades if total_vistes_calculades > 0 else 1
            edats_pct = {
                'tots': round((edats_dist['Tots'] / divisor) * 100),
                'm7': round((edats_dist['7+'] / divisor) * 100),
                'm13': round((edats_dist['13+'] / divisor) * 100),
                'm16': round((edats_dist['16+'] / divisor) * 100),
                'm18': round((edats_dist['18+'] / divisor) * 100),
            }

    except Exception as e:
        print(f"Error cargando estadisticas: {e}")
        total_views = trend_views = trend_ress = trend_guardats = trend_nota = trend_usuaris = vistes_pelis = vistes_series = 0
        top_contingut = noms_generes = valors_generes = evolucio_labels = evolucio_vistes = evolucio_usuaris = []
        edats_pct = {'tots': 0, 'm7': 0, 'm13': 0, 'm16': 0, 'm18': 0}

    context = {
        'plataforma': plataforma_nom,
        'pelicules': contingut,
        'metricas': {
            'total_views': total_views,
            'nota_mitjana': round(estadisticas_ressenyes['mitjana'] or 0, 1),
            'total_ressenyes': estadisticas_ressenyes['total'],
            'total_guardados': total_guardados,
            'usuaris_interessats': usuaris_interessats,
        },
        'tendencias': {
            'views': trend_views,
            'users': trend_usuaris,
            'nota': trend_nota,
            'ressenyes': trend_ress,
            'guardados': trend_guardats,
        },
        'top_contingut': top_contingut,
        'edats_pct': edats_pct,
        'grafic_tipus_data': json.dumps([vistes_pelis, vistes_series]),
        'grafic_generes_labels': json.dumps(noms_generes),
        'grafic_generes_data': json.dumps(valors_generes),
        'grafic_evolucio_labels': json.dumps(evolucio_labels),
        'grafic_evolucio_vistes': json.dumps(evolucio_vistes),
        'grafic_evolucio_usuaris': json.dumps(evolucio_usuaris),
    }

    return render(request, 'registration/dashboard_manager.html', context)

@login_required
def register_view(request):
    if request.method == "POST":
        try:
            # Llegim les dades que ens envia el Javascript
            data = json.loads(request.body)
            film_id = data.get("film")

            if not film_id:
                return JsonResponse({"error": "Falta l'ID de la pel·lícula"}, status=400)

            # Busquem la pel·lícula a la base de dades local
            film = get_object_or_404(Pelicula, id=film_id)
            # Fetch movie
            film = get_object_or_404(Pelicula, id=film_id)

            # Obtenim el registre d'aquest usuari i aquesta peli, o el creem a 0
            view_reg, created = Views.objects.get_or_create(
                usuari=request.user,
                pelicula=film,
                defaults={"count": 0}
            )
            # Create or update view
            view_reg, created = Views.objects.get_or_create(
                usuari=request.user,
                pelicula=film,
                defaults={"count": 0}
            )

            # Li sumem 1 visita
            view_reg.count += 1
            view_reg.save()

            print(f"Visita registrada! {film.titol} ara té {view_reg.count} visites d'aquest usuari.")

            return JsonResponse({"ok": True, "count": view_reg.count})

        except Exception as e:
            print("Error al registrar la visita:", str(e))
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not permited"}, status=405)
