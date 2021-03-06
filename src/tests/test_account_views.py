from django.urls import reverse

import account.models as models


def test_login(db, client_anon):
    response = client_anon.get(reverse("account:auth-login"))
    assert response.status_code == 200


def test_logout(db, account_objects):
    response = account_objects.client.get(reverse("account:auth-logout"), follow=True)
    assert response.status_code == 200


def test_confirm_email(db, account_objects):
    emconf = models.EmailConfirmation.start(account_objects.user)

    response = account_objects.client.get(
        reverse("account:auth-confirm-email", args=(emconf.secret,)), follow=True
    )

    assert response.status_code == 200

    assert (
        models.EmailConfirmation.objects.filter(user=account_objects.user).exists()
        is False
    )

    account_objects.user.usercfg.refresh_from_db()

    assert account_objects.user.usercfg.email_confirmed


def test_reset_password(db, account_objects, client_anon):

    response = client_anon.get(reverse("account:auth-reset-password-start"))

    assert response.status_code == 200

    pwdrst = models.PasswordReset.start(account_objects.user)

    response = client_anon.get(
        reverse("account:auth-reset-password", args=(pwdrst.secret,))
    )

    assert response.status_code == 200


def test_accept_invite(db, account_objects, account_objects_b):

    inv = models.Invitation.objects.create(
        org=account_objects.org, created_by=account_objects.user, email="test@localhost"
    )

    response = account_objects_b.client.get(
        reverse("account:accept-invite", args=(inv.secret,)), follow=True
    )

    assert response.status_code == 200

    account_objects_b.user.refresh_from_db()
    assert account_objects_b.user.org_set.filter(org=account_objects.org).exists()


def test_change_password(db, account_objects, client_anon):

    response = account_objects.client.get(reverse("account:change-password"))
    assert response.status_code == 200

    response = client_anon.get(reverse("account:change-password"))
    assert response.status_code == 302


def test_change_information(db, account_objects, client_anon):

    response = account_objects.client.get(reverse("account:change-information"))
    assert response.status_code == 200

    response = client_anon.get(reverse("account:change-information"))
    assert response.status_code == 302


def test_org_create(db, account_objects, client_anon):

    response = account_objects.client.get(reverse("account:create-organization"))
    assert response.status_code == 200

    response = client_anon.get(reverse("account:create-organization"))
    assert response.status_code == 302


def test_org_edit(db, account_objects, client_anon):

    response = account_objects.client.get(reverse("account:edit-organization"))
    assert response.status_code == 200

    response = client_anon.get(reverse("account:edit-organization"))
    assert response.status_code == 302


def test_org_invite(db, account_objects, client_anon):

    response = account_objects.client.get(reverse("account:invite"))
    assert response.status_code == 200

    response = client_anon.get(reverse("account:invite"))
    assert response.status_code == 302


def test_org_users(db, account_objects, client_anon):

    response = account_objects.client.get(reverse("account:users"))
    assert response.status_code == 200

    response = client_anon.get(reverse("account:users"))
    assert response.status_code == 302


def test_social(db, account_objects, client_anon):

    response = account_objects.client.get(reverse("account:social"))
    assert response.status_code == 200

    response = client_anon.get(reverse("account:social"))
    assert response.status_code == 302


def test_api_keys(db, account_objects, client_anon):

    response = account_objects.client.get(reverse("account:api-keys"))
    assert response.status_code == 200

    response = client_anon.get(reverse("account:api-keys"))
    assert response.status_code == 302


def test_index(db, account_objects, client_anon):

    response = account_objects.client.get(reverse("account:controlpanel"))
    assert response.status_code == 200

    response = client_anon.get(reverse("account:controlpanel"))
    assert response.status_code == 302
