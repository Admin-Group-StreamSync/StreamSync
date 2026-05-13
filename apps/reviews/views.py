from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from apps.contents.models import Pelicula
from apps.reviews.models import Feedback, Ressenya


# Create your views here.


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


@login_required
def delete_review(request, ressenya_id):
    review = get_object_or_404(Ressenya, id=ressenya_id, usuari=request.user)
    content_id_value, content_type = review.pelicula.id, review.pelicula.tipus
    review.delete()
    return redirect('pagina_contingut', tipus=content_type, content_id=content_id_value)

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