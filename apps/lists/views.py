from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect

from apps.contents.models import Pelicula
from apps.lists.models import Carpeta
from apps.lists.services import ListService
from apps.users.decorators.permissions import cap_manager_permes

# Create your views here.

OPTIONS = {
    'plataformas': ['CinePlus', 'StreamHub', 'PlayMax'],
    'idiomas': ['Català', 'Castellano', 'English', 'Français']
}

@login_required
def add_to_list(request, tipus, content_id):
    try:
        movie = ListService.get_movie_by_id(content_id)
    except Pelicula.DoesNotExist as exc:
        raise Http404 from exc
    folder_id = request.POST.get('carpeta_id')
    if folder_id:
        try:
            folder = ListService.get_user_folder(folder_id=folder_id, user=request.user)
        except Carpeta.DoesNotExist as exc:
            raise Http404 from exc
    else:
        folder = None
    ListService.add_to_personal_list(user=request.user, movie=movie, folder=folder)
    messages.success(request, "Afegit a la llista!")
    return redirect('pagina_contingut', tipus=tipus, content_id=content_id)

@login_required
@cap_manager_permes
def lists(request):
    return render(request, 'llistes.html', {
        'carpetes': request.user.les_meves_carpetes.all(),
        'elements_solts': ListService.get_user_unfoldered_items(request.user)
    })

@login_required
def folder_detail(request, carpeta_id):
    folder = get_object_or_404(Carpeta, id=carpeta_id, usuari=request.user)
    return render(request, 'detall_carpeta.html', {
        'carpeta': folder,
        'elements': ListService.get_folder_items(folder)
    })

@login_required
def create_list(request):
    if request.method == "POST":
        ListService.create_folder(
            user=request.user,
            name=request.POST.get('nom'),
            icon=request.POST.get('icona'),
            color=request.POST.get('color'),
        )
        return redirect('llistes')
    return render(request, 'crear_llista.html', {'opcions': OPTIONS})

@login_required
def edit_list(request, carpeta_id):
    folder = get_object_or_404(Carpeta, id=carpeta_id, usuari=request.user)
    if request.method == "POST":
        ListService.update_folder(
            folder=folder,
            name=request.POST.get('nom'),
            icon=request.POST.get('icona'),
            color=request.POST.get('color'),
        )
        return redirect('llistes')
    return render(request, 'editar_llista.html', {'carpeta': folder, 'opcions': OPTIONS})

@login_required
def delete_folder(request, carpeta_id):
    folder = get_object_or_404(Carpeta, id=carpeta_id, usuari=request.user)
    ListService.delete_folder(folder)
    return redirect('llistes')

@login_required
def remove_from_list(request, tipus, content_id):
    ListService.remove_movie_from_user_list(request.user, content_id)
    messages.success(request, "Element eliminat de la llista.")
    return redirect('llistes')
