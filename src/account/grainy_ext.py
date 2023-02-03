from django.contrib.auth import get_user_model
from django_grainy.remote import Authenticator

from account.rest.authentication import (
    APIKey,
    APIKeyAuthentication,
    InternalAPIKey,
    Permissions,
)


class APIKeyAuthenticator(Authenticator):
    def authenticate(self, request):
        permission_holder, _ = APIKeyAuthentication.authenticate(self, request)
        User = get_user_model()

        # personal api key, grab permissions for owning user

        if isinstance(permission_holder, APIKey):
            request.user = permission_holder.user

        if isinstance(permission_holder, User):
            request.user = permission_holder

        # internal api keys can be used to grab permission definitions
        # for a specific user
        #
        # user is identified via id through the `Grainy` http header

        if isinstance(permission_holder, InternalAPIKey):
            userid = request.headers.get("Grainy")
            if userid:
                user = get_user_model().objects.get(id=userid)
                request.user = user
                request.perms = Permissions(user)
            else:
                request.user = permission_holder
                request.perms = Permissions(permission_holder)
