from django_grainy.util import Permissions
from rest_framework import authentication, exceptions

from account.models import APIKey, OrganizationAPIKey, InternalAPIKey

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

        key_models = [APIKey, OrganizationAPIKey, InternalAPIKey]

        for model in key_models:

            try:
                if key:
                    api_key = model.objects.get(key=key)
                    request.api_key = api_key
                    if model == APIKey:
                        if not api_key.managed:
                            request.perms = Permissions(api_key)
                        return (api_key.user, None)
                    if model == OrganizationAPIKey:
                        request.perms = Permissions(api_key)
                        return (api_key, None)
                    if model == InternalAPIKey:
                        return (api_key, None)
                else:
                    return None
            except model.DoesNotExist:
                pass



        if not api_key:
            raise exceptions.AuthenticationFailed("Invalid api key")
