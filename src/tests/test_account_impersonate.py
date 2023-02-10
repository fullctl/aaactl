from django.contrib.auth import get_user_model
from django.core import management
from django.http import HttpRequest
from django.urls import reverse

from account.impersonate import is_impersonating, start_impersonation
from account.models import Impersonation
from tests.helpers import mock_csrf_session


def test_start_impersontation(db, account_objects, account_objects_b):
    management.call_command("fullctl_promote_user", "user_test", "--commit")
    user = get_user_model().objects.get(username="user_test")

    request = HttpRequest()
    request.method = "GET"
    request.user = user
    mock_csrf_session(request)
    impersontation_count = Impersonation.objects.count()

    start_impersonation(request, account_objects_b.user)
    assert Impersonation.objects.count() == impersontation_count + 1

    response = account_objects.client.get(
        reverse("account:controlpanel"),
    )
    assert (
        "Currently impersonating <b>" + account_objects_b.user.username + "</b>"
        in str(response.content)
    )


def test_is_impersontating(db, account_objects, account_objects_b):
    management.call_command("fullctl_promote_user", "user_test", "--commit")
    user = get_user_model().objects.get(username="user_test")

    request = HttpRequest()
    request.method = "GET"
    request.user = user
    mock_csrf_session(request)
    start_impersonation(request, account_objects_b.user)

    assert is_impersonating(request) == account_objects_b.user


def test_stop_impersontation(db, account_objects, account_objects_b):
    management.call_command("fullctl_promote_user", "user_test", "--commit")
    User = get_user_model()
    user = User.objects.get(username="user_test")

    request = HttpRequest()
    request.method = "GET"
    request.user = user
    mock_csrf_session(request)
    start_impersonation(request, account_objects_b.user)

    assert account_objects_b.user == is_impersonating(request)

    account_objects.client.get(
        reverse("admin:auth_user_actions", args=(user.id, "stop_impersonation"))
    )

    user = User.objects.get(username="user_test")
    request.user = user

    assert is_impersonating(request) is None
