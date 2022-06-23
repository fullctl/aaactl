from django import forms
from django.contrib import admin
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
    Organization,
    OrganizationAPIKey,
    OrganizationAPIKeyPermission,
    OrganizationManagedPermission,
    OrganizationUser,
    PasswordReset,
)

# registered models


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


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "user")
    search_fields = ("orguser_set__last_name", "name")
    inlines = (OrganizationUserInline,)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=True)
        for obj in formset.deleted_objects:
            for mperm in ManagedPermission.objects.all():
                mperm.revoke_user(obj.org, obj.user)
        for instance in instances:
            for mperm in ManagedPermission.objects.all():
                if instance.org.user == instance.user:
                    mperm.auto_grant_admin(instance.org, instance.user)
                else:
                    mperm.auto_grant_user(instance.org, instance.user)


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


class ManagedPermissionForm(forms.ModelForm):

    auto_grant_admins = PermissionFormField(
        initial=15, widget=BitmaskSelect(choices=PERM_CHOICES_FOR_FIELD)
    )

    auto_grant_users = PermissionFormField(
        initial=1, widget=BitmaskSelect(choices=PERM_CHOICES_FOR_FIELD)
    )


@admin.register(ManagedPermission)
class ManagedPermissionAdmin(admin.ModelAdmin):
    list_display = (
        "description",
        "namespace",
        "group",
        "managable",
        "grant_mode",
        "auto_grant_admins",
        "auto_grant_users",
        "created",
        "updated",
    )
    search_fields = ("group", "description", "namespace")
    form = ManagedPermissionForm

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
