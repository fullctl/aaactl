from django.urls import reverse

import account.models as models
from account.views.auth import valid_frontend_redirect


def test_login(db, client_anon):
    response = client_anon.get(reverse("account:auth-login"))
    assert response.status_code == 200


def test_valid_frontend_redirect(db, settings, account_objects):
    settings.FRONTEND_ORIGINS = ["http://localhost:8080"]
    url = valid_frontend_redirect(
        "http://localhost:8080", reverse("account:controlpanel"), account_objects.user
    )
    assert url[:28] == "http://localhost:8080/login/"

    url = valid_frontend_redirect(
        "http://localhost:8081", reverse("account:controlpanel"), account_objects.user
    )
    assert url == reverse("account:controlpanel")


def test_login_frontend(db, account_objects, client_anon, settings):
    response = client_anon.get(reverse("account:auth-login-frontend"))
    assert response.status_code == 200

    settings.FRONTEND_ORIGINS = ["http://localhost:8080"]
    payload = {
        "username_or_email": account_objects.user.username,
        "password": "test",
        "next": "http://localhost:8080",
    }
    response = client_anon.post(
        reverse("account:auth-login-frontend"),
        data=payload,
    )
    assert response.status_code == 302
    assert response.url[:28] == "http://localhost:8080/login/"

    payload = {"next": "http://localhost:8080"}
    response = account_objects.client.get(
        reverse("account:auth-login-frontend"), payload
    )
    assert response.status_code == 302
    assert response.url[:28] == "http://localhost:8080/login/"


def test_logout(db, account_objects):
    response = account_objects.client.get(reverse("account:auth-logout"), follow=True)
    assert response.status_code == 200


def test_confirm_email(db, account_objects):
    email_confirmation = models.EmailConfirmation.start(account_objects.user)

    response = account_objects.client.get(
        reverse("account:auth-confirm-email", args=(email_confirmation.secret,)),
        follow=True,
    )

    assert response.status_code == 200

    assert (
        models.EmailConfirmation.objects.filter(user=account_objects.user).exists()
        is False
    )

    account_objects.user.user_settings.refresh_from_db()

    assert account_objects.user.user_settings.email_confirmed


def test_reset_password(db, account_objects, client_anon):
    response = client_anon.get(reverse("account:auth-reset-password-start"))

    assert response.status_code == 200

    password_reset = models.PasswordReset.start(account_objects.user)

    response = client_anon.get(
        reverse("account:auth-reset-password", args=(password_reset.secret,))
    )

    assert response.status_code == 200


def test_accept_invite(db, account_objects, account_objects_b):
    invite = models.Invitation.objects.create(
        org=account_objects.org, created_by=account_objects.user, email="test@localhost"
    )

    response = account_objects_b.client.get(
        reverse("account:accept-invite", args=(invite.secret,)), follow=True
    )

    assert response.status_code == 200

    account_objects_b.user.refresh_from_db()
    assert account_objects_b.user.org_user_set.filter(org=account_objects.org).exists()


def test_index(db, account_objects, client_anon):
    response = account_objects.client.get(reverse("account:controlpanel"))
    assert response.status_code == 200

    response = client_anon.get(reverse("account:controlpanel"))
    assert response.status_code == 302
