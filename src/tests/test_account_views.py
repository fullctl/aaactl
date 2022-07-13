from django.urls import reverse

import account.models as models


def test_login(db, client_anon):
    response = client_anon.get(reverse("account:auth-login"))
    assert response.status_code == 200


def test_logout(db, account_objects):
    response = account_objects.client.get(reverse("account:auth-logout"), follow=True)
    assert response.status_code == 200


def test_confirm_email(db, account_objects):
    email_confirmation = models.EmailConfirmation.start(account_objects.user)

    response = account_objects.client.get(
        reverse("account:auth-confirm-email", args=(email_confirmation.secret,)), follow=True
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
    assert account_objects_b.user.orguser_set.filter(org=account_objects.org).exists()


def test_index(db, account_objects, client_anon):

    response = account_objects.client.get(reverse("account:controlpanel"))
    assert response.status_code == 200

    response = client_anon.get(reverse("account:controlpanel"))
    assert response.status_code == 302
