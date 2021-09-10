import os

from confu.util import SettingsManager
from django.utils.translation import gettext_lazy as _

cfg = SettingsManager(globals())
_DEFAULT_ARG = object()


def print_debug(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


def get_locale_name(code):
    """Gets the readble name for a locale code."""
    language_map = dict(django.conf.global_settings.LANGUAGES)

    # check for exact match
    if code in language_map:
        return language_map[code]

    # try for the language, fall back to just using the code
    language = code.split("-")[0]
    return language_map.get(language, code)


def try_include(filename):
    """Tries to include another file from the settings directory."""
    print_debug(f"including {filename} {RELEASE_ENV}")
    try:
        with open(filename) as f:
            exec(compile(f.read(), filename, "exec"), globals())

        print_debug(f"loaded additional settings file '{filename}'")

    except FileNotFoundError:
        print_debug(f"additional settings file '{filename}' was not found, skipping")


def read_file(name):
    with open(name) as fh:
        return fh.read()


# Intialize settings manager with global variable

settings_manager = SettingsManager(globals())


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# set RELEASE_ENV, usually one of dev, beta, tutor, prod
settings_manager.set_option("RELEASE_ENV", "dev")

# set DEBUG first, print_debug() depends on it
if RELEASE_ENV == "dev":
    settings_manager.set_bool("DEBUG", True)
else:
    settings_manager.set_bool("DEBUG", False)

# look for mainsite/settings/${RELEASE_ENV}.py and load if it exists
env_file = os.path.join(os.path.dirname(__file__), f"{RELEASE_ENV}.py")
try_include(env_file)

print_debug(f"Release env is '{RELEASE_ENV}'")

if RELEASE_ENV == "prod":
    # we only expose admin on non-production environments
    settings_manager.set_bool("EXPOSE_ADMIN", False)
else:
    settings_manager.set_bool("EXPOSE_ADMIN", True)

# set version, default from /srv/service/etc/VERSION
settings_manager.set_option(
    "PACKAGE_VERSION", read_file(os.path.join(BASE_DIR, "etc/VERSION")).strip()
)

# Contact email, from address, support email
settings_manager.set_from_env("SERVER_EMAIL")

# django secret key
settings_manager.set_from_env("SECRET_KEY")


# database

settings_manager.set_option("DATABASE_ENGINE", "postgresql_psycopg2")
settings_manager.set_option("DATABASE_HOST", "127.0.0.1")
settings_manager.set_option("DATABASE_PORT", "")
settings_manager.set_option("DATABASE_NAME", "account_service")
settings_manager.set_option("DATABASE_USER", "account_service")
settings_manager.set_option("DATABASE_PASSWORD", "")


# Keys

settings_manager.set_from_env("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY")
settings_manager.set_from_env("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET")
settings_manager.set_from_env("SOCIAL_AUTH_PEERINGDB_KEY")
settings_manager.set_from_env("SOCIAL_AUTH_PEERINGDB_SECRET")

settings_manager.set_option("RECAPTCHA_PUBLIC_KEY", "...")
settings_manager.set_option("RECAPTCHA_SECRET_KEY", "...")

settings_manager.set_from_env("STRIPE_PUBLIC_KEY")
settings_manager.set_from_env("STRIPE_SECRET_KEY")


# Django config

ALLOWED_HOSTS = ["*"]
SITE_ID = 1

TIME_ZONE = "UTC"
USE_TZ = True

LANGUAGE_CODE = "en-us"
USE_I18N = True
USE_L10N = True

ADMINS = ("Support", SERVER_EMAIL)
MANAGERS = ADMINS

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

settings_manager.set_option("HOST_URL", "https://localhost:8000")

settings_manager.set_option(
    "MEDIA_ROOT", os.path.abspath(os.path.join(BASE_DIR, "media"))
)
settings_manager.set_option("MEDIA_URL", f"/m/{PACKAGE_VERSION}/")

settings_manager.set_option(
    "STATIC_ROOT", os.path.abspath(os.path.join(BASE_DIR, "static"))
)
settings_manager.set_option("STATIC_URL", f"/s/{PACKAGE_VERSION}/")

settings_manager.set_option("SESSION_COOKIE_NAME", "tcacctsid")
# settings_manager.set_from_env("SESSION_COOKIE_DOMAIN")
# settings_manager.set_from_env("SESSION_COOKIE_SECURE")

settings_manager.set_option("DEFAULT_FROM_EMAIL", SERVER_EMAIL)

# TODO - normalize to either use the host or not (preferably not)
LOGIN_URL = "/account/auth/login/"
LOGIN_REDIRECT_URL = "/account"

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

settings_manager.set_default("MIDDLEWARE", [])
MIDDLEWARE += [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "fullctl.django.middleware.CurrentRequestContext",
]

ROOT_URLCONF = "account_service.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "account_service.wsgi.application"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
        "OPTIONS": {
            # maximum number of entries in the cache
            "MAX_ENTRIES": 5000,
            # once max entries are reach delete 500 of the oldest entries
            "CULL_FREQUENCY": 10,
        },
    }
}

DATABASES = {
    "default": {
        "ENGINE": f"django.db.backends.{DATABASE_ENGINE}",
        "HOST": DATABASE_HOST,
        "PORT": DATABASE_PORT,
        "NAME": DATABASE_NAME,
        "USER": DATABASE_USER,
        "PASSWORD": DATABASE_PASSWORD,
    }
}

# START CONCAT CONFIG
# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


MIDDLEWARE += ["account.middleware.RequestAugmentation"]

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
    # account_service apps
    "common",
    "account",
    "billing",
    "applications",
)

CRISPY_TEMPLATE_PACK = "bootstrap4"


AUTHENTICATION_BACKENDS = ["django_grainy.backends.GrainyBackend"]

VALIDATE_PASSWORD_LENGTH = 8


TEMPLATES[0]["OPTIONS"]["context_processors"] += [
    "account.context_processors.permissions",
    "account.context_processors.info",
]


INSTALLED_APPS += ("fullctl.django.apps.DjangoFullctlConfig",)


BILLING_COMPONENTS = ["fullctl.prefixctl"]

BILLING_HANDLERS = ["billing.product_handlers.fullctl.PrefixCtlPrefixes"]

BILLING_PROCESSORS = ["billing.payment_processors.stripe.Stripe"]


BILLING_AGREEMENT_NAME = "20C Recurring Services"
BILLING_AGREEMENT_DESCRIPTION = BILLING_AGREEMENT_NAME

BILLING_DEFAULT_CURRENCY = "USD"

settings_manager.set_option("BILLING_ENV", "test")
print_debug(f"Billing env is '{BILLING_ENV}'")

# OAUTH PROVIDER

INSTALLED_APPS += ["oauth2_provider", "corsheaders"]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "oauth2_provider.middleware.OAuth2TokenMiddleware",
] + MIDDLEWARE

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

# END CONCAT CONFIG

# dynamic config starts here

# enable all languages available in the locale directory
settings_manager.set_option("ENABLE_ALL_LANGUAGES", False)

if ENABLE_ALL_LANGUAGES:
    language_dict = dict(LANGUAGES)
    for locale_path in LOCALE_PATHS:
        for name in os.listdir(locale_path):
            path = os.path.join(locale_path, name)
            if not os.path.isdir(os.path.join(path, "LC_MESSAGES")):
                continue
            code = name.replace("_", "-").lower()
            if code not in language_dict:
                name = _(get_locale_name(code))
                language_dict[code] = name

    LANGUAGES = sorted(language_dict.items())


API_DOC_INCLUDES = {}
API_DOC_PATH = os.path.join(BASE_DIR, "docs", "api")
for i, j, files in os.walk(API_DOC_PATH):
    for file in files:
        base, ext = os.path.splitext(file)
        if ext == ".md":
            API_DOC_INCLUDES[base] = os.path.join(API_DOC_PATH, file)


DEBUG_EMAIL = DEBUG

TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG

# TODO need to figure out logging
# if DEBUG:
#    # make all loggers use the console.
#    for logger in LOGGING["loggers"]:
#        LOGGING["loggers"][logger]["handlers"] = ["console"]
#

# TODO EMAIL_SUBJECT_PREFIX = "[{}] ".format(RELEASE_ENV)

print_debug(f"loaded settings for version {PACKAGE_VERSION} (DEBUG: {DEBUG})")
