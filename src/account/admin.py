import reversion
from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django_grainy.forms import (
    PERM_CHOICES_FOR_FIELD,
    BitmaskSelect,
    PermissionFormField,
    UserPermissionForm,
)

from account.models import (
    APIKey,
    APIKeyPermission,
    EmailConfirmation,
    InternalAPIKey,
    InternalAPIKeyPermission,
    Invitation,
    ManagedPermission,
    ManagedPermissionRoleAutoGrant,
    Organization,
    OrganizationAPIKey,
    OrganizationAPIKeyPermission,
    OrganizationManagedPermission,
    OrganizationUser,
    OrganizationRole,
    PasswordReset,
    Role,
    UserPermissionOverride,
    UserSettings,
)

from fullctl.django.admin import BaseAdmin

# registered models

@admin.register(UserPermissionOverride)
class UserPermissionOverrideAdmin(BaseAdmin):
    list_display = ("user", "org", "namespace", "permissions", "created", "updated")
    search_fields = (
        "user__username",
        "user__email",
        "org__name",
        "org__slug",
    )

@admin.register(Role)
class RoleAdmin(BaseAdmin):
    list_display = ("name", "description", "level", "auto_set_on_creator", "auto_set_on_member", "created", "updated")
    ordering = ("level",)

@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ("user", "email_confirmed")


class InlineAPIKeyPermission(admin.TabularInline):
    model = APIKeyPermission
    extra = 1
    form = UserPermissionForm


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ("key", "user", "name", "managed", "readonly", "created")
    search_fields = ("name", "user__username", "user__email", "key")
    inlines = (InlineAPIKeyPermission,)


class InlineInternalAPIKeyPermission(admin.TabularInline):
    model = InternalAPIKeyPermission
    extra = 1
    form = UserPermissionForm


@admin.register(InternalAPIKey)
class InternalAPIKeyAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "created")
    search_fields = ("name", "key")
    inlines = (InlineInternalAPIKeyPermission,)


class InlineOrganizationAPIKeyPermission(admin.TabularInline):
    model = OrganizationAPIKeyPermission
    extra = 1
    form = UserPermissionForm


@admin.register(OrganizationAPIKey)
class OrganizationAPIKeyAdmin(admin.ModelAdmin):
    list_display = ("key", "org", "name", "managed", "created")
    search_fields = ("org__name", "org__slug", "email", "key")
    inlines = (InlineOrganizationAPIKeyPermission,)


class OrganizationUserInline(admin.TabularInline):
    model = OrganizationUser
    extra = 1
    fields = ("user", "is_default")

class OrganizationRoleInline(admin.TabularInline):
    model = OrganizationRole
    extra = 1
    fields = ("user", "role")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj=obj, **kwargs)
        if obj:
            formset.form.base_fields["user"].queryset = get_user_model().objects.filter(org_user_set__org=obj)
        return formset

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "user")
    search_fields = ("org_user_set__last_name", "name")
    inlines = (OrganizationUserInline, OrganizationRoleInline)

    @reversion.create_revision()
    def save_formset(self, request, form, formset, change):
        return super().save_formset(request, form, formset, change)


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("org", "email", "created_by", "created", "status")
    search_fields = ("org__name", "org__slug", "email")


@admin.register(EmailConfirmation)
class EmailConfirmationAdmin(admin.ModelAdmin):
    list_display = ("user", "email", "created", "updated", "status")
    search_fields = ("user__username", "user__last_name", "email")


@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    list_display = ("user", "email", "created", "updated", "status")
    search_fields = ("user__username", "user__last_name", "email")

    fields = ("version", "status", "user", "email")


class ManagedPermissionRoleAutoGrantForm(forms.ModelForm):

    permissions = PermissionFormField(
        initial=0, widget=BitmaskSelect(choices=PERM_CHOICES_FOR_FIELD)
    )


class ManagedPermissionRoleAutoGrantInline(admin.TabularInline):
    form = ManagedPermissionRoleAutoGrantForm
    model = ManagedPermissionRoleAutoGrant
    extra = 1
    fields = ("role", "permissions")


@admin.register(ManagedPermission)
class ManagedPermissionAdmin(admin.ModelAdmin):
    list_display = (
        "description",
        "namespace",
        "group",
        "managable",
        "grant_mode",
        "created",
        "updated",
    )
    ordering = ("description",)
    search_fields = ("group", "description", "namespace")
    inlines = (ManagedPermissionRoleAutoGrantInline,)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("namespace",)
        return super().get_readonly_fields(request, obj)


@admin.register(OrganizationManagedPermission)
class OrganizationManagedPermissionAdmin(admin.ModelAdmin):
    list_display = (
        "org",
        "managed_permission",
        "reason",
        "created",
    )


    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj=obj, **kwargs)
        form.base_fields["managed_permission"].queryset = ManagedPermission.objects.filter(grant_mode="restricted")
        return form
