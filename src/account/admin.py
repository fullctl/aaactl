from django.http import HttpResponse

from django import forms
from django.contrib import admin
from django_grainy.forms import UserPermissionForm, PermissionFormField, BitmaskSelect, PERM_CHOICES_FOR_FIELD

from account.models import (
    APIKey,
    APIKeyPermission,
    EmailConfirmation,
    Invitation,
    ManagedPermission,
    Organization,
    OrganizationUser,
    PasswordReset,
)

class AdminSite(admin.AdminSite):
     def get_urls(self):
         from django.urls import path
         urls = super().get_urls()
         urls += [
             path('diag/', self.admin_view(self.diag))
         ]
         return urls

     def diag(self, request):
        return HttpResponse(str(request.META), content_type="text/plain")

admin_site = AdminSite()


# registered models

class InlineAPIKeyPermission(admin.TabularInline):
    model = APIKeyPermission
    extra = 1
    form = UserPermissionForm


@admin.register(APIKey, site=admin_site)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ("key", "user", "managed", "created")
    search_fields = ("user__username", "user__email", "key")
    inlines = (InlineAPIKeyPermission,)


class OrganizationUserInline(admin.TabularInline):
    model = OrganizationUser
    extra = 1


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "user")
    search_fields = ("user_set__last_name", "name")
    inlines = (OrganizationUserInline,)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=True)
        for obj in formset.deleted_objects:
            for mperm in ManagedPermission.objects.all():
                mperm.revoke_user(obj.org, obj.user)
        for instance in instances:
            for mperm in ManagedPermission.objects.all():
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
        initial=15,
        widget=BitmaskSelect(choices=PERM_CHOICES_FOR_FIELD)
    )

    auto_grant_users = PermissionFormField(
        initial=1,
        widget=BitmaskSelect(choices=PERM_CHOICES_FOR_FIELD)
    )


@admin.register(ManagedPermission)
class ManagedPermissionAdmin(admin.ModelAdmin):
    list_display = ("description", "namespace", "group", "managable", "auto_grant_admins", "auto_grant_users", "created", "updated")
    search_fields = ("group", "description", "namespace")
    form = ManagedPermissionForm

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("namespace",)
        return super().get_readonly_fields(request, obj)



