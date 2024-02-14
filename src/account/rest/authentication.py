from django_grainy.util import Permissions
from fullctl.django.rest.authentication import key_from_request
from rest_framework import authentication, exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication

from account.models import APIKey, InternalAPIKey, OrganizationAPIKey


class TokenAuthentication(authentication.BaseAuthentication):
    """
    Both JWT and API Keys are passed in the Authorization header therefore we
    need to check both and return the one that is valid.
    """

    def authenticate(self, request):
        try:
            auth = self.authenticate_api_keys(request)
        except exceptions.AuthenticationFailed:
            auth = self.authenticate_jwt(request)

        if auth:
            return (auth[0], None)

    def authenticate_jwt(self, request):
        JWT_authenticator = JWTAuthentication()
        auth = JWT_authenticator.authenticate(request)
        if auth:
            request.perms = Permissions(auth[0])
            return auth

    def authenticate_api_keys(self, request):
        key = key_from_request(request)

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


class CustomJWTAuthentication(JWTAuthentication):
    '''
    Authenticate user with JWT access token set in cookies.
    '''

    def authenticate(self, request):

        raw_token = request.COOKIES.get("jwt_access_token", None)
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
        except exceptions.AuthenticationFailed:
            return None

        request.perms = Permissions(self.get_user(validated_token))
        return self.get_user(validated_token), validated_token
