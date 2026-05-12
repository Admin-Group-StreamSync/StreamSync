from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from apps.contents.models import Pelicula
from apps.users.decorators.permissions import cap_manager_permes
from apps.users.models import LlistaPersonal, Carpeta
from apps.users.views import OPTIONS


# Create your views here.


@cap_manager_permes
def lists(request):
    return render(request, 'llistes.html', {
        'carpetes': request.user.les_meves_carpetes.all(),
        'elements_solts': LlistaPersonal.objects.filter(usuari=request.user, carpeta__isnull=True)
    })


@login_required
def folder_detail(request, carpeta_id):
    folder = get_object_or_404(Carpeta, id=carpeta_id, usuari=request.user)
    return render(request, 'detall_carpeta.html', {
        'carpeta': folder,
        'elements': LlistaPersonal.objects.filter(carpeta=folder)
    })


@login_required
def create_list(request):
    if request.method == "POST":
        Carpeta.objects.create(
            usuari=request.user, nom=request.POST.get('nom'),
            icona=request.POST.get('icona'), color=request.POST.get('color')
        )
        return redirect('llistes')
    return render(request, 'crear_llista.html', {'opcions': OPTIONS})


@login_required
def edit_list(request, carpeta_id):
    folder = get_object_or_404(Carpeta, id=carpeta_id, usuari=request.user)
    if request.method == "POST":
        folder.nom, folder.icona, folder.color = request.POST.get('nom'), request.POST.get('icona'), request.POST.get('color')
        folder.save()
        return redirect('llistes')
    return render(request, 'editar_llista.html', {'carpeta': folder, 'opcions': OPTIONS})


@login_required
def delete_folder(request, carpeta_id):
    get_object_or_404(Carpeta, id=carpeta_id, usuari=request.user).delete()
    return redirect('llistes')


@login_required
def remove_from_list(request, tipus, content_id):
    LlistaPersonal.objects.filter(usuari=request.user, pelicula_id=content_id).delete()
    messages.success(request, "Element eliminat de la llista.")
    return redirect('llistes')


@login_required
def add_to_list(request, tipus, content_id):
    movie = get_object_or_404(Pelicula, id=content_id)
    folder_id = request.POST.get('carpeta_id')
    folder = get_object_or_404(Carpeta, id=folder_id, usuari=request.user) if folder_id else None
    LlistaPersonal.objects.get_or_create(usuari=request.user, pelicula=movie, carpeta=folder)
    messages.success(request, "Afegit a la llista!")
    return redirect('pagina_contingut', tipus=tipus, content_id=content_id)