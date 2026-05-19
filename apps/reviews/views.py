from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect

from apps.contents.models import Pelicula
from apps.reviews.models import Ressenya
from apps.reviews.services import ReviewService


# Create your views here.


def feedback_view(request):
    if request.method == "POST":
        tipus = request.POST.get("tipus")
        title = request.POST.get("titol")
        description = request.POST.get("descripcio")
        rating = request.POST.get("rating")

        ReviewService.create_feedback(tipus, title, description, rating)

        messages.success(request, "Gràcies per la teva opinió!")

        return redirect("feedback")

    return render(request, "pages/feedback.html")


@login_required
def delete_review(request, ressenya_id):
    try:
        review = ReviewService.get_user_review_by_id(review_id=ressenya_id, user=request.user)
    except Ressenya.DoesNotExist as exc:
        raise Http404 from exc
    content_id_value, content_type = review.pelicula.id, review.pelicula.tipus
    ReviewService.delete_review(review)
    return redirect('pagina_contingut', tipus=content_type, content_id=content_id_value)

@login_required
def publish_review(request, tipus, content_id):
    if request.method == "POST":
        try:
            movie_db = ReviewService.get_movie_by_id(content_id=content_id)
        except Pelicula.DoesNotExist as exc:
            raise Http404 from exc
        ReviewService.create_or_update_review(
            user=request.user,
            movie=movie_db,
            score=request.POST.get('puntuacio'),
            comment=request.POST.get('comentari'),
        )
        messages.success(request, "Ressenya publicada!")
    return redirect('pagina_contingut', tipus=tipus, content_id=content_id)
