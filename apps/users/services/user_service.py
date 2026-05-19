from django.contrib.auth import get_user_model


User = get_user_model()


class UserService:
    @staticmethod
    def get_user_by_id(user_id):
        return User.objects.get(id=user_id)
