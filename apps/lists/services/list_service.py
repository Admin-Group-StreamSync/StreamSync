from apps.contents.models import Pelicula
from apps.lists.models import Carpeta, LlistaPersonal


class ListService:
    @staticmethod
    def get_movie_by_id(content_id):
        return Pelicula.objects.get(id=content_id)

    @staticmethod
    def get_user_folder(folder_id, user):
        return Carpeta.objects.get(id=folder_id, usuari=user)

    @staticmethod
    def add_to_personal_list(user, movie, folder=None):
        return LlistaPersonal.objects.get_or_create(
            usuari=user,
            pelicula=movie,
            carpeta=folder,
        )

    @staticmethod
    def get_user_unfoldered_items(user):
        return LlistaPersonal.objects.filter(usuari=user, carpeta__isnull=True)

    @staticmethod
    def get_folder_items(folder):
        return LlistaPersonal.objects.filter(carpeta=folder)

    @staticmethod
    def create_folder(user, name, icon, color):
        return Carpeta.objects.create(
            usuari=user,
            nom=name,
            icona=icon,
            color=color,
        )

    @staticmethod
    def update_folder(folder, name, icon, color):
        folder.nom = name
        folder.icona = icon
        folder.color = color
        folder.save()
        return folder

    @staticmethod
    def delete_folder(folder):
        folder.delete()

    @staticmethod
    def remove_movie_from_user_list(user, content_id):
        return LlistaPersonal.objects.filter(usuari=user, pelicula_id=content_id).delete()
