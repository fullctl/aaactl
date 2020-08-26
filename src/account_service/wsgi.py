"""
WSGI config for account_service project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# XXX use/test __name__
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "account_service.settings")

application = get_wsgi_application()
