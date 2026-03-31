from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone
from .models import ApiKey


class ApiKeyAuthentication(BaseAuthentication):
    """
    Autenticació mitjançant header X-API-KEY.
    Comproba que la key existeix, esta activa i no ha expirat.
    """

    def authenticate(self, request):
        api_key = request.headers.get('X-API-KEY')

        if not api_key:
            raise AuthenticationFailed('X-API-KEY header requerido.')

        try:
            key = ApiKey.objects.get(api_key=api_key, active=True)
        except ApiKey.DoesNotExist:
            raise AuthenticationFailed('API key inválida o inactiva.')

        if key.is_expired():
            raise AuthenticationFailed('API key expirada.')

        # DRF espera (user, auth). Tornem None com user (API publica).
        return (None, key)