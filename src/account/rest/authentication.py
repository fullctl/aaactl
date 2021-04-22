from django_grainy.util import Permissions
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions

from account.models import APIKey, OrganizationAPIKey

class APIKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        key = request.GET.get("key")

        if not key:
            auth = request.headers.get("Authorization")
            if auth:
                auth = auth.split(" ")
                if auth[0] == "Bearer":
                    key = auth[1]

        api_key = None

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
            pass


        try:
            if key:
                api_key = OrganizationAPIKey.objects.get(key=key)
                request.api_key = api_key
                request.perms = Permissions(api_key)
                User = get_user_model()
                return (api_key, None)
            else:
                return None
        except OrganizationAPIKey.DoesNotExist:
            pass




        if not api_key:
            raise exceptions.AuthenticationFailed("Invalid api key")
