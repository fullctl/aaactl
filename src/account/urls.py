from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

import account.views.auth
import account.views.controlpanel

urlpatterns = [
    path("auth/o/profile/", account.views.auth.oauth_profile, name="oauth-profile"),
    path("auth/login/", account.views.auth.login, name="auth-login"),
    path("auth/logout/", account.views.auth.logout, name="auth-logout"),
    path("auth/register/", account.views.auth.register, name="auth-register"),
    path(
        "auth/confirm-email/<secret>/",
        account.views.auth.confirm_email,
        name="auth-confirm-email",
    ),
    path(
        "auth/reset-password/start/",
        account.views.auth.start_reset_password,
        name="auth-reset-password-start",
    ),
    path(
        "auth/reset-password/<secret>/",
        account.views.auth.reset_password,
        name="auth-reset-password",
    ),
    path(
        "auth/accept-invite/<secret>/",
        account.views.auth.accept_invite,
        name="accept-invite",
    ),
    # TODO: set as cookie instead to help security
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path(
        "token/cookie/",
        account.views.auth.JWTCookieLoginView.as_view(),
        name="token_cookie_login",
    ),
    path(
        "token/refreshcookie/",
        account.views.auth.JWTCookieRefreshView.as_view(),
        name="token_cookie_refresh",
    ),
    path("", account.views.controlpanel.index, name="controlpanel"),
]
