from django_grainy.remote import Authenticator

from account.rest.authentication import APIKeyAuthentication

class APIKeyAuthenticator(Authenticator):
    def authenticate(self, request):
        APIKeyAuthentication.authenticate(self, request)
        if getattr(request, "api_key", None):
            request.user = request.api_key.user

