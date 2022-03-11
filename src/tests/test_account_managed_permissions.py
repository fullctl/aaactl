import pytest
from django_grainy.util import Permissions
from django.contrib.auth import get_user_model

from account.models import ManagedPermission, OrganizationManagedPermission


@pytest.mark.django_db
def test_grant_mode_auto(account_objects):

    mperm = ManagedPermission.objects.create(
        namespace="test.mperm",
        status="ok",
        group="test",
        description="test",
        managable=True,
        auto_grant_admins=15,
        auto_grant_users=1,
    )

    assert Permissions(account_objects.user).check("test.mperm", "r")

    mperm.delete()

    assert not Permissions(account_objects.user).check("test.mperm", "r")


@pytest.mark.django_db
def test_grant_mode_restricted(account_objects):

    mperm = ManagedPermission.objects.create(
        namespace="test.mperm",
        status="ok",
        group="test",
        grant_mode="restricted",
        description="test",
        managable=True,
        auto_grant_admins=15,
        auto_grant_users=1,
    )

    assert not Permissions(account_objects.user).check("test.mperm", "r")

    omperm = OrganizationManagedPermission.objects.create(
        org=account_objects.org, managed_permission=mperm, reason="test"
    )

    assert Permissions(account_objects.user).check("test.mperm", "r")

    omperm.delete()

    assert not Permissions(account_objects.user).check("test.mperm", "r")

@pytest.mark.django_db
def test_grant_mode_restricted_add_user(account_objects):

    mperm = ManagedPermission.objects.create(
        namespace="test.mperm",
        status="ok",
        group="test",
        grant_mode="restricted",
        description="test",
        managable=True,
        auto_grant_admins=15,
        auto_grant_users=1,
    )

    user_2 = get_user_model().objects.create_user(
        username="user_2", email="user2@localhost", password="user2"
    )

    account_objects.org.add_user(user_2)

    assert not Permissions(user_2).check("test.mperm", "r")

    omperm = OrganizationManagedPermission.objects.create(
        org=account_objects.org, managed_permission=mperm, reason="test"
    )

    assert Permissions(user_2).check("test.mperm", "r")

    omperm.delete()

    assert not Permissions(user_2).check("test.mperm", "r")

@pytest.mark.django_db
def test_grant_mode_restricted_add_user_granted(account_objects):

    mperm = ManagedPermission.objects.create(
        namespace="test.mperm",
        status="ok",
        group="test",
        grant_mode="restricted",
        description="test",
        managable=True,
        auto_grant_admins=15,
        auto_grant_users=1,
    )

    user_2 = get_user_model().objects.create_user(
        username="user_2", email="user2@localhost", password="user2"
    )

    omperm = OrganizationManagedPermission.objects.create(
        org=account_objects.org, managed_permission=mperm, reason="test"
    )

    account_objects.org.add_user(user_2)

    assert Permissions(user_2).check("test.mperm", "r")

    omperm.delete()

    assert not Permissions(user_2).check("test.mperm", "r")
