import reversion
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from django_grainy.helpers import str_flags
from django_grainy.util import get_permissions
from fullctl.django.auditlog import auditlog
from fullctl.django.rest.core import BadRequest
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

import account.models as models
from account.rest.decorators import disable_api_key, set_org
from account.rest.route import route
from account.rest.serializers import Serializers
from account.session import set_selected_org
from applications.models import Service
from common.rest.decorators import grainy_endpoint, user_endpoint


@route
class UserInformation(viewsets.ViewSet):
    serializer_class = Serializers.user
    queryset = Serializers.user.Meta.model.objects.all()

    @user_endpoint()
    def list(self, request):
        serializer = Serializers.user(request.user)
        return Response(serializer.data)

    @user_endpoint()
    def put(self, request):
        if request.user.has_usable_password():
            serializer = Serializers.userpasswordprotected(
                data=request.data,
                many=False,
                context={"user": request.user},
            )
        else:
            serializer = Serializers.user(
                data=request.data,
                many=False,
                context={"user": request.user},
            )

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=["PUT"])
    @user_endpoint()
    @disable_api_key
    def user_settings(self, request):
        serializer = Serializers.user_settings(
            instance=request.user.user_settings,
            data=request.data,
            many=False,
            context={"user": request.user, "request": request},
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=["PUT"])
    @auditlog()
    @user_endpoint()
    @disable_api_key
    def set_password(self, request, auditlog=None):
        serializer = Serializers.pwd(
            data=request.data,
            many=False,
            context={"user": request.user, "request": request},
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        serializer.save()

        auditlog.log("set_password")

        return Response(serializer.data)

    @action(detail=False, methods=["POST"])
    @user_endpoint()
    def resend_confirmation_mail(self, request):

        user_settings, created = models.UserSettings.objects.get_or_create(
            user=request.user
        )

        if user_settings.email_confirmed:
            return Response(
                {"non_field_errors": [_("Email address already confirmed")]}, status=400
            )

        models.EmailConfirmation.start(request.user)

        return Response({})

    @action(detail=False)
    @user_endpoint()
    @disable_api_key
    def keys(self, request):
        user = request.user
        queryset = models.APIKey.objects.filter(user__id=user.id)
        serializer = Serializers.key(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False)
    @user_endpoint()
    @disable_api_key
    def invites(self, request):
        user = request.user
        queryset = models.Invitation.objects.filter(email=user.email)
        serializer = Serializers.invite(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False, methods=["POST"], url_path="accept-invite/(?P<invite_id>[^/.]+)"
    )
    @user_endpoint()
    @disable_api_key
    def accept_invite(self, request, invite_id=None):
        user = request.user
        invite = models.Invitation.objects.get(email=user.email, id=invite_id)
        serializer = Serializers.invite(invite)
        data = serializer.data
        invite.complete(user)
        return Response(data)

    @action(
        detail=False, methods=["POST"], url_path="reject-invite/(?P<invite_id>[^/.]+)"
    )
    @user_endpoint()
    @disable_api_key
    def reject_invite(self, request, invite_id=None):
        user = request.user
        invite = models.Invitation.objects.get(email=user.email, id=invite_id)
        serializer = Serializers.invite(invite)
        data = serializer.data
        invite.delete()
        return Response(data)

    @action(detail=False, methods=["POST"], url_path="set-default-org")
    @user_endpoint()
    @disable_api_key
    def set_default_org(self, request):
        if not request.selected_org:
            return Response({"non_field_errors": ["no org selected"]}, status=400)

        request.selected_org.set_as_default(request.user)

        return Response({})

    @action(detail=False, methods=["POST"])
    @auditlog()
    @user_endpoint()
    @disable_api_key
    def create_key(self, request, auditlog=None):
        context = {"user": request.user}
        data = dict(request.data)
        data.update(user=request.user.id)
        serializer = Serializers.key(data=data, many=False, context=context)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        key = serializer.save()
        return Response(Serializers.key(key, many=False).data)

    @action(detail=False, methods=["DELETE"])
    @auditlog()
    @user_endpoint()
    @disable_api_key
    def key(self, request, auditlog=None):
        key = models.APIKey.objects.get(id=request.data.get("id"), user=request.user)
        response = Response(Serializers.key(instance=key, many=False).data)
        key.delete()
        return response

    def get_throttles(self):
        if self.action in ["resend_confirmation_mail"]:
            self.throttle_scope = "resend_email"
        return super().get_throttles()


@route
class Organization(viewsets.ViewSet):
    serializer_class = Serializers.org
    queryset = models.Organization.objects.all()

    @user_endpoint()
    def list(self, request):
        serializer = Serializers.org(
            models.Organization.get_for_user(request.user),
            many=True,
            context={
                "user": request.user,
                "selected_org": getattr(request, "selected_org", None),
            },
        )
        return Response(serializer.data)

    @set_org
    @grainy_endpoint("org.{org.id}")
    def retrieve(self, request, pk, org):
        org = models.Organization.objects.get(slug=pk)
        serializer = Serializers.org(org, many=False, context={"user": request.user})
        return Response(serializer.data)

    @action(detail=False, methods=["POST"])
    @user_endpoint()
    @disable_api_key
    def select(self, request):
        org_id = request.data.get("id")
        userorg = models.OrganizationUser.objects.get(
            user_id=request.user.id, org_id=org_id
        )
        set_selected_org(request, userorg.org)
        return Response(
            Serializers.org(userorg.org, context={"user": request.user}).data
        )

    @auditlog()
    @user_endpoint()
    def create(self, request, auditlog=None):
        serializer = Serializers.org(
            data=request.data, many=False, context={"user": request.user}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        org = serializer.save()

        auditlog.set("org", org)

        if not hasattr(request, "api_key"):
            set_selected_org(request, org)
        return Response(
            Serializers.org(org, many=False, context={"user": request.user}).data
        )

    @set_org
    @auditlog()
    @grainy_endpoint("org.{org.id}.manage", explicit=False)
    def update(self, request, pk, org, auditlog=None):
        user = request.user
        if user.has_usable_password():
            serializer = Serializers.orgeditpwdprotected(
                instance=org,
                data=request.data,
                many=False,
                context={"user": user, "org": org},
            )
        else:
            serializer = Serializers.orgedit(
                instance=org,
                data=request.data,
                many=False,
                context={"user": user, "org": org},
            )

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        org = serializer.save()

        auditlog.set("org", org)

        return Response(
            Serializers.org(org, many=False, context={"user": request.user}).data
        )

    @action(detail=True, methods=["GET"])
    @set_org
    @grainy_endpoint("user.{org.id}", explicit=False)
    def users(self, request, pk, org):
        serializer = Serializers.org_user(
            org.org_user_set.all(),
            many=True,
            context={
                "user": request.user,
                "services": [svc for svc in Service.objects.all()],
                "perms": request.perms,
            },
        )
        return Response(serializer.data)

    @action(detail=True, methods=["DELETE"])
    @set_org
    @auditlog()
    @grainy_endpoint("user.{org.id}", explicit=False)
    def user(self, request, pk, org, auditlog=None):
        org_user = models.OrganizationUser.objects.get(
            id=request.data.get("id"), org=org
        )
        if org_user.user == request.user:
            return Response(
                {
                    "non_field_errors": [
                        _(
                            "Cannot remove yourself from the organization through this endpoint"
                        )
                    ]
                },
                status=400,
            )

        org.remove_user(org_user.user)

        return Response(Serializers.org_user(instance=org_user, many=False).data)

    @action(detail=True, methods=["POST"])
    @set_org
    @auditlog()
    @grainy_endpoint("user.{org.id}", explicit=False)
    def add_role(self, request, pk, org, auditlog=None):

        user = models.OrganizationUser.objects.get(
            id=request.data.get("org_user")
        ).user_id
        role = models.Role.objects.get(id=request.data.get("role"))

        if models.OrganizationRole.objects.filter(
            org=org, user=user, role=role
        ).exists():
            return BadRequest({"non_field_errors": [_("User already has this role")]})

        serializer = Serializers.org_user_role(
            data={
                "org": org.id,
                "user": user,
                "role": request.data.get("role"),
            },
            many=False,
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=["POST"])
    @set_org
    @auditlog()
    @grainy_endpoint("user.{org.id}", explicit=False)
    def remove_role(self, request, pk, org, auditlog=None):
        user = models.OrganizationUser.objects.get(
            id=request.data.get("org_user")
        ).user_id
        role = models.Role.objects.get(id=request.data.get("role"))
        user_role = models.OrganizationRole.objects.get(org=org, user=user, role=role)
        serializer = Serializers.org_user_role(user_role)
        response = Response(serializer.data)
        user_role.delete()
        return response

    @action(detail=True, methods=["PUT"])
    @set_org
    @auditlog()
    @grainy_endpoint("user.{org.id}", explicit=False)
    def set_permissions(self, request, pk, org, auditlog=None):
        serializer = Serializers.org_userperm(
            data={
                "org": org.id,
                "org_user": request.data.get("id"),
                "component": request.data.get("component"),
                "permissions": request.data.get("permissions"),
            },
            many=False,
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        serializer.save()

        return Response(serializer.data)

    @action(detail=True, methods=["POST"])
    @set_org
    @auditlog()
    @grainy_endpoint("user.{org.id}", explicit=False)
    def remove_permissions(self, request, pk, org, auditlog=None):
        override = models.UserPermissionOverride.objects.get(
            org=org, id=request.data.get("id")
        )
        user = override.user
        namespace = override.namespace
        override.delete()
        permissions = get_permissions(
            get_user_model().objects.get(id=user.id), namespace
        )

        return Response({"perms": str_flags(permissions)})

    @action(detail=True, methods=["GET"])
    @set_org
    @grainy_endpoint("org_key.{org.id}", explicit=False)
    def keys(self, request, pk, org):
        serializer = Serializers.org_key(
            org.org_key_set.filter(managed=True),
            many=True,
            context={
                "user": request.user,
                "services": [svc for svc in Service.objects.all()],
                "perms": request.perms,
            },
        )
        return Response(serializer.data)

    @action(detail=True, methods=["PUT"])
    @set_org
    @auditlog()
    @grainy_endpoint("org_key.{org.id}", explicit=False)
    def set_key_permissions(self, request, pk, org, auditlog=None):
        serializer = Serializers.org_key_permission(
            data={
                "org": org.id,
                "org_key": request.data.get("id"),
                "component": request.data.get("component"),
                "permissions": request.data.get("permissions"),
            },
            many=False,
        )

        org_key = models.OrganizationAPIKey.objects.get(
            org=org, id=request.data.get("id")
        )

        if not org_key.managed:
            return Response({"id": ["not a managed key"]}, status=400)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        serializer.save()

        return Response(serializer.data)

    @action(detail=True, methods=["DELETE"])
    @set_org
    @auditlog()
    @grainy_endpoint("org_key.{org.id}", explicit=False)
    def key(self, request, pk, org, auditlog=None):
        org_key = models.OrganizationAPIKey.objects.get(
            id=request.data.get("id"), org=org
        )
        response = Response(Serializers.org_key(instance=org_key, many=False).data)
        org_key.delete()

        return response

    @action(detail=True, methods=["POST"])
    @set_org
    @auditlog()
    @grainy_endpoint("org_key.{org.id}", explicit=False)
    def create_key(self, request, pk, org, auditlog=None):
        context = {"user": request.user, "org": org}
        data = dict(request.data)
        data.update(org=org.id)
        serializer = Serializers.org_key(data=data, many=False, context=context)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        org_key = serializer.save()

        for mperm in models.ManagedPermission.objects.all():
            mperm.auto_grant_key(org_key)
        return Response(Serializers.org_key(org_key, many=False).data)

    @action(detail=True, methods=["GET"])
    @set_org
    @grainy_endpoint("user.{org.id}", explicit=False)
    def invites(self, request, pk, org):
        invitations = models.Invitation.objects.filter(org__slug=pk)
        serializer = Serializers.invite(invitations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["POST"])
    @set_org
    @auditlog()
    @grainy_endpoint("user.{org.id}", explicit=False)
    def invite(self, request, pk, org, auditlog=None):
        context = {"user": request.user, "org": org}
        serializer = Serializers.invite(data=request.data, many=False, context=context)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        invite = serializer.save()
        return Response(Serializers.invite(invite, many=False).data)

    def get_throttles(self):
        if self.action in ["invite"]:
            self.throttle_scope = "invite"
        return super().get_throttles()


@route
class PasswordReset(viewsets.ViewSet):
    ref_tag = "password_reset"
    serializer_class = Serializers.start_password_reset
    queryset = models.PasswordReset.objects.all()

    @action(detail=False, methods=["POST"], permission_classes=[AllowAny])
    @reversion.create_revision()
    def start(self, request):
        serializer = Serializers.start_password_reset(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        password_reset = serializer.save()
        return Response(
            Serializers.start_password_reset(password_reset, many=False).data
        )

    @action(detail=False, methods=["POST"], permission_classes=[AllowAny])
    @reversion.create_revision()
    def complete(self, request):
        serializer = Serializers.password_reset(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        password_reset = serializer.save()
        messages.info(request, _("Password has been updated"))
        return Response(Serializers.password_reset(password_reset, many=False).data)

    def get_throttles(self):
        if self.action in ["start"]:
            self.throttle_scope = "password_reset"
        return super().get_throttles()
