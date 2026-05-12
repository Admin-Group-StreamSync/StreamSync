import os
import requests
from datetime import timedelta
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import update_session_auth_hash, login
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Count, Avg, Sum

from apps.external_apis import get_genres_from_api, get_age_ratings_from_api

from apps.users.decorators.permissions import cap_manager_permes
from apps.users.models.models import  LlistaPersonal, Carpeta, Profile, Ressenya, Views, Feedback
from apps.users.forms.forms import UserRegistrationForm, UserUpdateForm

# 1. LOAD CONFIGURATION
from django.shortcuts import redirect

from apps.contents.models import Pelicula
from apps.contents.services import get_all_series, get_all_movies, enrich_tmdb_images



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
def delete_review(request, ressenya_id):
    review = get_object_or_404(Ressenya, id=ressenya_id, usuari=request.user)
    content_id_value, content_type = review.pelicula.id, review.pelicula.tipus
    review.delete()
    return redirect('pagina_contingut', tipus=content_type, content_id=content_id_value)


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





