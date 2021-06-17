import datetime
import secrets

import reversion
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext as _
from django_grainy.decorators import grainy_model
from django_grainy.models import Permission, PermissionField, PermissionManager
from django_grainy.util import Permissions, check_permissions

from common.email import email_noreply
from common.models import HandleRefModel

# Create your models here.


@reversion.register
class UserSettings(HandleRefModel):
    """
    Extra user fields
    """

    user = models.OneToOneField(
        get_user_model(), on_delete=models.CASCADE, related_name="usercfg"
    )
    email_confirmed = models.BooleanField(
        default=False, help_text=_("Has the user confirmed his email")
    )

    class Meta:
        db_table = "account_user_settings"
        verbose_name = _("User Settings")
        verbose_name_plural = _("User Settings")

    class HandleRef:
        tag = "usercfg"


def generate_org_name():
    i = 0
    while i < 1000:
        name = secrets.token_urlsafe(8)
        if not Organization.objects.filter(name=name).exists():
            return name
        i += 1
    raise OSError(_("Unable to generate unique organization name"))


def generate_org_slug():
    i = 0
    while i < 1000:
        slug = secrets.token_urlsafe(8).lower()
        if not Organization.objects.filter(slug=slug).exists():
            return slug
        i += 1
    raise OSError(_("Unable to generate unique organization slug"))


@reversion.register
@grainy_model(namespace="org")
class Organization(HandleRefModel):
    name = models.CharField(max_length=255, unique=True, default=generate_org_name)
    slug = models.CharField(max_length=255, unique=True, default=generate_org_slug)
    user = models.OneToOneField(
        get_user_model(),
        on_delete=models.SET_NULL,
        related_name="personal_org",
        blank=True,
        null=True,
        unique=True,
        help_text=_(
            "If set, designates this organzation as a user's personal organization"
        ),
    )

    class Meta:
        db_table = "account_organization"
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")

    class HandleRef:
        tag = "org"

    @classmethod
    def personal_org(cls, user):

        if not cls.objects.filter(slug=user.username).exists():
            slug = user.username
        else:
            slug = generate_org_slug()

        org, created = cls.objects.get_or_create(user=user, slug=slug)

        if created:
            org.add_user(user, "crud")

        return org

    @classmethod
    def get_for_user(cls, user, perms="r"):
        return Permissions(user).instances(cls, perms, ignore_grant_all=True)

    @property
    def permission_namespaces(self):
        if not hasattr(self, "_permission_namespaces"):
            mperms = ManagedPermission.objects.filter(status="ok", group="aaactl")
            r = []
            for mperm in mperms:
                r.append(mperm.namespace)
            self._permission_namespaces = r

        return self._permission_namespaces

    @property
    def users(self):
        for orguser in self.orguser_set.all():
            yield orguser.user

    @property
    def label(self):
        if self.user_id:
            return _("Personal")
        return self.name

    @property
    def label_long(self):
        if self.user_id:
            return _("Your Personal Organization")
        return self.name

    def __str__(self):
        return self.label

    @reversion.create_revision()
    def add_user(self, user, perms="r"):
        orguser, created = OrganizationUser.objects.get_or_create(org=self, user=user)
        if created:
            for mperm in ManagedPermission.objects.all():
                if perms == "r":
                    mperm.auto_grant_user(self, user)
                else:
                    mperm.auto_grant_admin(self, user)

        return orguser

    @reversion.create_revision()
    def remove_user(self, user):
        self.orguser_set.filter(user=user).delete()
        for mperm in ManagedPermission.objects.all():
            mperm.revoke_user(self, user)

    def clean_slug(self, value):
        value = value.lower()
        protected_values = ["personal"]
        if value in protected_values:
            raise ValidationError(_("Protected value: {}").format(value))
        return value

    def is_admin_user(self, user):

        if self.user == user:
            return True

        return check_permissions(user, self, "c", ignore_grant_all=True)


@reversion.register
class OrganizationUser(HandleRefModel):
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="orguser_set"
    )
    org = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="orguser_set"
    )

    class Meta:
        db_table = "account_organization_user"
        verbose_name = _("Organization User Membership")
        verbose_name_plural = _("Organization User Memberships")

    class HandleRef:
        tag = "orguser"

    def __str__(self):
        return f"{self.org.slug}:{self.user.username} ({self.id})"


def generate_api_key():
    i = 0
    while i < 1000:
        key = secrets.token_urlsafe()
        if not APIKey.objects.filter(key=key).exists():
            return key
        i += 1
    raise OSError(_("Unable to generate unique api key"))


class APIKeyBase(HandleRefModel):

    name = models.CharField(max_length=255, blank=True, null=True)
    key = models.CharField(max_length=255, default=generate_api_key, unique=True)
    managed = models.BooleanField(
        default=True, help_text=_("Is the API Key managed by the owner")
    )

    class Meta:
        abstract = True

    @property
    def is_authenticated(self):
        return True

    @property
    def key_id(self):
        return self.key[:8]

    def __str__(self):
        return f"{self.key_id} ({self.id})"


@reversion.register
@grainy_model(namespace="key")
class APIKey(APIKeyBase):
    """
    Describes a personal APIKey
    """

    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="key_set"
    )
    readonly = models.BooleanField(default=False)

    class Meta:
        db_table = "account_api_key"
        verbose_name = _("Personal API Key")
        verbose_name_plural = _("Personal API Keys")

    class HandleRef:
        tag = "key"


@reversion.register
class APIKeyPermission(HandleRefModel, Permission):
    """
    Describes API key permissions
    """

    api_key = models.ForeignKey(
        APIKey, on_delete=models.CASCADE, related_name="grainy_permissions"
    )

    objects = PermissionManager()

    class Meta:
        db_table = "account_api_key_permission"
        verbose_name = _("API Key Permission")
        verbose_name_plural = _("API Key Permissions")

    class HandleRef:
        tag = "keyperm"


@reversion.register
@grainy_model(namespace="_key_")
class InternalAPIKey(APIKeyBase):
    """
    Describes internal APIKey
    """

    class Meta:
        db_table = "account_internal_api_key"
        verbose_name = _("Internal API Key")
        verbose_name_plural = _("Internal API Keys")

    class HandleRef:
        tag = "_key_"

    @classmethod
    def require(cls):
        if not cls.objects.all().count():
            key = cls.objects.create()
            key.grainy_permissions.add_permission("*.*", "crud")


@reversion.register
class InternalAPIKeyPermission(HandleRefModel, Permission):
    """
    Describes API key permissions
    """

    api_key = models.ForeignKey(
        InternalAPIKey, on_delete=models.CASCADE, related_name="grainy_permissions"
    )

    objects = PermissionManager()

    class Meta:
        db_table = "account_internal_api_key_permission"
        verbose_name = _("Internal API Key Permission")
        verbose_name_plural = _("Internal API Key Permissions")

    class HandleRef:
        tag = "keyperm"


@reversion.register
@grainy_model(namespace="orgkey", namespace_instance="{namespace}.{instance.org_id}")
class OrganizationAPIKey(APIKeyBase):
    """
    Describes a organization APIKey
    """

    org = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="orgkey_set"
    )
    email = models.EmailField()

    class Meta:
        db_table = "account_org_api_key"
        verbose_name = _("Organization API Key")
        verbose_name_plural = _("Organization API Keys")

    class HandleRef:
        tag = "orgkey"


@reversion.register
class OrganizationAPIKeyPermission(HandleRefModel, Permission):
    """
    Describes organization API key permissions
    """

    api_key = models.ForeignKey(
        OrganizationAPIKey, on_delete=models.CASCADE, related_name="grainy_permissions"
    )

    objects = PermissionManager()

    class Meta:
        db_table = "account_org_api_key_permission"
        verbose_name = _("Organization API Key Permission")
        verbose_name_plural = _("Organization API Key Permissions")

    class HandleRef:
        tag = "orgkeyperm"

    def __str__(self):
        return f"{self.namespace} ({self.id})"


def generate_emconf_secret():
    i = 0
    while i < 1000:
        secret = secrets.token_urlsafe()
        if not EmailConfirmation.objects.filter(secret=secret).exists():
            return secret
        i += 1
    raise OSError(_("Unable to generate unique email confirmation secret"))


@reversion.register
class EmailConfirmation(HandleRefModel):
    """
    Describes email confirmation process
    """

    user = models.OneToOneField(
        get_user_model(), on_delete=models.CASCADE, related_name="emconf"
    )

    secret = models.CharField(max_length=255, default=generate_emconf_secret)

    email = models.EmailField()

    class Meta:
        db_table = "account_email_confirmation"
        verbose_name = _("Email Confirmation Process")
        verbose_name_plural = _("Email Confirmation Processes")

    class HandleRef:
        tag = "emconf"

    @classmethod
    def start(cls, user):
        try:
            user.emconf.delete()
        except cls.DoesNotExist:
            pass

        with reversion.create_revision():
            instance = cls.objects.create(user=user, email=user.email, status="pending")

        email_noreply(
            user.email,
            _("Confirm your email address"),
            render(
                None, "account/email/confirm-email.txt", {"instance": instance}
            ).content.decode("utf-8"),
        )

        return instance

    @property
    def url(self):
        return "{}{}".format(
            settings.HOST_URL,
            reverse("account:auth-confirm-email", args=(self.secret,)),
        )

    @reversion.create_revision()
    def complete(self):
        usercfg, _ = UserSettings.objects.get_or_create(user=self.user)
        usercfg.email_confirmed = True
        usercfg.save()

        self.delete()


def generate_pwdrst_secret():
    i = 0
    while i < 1000:
        secret = secrets.token_urlsafe()
        if not PasswordReset.objects.filter(secret=secret).exists():
            return secret
        i += 1
    raise OSError(_("Unable to generate unique password reset secret"))


@reversion.register
class PasswordReset(HandleRefModel):
    """
    Describes password reset process
    """

    user = models.OneToOneField(
        get_user_model(), on_delete=models.CASCADE, related_name="password_reset"
    )

    secret = models.CharField(max_length=255, default=generate_pwdrst_secret)

    email = models.EmailField()

    class Meta:
        db_table = "account_password_reset"
        verbose_name = _("Password Reset Process")
        verbose_name_plural = _("Password Reset Processes")

    class HandleRef:
        tag = "pwdrst"

    @classmethod
    def start(cls, user):
        try:
            user.password_reset.delete()
        except cls.DoesNotExist:
            pass

        with reversion.create_revision():
            instance = cls.objects.create(user=user, email=user.email, status="pending")

        email_noreply(
            user.email,
            _("Password Reset"),
            render(
                None, "account/email/password-reset.txt", {"instance": instance}
            ).content.decode("utf-8"),
        )

        return instance

    @property
    def expired(self):
        delta = datetime.datetime.now(datetime.timezone.utc) - self.created
        return delta.hours >= 1

    @property
    def url(self):
        return "{}{}".format(
            settings.HOST_URL,
            reverse("account:auth-reset-password", args=(self.secret,)),
        )

    @reversion.create_revision()
    def complete(self, new_password):
        self.user.set_password(new_password)
        self.user.save()
        self.delete()


def generate_invite_secret():
    i = 0
    while i < 1000:
        secret = secrets.token_urlsafe()
        if not Invitation.objects.filter(secret=secret).exists():
            return secret
        i += 1
    raise OSError(_("Unable to generate unique invitation secret"))


@reversion.register
class ManagedPermission(HandleRefModel):

    """
    Describes a custom permission definition, allowing
    to add app / service specific permissions to be managed
    through aaactl
    """

    namespace = models.CharField(
        max_length=255,
        help_text=_(
            "The permission namespace. The following variables are available for formatting: {org_id}"
        ),
    )

    group = models.CharField(
        max_length=255, help_text=_("Belongs to this group of permissions")
    )

    description = models.CharField(
        max_length=255, help_text=_("What is this permission namespace used for?")
    )

    managable = models.BooleanField(
        default=True, help_text=_("Can organization admins manage this permission?")
    )

    auto_grant_admins = PermissionField(
        help_text=_(
            "Auto grants the permission at the following level to organization admins"
        )
    )

    auto_grant_users = PermissionField(
        help_text=_(
            "Auto grants the permission at the following level to organization members and api keys"
        )
    )

    class Meta:
        db_table = "account_managed_permission"
        verbose_name = _("Managed permission")
        verbose_name_plural = _("Managed permissions")

    class HandleRef:
        tag = "mperm"

    @classmethod
    def grant_all_key(cls, orgkey, admin=False):
        for mperm in cls.objects.all():
            mperm.auto_grant_key(orgkey, admin=admin)

    @classmethod
    def grant_all_user(cls, user, admin=False):
        mperms = [mperm for mperm in cls.objects.all()]
        for orguser in user.orguser_set.all():
            for mperm in mperms:
                if admin:
                    mperm.auto_grant_admin(orguser.org, orguser.user)
                else:
                    mperm.auto_grant_user(orguser.org, orguser.user)

    @classmethod
    def revoke_all_key(cls, orgkey):
        for mperm in cls.objects.all():
            mperm.revoke_key(orgkey)

    @classmethod
    def revoke_all_user(cls, user):
        mperms = [mperm for mperm in cls.objects.all()]
        for orguser in user.orguser_set.all():
            for mperm in mperms:
                mperm.revoke_user(orguser.org, orguser.user)

    def __str__(self):
        return f"{self.group} - {self.description}"

    def auto_grant(self, org):

        for user in org.users:
            if org.is_admin_user(user):
                self.auto_grant_admin(org, user)
            else:
                self.auto_grant_user(org, user)

        for key in org.orgkey_set.all():
            self.auto_grant_key(key)

    def revoke(self, org):
        for user in org.users:
            self.revoke_user(org, user)

        for key in org.orgkey_set.all():
            self.revoke_key(org, key)

    def revoke_user(self, org, user):
        ns = self.namespace.format(org_id=org.pk)
        user.grainy_permissions.delete_permission(ns)

    def revoke_key(self, orgkey):
        org = orgkey.org
        ns = self.namespace.format(org_id=org.pk)
        orgkey.grainy_permissions.delete_permission(ns)

    def auto_grant_admin(self, org, user):
        ns = self.namespace.format(org_id=org.pk)
        user.grainy_permissions.add_permission(ns, self.auto_grant_admins)

    def auto_grant_user(self, org, user):
        ns = self.namespace.format(org_id=org.pk)
        user.grainy_permissions.add_permission(ns, self.auto_grant_users)

    def auto_grant_key(self, orgkey, admin=False):
        org = orgkey.org
        ns = self.namespace.format(org_id=org.pk)

        if admin:
            perms = self.auto_grant_admins
        else:
            perms = self.auto_grant_users

        orgkey.grainy_permissions.add_permission(ns, perms)


@reversion.register
class Invitation(HandleRefModel):
    secret = models.CharField(max_length=255, default=generate_invite_secret)
    org = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="inv_set"
    )
    created_by = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name="inv_set",
    )
    email = models.EmailField()
    service = models.ForeignKey(
        "applications.Service",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inv_set",
    )

    class Meta:
        db_table = "account_invitation"
        verbose_name = _("Invitation")
        verbose_name_plural = _("Invitations")

    class HandleRef:
        tag = "inv"

    @property
    def expired(self):
        delta = datetime.datetime.now(datetime.timezone.utc) - self.created
        return delta.days >= 3

    @property
    def url(self):
        return "{}{}".format(
            settings.HOST_URL, reverse("account:accept-invite", args=(self.secret,))
        )

    def __str__(self):
        return f"{self.org.slug}:{self.email} ({self.id})"

    def send(self):
        if self.created_by:
            inviting_person = self.created_by.get_full_name()
        else:
            inviting_person = "[Deleted user]"
        email_noreply(
            self.email,
            _("Invitation to join {}").format(self.org.label),
            render(
                None,
                "account/email/invite.txt",
                {
                    "inv": self,
                    "inviting_person": inviting_person,
                    "org": self.org,
                    "host": settings.HOST_URL,
                },
            ).content.decode("utf-8"),
        )

    @reversion.create_revision()
    def complete(self, user):
        if not self.expired and not self.org.orguser_set.filter(user=user).exists():
            self.org.add_user(user, "r")
        Invitation.objects.filter(org=self.org, email=self.email).delete()
