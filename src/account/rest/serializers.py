import logging
import re

from django.contrib.auth import get_user_model, update_session_auth_hash
from django.utils.translation import gettext as _
from django_grainy.util import Permissions
from rest_framework import serializers

import account.forms as forms
import account.models as models
from common.rest import HANDLEREF_FIELDS


class Serializers(object):
    pass


def register(cls):
    if not hasattr(cls, "ref_tag"):
        cls.ref_tag = cls.Meta.model.HandleRef.tag
        cls.Meta.fields += HANDLEREF_FIELDS
    setattr(Serializers, cls.ref_tag, cls)
    return cls


class FormValidationMixin(object):
    required_context = ["user"]

    def get_form(self, data):
        return self.form(data)

    def validate(self, data):
        for k in self.required_context:
            if k not in self.context:
                raise serializers.ValidationError("Context missing: {}".format(k))

        form = self.get_form(data)

        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        data["form_data"] = form.cleaned_data

        return data


class PermissionNamespacesMixin(object):
    @property
    def permission_namespaces(self):
        if not hasattr(self, "_permission_namespaces"):
            mperms = models.ManagedPermission.objects.filter(status="ok", managable=True).order_by("group", "description")
            r = []
            for mperm in mperms:
                r.append( (mperm.namespace, mperm.description) )
            self._permission_namespaces = r


        return self._permission_namespaces




@register
class OrganizationUser(PermissionNamespacesMixin, serializers.ModelSerializer):
    ref_tag = "orguser"

    name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    you = serializers.SerializerMethodField()
    manageable = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = models.OrganizationUser
        fields = ["id", "name", "email", "you", "manageable", "permissions"]

    def get_name(self, obj):
        return "{} {}".format(obj.user.first_name, obj.user.last_name)

    def get_email(self, obj):
        return obj.user.email

    def get_you(self, obj):
        return obj.user == self.context.get("user")

    def get_manageable(self, obj):
        perms = self.context.get("perms")
        if perms:
            return perms.get(f"user.{obj.org.id}", as_string=True)
        return "r"

    def get_permissions(self, obj):
        perms = Permissions(obj.user)
        rv = dict(
            [
                (ns, {"perms": perms.get(ns.format(org_id=obj.org.id), as_string=True), "label": label})
                for ns, label in self.permission_namespaces
            ]
        )

        # for svc in self.context.get("services",[]):
        #    rv[svc.slug] = perms.get([obj.org, svc], as_string=True)
        return rv


@register
class OrganizationUserPermissions(PermissionNamespacesMixin, serializers.Serializer):
    ref_tag = "orguserperm"

    org = serializers.PrimaryKeyRelatedField(queryset=models.Organization.objects.all())
    orguser = serializers.PrimaryKeyRelatedField(
        queryset=models.OrganizationUser.objects.all()
    )
    component = serializers.CharField()
    permissions = serializers.CharField(allow_blank=True)

    def validate_component(self, value):
        value = value.lower()
        if value not in dict(self.permission_namespaces):
            raise serializers.ValidationError(_("Not a valid permissioning component"))

        return value

    def validate_permissions(self, value):
        value = value.lower()
        if re.search("[^crud]", value):
            raise serializers.ValidationError(
                _("Invalid permissioning flags: {}").format(value)
            )

        return value

    def validate(self, data):
        if data.get("orguser").org != data.get("org"):
            raise serializers.ValidationError(_("Invalid user to org relationship id"))

        return data

    def save(self):
        data = self.validated_data
        orguser = data["orguser"]
        org = data["org"]
        component = data["component"]
        permissions = data["permissions"]

        orguser.user.grainy_permissions.add_permission(component.format(org_id=org.id), permissions)

        return orguser


@register
class Organization(serializers.ModelSerializer):
    ref_tag = "org"

    personal = serializers.SerializerMethodField()
    label = serializers.CharField(read_only=True)
    selected = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()

    class Meta:
        model = models.Organization
        fields = ["id", "name", "label", "slug", "selected", "personal", "is_admin"]

    def get_personal(self, obj):
        if obj.user == self.context.get("user"):
            return True
        return False

    def get_selected(self, obj):
        selected_org = self.context.get("selected_org")
        return selected_org and selected_org.id == obj.id

    def get_is_admin(self, obj):
        user = self.context.get("user")
        if not hasattr(self, "_perms"):
            self._perms = Permissions(user)
        return self._perms.check(obj, "crud")

    def validate(self, data):
        user = self.context.get("user")

        if not user:
            raise serializers.ValidationError("No user context")

        form = forms.CreateOrganization(data)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        return data

    def save(self):
        data = self.validated_data

        org = models.Organization.objects.create(
            name=data.get("name"), slug=data.get("slug")
        )
        org.add_user(self.context.get("user"), "crud")
        return org


@register
class EditOrg(FormValidationMixin, serializers.ModelSerializer):
    ref_tag = "orgedit"
    form = forms.EditOrganization
    required_context = ["org", "user"]

    class Meta:
        model = models.Organization
        fields = ["name", "slug"]

    def validate_name(self, value):
        org = self.context.get("org")
        if org.user_id:
            return org.name
        return value

    def get_form(self, data):
        return self.form(self.context.get("org"), data)


@register
class EditOrgPasswordProtected(EditOrg):

    ref_tag = "orgeditpwdprotected"
    form = forms.EditOrganizationPasswordProtected
    required_context = ["org", "user"]

    password = serializers.CharField(write_only=True)

    class Meta(EditOrg.Meta):
        fields = EditOrg.Meta.fields + ["password"]

    def get_form(self, data):
        return self.form(self.context.get("user"), self.context.get("org"), data)


@register
class UserInformation(FormValidationMixin, serializers.ModelSerializer):
    ref_tag = "user"
    form = forms.UserInformationBase
    username = serializers.CharField(validators=[])

    class Meta:
        model = get_user_model()
        fields = ["username", "first_name", "last_name", "email"]

    def save(self):
        data = self.validated_data
        user = self.context.get("user")

        user.first_name = data.get("first_name")
        user.last_name = data.get("last_name")
        user.username = data.get("username")

        if user.email != data.get("email"):
            user.email = data.get("email")
            usercfg, _ = models.UserSettings.objects.get_or_create(user=user)
            usercfg.email_confirmed = False
            usercfg.save()

            models.EmailConfirmation.start(user)

        user.save()


@register
class UserInformationPasswordProtected(UserInformation):
    ref_tag = "userpasswordprotected"
    form = forms.ChangeInformation
    password = serializers.CharField(write_only=True)

    class Meta(UserInformation.Meta):
        fields = UserInformation.Meta.fields + ["password"]

    def get_form(self, data):
        return self.form(self.context.get("user"), data)


@register
class ChangePassword(serializers.Serializer):
    ref_tag = "pwd"

    password = serializers.CharField(write_only=True, required=False)
    password_new = serializers.CharField(write_only=True)
    password_confirmation = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context.get("user")

        if not user:
            raise serializers.ValidationError("No user context")

        if user.has_usable_password():
            form = forms.ChangePassword(user, data)
        else:
            form = forms.ChangePasswordBase(data)

        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        return data

    def save(self):
        data = self.validated_data
        request = self.context.get("request")
        user = self.context.get("user")
        user.set_password(data["password_new"])
        user.save()

        if request:
            update_session_auth_hash(request, user)


@register
class Invitation(FormValidationMixin, serializers.ModelSerializer):
    org_name = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()

    form = forms.InviteToOrganization
    required_context = ["org", "user"]

    class Meta:
        model = models.Invitation
        fields = ["org_id", "org_name", "slug", "email", "user_name"]

    def get_org_name(self, obj):
        return obj.org.name

    def get_user_name(self, obj):
        email = obj.email
        user = get_user_model().objects.filter(email=email).first()
        if user:
            return user.get_full_name()
        else:
            return ""

    def get_slug(self, obj):
        return obj.org.slug

    def save(self):
        data = self.validated_data
        data["created_by"] = self.context.get("user")
        data["org"] = self.context.get("org")
        data.pop("form_data", None)

        inv = models.Invitation.objects.filter(
            email=data["email"], org=data["org"]
        ).first()

        if inv:
            inv.created_by = data["created_by"]
            if data.get("service"):
                inv.service = data["service"]
            inv.save(update_fields=["created_by", "updated", "service"])

        else:
            inv = models.Invitation.objects.create(status="pending", **data)

        inv.send()

        return inv


@register
class StartPasswordReset(FormValidationMixin, serializers.ModelSerializer):

    ref_tag = "start_pwdrst"
    required_context = []
    form = forms.StartPasswordReset

    class Meta:
        model = models.PasswordReset
        fields = ["email"]

    def save(self):
        logger = logging.getLogger(__name__)
        data = self.validated_data

        email = data.get("email")

        target_user = None
        for user in get_user_model().objects.filter(email=email):
            if user.has_usable_password():
                target_user = user
                break

        if target_user:
            logger.info("User found, starting password reset")
            return models.PasswordReset.start(target_user)
        else:
            logger.warning("No user found connected to email")
            return models.PasswordReset(email=email)


@register
class PasswordReset(FormValidationMixin, serializers.Serializer):

    required_context = []
    form = forms.PasswordReset

    password_new = serializers.CharField(write_only=True)
    password_confirmation = serializers.CharField(write_only=True)
    secret = serializers.CharField(write_only=True)

    class Meta:
        model = models.PasswordReset
        fields = ["secret", "password_new", "password_confirmation"]

    def save(self):
        data = self.validated_data
        instance = data["form_data"]["pwdrst"]
        instance.complete(data["password_new"])
        return instance


@register
class APIKey(serializers.ModelSerializer):
    class Meta:
        model = models.APIKey
        fields = ["key", "created", "status"]
