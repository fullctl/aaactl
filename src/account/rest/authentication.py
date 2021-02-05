from django_grainy.util import Permissions
from rest_framework import authentication, exceptions

from account.models import APIKey


class APIKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        key = request.GET.get("key")

        if not key:
            auth = request.headers.get("Authorization")
            if auth:
                auth = auth.split(" ")
                if auth[0] == "Bearer":
                    key = auth[1]

        try:
            if key:
                api_key = APIKey.objects.get(key=key)
                request.api_key = api_key
                if not api_key.managed:
                    request.perms = Permissions(api_key)
                return (api_key.user, None)
            else:
                return None
        except APIKey.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid api key")
