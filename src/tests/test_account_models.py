from django.contrib.auth import authenticate, get_user_model

from account.models import EmailConfirmation, Invitation, PasswordReset


def test_personal_org(db, account_objects):
    assert account_objects.user.personal_org


def test_personal_org_user_del(db, account_objects):
    personal_org = account_objects.user.personal_org
    assert personal_org.label == "user_test (Personal)"

    account_objects.user.delete()
    personal_org.refresh_from_db()

    assert personal_org.user is None
    assert personal_org.label == "PersonalOrgtest"


def test_org_user_add(db, account_objects):
    assert account_objects.org.org_user_set.filter(user=account_objects.user).exists()


def test_api_key_autocreate(db, account_objects):
    assert account_objects.user.key_set.count() == 1
    key = account_objects.user.key_set.first()
    assert key.managed is True


def test_email_confirmation_process(db, account_objects):
    user = account_objects.user
    email_confirmation = EmailConfirmation.start(user)

    assert user.user_settings.email_confirmed is False

    email_confirmation.complete()

    user.user_settings.refresh_from_db()

    assert user.user_settings.email_confirmed


def test_password_reset_process(db, account_objects):
    user = account_objects.user

    assert authenticate(username=user.username, password="test")

    password_reset = PasswordReset.start(user)

    password_reset.complete("newpassword")

    assert authenticate(username=user.username, password="newpassword")

    assert password_reset.id is None


def test_invite_process(db, account_objects, account_objects_b):
    invite = Invitation.objects.create(
        org=account_objects.org,
        created_by=account_objects.user,
        email="test@localhost",
    )

    invite.send()

    invite.complete(account_objects_b.user)

    assert account_objects.org.org_user_set.filter(user=account_objects_b.user).exists()


def test_invite_user_del(db, account_objects, account_objects_b, capsys):
    invite = Invitation.objects.create(
        org=account_objects.org,
        created_by=account_objects.user,
        email="test@localhost",
    )

    account_objects.user.delete()
    invite.refresh_from_db()
    assert invite.created_by is None

    invite.send()

    invite.complete(account_objects_b.user)
    assert account_objects.org.org_user_set.filter(user=account_objects_b.user).exists()


def test_auto_user_to_org(db, account_objects, settings):
    settings.AUTO_USER_TO_ORG = "test"

    user = get_user_model().objects.create_user(
        username="new_user",
        password="new_user",
        email="new_user@localhost",
    )

    assert user.org_user_set.filter(org__slug="test").exists()

    settings.AUTO_USER_TO_ORG = None

    user = get_user_model().objects.create_user(
        username="new_user_2",
        password="new_user_2",
        email="new_user_2@localhost",
    )

    assert not user.org_user_set.filter(org__slug="test").exists()
