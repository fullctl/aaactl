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

                    # a matching key was found

                    api_key = model.objects.get(key=key)
                    request.api_key = api_key

                    if model == APIKey:

                        # personal api key

                        if not api_key.managed:

                            # unmanaged personal keys have their own set of permissions

                            request.perms = Permissions(api_key)

                        else:

                            # managed personal keys inherit the users permissions

                            request.perms = Permissions(api_key.user)

                        return (api_key.user, None)
                    if model == OrganizationAPIKey:

                        # Organization API Key

                        request.perms = Permissions(api_key)
                        return (api_key, None)
                    if model == InternalAPIKey:

                        # Inernal API Key

                        return (api_key, None)
                else:
                    return None
            except model.DoesNotExist:
                pass



        if not api_key:
            raise exceptions.AuthenticationFailed("Invalid api key")
