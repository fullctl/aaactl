import fullctl.django.models.concrete.tasks as task_models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from account.models import (
    APIKey,
    EmailConfirmation,
    ManagedPermission,
    Organization,
    OrganizationUser,
    UserSettings,
)


@receiver(post_save, sender=Organization)
def sync_org(sender, **kwargs):
    task_models.CallCommand.create_task("aaactl_sync", "org", kwargs["instance"].id)


@receiver(post_save, sender=get_user_model())
def sync_user(sender, **kwargs):
    task_models.CallCommand.create_task("aaactl_sync", "user", kwargs["instance"].id)


@receiver(post_save, sender=OrganizationUser)
def sync_orguser_add(sender, **kwargs):
    if kwargs.get("created"):
        task_models.CallCommand.create_task(
            "aaactl_sync", "orguser", kwargs["instance"].user_id
        )


@receiver(post_delete, sender=OrganizationUser)
def sync_orguser_delete(sender, **kwargs):
    task_models.CallCommand.create_task(
        "aaactl_sync", "orguser", kwargs["instance"].user_id
    )


@receiver(post_save, sender=get_user_model())
def create_user_config(sender, **kwargs):
    if kwargs.get("created"):
        user = kwargs.get("instance")
        UserSettings.objects.get_or_create(user=user)
        EmailConfirmation.start(user)


@receiver(post_save, sender=get_user_model())
def generate_api_key(sender, **kwargs):
    if kwargs.get("created"):
        user = kwargs.get("instance")
        APIKey.objects.create(user=user, managed=True)


# @receiver(post_save, sender=get_user_model())
# def set_initial_permissions(sender, **kwargs):
#    if kwargs.get("created"):
#        user = kwargs.get("instance")
#        user.grainy_permissions.add_permission(f"user.{user.id}", "crud")


@receiver(post_save, sender=get_user_model())
def create_personal_org(sender, **kwargs):
    if kwargs.get("created"):
        user = kwargs.get("instance")
        Organization.personal_org(user)


@receiver(post_save, sender=ManagedPermission)
def set_permissions(sender, **kwargs):

    created = kwargs.get("created")
    mperm = kwargs.get("instance")

    if created:
        for org in Organization.objects.all():
            mperm.auto_grant(org)
    else:
        for org in Organization.objects.all():
            if not mperm.managable:
                mperm.revoke(org)
            mperm.auto_grant(org)


@receiver(post_delete, sender=ManagedPermission)
def revoke_permissions(sender, **kwargs):
    mperm = kwargs.get("instance")

    for org in Organization.objects.all():
        mperm.revoke(org)
