import os

from django.core.paginator import Paginator
from django.shortcuts import render
from thefuzz import fuzz, process

from apps.contents.models import Pelicula
from apps.contents.services import get_all_series, get_all_movies, get_directors_from_api, get_genres_from_api, \
    get_age_ratings_from_api, get_tmdb_image, enrich_tmdb_images, OPTIONS
from apps.lists.models import LlistaPersonal
from apps.reviews.models import Ressenya
from apps.users.decorators.permissions import cap_manager_permes

# Create your views here.


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