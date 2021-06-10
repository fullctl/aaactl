import sys

from django.apps import AppConfig


class AccountConfig(AppConfig):
    name = "account"

    def ready(self):
        import account.signals  # noqa: F401

        self.require_internal_api_key()

    def require_internal_api_key(self):
        from account.models import InternalAPIKey

        if "migrate" not in sys.argv:
            InternalAPIKey.require()
