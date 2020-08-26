from django_grainy.util import Permissions

from django.contrib.auth import authenticate

from account.models import EmailConfirmation, UserSettings, PasswordReset, Invitation


def test_personal_org(db, account_objects):
    assert account_objects.user.personal_org

def test_personal_org_user_del(db, account_objects):
    personal_org = account_objects.user.personal_org
    assert personal_org.label == "Personal"

    account_objects.user.delete()
    personal_org.refresh_from_db()

    assert personal_org.user == None
    assert personal_org.label == "PersonalOrgtest"


def test_org_user_add(db, account_objects):
    assert account_objects.org.user_set.filter(user=account_objects.user).exists()


def test_api_key_autocreate(db, account_objects):
    assert account_objects.user.key_set.count() == 1
    key = account_objects.user.key_set.first()
    assert key.managed == False

    perms = Permissions(key)
    assert perms.check("user.{user.id}".format(user=account_objects.user), "crud")


def test_emconf_process(db, account_objects):

    user = account_objects.user
    emconf = EmailConfirmation.start(user)

    assert user.usercfg.email_confirmed == False

    emconf.complete()

    user.usercfg.refresh_from_db()

    assert user.usercfg.email_confirmed


def test_pwdrst_process(db, account_objects):

    user = account_objects.user

    assert authenticate(username=user.username, password="test")

    pwdrst = PasswordReset.start(user)

    pwdrst.complete("newpassword")

    assert authenticate(username=user.username, password="newpassword")

    assert pwdrst.id is None


def test_inv_process(db, account_objects, account_objects_b):
    inv = Invitation.objects.create(
        org=account_objects.org,
        created_by=account_objects.user,
        email="test@localhost",
    )

    inv.send()

    inv.complete(account_objects_b.user)

    assert account_objects.org.user_set.filter(user=account_objects_b.user).exists()


def test_inv_user_del(db, account_objects, account_objects_b, capsys):
    inv = Invitation.objects.create(
        org=account_objects.org,
        created_by=account_objects.user,
        email="test@localhost",
    )

    account_objects.user.delete()
    inv.refresh_from_db()
    assert inv.created_by == None

    inv.send()

    stdout = capsys.readouterr().out
    assert "[Deleted user]" in stdout

    inv.complete(account_objects_b.user)
    assert account_objects.org.user_set.filter(user=account_objects_b.user).exists()

