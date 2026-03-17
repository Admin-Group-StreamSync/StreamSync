from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from .forms import RegistroUsuarioForm, UserUpdateForm
from .models import Profile



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
        datos_paso1 = request.session['datos_registro_paso1']
        form = RegistroUsuarioForm(datos_paso1)

        if form.is_valid():
            user = form.save()
            plats = request.POST.getlist('plataformas')
            gens = request.POST.getlist('generos')
            Profile.objects.create(user=user, plataformes=plats, generes=gens)

            del request.session['datos_registro_paso1']
            login(request, user)
            return redirect('pagina_principal')

    return render(request, 'registration/sign_in2.html')

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
        perfil.plataformes = request.POST.getlist('plataformas')
        perfil.generes = request.POST.getlist('generos')
        perfil.save()
        messages.success(request, "Preferències guardades!")
        return redirect('profile2')

    return render(request, 'profile2.html')


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



DADES_CONTINGUT = [
    {'id': 1, 'titol': 'Inception', 'genere': 'Ciència Ficció', 'rating': '4.8', 'director': 'Christopher Nolan',
     'edat': '+13',
     'sinopsi': 'Un lladre que roba secrets corporatius a través de l\'ús de la tecnologia de compartició de somnis.'},
    {'id': 2, 'titol': 'The Dark Knight', 'genere': 'Acció', 'rating': '4.9', 'director': 'Christopher Nolan',
     'edat': '+13',
     'sinopsi': 'Quan l\'amenaça coneguda com el Joker emergeix del seu passat, causa el caos a la gent de Gotham.'},
    {'id': 3, 'titol': 'Interstellar', 'genere': 'Aventura', 'rating': '4.7', 'director': 'Christopher Nolan',
     'edat': '+7',
     'sinopsi': 'Un equip d\'exploradors viatja a través d\'un forat de cuc a l\'espai en un intent de garantir la supervivència de la humanitat.'},{
        'id': 4,
        'titol': 'Breaking Bad',
        'genere': 'Drama',
        'rating': '5.0',
        'director': 'Vince Gilligan',
        'edat': '+18',
        'sinopsi': 'Un professor de química de l\'institut amb un càncer de pulmó inoperable es dedica a fabricar i vendre metamfetamina per assegurar el futur financer de la seva família.'
    },
    {
        'id': 5,
        'titol': 'Toy Story',
        'genere': 'Animació',
        'rating': '4.5',
        'director': 'John Lasseter',
        'edat': 'Tots els públics',
        'sinopsi': 'Un ninot de vaquer se sent amenaçat i gelós quan una nova figura d\'acció d\'un astronauta el substitueix com el joguet preferit a l\'habitació d\'un nen.'
    },
    {
        'id': 6,
        'titol': 'The Shining',
        'genere': 'Terror',
        'rating': '4.4',
        'director': 'Stanley Kubrick',
        'edat': '+18',
        'sinopsi': 'Una família es queda a passar l\'hivern en un hotel aïllat on una presència espiritual influeix en el pare cap a la violència, mentre que el seu fill té visions horroroses.'
    },
    {
        'id': 7,
        'titol': 'Parasite',
        'genere': 'Drama',
        'rating': '4.6',
        'director': 'Bong Joon-ho',
        'edat': '+16',
        'sinopsi': 'La cobdícia i la discriminació de classe amenacen la nova relació formada entre la riquesa de la família Park i la pobresa del clan Kim.'
    },
    {
        'id': 8,
        'titol': 'Stranger Things',
        'genere': 'Ciència Ficció',
        'rating': '4.7',
        'director': 'The Duffer Brothers',
        'edat': '+13',
        'sinopsi': 'Quan un nen desapareix, la seva mare, un cap de policia i els seus amics han d\'enfrontar-se a forces aterridores per tal de recuperar-lo.'
    },
    {
        'id': 9,
        'titol': 'The Office',
        'genere': 'Comèdia',
        'rating': '4.9',
        'director': 'Greg Daniels',
        'edat': '+13',
        'sinopsi': 'Un fals documental sobre la vida quotidiana dels empleats d\'una oficina en una empresa paperera a Scranton, Pennsilvània.'
    },
    {
        'id': 10,
        'titol': 'Dune',
        'genere': 'Ciència Ficció',
        'rating': '4.3',
        'director': 'Denis Villeneuve',
        'edat': '+13',
        'sinopsi': 'Adaptació cinematogràfica de la novel·la de ciència-ficció de Frank Herbert sobre el fill d\'una família noble que tracta de protegir l\'actiu més valuós de la galàxia.'
    },
    {
        'id': 11,
        'titol': 'Spirited Away',
        'genere': 'Animació',
        'rating': '4.8',
        'director': 'Hayao Miyazaki',
        'edat': 'Tots els públics',
        'sinopsi': 'Durant el trasllat de la seva família al camp, una nena de 10 anys entra en un món governat per déus, bruixes i esperits, on els humans es transformen en bèsties.'
    },
    {
        'id': 12,
        'titol': 'Gladiator',
        'genere': 'Acció',
        'rating': '4.7',
        'director': 'Ridley Scott',
        'edat': '+16',
        'sinopsi': 'Un general romà és traït i la seva família assassinada pel fill corrupte d\'un emperador. Torna a Roma com a gladiador per buscar venjança.'
    },
]


def catalogo(request):
    return render(request, 'cataleg.html', {'contenidos': DADES_CONTINGUT})


def detall_contingut(request, content_id):

    contingut = next((item for item in DADES_CONTINGUT if item['id'] == content_id), None)

    if contingut is None:
        return redirect('catalogo')

    return render(request, 'pagina_contingut.html', {'item': contingut})
