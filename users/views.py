from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.http import Http404
from .forms import RegistroUsuarioForm, UserUpdateForm
from .models import Profile

# --- CONFIGURACIÓ I CONSTANTS ---
OPCIONS_PREFERENCIES = {
    'plataformes': ["CinePlus", "StreamHub", "PlayMax"],
    'generes': ["Acció", "Comèdia", "Drama", "Sci-Fi", "Crime", "Animation", "Thriller", "Terror"],
    'idiomes': ["Català", "Castellà", "Anglès"],
    'edats': ["TP", "7+", "13+", "16+", "18+"],
}

# --- BASE DE DADES DE CONTINGUT ---
DADES_CONTINGUT = [
    {
        'id': 'm1', 'tipus': 'movie', 'titol': "Kingsman: El Servicio Secreto", 'rating': 10.0, 'any': 2014,
        'genere': 'Acció', 'plataforma': 'CinePlus', 'director': 'Matthew Vaughn', 'edat': '16+',
        'durada': '2h 9min', 'sinopsi': "Un noi del carrer és reclutat per una organització d'espionatge.",
        'imatge': 'https://m.media-amazon.com/images/I/71ESaWmDv2L._AC_UF894,1000_QL80_.jpg'
    },
    {
        'id': 's1', 'tipus': 'series', 'titol': "Agentes de S.H.I.E.L.D", 'rating': 10.0, 'any': 2013,
        'genere': 'Acció', 'plataforma': 'StreamHub', 'director': 'Joss Whedon', 'edat': '13+',
        'durada': '7 Temporades', 'sinopsi': "L'agent Phil Coulson investiga casos estranys.",
        'imatge': 'https://m.media-amazon.com/images/M/MV5BMTkwODYyMjgzOV5BMl5BanBnXkFtZTgwODAzMTE5MjE@._V1_.jpg'
    },
    {
        'id': 'm2', 'tipus': 'movie', 'titol': "Star Trek", 'rating': 9.8, 'any': 2009,
        'genere': 'Sci-Fi', 'plataforma': 'PlayMax', 'director': 'J.J. Abrams', 'edat': '13+',
        'durada': '2h 7min', 'sinopsi': "Kirk i Spock uneixen forces a l'USS Enterprise.",
        'imatge': 'https://cdng.europosters.eu/pod_public/1300/263680.jpg'
    },
    {
        'id': 's2', 'tipus': 'series', 'titol': "Suits: La Clave del Éxito", 'rating': 9.8, 'any': 2011,
        'genere': 'Drama', 'plataforma': 'CinePlus', 'director': 'Aaron Korsh', 'edat': '13+',
        'durada': '9 Temporades', 'sinopsi': "Un advocat estrella contracta un jove brillant sense títol.",
        'imatge': 'https://www.aceprensa.com/wp-content/uploads/2014/01/37680-1-683x1024.jpg'
    },
    {
        'id': 'm4', 'tipus': 'movie', 'titol': "Interstellar", 'rating': 9.4, 'any': 2014,
        'genere': 'Sci-Fi', 'plataforma': 'PlayMax', 'director': 'Christopher Nolan', 'edat': '13+',
        'durada': '2h 49min', 'sinopsi': "Viatge a través d'un forat de cuc per salvar la humanitat.",
        'imatge': 'https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg'
    },
    {
        'id': 'ps1', 'tipus': 'series', 'titol': "Breaking Bad", 'rating': 9.5, 'any': 2008,
        'genere': 'Drama', 'plataforma': 'StreamHub', 'director': 'Vince Gilligan', 'edat': '18+',
        'durada': '5 Temporades', 'sinopsi': "Un professor de química comença a fabricar droga.",
        'imatge': 'https://cdng.europosters.eu/pod_public/1300/251700.jpg'
    }
]

# --- VISTES PÚBLIQUES ---

def pagina_principal(request):
    """Pàgina d'inici amb tendències (Top 4)"""
    tendencies = sorted(DADES_CONTINGUT, key=lambda x: float(x['rating']), reverse=True)[:4]
    return render(request, 'pages/pagina_principal.html', {'tendencies': tendencies})


def catalogo(request, tipus=None):
    """Catàleg unificat amb filtres dinàmics per plataforma, gènere i tipus"""

    # 1. Determinem el tipus (movie/series):
    # El traiem de la URL (paràmetre 'tipus') o del camp hidden del formulari (request.GET)
    filtre_tipus = tipus if tipus else request.GET.get('tipus', '')

    resultats = DADES_CONTINGUT

    # 2. Apliquem el filtre de tipus primer per separar Pel·lícules de Sèries
    if filtre_tipus:
        resultats = [i for i in resultats if i.get('tipus') == filtre_tipus]

    # 3. Recollim la resta de paràmetres del formulari
    query = request.GET.get('q', '')
    plataforma_sel = request.GET.get('plataforma', '')
    genere_sel = request.GET.get('genere', '')
    director_sel = request.GET.get('director', '')
    edat_sel = request.GET.get('edat', '')
    valoracio_sel = request.GET.get('valoracio', '0')

    # 4. Filtrem segons els paràmetres seleccionats
    if query:
        resultats = [i for i in resultats if query.lower() in i['titol'].lower()]
    if plataforma_sel:
        resultats = [i for i in resultats if i.get('plataforma') == plataforma_sel]
    if genere_sel:
        resultats = [i for i in resultats if i.get('genere') == genere_sel]
    if director_sel:
        resultats = [i for i in resultats if director_sel.lower() in i.get('director', '').lower()]
    if edat_sel:
        resultats = [i for i in resultats if i.get('edat') == edat_sel]

    # Filtre de valoració (Rating mínim)
    try:
        val_min = float(valoracio_sel)
        resultats = [i for i in resultats if float(i.get('rating', 0)) >= val_min]
    except (ValueError, TypeError):
        valoracio_sel = "0"

    context = {
        'contenidos': resultats,
        'opcions': OPCIONS_PREFERENCIES,
        'tipus_actual': filtre_tipus, # Indispensable per al <input type="hidden">
        'query': query,
        'plataforma_sel': plataforma_sel,
        'genere_sel': genere_sel,
        'director_sel': director_sel,
        'edat_sel': edat_sel,
        'valoracio_sel': valoracio_sel,
    }
    return render(request, 'cataleg.html', context)


def detall_contingut(request, content_id):
    """Pàgina de detall d'un contingut"""
    item = next((item for item in DADES_CONTINGUT if item['id'] == content_id), None)
    if not item:
        raise Http404("Contingut no trobat")
    return render(request, 'pagina_contingut.html', {'item': item})


# --- GESTIÓ D'USUARIS ---

def crear_cuenta(request):
    """Registre de nou usuari"""
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(
                user=user,
                plataformes=request.POST.getlist('plataformas'),
                generes=request.POST.getlist('generos'),
                idiomes=request.POST.getlist('idiomas'),
                edats=request.POST.getlist('edats')
            )
            messages.success(request, "Compte creat correctament! Ja pots iniciar sessió.")
            return redirect('login')
    else:
        form = RegistroUsuarioForm()
    return render(request, 'registration/registre.html', {'form': form, 'opcions': OPCIONS_PREFERENCIES})


@login_required
def pagina_perfil1(request):
    perfil = request.user.profile
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Dades personals actualitzades!")
            return redirect('pagina_perfil1')
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, 'registration/pagina_perfil1.html', {'form': form, 'perfil': perfil})


@login_required
def profile2(request):
    """Gestió de preferències de contingut"""
    perfil = request.user.profile
    if request.method == 'POST':
        perfil.plataformes = request.POST.getlist('plataformas')
        perfil.generes = request.POST.getlist('generos')
        perfil.idiomes = request.POST.getlist('idiomas')
        perfil.edats = request.POST.getlist('edats')
        perfil.save()
        messages.success(request, "Preferències actualitzades correctament!")
        return redirect('profile2')
    return render(request, 'profile2.html', {'opcions': OPCIONS_PREFERENCIES, 'perfil': perfil})


@login_required
def cambiar_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Contrasenya canviada amb èxit!")
            return redirect('pagina_perfil1')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'registration/cambiar_password.html', {'form': form})


@login_required
def esborrar_compte(request):
    if request.method == 'POST':
        request.user.delete()
        messages.success(request, "El teu compte ha estat eliminat correctament.")
        return redirect('pagina_principal')
    return redirect('pagina_perfil1')


@login_required
def llistes(request):
    """Secció de llistes personals"""
    return render(request, 'llistes.html')