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


@receiver(post_save, sender=ManagedPermission)
def set_permissions(sender, **kwargs):

    created = kwargs.get("created")
    mperm = kwargs.get("instance")

    if created:
        for org in Organization.objects.all():
            mperm.auto_grant(org)
    else:
        for org in Organization.objects.all():
            mperm.revoke(org)
            mperm.auto_grant(org)


@receiver(post_delete, sender=ManagedPermission)
def revoke_permissions(sender, **kwargs):
    mperm = kwargs.get("instance")

    for org in Organization.objects.all():
        mperm.revoke(org)


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

    if instance.org.user == instance.user:
        qset = Role.objects.filter(auto_set_on_creator=True)
    else:
        qset = Role.objects.filter(auto_set_on_member=True)

    for role in qset:
        OrganizationRole.objects.get_or_create(user=instance.user, org=instance.org, role=role)

@receiver(pre_save, sender=OrganizationRole)
def pre_save_org_role(sender, **kwargs):
    instance = kwargs.get("instance")
    if not kwargs.get("created"):
        instance._previous = OrganizationRole.objects.filter(id=instance.id).first()
    else:
        instance._previous = None

@receiver(post_save, sender=OrganizationRole)
def save_org_role(sender, **kwargs):
    instance = kwargs.get("instance")

    prev = getattr(instance, "_previous", None)

    if prev and (prev.role != instance.role or prev.user != instance.user):
        prev_role_exists = OrganizationRole.objects.filter(user=prev.user, org=prev.org, role=prev.role).exists()
        if not prev_role_exists:
            for managed_permission in ManagedPermission.objects.filter(role_auto_grants__role=prev.role):
                managed_permission.revoke(prev.org, prev.user)

    for managed_permission in ManagedPermission.objects.filter(role_auto_grants__role=instance.role):
        managed_permission.apply(instance.org, instance.user)

@receiver(pre_delete, sender=OrganizationRole)
def del_org_role(sender, **kwargs):
    instance = kwargs.get("instance")
    created = kwargs.get("created")

    for managed_permission in ManagedPermission.objects.filter(role_auto_grants__role=instance.role):
        managed_permission.revoke(instance.org, instance.user)



def save_org_role(**kwargs):

    sync_roles = []
    orgs = {}
    users = {}

    for version in kwargs.get("versions"):
        instance = version.object
        if isinstance(instance, OrganizationRole):
            try:
                prev_version = Version.objects.get_for_object(instance)[1]
                prev_data = prev_version.field_dict
                new_data = version.field_dict
                sync_roles.append((prev_data["org_id"], prev_data["user_id"]))
                sync_roles.append((new_data["org_id"], new_data["user_id"]))
            except IndexError:
                sync_roles.append((instance.org_id, instance.user_id))
        elif isinstance(instance, OrganizationUser):
            sync_roles.append(instance.org_id, instance.user_id)
            if not instance.id:
                print("DELETED", instance)
                qset_remove_roles = OrganizationRole.objects.filter(org_id=intance.org_id, user_id=instance.user_id)

    sync_roles = list(set(sync_roles))
    managed_permissions = [mperm for mperm in ManagedPermission.objects.all()]

    for org_id, user_id in sync_roles:

        org = orgs.get(org_id)
        if not org:
            org = orgs[org_id] = Organization.objects.get(id=org_id)

        user = users.get(user_id)
        if not user:
            user = users[user_id] = get_user_model().objects.get(id=user_id)

        for managed_permission in managed_permissions:
            managed_permission.apply(org, user)

#post_revision_commit.connect(save_org_role)


