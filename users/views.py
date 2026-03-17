from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from .forms import RegistroUsuarioForm, UserUpdateForm
from .models import Profile


OPCIONS_PREFERENCIES = {
    'plataformes': ["Netflix","MAX", "Prime Video", "Disney+"],
    'generes': ["Action", "Comedy", "Drama", "Sci-Fi", "Crime", "Animation", "Thriller"],
    'idiomes': ["English", "Spanish", "French", "Japanese", "Korean"],
    'edats': ["G", "PG", "PG-13", "R"],
    'paisos': ["USA", "UK", "Spain", "Japan", "South Korea"]
}
def pagina_principal(request):
    tendencies = sorted(DADES_CONTINGUT, key=lambda x: float(x['rating']), reverse=True)[:4]
    return render(request, 'pages/pagina_principal.html', {'tendencies': tendencies})

@login_required
def llistes(request):
    return render(request, 'llistes.html')


# credencials registre
def crear_cuenta(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            request.session['datos_registro_paso1'] = request.POST.dict()
            return redirect('sign_in2')
    else:
        datos_previos = request.session.get('datos_registro_paso1', None)
        form = RegistroUsuarioForm(initial=datos_previos) if datos_previos else RegistroUsuarioForm()

    return render(request, 'registration/registre.html', {'form': form})


# registre preferencies
def preferencias_registro(request):
    if 'datos_registro_paso1' not in request.session:
        return redirect('crear_cuenta')

    if request.method == 'POST':
        if request.POST.get('accio') == 'enrere':
            request.session['datos_registro_paso2'] = {
                'plataformas': request.POST.getlist('plataformas'),
                'generos': request.POST.getlist('generos'),
                'idiomas': request.POST.getlist('idiomas'),
                'paisos': request.POST.getlist('paisos'),
                'edats': request.POST.getlist('edats'),
            }
            return redirect('crear_cuenta')

        datos_paso1 = request.session['datos_registro_paso1']
        form = RegistroUsuarioForm(datos_paso1)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(
                user=user,
                plataformes=request.POST.getlist('plataformas'),
                generes=request.POST.getlist('generos'),
                idiomes=request.POST.getlist('idiomas'),
                paisos=request.POST.getlist('paisos'),
                edats=request.POST.getlist('edats')
            )
            del request.session['datos_registro_paso1']
            if 'datos_registro_paso2' in request.session:
                del request.session['datos_registro_paso2']

            login(request, user)
            return redirect('pagina_principal')

    datos_paso2 = request.session.get('datos_registro_paso2', {})

    return render(request, 'registration/sign_in2.html', {
        'datos_paso2': datos_paso2,
        'opcions': OPCIONS_PREFERENCIES
    })


@login_required
def pagina_perfil1(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Dades actualitzades correctament!")
            return redirect('pagina_perfil1')
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, 'registration/pagina_perfil1.html', {'form': form})


# preferencies
@login_required
def profile2(request):
    perfil = request.user.profile
    if request.method == 'POST':
        # Guardem el que l'usuari ha seleccionat
        perfil.plataformes = request.POST.getlist('plataformas')
        perfil.generes = request.POST.getlist('generos')
        perfil.idiomes = request.POST.getlist('idiomas')
        perfil.edats = request.POST.getlist('edats')
        perfil.paisos = request.POST.getlist('paisos')
        perfil.save()
        messages.success(request, "Preferències actualitzades!")
        return redirect('profile2')


    return render(request, 'profile2.html', {'opcions': OPCIONS_PREFERENCIES})


@login_required
def cambiar_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Contrasenya canviada!")
            return redirect('pagina_perfil1')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'registration/cambiar_password.html', {'form': form})


@login_required
def esborrar_compte(request):
    if request.method == 'POST':
        request.user.delete()
        messages.success(request, "Compte esborrat correctament.")
        return redirect('pagina_principal')
    return redirect('pagina_perfil1')


#simulació
DADES_CONTINGUT = [
    # --- PEL·LÍCULES ---
    {'id': 'm1', 'tipus': 'movie', 'titol': 'Inception',
     'synopsis': 'Un lladre que roba secrets corporatius a través de l\'ús de la tecnologia de compartició de somnis.',
     'any': 2010, 'rating': 8.8, 'genere': 'Sci-Fi', 'director': 'Christopher Nolan', 'edat': 'PG-13',
     'idioma': 'English', 'pais': 'USA'},
    {'id': 'm2', 'tipus': 'movie', 'titol': 'Pulp Fiction',
     'synopsis': 'Vides creuades de mafiosos, boxejadors i lladres.', 'any': 1994, 'rating': 8.9, 'genere': 'Crime',
     'director': 'Quentin Tarantino', 'edat': 'R', 'idioma': 'English', 'pais': 'USA'},
    {'id': 'm3', 'tipus': 'movie', 'titol': 'Parasite',
     'synopsis': 'La cobdícia i la discriminació de classe amenacen la relació entre la família Park i el clan Kim.',
     'any': 2019, 'rating': 8.6, 'genere': 'Thriller', 'director': 'Bong Joon-ho', 'edat': 'R', 'idioma': 'Korean',
     'pais': 'South Korea'},
    {'id': 'm4', 'tipus': 'movie', 'titol': 'Spirited Away',
     'synopsis': 'Durant un trasllat, una nena entra en un món governat per déus, bruixes i esperits.', 'any': 2001,
     'rating': 8.6, 'genere': 'Animation', 'director': 'Hayao Miyazaki', 'edat': 'G', 'idioma': 'Japanese',
     'pais': 'Japan'},
    {'id': 'm5', 'tipus': 'movie', 'titol': 'Dune',
     'synopsis': 'Un jove hereu ha de viatjar a un perillós planeta desèrtic.', 'any': 2021, 'rating': 8.1,
     'genere': 'Sci-Fi', 'director': 'Denis Villeneuve', 'edat': 'PG-13', 'idioma': 'English', 'pais': 'Canada'},
    {'id': 'm6', 'tipus': 'movie', 'titol': 'Volver', 'synopsis': 'Dues germanes tornen al seu poble natal a La Manxa.',
     'any': 2006, 'rating': 7.6, 'genere': 'Drama', 'director': 'Pedro Almodóvar', 'edat': 'PG-13', 'idioma': 'Spanish',
     'pais': 'Spain'},

    # --- SÈRIES ---
    {'id': 's1', 'tipus': 'series', 'titol': 'Stranger Things',
     'synopsis': 'Un grup de nens descobreixen misteris sobrenaturals a Hawkins.', 'any': 2016, 'rating': 8.7,
     'genere': 'Sci-Fi', 'director': 'Danny Boyle', 'edat': 'PG-13', 'idioma': 'English', 'pais': 'UK'},
    {'id': 's2', 'tipus': 'series', 'titol': 'Breaking Bad',
     'synopsis': 'Un professor de química es dedica a fabricar metamfetamina després d\'un diagnòstic terminal.',
     'any': 2008, 'rating': 9.5, 'genere': 'Drama', 'director': 'Danny Boyle', 'edat': 'R', 'idioma': 'English',
     'pais': 'UK'},
    {'id': 's3', 'tipus': 'series', 'titol': 'The Queen\'s Gambit',
     'synopsis': 'Una jove òrfena es converteix en un prodigi dels escacs.', 'any': 2020, 'rating': 8.6,
     'genere': 'Drama', 'director': 'Fernando Trueba', 'edat': 'PG-13', 'idioma': 'Spanish', 'pais': 'Spain'},
    {'id': 's4', 'tipus': 'series', 'titol': 'Arcane',
     'synopsis': 'Explica les històries d\'origen dels personatges de League of Legends.', 'any': 2021, 'rating': 9.1,
     'genere': 'Animation', 'director': 'Hayao Miyazaki', 'edat': 'PG', 'idioma': 'Japanese', 'pais': 'Japan'},
    {'id': 's5', 'tipus': 'series', 'titol': 'La Casa de Papel: Berlin',
     'synopsis': 'Spin-off centrat en Berlín, el cervell darrere dels atracaments.', 'any': 2023, 'rating': 7.8,
     'genere': 'Crime', 'director': 'Álex de la Iglesia', 'edat': 'R', 'idioma': 'Spanish', 'pais': 'Spain'},
    {'id': 's6', 'tipus': 'series', 'titol': 'Doctor Who',
     'synopsis': 'Un alienígena viatger del temps salva civilitzacions.', 'any': 2005, 'rating': 8.6,
     'genere': 'Sci-Fi', 'director': 'Danny Boyle', 'edat': 'PG', 'idioma': 'English', 'pais': 'UK'},
]


def catalogo(request):
    # (El teu codi de capturar filtres existents)
    query = request.GET.get('q', '')
    genere_filtre = request.GET.get('genere', 'Tots')
    edat_filtre = request.GET.get('edat', 'Tots')
    any_filtre = request.GET.get('any', 'Tots')
    ordre = request.GET.get('ordre', 'populars')
    tipus_filtre = request.GET.get('tipus', '')

    # NOU FILTRE: Idioma
    idioma_filtre = request.GET.get('idioma', 'Tots')

    resultats = DADES_CONTINGUT

    # Títol Dinàmic
    if tipus_filtre == 'series':
        resultats = [i for i in resultats if i.get('tipus') == 'series']
        titol_pagina = "Catàleg de Sèries"
    elif tipus_filtre == 'movie':
        resultats = [i for i in resultats if i.get('tipus') == 'movie']
        titol_pagina = "Catàleg de Pel·lícules"
    else:
        titol_pagina = "Catàleg de Contingut"

    if query: resultats = [i for i in resultats if query.lower() in i['titol'].lower()]
    if genere_filtre != 'Tots': resultats = [i for i in resultats if i['genere'] == genere_filtre]
    if edat_filtre != 'Tots': resultats = [i for i in resultats if i['edat'] == edat_filtre]
    if any_filtre != 'Tots': resultats = [i for i in resultats if str(i.get('any')) == any_filtre]

    # APLICAR FILTRE IDIOMA
    if idioma_filtre != 'Tots': resultats = [i for i in resultats if i.get('idioma') == idioma_filtre]

    if ordre == 'valorats':
        resultats = sorted(resultats, key=lambda x: float(x.get('rating', 0)), reverse=True)
    elif ordre == 'recents':
        resultats = sorted(resultats, key=lambda x: int(x.get('any', 0)), reverse=True)

    context = {
        'contenidos': resultats, 'query': query, 'genere_sel': genere_filtre,
        'edat_sel': edat_filtre, 'any_sel': any_filtre, 'ordre_sel': ordre,
        'idioma_sel': idioma_filtre,  # <-- Afegit per l'HTML
        'tipus_sel': tipus_filtre, 'titol_pagina': titol_pagina
    }
    return render(request, 'cataleg.html', context)


def detall_contingut(request, content_id):

    contingut = next((item for item in DADES_CONTINGUT if item['id'] == content_id), None)

    if contingut is None:
        return redirect('catalogo')

    return render(request, 'pagina_contingut.html', {'item': contingut})


# En tu archivo views.py

def sign_in2(request):
    if request.method == 'POST':
        # 1. Capturar todas las selecciones usando getlist() (porque son múltiples checkboxes)
        plataformas_seleccionadas = request.POST.getlist('plataformas')
        generos_seleccionados = request.POST.getlist('generos')
        idiomas_seleccionados = request.POST.getlist('idiomas')
        edats_seleccionadas = request.POST.getlist('edats')
        paisos_seleccionados = request.POST.getlist('paisos')

        # 2. Aquí asumo que obtienes al usuario recién creado, por ejemplo:
        # usuario = request.user  (si ya está logueado)
        # o lo creas en este mismo paso.

        # 3. Guardar las listas en el perfil del usuario
        perfil = usuario.profile  # Asegúrate de usar el nombre correcto de tu relación
        perfil.plataformes = plataformas_seleccionadas
        perfil.generes = generos_seleccionados
        perfil.idiomes = idiomas_seleccionados
        perfil.edats = edats_seleccionadas
        perfil.paisos = paisos_seleccionados

        perfil.save()  # Guardamos en la base de datos

        # 4. Redirigir a la página principal o al perfil
        return redirect('pagina_principal')

    # Si es un GET, simplemente renderizas la página con las opciones
    return render(request, 'sign_in2.html')
