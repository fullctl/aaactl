import os
import sys  # noqa

from django.utils.translation import gettext_lazy as _  # noqa
from fullctl.django import settings

SERVICE_TAG = "aaactl"

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
# project base (/srv/service)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Intialize settings manager with global variable
settings_manager = settings.SettingsManager(globals())
settings_manager.set_release_env()

# look for mainsite/settings/${RELEASE_ENV}.py and load if it exists
env_file = os.path.join(os.path.dirname(__file__), f"{RELEASE_ENV}.py")
settings_manager.try_include(env_file)


# set version, default from /srv/service/etc/VERSION
settings_manager.set_option(
    "PACKAGE_VERSION", settings.read_file(os.path.join(BASE_DIR, "etc/VERSION")).strip()
)

settings_manager.set_default_v1()


# Keys

settings_manager.set_from_env("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY")
settings_manager.set_from_env("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET")
settings_manager.set_from_env("SOCIAL_AUTH_PEERINGDB_KEY")
settings_manager.set_from_env("SOCIAL_AUTH_PEERINGDB_SECRET")

settings_manager.set_option("RECAPTCHA_PUBLIC_KEY", "...")
settings_manager.set_option("RECAPTCHA_SECRET_KEY", "...")

settings_manager.set_from_env("STRIPE_PUBLIC_KEY")
settings_manager.set_from_env("STRIPE_SECRET_KEY")

# TODO - normalize to either use the host or not (preferably not)
LOGIN_URL = "/account/auth/login/"
LOGIN_REDIRECT_URL = "/account"

# hard overwrite MIDDLEWARE, since ordering here is important
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "oauth2_provider.middleware.OAuth2TokenMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "fullctl.django.middleware.CurrentRequestContext",
    "account.middleware.RequestAugmentation",
]

INSTALLED_APPS += (
    # base
    "django.contrib.sites",
    "django_grainy",
    "reversion",
    "captcha",
    "django_handleref",
    "rest_framework",
    # rendering
    "crispy_forms",
    # oauth
    "social_django",
    # aaactl apps
    "common",
    "account",
    "billing",
    "applications",
    "fullctl.django.apps.DjangoFullctlConfig",
)

CRISPY_TEMPLATE_PACK = "bootstrap4"

TEMPLATES[0]["OPTIONS"]["context_processors"] += [
    "account.context_processors.permissions",
    "account.context_processors.info",
]


# Billing integration

settings_manager.set_option("BILLING_ENV", "test")
settings_manager.set_option("BILLING_AGREEMENT_NAME", "aaactl")
BILLING_AGREEMENT_DESCRIPTION = BILLING_AGREEMENT_NAME
BILLING_COMPONENTS = ["fullctl.prefixctl"]
BILLING_HANDLERS = ["billing.product_handlers.fullctl.PrefixCtlPrefixes"]
BILLING_PROCESSORS = ["billing.payment_processors.stripe.Stripe"]
BILLING_DEFAULT_CURRENCY = "USD"


# Auth

AUTHENTICATION_BACKENDS = ["django_grainy.backends.GrainyBackend"]
VALIDATE_PASSWORD_LENGTH = 8

# OAUTH PROVIDER

INSTALLED_APPS += ["oauth2_provider", "corsheaders"]

# MIDDLEWARE for OAuth set above for ordering

AUTHENTICATION_BACKENDS = [
    "oauth2_provider.backends.OAuth2Backend"
] + AUTHENTICATION_BACKENDS

DEFAULT_SCOPES = ["email", "profile", "peeringdb"]

CORS_ORIGIN_ALLOW_ALL = True

OAUTH2_PROVIDER = {
    "SCOPES": {
        "profile": "user profile",
        "email": "email address",
        "api_keys": "20c api keys",
        "provider:peeringdb": "peeringdb entity associations",
    },
    "ALLOWED_REDIRECT_URI_SCHEMES": ["https"],
    "REQUEST_APPROVAL_PROMPT": "auto",
}

# SOCIAL AUTH

SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

# Supported backends

AUTHENTICATION_BACKENDS = [
    "social_core.backends.google.GoogleOAuth2",
    "account.social_backends.peeringdb.PeeringDBOAuth2",
] + AUTHENTICATION_BACKENDS


SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.social_user",
    "account.social_backends.pipelines.get_username",
    "social_core.pipeline.social_auth.associate_by_email",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "account.social_backends.pipelines.sync_peeringdb",
    "social_core.pipeline.user.user_details",
)

# We are using postgres so make use of postgres json field

SOCIAL_AUTH_POSTGRES_JSONFIELD = True

# Template Context processors

TEMPLATES[0]["OPTIONS"]["context_processors"] += [
    "social_django.context_processors.backends",
    "social_django.context_processors.login_redirect",
]

# BACKEND: PeeringDB

settings_manager.set_option("PDB_ENDPOINT", "https://peeringdb.com")
PDB_OAUTH_ACCESS_TOKEN_URL = f"{PDB_ENDPOINT}/oauth2/token/"
PDB_OAUTH_AUTHORIZE_URL = f"{PDB_ENDPOINT}/oauth2/authorize/"
PDB_OAUTH_PROFILE_URL = f"{PDB_ENDPOINT}/profile/v1"


# django rest framework

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["common.rest.JSONRenderer"],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        #        'rest_framework.authentication.BasicAuthentication',
        "account.rest.authentication.APIKeyAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    # Use hyperlinked styles by default.
    # Only used if the `serializer_class` attribute is not set on a view.
    "DEFAULT_MODEL_SERIALIZER_CLASS": "rest_framework.serializers.HyperlinkedModelSerializer",
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    # Handle rest of permissioning via django-namespace-perms
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    # FIXME: need to somehow allow different drf settings by app
    "EXCEPTION_HANDLER": "common.rest.exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "invite": "5/minute",
        "resend_email": "5/minute",
        "password_reset": "5/minute",
    },
}

settings_manager.set_default_append()

# look for mainsite/settings/${RELEASE_ENV}_append.py and load if it exists
env_file = os.path.join(os.path.dirname(__file__), f"{RELEASE_ENV}_append.py")
settings_manager.try_include(env_file)

# TODO combine to log summarry to INFO
# add BILLING_ENV
settings.print_debug(f"loaded settings for version {PACKAGE_VERSION} (DEBUG: {DEBUG})")
