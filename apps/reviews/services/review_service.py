from apps.contents.models import Pelicula
from apps.reviews.models import Feedback, Ressenya


class ReviewService:
    @staticmethod
    def create_feedback(tipus, title, description, rating=None):
        return Feedback.objects.create(
            tipus=tipus,
            titol=title,
            descripcio=description,
            rating=rating if rating else None,
        )

    @staticmethod
    def get_user_review_by_id(review_id, user):
        return Ressenya.objects.get(id=review_id, usuari=user)

    @staticmethod
    def delete_review(review):
        review.delete()

    @staticmethod
    def get_movie_by_id(content_id):
        return Pelicula.objects.get(id=content_id)

    @staticmethod
    def create_or_update_review(user, movie, score, comment):
        return Ressenya.objects.update_or_create(
            usuari=user,
            pelicula=movie,
            defaults={"puntuacio": score, "comentari": comment},
        )
