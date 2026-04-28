import os
import requests
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

import json
from django.utils import timezone
from datetime import timedelta
from .models import Pelicula, LlistaPersonal, Carpeta, Profile, Ressenya, Views
from .forms import RegistroUsuarioForm, UserUpdateForm
from functools import wraps
from django.shortcuts import redirect
import json
# 1. CARREGUEM CONFIGURACIÓ
load_dotenv()

urls_list = os.getenv('API_BASE_URLS', '').split(',')
keys_list = os.getenv('API_KEYS_DJANGO', '').split(',')
API_CONFIG = dict(zip(urls_list, keys_list))

OPCIONS = {
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

def mapejar_dades(item, port):
    port_net = str(port).replace('/','')
    plataformes = {"8080": "CinePlus", "8081": "StreamHub", "8082": "PlayMax"}

    # Unificació de claus bàsiques
    titol = item.get('title') or item.get('titol') or "Sense títol"
    synopsis = item.get('synopsis') or "Sense sinopsi disponible."
    # Movies usen 'year', Series usen 'start_year'
    any_contingut = item.get('year') or item.get('start_year') or 0

    return {
        'id': f"{port}_{item.get('id')}",
        'titol': titol,
        'sinopsi': synopsis,
        'any': any_contingut,
        'any_fi': item.get('end_year'),          # ✅ Nou
        'total_seasons': item.get('total_seasons'),  # ✅ Nou
        'rating': item.get('rating', '0.0'),
        'imatge': item.get('imatge') or 'https://via.placeholder.com/300x450',
        'plataforma': plataformes.get(port, "Altres"),

        # Guardem els IDs tal qual ens els dóna l'API ara
        'genre_id': item.get('genre_id'),
        'director_id': item.get('director_id'),
        'age_rating_id': item.get('age_rating_id'),

        # Valors per defecte que omplirem a la vista de detall
        'genere_nom': "General",
        'director_nom': "Desconegut",
        'edat_nom': "N/A"
    }

# --- 3. CRIDES API ---

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
    """Afegeix noms de gènere i edat a una llista d'objectes que només tenen IDs."""
    genres_api = get_genres_from_api()
    ratings_api = get_age_ratings_from_api()

    mapa_genres = {str(g['id']): g['name'] for g in genres_api}
    mapa_ratings = {str(r['id']): r.get('description', 'N/A') for r in ratings_api}

    for item in llista_contingut:
        gid = str(item.get('genre_id'))
        eid = str(item.get('age_rating_id'))

        item['genere_nom'] = mapa_genres.get(gid, "General")
        item['edat_nom'] = mapa_ratings.get(eid, "N/A")

        # Opcional: assegura't que el tipus estigui definit per a l'enllaç de la card
        if 'tipus' not in item:
            # Si l'API no ho diu, pots inferir-ho o defecte a movie
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
@cap_manager_permes
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

    # 3. Filtrar Recomanacions "Per a tu"
    recomanacions_perfil = []
    if request.user.is_authenticated:
        try:
            p = request.user.profile
            filtrades = totes

            # A. Filtre per Tipus (Pelis/Sèries)
            if p.tipus:
                filtrades = [x for x in filtrades if x['tipus'] in p.tipus]

            # B. Filtre per Plataformes (CinePlus, PlayMax...)
            if p.plataformes:
                filtrades = [x for x in filtrades if x.get('plataforma') in p.plataformes]

            # C. Filtre per Gèneres (UNIFICAT: ID amb ID)
            if p.generes:
                # Comprovem si l'ID del gènere de la peli està dins de la llista d'IDs del perfil
                filtrades = [x for x in filtrades if str(x.get('genre_id')) in p.generes]

            # D. Filtre per Edat (UNIFICAT: ID amb ID)
            if p.edat_rating:
                # Comprovem si l'ID de l'edat de la peli està dins de la llista d'IDs del perfil
                filtrades = [x for x in filtrades if str(x.get('age_rating_id')) in p.edat_rating]

            # Ordenem per nota i agafem 4
            recomanacions_perfil = enriquir(
                sorted(filtrades, key=lambda x: float(x.get('rating', 0)), reverse=True)[:4])

        except Exception as e:
            print(f"Error filtrant preferències: {e}")
            recomanacions_perfil = []

    # 4. Seccions generals
    tendencies = enriquir(totes[:4])
    millor_valorades = enriquir(sorted(totes, key=lambda x: float(x.get('rating', 0)), reverse=True)[:4])

    return render(request, 'pages/pagina_principal.html', {
        'tendencies': tendencies,
        'millor_valorades': millor_valorades,
        'recomanacions_perfil': recomanacions_perfil,
        'genres_api': genres_api,
        'ratings': ratings_api
    })

@cap_manager_permes
def detall_contingut(request, tipus, content_id):
    # 1. Agafem el contingut mapejat (que només té IDs)
    totes = get_all_series() if tipus == 'series' else get_all_movies()
    item = next((p for p in totes if str(p['id']) == str(content_id)), None)

    if not item:
        return render(request, '404.html', status=404)

    # 2. ANEM A BUSCAR ELS NOMS REALS ALS ALTRES ENDPOINTS
    # Traduïm el Gènere
    genres = get_genres_from_api()
    item['genere_nom'] = next((g['name'] for g in genres if str(g['id']) == str(item['genre_id'])), "General")

    # Traduïm el Director
    directors = get_directors_from_api()
    item['director_nom'] = next((d['name'] for d in directors if str(d['id']) == str(item['director_id'])),
                                "Desconegut")

    # Traduïm l'Edat
    ratings = get_age_ratings_from_api()
    # L'API de ratings sol tenir 'title' o 'name'
    item['edat_nom'] = next((r.get('title') or r.get('name') or r.get('description')
                             for r in ratings if str(r['id']) == str(item['age_rating_id'])), "N/A")

    # 3. Sincronització DB Local (per a ressenyes i llistes)
    peli_db, _ = Pelicula.objects.update_or_create(
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

    return render(request, 'pagina_contingut.html', {
        'item': item,
        'tipus': tipus,
        'ja_guardada': LlistaPersonal.objects.filter(usuari=request.user,
                                                     pelicula=peli_db).exists() if request.user.is_authenticated else False,
        'carpetes': request.user.les_meves_carpetes.all() if request.user.is_authenticated else [],
        'ressenyes': Ressenya.objects.filter(pelicula=peli_db).order_by('-data_publicacio'),
        'recomanacions': [p for p in totes if str(p['id']) != str(content_id)][:5],
    })

@cap_manager_permes
def catalogo(request, tipus=None):
    # 1. Obtenim les dades brutes
    if tipus == 'movie':
        totes = get_all_movies()
    elif tipus == 'series':
        totes = get_all_series()
    else:
        totes = get_all_movies() + get_all_series()

    # 2. Carreguem totes les traduccions de l'API
    genres_api = get_genres_from_api()
    ratings_api = get_age_ratings_from_api()
    directors_api = get_directors_from_api()  # Necessari per traduir l'ID a nom

    mapa_genres = {str(g['id']): g['name'] for g in genres_api}
    mapa_ratings = {str(r['id']): r.get('description', 'N/A') for r in ratings_api}
    # Creem un mapa de directors: { "1": "Christopher Nolan" }
    mapa_directors = {str(d['id']): d['name'] for d in directors_api}

    # 3. Recollim filtres (incloent el de director)
    f = {
        'p': request.GET.get('plataforma', ''),
        'g': request.GET.get('genere', ''),
        'e': request.GET.get('edat', ''),
        'v': request.GET.get('valoracio', '0'),
        'd': request.GET.get('director', '').strip().lower()  # Cerca de text en minúscules
    }

    resultats = []
    for item in totes:
        # --- TRADUCCIÓ DE NOMS PER A LES CARDS ---
        gid = str(item.get('genre_id'))
        eid = str(item.get('age_rating_id'))
        did = str(item.get('director_id'))

        item['genere_nom'] = mapa_genres.get(gid, "General")
        item['edat_nom'] = mapa_ratings.get(eid, "N/A")
        item['director_nom'] = mapa_directors.get(did, "Desconegut")

        # --- FILTRATGE ---
        if f['p'] and item.get('plataforma') != f['p']: continue
        if f['g'] and gid != f['g']: continue
        if f['e'] and eid != f['e']: continue

        # Filtre de Director: Cerca si el text escrit està DINS del nom del director
        if f['d'] and f['d'] not in item['director_nom'].lower():
            continue

        try:
            if float(item.get('rating', 0)) < float(f['v']): continue
        except:
            pass

        resultats.append(item)

    return render(request, 'cataleg.html', {
        'contenidos': resultats,
        'tipus_actual': tipus,
        'opcions': OPCIONS,
        'genres_api': genres_api,
        'ratings': ratings_api,
        'filtros_sel': f
    })


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
@cap_manager_permes
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
        carpeta.nom, carpeta.icona, carpeta.color = request.POST.get('nom'), request.POST.get(
            'icona'), request.POST.get('color')
        carpeta.save()
        return redirect('llistes')
    return render(request, 'editar_llista.html', {'carpeta': carpeta, 'opcions': OPCIONS})


@login_required
def eliminar_carpeta(request, carpeta_id):
    get_object_or_404(Carpeta, id=carpeta_id, usuari=request.user).delete()
    return redirect('llistes')


@login_required
def treure_de_llista(request, tipus, content_id):  # Afegim 'tipus' com a paràmetre
    # Eliminem l'element de la llista personal de l'usuari
    LlistaPersonal.objects.filter(usuari=request.user, pelicula_id=content_id).delete()

    # Missatge de confirmació (opcional, però queda molt bé)
    messages.success(request, "Element eliminat de la llista.")

    # Redirigim a la pàgina de llistes (o pots redirigir a la carpeta si ho prefereixes)
    return redirect('llistes')


# --- 6. REGISTRE I PERFIL ---

def crear_cuenta(request):
    genres_api = get_genres_from_api()
    ratings_api = get_age_ratings_from_api()
    plataformes_api = OPCIONS.get('plataformas', [])

    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()  # Signal crea Profile buit

            # ✅ Guardem preferències ABANS del login per evitar interferències
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
@cap_manager_permes
def profile2(request):
    # Accedim al perfil directament a través de la relació OneToOne
    try:
        perfil = request.user.profile
    except Profile.DoesNotExist:
        perfil = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        # DEBUG: Mira la terminal per veure si arriben dades
        print("--- POST DETECTAT A PREFERÈNCIES ---")
        print(f"Dades enviades: {request.POST}")

        # Guardem el que arriba del formulari (plural 'generos')
        perfil.tipus = request.POST.getlist('tipus')
        perfil.plataformes = request.POST.getlist('plataformes')
        perfil.generes = request.POST.getlist('generos')
        perfil.edat_rating = request.POST.getlist('edats')

        perfil.save()

        print(f"Perfil de {request.user.username} guardat correctament.")
        messages.success(request, "Preferències actualitzades!")
        return redirect('profile2')

    # GET: Carreguem dades
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

    # 1. Carreguem dades i assignem tipus
    movies = get_all_movies()
    for m in movies: m['tipus'] = 'movie'
    series = get_all_series()
    for s in series: s['tipus'] = 'series'

    totes = movies + series
    resultat_principal = None
    recomanacions = []

    if query:
        # 2. Motor Fuzz per trobar la millor coincidència
        titols = [p['titol'] for p in totes]
        matches = process.extract(query, titols, scorer=fuzz.token_set_ratio, limit=1)

        if matches and matches[0][1] > 65:
            # Trobem l'objecte de la millor coincidència
            resultat_principal = next(p for p in totes if p['titol'] == matches[0][0])

            # 3. SISTEMA DE RECOMANACIONS (Similitud)
            # Filtrem per no recomanar la mateixa pel·lícula que ja estem mostrant
            altres = [p for p in totes if p['id'] != resultat_principal['id']]

            def calcular_puntuacio(item):
                score = 0
                # Mateix Director: +10 punts
                if item.get('director_id') == resultat_principal.get('director_id'):
                    score += 10
                # Mateix Gènere: +5 punts
                if item.get('genre_id') == resultat_principal.get('genre_id'):
                    score += 5
                # Mateix Age Rating: +2 punts
                if item.get('age_rating_id') == resultat_principal.get('age_rating_id'):
                    score += 2
                return score

            # Ordenem la llista segons la puntuació (de més gran a més petita)
            recomanacions = sorted(altres, key=calcular_puntuacio, reverse=True)

            # Només ens quedem amb aquelles que tinguin alguna similitud (score > 0)
            # i limitem a les 5 millors
            recomanacions = [p for p in recomanacions if calcular_puntuacio(p) > 0][:5]

    return render(request, 'cerca_contingut.html', {
        'query': query,
        'resultat': resultat_principal,
        'resultats': recomanacions  # Ara 'resultats' són les recomanacions ordenades
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

            # Obtenim el registre d'aquest usuari i aquesta peli, o el creem a 0
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

    return JsonResponse({"error": "Mètode no permès"}, status=405)


