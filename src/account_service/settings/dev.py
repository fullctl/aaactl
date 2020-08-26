import logging
import secrets


set_option("SERVER_EMAIL", "root@localhost")

set_from_env("SECRET_KEY", None)
if not SECRET_KEY:
    print_debug("SECRET_KEY not set, generating an ephemeral one")
    SECRET_KEY = secrets.token_urlsafe(64)

SILENCED_SYSTEM_CHECKS = ["captcha.recaptcha_test_key_error"]

# random static URL to stop caching
STATIC_URL = "/s/{}/".format(secrets.token_urlsafe(1))
