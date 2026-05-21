import os
from django.core.paginator import Paginator
from django.shortcuts import render
from django.http import Http404  # ✅ Evita problemes si no existeix 404.html
from django.db.models import Avg
from thefuzz import fuzz, process

from apps.contents.models import Pelicula
from apps.contents.services.content_service import (
    get_all_series, get_all_movies, get_directors_from_api,
    get_genres_from_api, get_age_ratings_from_api,
    get_tmdb_image, enrich_tmdb_images, OPTIONS
)
from apps.lists.models import LlistaPersonal
from apps.reviews.models import Ressenya
from apps.users.decorators.permissions import cap_manager_permes


@cap_manager_permes
def content_detail(request, tipus, content_id):
    # 1. Carreguem el contingut segons el tipus de la URL a
    all_content = get_all_series() if tipus == 'series' else get_all_movies()

    # ✅ SOLUCIÓ DEFINITIVA: Busquem per la ID completa de Render que ve de la URL
    # D'aquesta manera, si demanes la sèrie '..._22' no es barrejarà amb la pel·lícula '..._22'
    item = next((p for p in all_content if str(p['id']) == str(content_id)), None)

    # 🔄 Si per algun motiu de memòria de Render l'ID complet no coincideix exactament,
    # fem una segona cerca de seguretat comparant només el número final
    if not item:
        def extreure_numero_id(cid):
            return str(cid).split('_')[-1] if '_' in str(cid) else str(cid)

        target_number = extreure_numero_id(content_id)
        item = next((p for p in all_content if extreure_numero_id(p['id']) == target_number), None)

    if not item:
        raise Http404("No s'ha trobat el contingut sol·licitat.")

    if 'plataformes_disponibles' not in item or not item['plataformes_disponibles']:
        item['plataformes_disponibles'] = [item.get('plataforma', 'N/A')]

    # Carreguem traduccions una sola vegada
    genres = get_genres_from_api()
    directors = get_directors_from_api()
    ratings = get_age_ratings_from_api()

    mapa_genres = {str(g['id']): g['name'] for g in genres}
    mapa_ratings = {str(r['id']): r.get('description') or r.get('title') or r.get('name') or 'N/A' for r in ratings}
    mapa_directors = {str(d['id']): d['name'] for d in directors}

    item['genere_nom'] = mapa_genres.get(str(item.get('genre_id')), 'General')
    item['director_nom'] = mapa_directors.get(str(item.get('director_id')), 'Desconegut')
    item['edat_nom'] = mapa_ratings.get(str(item.get('age_rating_id')), 'N/A')
    item['imatge'] = get_tmdb_image(item['titol'])

    # ✅ Per desar correctament a la base de dades sense trencar l'IntegerField:
    # Si l'id de l'item té un '_' extraiem només el número final (ex: '22') per desar-lo com a enter
    id_numeric_str = str(item['id']).split('_')[-1] if '_' in str(item['id']) else str(item['id'])
    db_id = int(id_numeric_str) if id_numeric_str.isdigit() else item['id']

    movie_db, _ = Pelicula.objects.update_or_create(
        id=db_id,
        defaults={
            "titol": item['titol'],
            "any": item['any'],
            "valoracio": float(item.get('rating') or 0),
            "imatge": item.get('imatge'),
            "tipus": tipus,
            "plataforma": item.get('plataforma')
        }
    )

    # Filtrem recomanacions comparant les IDs completes de Render
    raw_recommendations = [p for p in all_content if str(p['id']) != str(item['id'])][:5]
    for r in raw_recommendations:
        r['genere_nom'] = mapa_genres.get(str(r.get('genre_id')), 'General')
        r['edat_nom'] = mapa_ratings.get(str(r.get('age_rating_id')), 'N/A')

    recommendations = enrich_tmdb_images(raw_recommendations)

    ressenya_usuari = None
    if request.user.is_authenticated:
        ressenya_usuari = Ressenya.objects.filter(usuari=request.user, pelicula=movie_db).first()

    community_rating = Ressenya.objects.filter(pelicula=movie_db).aggregate(avg=Avg('puntuacio'))['avg']
    if community_rating is not None:
        community_rating = round(community_rating, 1)

    return render(request, 'pagina_contingut.html', {
        'item': item,
        'tipus': tipus,
        'ja_guardada': LlistaPersonal.objects.filter(usuari=request.user,
                                                     pelicula=movie_db).exists() if request.user.is_authenticated else False,
        'carpetes': request.user.les_meves_carpetes.all() if request.user.is_authenticated else [],
        'ressenyes': Ressenya.objects.filter(pelicula=movie_db).order_by('-data_publicacio'),
        'recomanacions': recommendations,
        'ressenya_usuari': ressenya_usuari,
        'community_rating': community_rating,
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

        # ✅ Millorat el filtre de plataformes perquè cerqui bé dins el nou format de llista deduplicat
        plataformes_item = item.get('plataformes_disponibles', [item.get('plataforma', '')])
        if filters['p'] and filters['p'] not in plataformes_item: continue
        if filters['g'] and gid != filters['g']: continue
        if filters['e'] and eid != filters['e']: continue
        if filters['d'] and filters['d'] not in item['director_nom'].lower(): continue

        try:
            if float(item.get('rating', 0)) < float(filters['v']): continue
        except ValueError:
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

    genres_api = get_genres_from_api()
    ratings_api = get_age_ratings_from_api()
    mapa_genres = {str(g['id']): g['name'] for g in genres_api}
    mapa_ratings = {str(r['id']): r.get('description', 'N/A') for r in ratings_api}

    if query:
        titles = [p['titol'] for p in all_content]
        matches = process.extract(query, titles, scorer=fuzz.token_set_ratio, limit=1)

        if matches and matches[0][1] > 65:
            main_result = next(p for p in all_content if p['titol'] == matches[0][0])

            main_result['genere_nom'] = mapa_genres.get(str(main_result.get('genre_id')), 'General')
            main_result['edat_nom'] = mapa_ratings.get(str(main_result.get('age_rating_id')), 'N/A')
            main_result['imatge'] = get_tmdb_image(main_result['titol'])

            others = [p for p in all_content if p['id'] != main_result['id']]

            recommendations = [
                p for p in others
                if p.get('genre_id') == main_result.get('genre_id')
            ][:5]

            for item in recommendations:
                item['genere_nom'] = mapa_genres.get(str(item.get('genre_id')), 'General')
                item['edat_nom'] = mapa_ratings.get(str(item.get('age_rating_id')), 'N/A')

            enrich_tmdb_images(recommendations)

    return render(request, 'cerca_contingut.html', {
        'query': query,
        'resultat': main_result,
        'resultats': recommendations
    })