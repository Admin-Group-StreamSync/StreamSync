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
    def add_content_to_user_list(user, content_id, folder_id=None):
        movie = ListService.get_movie_by_id(content_id)
        folder = None
        if folder_id:
            folder = ListService.get_user_folder(folder_id=folder_id, user=user)
        return ListService.add_to_personal_list(user=user, movie=movie, folder=folder)

    @staticmethod
    def get_user_unfoldered_items(user):
        return LlistaPersonal.objects.filter(usuari=user, carpeta__isnull=True)

    @staticmethod
    def get_folder_items(folder):
        return LlistaPersonal.objects.filter(carpeta=folder)

    @staticmethod
    def get_lists_context(user):
        return {
            "carpetes": user.les_meves_carpetes.all(),
            "elements_solts": ListService.get_user_unfoldered_items(user),
        }

    @staticmethod
    def get_folder_detail_context(user, folder_id):
        folder = ListService.get_user_folder(folder_id=folder_id, user=user)
        return {
            "carpeta": folder,
            "elements": ListService.get_folder_items(folder),
        }

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
    def delete_user_folder(user, folder_id):
        folder = ListService.get_user_folder(folder_id=folder_id, user=user)
        ListService.delete_folder(folder)
        return folder

    @staticmethod
    def remove_movie_from_user_list(user, content_id):
        return LlistaPersonal.objects.filter(usuari=user, pelicula_id=content_id).delete()

    @staticmethod
    def get_user_folder_for_edit(user, folder_id):
        return ListService.get_user_folder(folder_id=folder_id, user=user)

    @staticmethod
    def update_user_folder(user, folder_id, name, icon, color):
        folder = ListService.get_user_folder(folder_id=folder_id, user=user)
        return ListService.update_folder(folder=folder, name=name, icon=icon, color=color)
