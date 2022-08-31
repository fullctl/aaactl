"""
Superuser user impersonation
"""

from django.contrib.auth import get_user_model

from account.models import Impersonation


def is_impersonating(request):
    """
    Returns whether or not the supplied request is currently impersonating a user

    Will return None if no impersonation is set up.

    Otherwise will return User instance for user being impersonated
    """

    if getattr(request, "impersonating", None):

        # Only superusers are ever able to impersonate anyone
        if not getattr(request.impersonating.superuser, "is_superuser", False):
            return None

        return request.impersonating.user
    elif not getattr(request.user, "is_superuser", False):
        return None

    try:
        return request.user.impersonating.user
    except Impersonation.DoesNotExist:
        return None


def start_impersonation(request, user):

    """
    start impersonating the specified user
    """

    # Only superusers are ever able to impersonate anyone
    if not getattr(request.user, "is_superuser", False):
        return

    # stop current personation

    stop_impersonation(request)

    if not isinstance(user, get_user_model()):
        raise TypeError(f"user needs to be of {get_user_model()} type")

    # cannot impersonate self

    if request.user == user:
        return

    Impersonation.objects.create(user=user, superuser=request.user)


def stop_impersonation(request):
    """
    stop impersonating
    """

    impersonating = getattr(request, "impersonating", None)

    if not impersonating:
        return

    request.user = impersonating.superuser

    try:
        impersonating.delete()
    except Impersonation.DoesNotExist:
        pass

    request.impersonating = None
