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

# Importem els teus models i formularis
from .models import Pelicula, LlistaPersonal, Carpeta, Profile, Ressenya, Views, Feedback
from .forms import RegistroUsuarioForm, UserUpdateForm

# 1. CARREGUEM CONFIGURACIÓ
load_dotenv()

urls_list = os.getenv('API_BASE_URLS', '').split(',')
keys_list = os.getenv('API_KEYS_DJANGO', '').split(',')
API_CONFIG = dict(zip(urls_list, keys_list))

TMDB_API_KEY = os.getenv('TMDB_API_KEY')

OPCIONS = {
    'plataformas': ['CinePlus', 'StreamHub', 'PlayMax'],
    'idiomas': ['Català', 'Castellano', 'English', 'Français']
}


class StreamSyncLoginView(LoginView):
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Benvingut/da de nou, {form.get_user().username}!")
        return response


# --- 2. FUNCIONS TMDB ---

def get_imatge_tmdb(titol):
    """Busca la imatge d'un contingut a TMDB per títol."""
    try:
        response = requests.get(
            "https://api.themoviedb.org/3/search/multi",
            params={
                "api_key": TMDB_API_KEY,
                "query": titol,
                "language": "en"
            },
            timeout=2
        )
        if response.status_code == 200:
            resultats = response.json().get("results", [])
            if resultats and resultats[0].get("poster_path"):
                return f"https://image.tmdb.org/t/p/w500{resultats[0]['poster_path']}"
    except (requests.RequestException, ValueError):
        pass
    return 'https://via.placeholder.com/300x450'


def enriquir_imatges_tmdb(llista):
    """Afegeix imatges de TMDB a tota una llista en paral·lel."""
    def carregar_imatge(item):
        item['imatge'] = get_imatge_tmdb(item['titol'])
        return item

    with ThreadPoolExecutor(max_workers=10) as executor:
        llista = list(executor.map(carregar_imatge, llista))
    return llista


# --- 3. MAPEIG DE DADES ---

def mapejar_dades(item, port):
    plataformes = {"8080": "CinePlus", "8081": "StreamHub", "8082": "PlayMax"}

    titol = item.get('title') or item.get('titol') or "Sense títol"
    synopsis = item.get('synopsis') or "Sense sinopsi disponible."
    any_contingut = item.get('year') or item.get('start_year') or 0

    return {
        'id': f"{port}_{item.get('id')}",
        'titol': titol,
        'sinopsi': synopsis,
        'any': any_contingut,
        'any_fi': item.get('end_year'),
        'total_seasons': item.get('total_seasons'),
        'rating': item.get('rating', '0.0'),
        'imatge': item.get('imatge') or 'https://via.placeholder.com/300x450',
        'plataforma': plataformes.get(port, "Altres"),
        'genre_id': item.get('genre_id'),
        'director_id': item.get('director_id'),
        'age_rating_id': item.get('age_rating_id'),
        'genere_nom': "General",
        'director_nom': "Desconegut",
        'edat_nom': "N/A"
    }


# --- 4. CRIDES API STREAMSYNC ---

def get_all_movies(query=None):
    resultats = []
    for base_url, key in API_CONFIG.items():
        headers = {'x-api-key': key}
        port = base_url.split(':')[-1]
        params = {'title': query} if query else {}
        try:
            response = requests.get(f"{base_url}/movies", headers=headers, params=params, timeout=2)
            if response.status_code == 200:
                for item in response.json():
                    obj = mapejar_dades(item, port)
                    obj['tipus'] = 'movie'
                    resultats.append(obj)
        except:
            pass
    return resultats


def enriquir_dades_api(llista_contingut):
    genres_api = get_genres_from_api()
    ratings_api = get_age_ratings_from_api()

    mapa_genres = {str(g['id']): g['name'] for g in genres_api}
    mapa_ratings = {str(r['id']): r.get('description', 'N/A') for r in ratings_api}

    for item in llista_contingut:
        gid = str(item.get('genre_id'))
        eid = str(item.get('age_rating_id'))
        item['genere_nom'] = mapa_genres.get(gid, "General")
        item['edat_nom'] = mapa_ratings.get(eid, "N/A")
        if 'tipus' not in item:
            item['tipus'] = item.get('media_type', 'movie')

    return llista_contingut


def get_all_series(query=None):
    resultats = []
    for base_url, key in API_CONFIG.items():
        headers = {'x-api-key': key}
        port = base_url.split(':')[-1]
        params = {'title': query} if query else {}
        try:
            response = requests.get(f"{base_url}/series", headers=headers, params=params, timeout=2)
            if response.status_code == 200:
                for item in response.json():
                    obj = mapejar_dades(item, port)
                    obj['tipus'] = 'series'
                    resultats.append(obj)
        except:
            pass
    return resultats


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


# --- 4. VISTES PRINCIPALS ---

def pagina_principal(request):
    # 1. Obtenim i etiquetem les dades
    movies = get_all_movies()
    for m in movies: m['tipus'] = 'movie'

    series = get_all_series()
    for s in series: s['tipus'] = 'series'

    totes = movies + series

    # 2. Carreguem diccionaris de traducció de l'API (només per visualització)
    genres_api = get_genres_from_api()
    ratings_api = get_age_ratings_from_api()

    mapa_genres = {str(g['id']): g['name'] for g in genres_api}
    mapa_ratings = {str(r['id']): r.get('description', 'N/A') for r in ratings_api}

    def enriquir(llista):
        for item in llista:
            gid = str(item.get('genre_id'))
            eid = str(item.get('age_rating_id'))
            item['genere_nom'] = mapa_genres.get(gid, "General")
            item['edat_nom'] = mapa_ratings.get(eid, "N/A")
        return llista

    recomanacions_perfil = []
    if request.user.is_authenticated:
        try:
            p = request.user.profile
            filtrades = totes

            if p.tipus:
                filtrades = [x for x in filtrades if x['tipus'] in p.tipus]
            if p.plataformes:
                filtrades = [x for x in filtrades if x.get('plataforma') in p.plataformes]
            if p.generes:
                filtrades = [x for x in filtrades if str(x.get('genre_id')) in p.generes]
            if p.edat_rating:
                filtrades = [x for x in filtrades if str(x.get('age_rating_id')) in p.edat_rating]

            top4 = sorted(filtrades, key=lambda x: float(x.get('rating', 0)), reverse=True)[:4]
            recomanacions_perfil = enriquir_imatges_tmdb(enriquir(top4))  # ✅ TMDB en paral·lel

        except Exception as e:
            print(f"Error filtrant preferències: {e}")
            recomanacions_perfil = []

    tendencies = enriquir_imatges_tmdb(enriquir(totes[:4]))  # ✅ TMDB en paral·lel
    millor_valorades = enriquir_imatges_tmdb(
        enriquir(sorted(totes, key=lambda x: float(x.get('rating', 0)), reverse=True)[:4])
    )  # ✅ TMDB en paral·lel

    return render(request, 'pages/pagina_principal.html', {
        'tendencies': tendencies,
        'millor_valorades': millor_valorades,
        'recomanacions_perfil': recomanacions_perfil,
        'genres_api': genres_api,
        'ratings': ratings_api
    })


def detall_contingut(request, tipus, content_id):
    totes = get_all_series() if tipus == 'series' else get_all_movies()
    item = next((p for p in totes if str(p['id']) == str(content_id)), None)

    if not item:
        return render(request, '404.html', status=404)

    genres = get_genres_from_api()
    item['genere_nom'] = next((g['name'] for g in genres if str(g['id']) == str(item['genre_id'])), "General")

    directors = get_directors_from_api()
    item['director_nom'] = next((d['name'] for d in directors if str(d['id']) == str(item['director_id'])), "Desconegut")

    ratings = get_age_ratings_from_api()
    item['edat_nom'] = next((r.get('title') or r.get('name') or r.get('description')
                             for r in ratings if str(r['id']) == str(item['age_rating_id'])), "N/A")

    # ✅ Imatge TMDB per al contingut principal
    item['imatge'] = get_imatge_tmdb(item['titol'])

    peli_db, _ = Pelicula.objects.update_or_create(
        id=item['id'],
        defaults={
            "titol": item['titol'],
            "any": item['any'],
            "valoracio": float(item.get('rating', 0)),
            "imatge": item.get('imatge'),
            "tipus": tipus
        }
    )

    # ✅ Recomanacions amb imatges TMDB en paral·lel
    recomanacions_raw = [p for p in totes if str(p['id']) != str(content_id)][:5]
    recomanacions = enriquir_imatges_tmdb(recomanacions_raw)

    return render(request, 'pagina_contingut.html', {
        'item': item,
        'tipus': tipus,
        'ja_guardada': LlistaPersonal.objects.filter(usuari=request.user,
                                                     pelicula=peli_db).exists() if request.user.is_authenticated else False,
        'carpetes': request.user.les_meves_carpetes.all() if request.user.is_authenticated else [],
        'ressenyes': Ressenya.objects.filter(pelicula=peli_db).order_by('-data_publicacio'),
        'recomanacions': recomanacions,  # ✅ Ara amb imatges
    })


def catalogo(request, tipus=None):
    if tipus == 'movie':
        totes = get_all_movies()
    elif tipus == 'series':
        totes = get_all_series()
    else:
        totes = get_all_movies() + get_all_series()

    genres_api = get_genres_from_api()
    ratings_api = get_age_ratings_from_api()
    directors_api = get_directors_from_api()

    mapa_genres = {str(g['id']): g['name'] for g in genres_api}
    mapa_ratings = {str(r['id']): r.get('description', 'N/A') for r in ratings_api}
    mapa_directors = {str(d['id']): d['name'] for d in directors_api}

    f = {
        'p': request.GET.get('plataforma', ''),
        'g': request.GET.get('genere', ''),
        'e': request.GET.get('edat', ''),
        'v': request.GET.get('valoracio', '0'),
        'd': request.GET.get('director', '').strip().lower()
    }

    # 1. Traduïm i filtrem tots els resultats
    resultats = []
    for item in totes:
        gid = str(item.get('genre_id'))
        eid = str(item.get('age_rating_id'))
        did = str(item.get('director_id'))

        item['genere_nom'] = mapa_genres.get(gid, "General")
        item['edat_nom'] = mapa_ratings.get(eid, "N/A")
        item['director_nom'] = mapa_directors.get(did, "Desconegut")

        if f['p'] and item.get('plataforma') != f['p']: continue
        if f['g'] and gid != f['g']: continue
        if f['e'] and eid != f['e']: continue
        if f['d'] and f['d'] not in item['director_nom'].lower(): continue

        try:
            if float(item.get('rating', 0)) < float(f['v']): continue
        except:
            pass

        resultats.append(item)

    # 2. Paginació sobre els resultats filtrats
    paginator = Paginator(resultats, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # 3. ✅ TMDB només pels 12 de la pàgina actual (en paral·lel)
    enriquir_imatges_tmdb(list(page_obj.object_list))

    # 4. Paràmetres de filtre per mantenir-los a la URL de paginació
    filtres_url = f"&plataforma={f['p']}&genere={f['g']}&edat={f['e']}&valoracio={f['v']}&director={f['d']}"

    return render(request, 'cataleg.html', {
        'contenidos': page_obj.object_list,
        'page_obj': page_obj,
        'filtres_url': filtres_url,
        'tipus_actual': tipus,
        'opcions': OPCIONS,
        'genres_api': genres_api,
        'ratings': ratings_api,
        'filtros_sel': f
    })

def feedback_view(request):
    if request.method == "POST":
        tipus = request.POST.get("tipus")
        titol = request.POST.get("titol")
        descripcio = request.POST.get("descripcio")
        rating = request.POST.get("rating")

        Feedback.objects.create(
            tipus=tipus,
            titol=titol,
            descripcio=descripcio,
            rating=rating if rating else None
        )

        messages.success(request, "Gràcies per la teva opinió!")

        return redirect("feedback")

    return render(request, "pages/feedback.html")

# --- 5. GESTIÓ D'USUARI I LLISTES ---

@login_required
def publicar_ressenya(request, tipus, content_id):
    if request.method == "POST":
        peli_db = get_object_or_404(Pelicula, id=content_id)
        Ressenya.objects.update_or_create(
            usuari=request.user, pelicula=peli_db,
            defaults={'puntuacio': request.POST.get('puntuacio'), 'comentari': request.POST.get('comentari')}
        )
        messages.success(request, "Ressenya publicada!")
    return redirect('pagina_contingut', tipus=tipus, content_id=content_id)


@login_required
def afegir_a_llista(request, tipus, content_id):
    peli = get_object_or_404(Pelicula, id=content_id)
    id_c = request.POST.get('carpeta_id')
    carpeta = get_object_or_404(Carpeta, id=id_c, usuari=request.user) if id_c else None
    LlistaPersonal.objects.get_or_create(usuari=request.user, pelicula=peli, carpeta=carpeta)
    messages.success(request, "Afegit a la llista!")
    return redirect('pagina_contingut', tipus=tipus, content_id=content_id)


@login_required
def eliminar_ressenya(request, ressenya_id):
    ressenya = get_object_or_404(Ressenya, id=ressenya_id, usuari=request.user)
    p_id, p_tipus = ressenya.pelicula.id, ressenya.pelicula.tipus
    ressenya.delete()
    return redirect('pagina_contingut', tipus=p_tipus, content_id=p_id)


@login_required
def llistes(request):
    return render(request, 'llistes.html', {
        'carpetes': request.user.les_meves_carpetes.all(),
        'elements_solts': LlistaPersonal.objects.filter(usuari=request.user, carpeta__isnull=True)
    })


@login_required
def detall_carpeta(request, carpeta_id):
    carpeta = get_object_or_404(Carpeta, id=carpeta_id, usuari=request.user)
    return render(request, 'detall_carpeta.html', {
        'carpeta': carpeta,
        'elements': LlistaPersonal.objects.filter(carpeta=carpeta)
    })


@login_required
def crear_llista(request):
    if request.method == "POST":
        Carpeta.objects.create(
            usuari=request.user, nom=request.POST.get('nom'),
            icona=request.POST.get('icona'), color=request.POST.get('color')
        )
        return redirect('llistes')
    return render(request, 'crear_llista.html', {'opcions': OPCIONS})


@login_required
def editar_llista(request, carpeta_id):
    carpeta = get_object_or_404(Carpeta, id=carpeta_id, usuari=request.user)
    if request.method == "POST":
        carpeta.nom, carpeta.icona, carpeta.color = request.POST.get('nom'), request.POST.get('icona'), request.POST.get('color')
        carpeta.save()
        return redirect('llistes')
    return render(request, 'editar_llista.html', {'carpeta': carpeta, 'opcions': OPCIONS})


@login_required
def eliminar_carpeta(request, carpeta_id):
    get_object_or_404(Carpeta, id=carpeta_id, usuari=request.user).delete()
    return redirect('llistes')


@login_required
def treure_de_llista(request, tipus, content_id):
    LlistaPersonal.objects.filter(usuari=request.user, pelicula_id=content_id).delete()
    messages.success(request, "Element eliminat de la llista.")
    return redirect('llistes')


# --- 7. REGISTRE I PERFIL ---

def crear_cuenta(request):
    genres_api = get_genres_from_api()
    ratings_api = get_age_ratings_from_api()
    plataformes_api = OPCIONS.get('plataformas', [])

    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()

            perfil = user.profile
            perfil.tipus = request.POST.getlist('tipus')
            perfil.plataformes = request.POST.getlist('plataformes')
            perfil.generes = request.POST.getlist('generos')
            perfil.edat_rating = request.POST.getlist('edats')
            perfil.save()

            login(request, user)
            messages.success(request, f"Benvingut/da, {user.username}!")
            return redirect('pagina_principal')
        else:
            print("Errors del formulari:", form.errors)
            messages.error(request, "Error en el formulari.")
    else:
        form = RegistroUsuarioForm()

    context = {
        'form': form,
        'opcions': {
            'tipus': [('movie', 'Pel·lícules'), ('series', 'Sèries')],
            'plataformas': plataformes_api,
            'genres_api': genres_api,
            'ratings_api': ratings_api
        }
    }
    return render(request, 'registration/registre.html', context)


@login_required
def pagina_perfil1(request):
    form = UserUpdateForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Perfil actualitzat!")
    return render(request, 'registration/pagina_perfil1.html', {'form': form})


@login_required
def profile2(request):
    try:
        perfil = request.user.profile
    except Profile.DoesNotExist:
        perfil = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        perfil.tipus = request.POST.getlist('tipus')
        perfil.plataformes = request.POST.getlist('plataformes')
        perfil.generes = request.POST.getlist('generos')
        perfil.edat_rating = request.POST.getlist('edats')
        perfil.save()

        messages.success(request, "Preferències actualitzades!")
        return redirect('profile2')

    genres = get_genres_from_api()
    ratings = get_age_ratings_from_api()

    context = {
        'perfil': perfil,
        'genres_api': genres,
        'ratings_api': ratings,
        'opcions': {
            'tipus': [('movie', 'Pel·lícules'), ('series', 'Sèries')],
            'plataformas': OPCIONS.get('plataformas', []),
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
def esborrar_compte(request):
    if request.method == 'POST':
        request.user.delete()
        return redirect('pagina_principal')
    return render(request, 'registration/esborrar_compte.html')


def cerca_contingut(request):
    query = request.GET.get('q', '').strip()

    movies = get_all_movies()
    for m in movies: m['tipus'] = 'movie'
    series = get_all_series()
    for s in series: s['tipus'] = 'series'

    totes = movies + series
    resultat_principal = None
    recomanacions = []

    if query:
        titols = [p['titol'] for p in totes]
        matches = process.extract(query, titols, scorer=fuzz.token_set_ratio, limit=1)

        if matches and matches[0][1] > 65:
            resultat_principal = next(p for p in totes if p['titol'] == matches[0][0])

            # ✅ TMDB per al resultat principal
            resultat_principal['imatge'] = get_imatge_tmdb(resultat_principal['titol'])

            altres = [p for p in totes if p['id'] != resultat_principal['id']]

            def calcular_puntuacio(item):
                score = 0
                if item.get('director_id') == resultat_principal.get('director_id'):
                    score += 10
                if item.get('genre_id') == resultat_principal.get('genre_id'):
                    score += 5
                if item.get('age_rating_id') == resultat_principal.get('age_rating_id'):
                    score += 2
                return score

            recomanacions = sorted(altres, key=calcular_puntuacio, reverse=True)
            recomanacions = [p for p in recomanacions if calcular_puntuacio(p) > 0][:5]

            # ✅ TMDB per a les recomanacions en paral·lel
            enriquir_imatges_tmdb(recomanacions)

    return render(request, 'cerca_contingut.html', {
        'query': query,
        'resultat': resultat_principal,
        'resultats': recomanacions
    })

@login_required
@api_view(['POST'])
def register_view(request):
    film_id = request.data.get("film")

    # comprobar que llega film_id
    if not film_id:
        return HttpResponse({"error": "film_id requerido"}, status=400)#

    # obtener película
    film = get_object_or_404(Pelicula, id=film_id)

    # crear o actualizar view
    view_reg, created = Views.objects.get_or_create(
        usuari=request.user,
        pelicula=film,
        defaults={"count": 0}
    )

    view_reg.count += 1
    view_reg.save()

    return HttpResponse({"ok": True, "count": view_reg.count})


