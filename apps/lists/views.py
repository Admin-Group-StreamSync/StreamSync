from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect

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
    folder_id = request.POST.get('carpeta_id') or None
    try:
        ListService.add_content_to_user_list(
            user=request.user,
            content_id=content_id,
            folder_id=folder_id,
        )
    except (Pelicula.DoesNotExist, Carpeta.DoesNotExist) as exc:
        raise Http404 from exc
    messages.success(request, "Afegit a la llista!")
    return redirect('pagina_contingut', tipus=tipus, content_id=content_id)

@login_required
@cap_manager_permes
def lists(request):
    return render(request, 'llistes.html', ListService.get_lists_context(request.user))

@login_required
def folder_detail(request, carpeta_id):
    try:
        context = ListService.get_folder_detail_context(request.user, carpeta_id)
    except Carpeta.DoesNotExist as exc:
        raise Http404 from exc
    return render(request, 'detall_carpeta.html', context)

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
    try:
        folder = ListService.get_user_folder_for_edit(request.user, carpeta_id)
    except Carpeta.DoesNotExist as exc:
        raise Http404 from exc
    if request.method == "POST":
        ListService.update_user_folder(
            user=request.user,
            folder_id=carpeta_id,
            name=request.POST.get('nom'),
            icon=request.POST.get('icona'),
            color=request.POST.get('color'),
        )
        return redirect('llistes')
    return render(request, 'editar_llista.html', {'carpeta': folder, 'opcions': OPTIONS})

@login_required
def delete_folder(request, carpeta_id):
    try:
        ListService.delete_user_folder(request.user, carpeta_id)
    except Carpeta.DoesNotExist as exc:
        raise Http404 from exc
    return redirect('llistes')

@login_required
def remove_from_list(request, tipus, content_id):
    ListService.remove_movie_from_user_list(request.user, content_id)
    messages.success(request, "Element eliminat de la llista.")
    return redirect('llistes')
