import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from apps.analytics.models import Views
from apps.contents.models import Pelicula
from apps.contents.services import get_all_movies, get_all_series, get_age_ratings_from_api, get_genres_from_api
from apps.lists.models import LlistaPersonal
from apps.reviews.models import Ressenya
from apps.users.models.models import Profile


# Create your views here.

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

            # Fetch movie
            film = get_object_or_404(Pelicula, id=film_id)


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
