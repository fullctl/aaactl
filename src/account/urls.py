from django.urls import path

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
    path("", account.views.controlpanel.index, name="controlpanel"),
]
