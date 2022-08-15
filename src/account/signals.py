import fullctl.django.models.concrete.tasks as task_models

from reversion.models import Version
from reversion.signals import post_revision_commit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver

from account.models import (
    APIKey,
    EmailConfirmation,
    ManagedPermission,
    ManagedPermissionRoleAutoGrant,
    Organization,
    OrganizationManagedPermission,
    OrganizationUser,
    OrganizationRole,
    Role,
    UserSettings,
)


@receiver(post_save, sender=Organization)
def sync_org(sender, **kwargs):
    task_models.CallCommand.create_task("aaactl_sync", "org", kwargs["instance"].id)


@receiver(post_save, sender=get_user_model())
def sync_user(sender, **kwargs):
    task_models.CallCommand.create_task("aaactl_sync", "user", kwargs["instance"].id)


@receiver(post_save, sender=OrganizationUser)
def sync_org_user_add(sender, **kwargs):
    task_models.CallCommand.create_task(
        "aaactl_sync", "org_user", kwargs["instance"].user_id
    )


@receiver(post_delete, sender=OrganizationUser)
def sync_org_user_delete(sender, **kwargs):
    task_models.CallCommand.create_task(
        "aaactl_sync", "org_user", kwargs["instance"].user_id
    )


@receiver(post_save, sender=get_user_model())
def create_user_config(sender, **kwargs):
    if kwargs.get("created"):
        user = kwargs.get("instance")
        if settings.ENABLE_EMAIL_CONFIRMATION:
            UserSettings.objects.get_or_create(user=user)
            EmailConfirmation.start(user)
        else:
            UserSettings.objects.get_or_create(user=user, email_confirmed=True)


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


@receiver(post_save, sender=ManagedPermissionRoleAutoGrant)
def set_permissions(sender, **kwargs):

    created = kwargs.get("created")
    mperm = kwargs.get("instance").managed_permission

    for org in Organization.objects.all():
        mperm.apply(org=org, role=kwargs.get("instance").role)

@receiver(pre_delete, sender=ManagedPermissionRoleAutoGrant)
def revoke_permissions(sender, **kwargs):
    mperm = kwargs.get("instance").managed_permission

    for org in Organization.objects.all():
        mperm.revoke(org=org, role=kwargs.get("instance").role)


@receiver(post_save, sender=OrganizationManagedPermission)
def set_org_manage_permission(sender, **kwargs):
    instance = kwargs.get("instance")
    instance.apply()


@receiver(pre_delete, sender=OrganizationManagedPermission)
def delete_org_manage_permission(sender, **kwargs):
    instance = kwargs.get("instance")
    instance.managed_permission.revoke(instance.org)

@receiver(pre_delete, sender=OrganizationUser)
def delete_org_user(sender, **kwargs):
    instance = kwargs.get("instance")
    OrganizationRole.objects.filter(user=instance.user, org=instance.org).delete()

@receiver(post_save, sender=OrganizationUser)
def save_org_user(sender, **kwargs):
    instance = kwargs.get("instance")
    created = kwargs.get("created")

    if not created:
        return

    if instance.org.org_user_set.count() == 1:
        qset = Role.objects.filter(auto_set_on_creator=True)
    else:
        qset = Role.objects.filter(auto_set_on_member=True)

    for role in qset:
        OrganizationRole.objects.get_or_create(user=instance.user, org=instance.org, role=role)

"""
@receiver(post_save, sender=OrganizationRole)
def save_org_role(sender, **kwargs):
    instance = kwargs.get("instance")
    ManagedPermission.apply_roles(instance.org, instance.user)
"""


@receiver(post_delete, sender=OrganizationRole)
def del_org_role(sender, **kwargs):
    instance = kwargs.get("instance")
    ManagedPermission.apply_roles(instance.org, instance.user)

def sync_roles(**kwargs):
    for vs in kwargs.get("versions"):
        instance = vs.object

        if isinstance(instance, OrganizationRole):
            ManagedPermission.apply_roles(instance.org, instance.user)

post_revision_commit.connect(sync_roles)
