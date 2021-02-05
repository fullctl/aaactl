import reversion
from django.contrib import messages
from django.utils.translation import gettext as _
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
    def set_password(self, request):
        serializer = Serializers.pwd(
            data=request.data,
            many=False,
            context={"user": request.user, "request": request},
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=["POST"])
    @user_endpoint()
    def resend_confirmation_mail(self, request):

        usercfg, created = models.UserSettings.objects.get_or_create(user=request.user)

        if usercfg.email_confirmed:
            return Response(
                {"non_field_errors": [_("Email address already confirmed")]}, status=400
            )

        models.EmailConfirmation.start(request.user)

        return Response({})

    @action(detail=False)
    @user_endpoint()
    @disable_api_key
    def api_keys(self, request):
        user = request.user
        queryset = models.APIKey.objects.filter(user__id=user.id)
        serializer = Serializers.key(queryset, many=True)
        return Response(serializer.data)

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

    @user_endpoint()
    def create(self, request):
        serializer = Serializers.org(
            data=request.data, many=False, context={"user": request.user}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        org = serializer.save()
        if not hasattr(request, "api_key"):
            set_selected_org(request, org)
        return Response(
            Serializers.org(org, many=False, context={"user": request.user}).data
        )

    @set_org
    @grainy_endpoint("org.{org.id}.manage", explicit=False)
    def update(self, request, pk, org):
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
        return Response(
            Serializers.org(org, many=False, context={"user": request.user}).data
        )

    @action(detail=True, methods=["GET"])
    @set_org
    @grainy_endpoint("org.{org.id}.users", explicit=False)
    def users(self, request, pk, org):
        serializer = Serializers.orguser(
            org.user_set.all(),
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
    @grainy_endpoint("org.{org.id}.users", explicit=False)
    def user(self, request, pk, org):
        orguser = models.OrganizationUser.objects.get(
            id=request.data.get("id"), org=org
        )
        if orguser.user == request.user:
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

        org.remove_user(orguser.user)
        return Response(Serializers.orguser(instance=orguser, many=False).data)

    @action(detail=True, methods=["PUT"])
    @set_org
    @grainy_endpoint("org.{org.id}.users", explicit=False)
    def set_permissions(self, request, pk, org):
        serializer = Serializers.orguserperm(
            data={
                "org": org.id,
                "orguser": request.data.get("id"),
                "component": request.data.get("component"),
                "permissions": request.data.get("permissions"),
            },
            many=False,
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=["GET"])
    @set_org
    @grainy_endpoint("org.{org.id}.users", explicit=False)
    def invites(self, request, pk, org):
        invitations = models.Invitation.objects.filter(org__slug=pk)
        serializer = Serializers.inv(invitations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["POST"])
    @set_org
    @grainy_endpoint("org.{org.id}.users", explicit=False)
    def invite(self, request, pk, org):
        context = {"user": request.user, "org": org}
        serializer = Serializers.inv(data=request.data, many=False, context=context)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        inv = serializer.save()
        return Response(Serializers.inv(inv, many=False).data)

    def get_throttles(self):
        if self.action in ["invite"]:
            self.throttle_scope = "invite"
        return super().get_throttles()


@route
class PasswordReset(viewsets.ViewSet):
    ref_tag = "pwdrst"
    serializer_class = Serializers.start_pwdrst
    queryset = models.PasswordReset.objects.all()

    @action(detail=False, methods=["POST"], permission_classes=[AllowAny])
    @reversion.create_revision()
    def start(self, request):
        serializer = Serializers.start_pwdrst(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        pwdrst = serializer.save()
        return Response(Serializers.start_pwdrst(pwdrst, many=False).data)

    @action(detail=False, methods=["POST"], permission_classes=[AllowAny])
    @reversion.create_revision()
    def complete(self, request):
        serializer = Serializers.pwdrst(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        pwdrst = serializer.save()
        messages.info(request, _("Password has been updated"))
        return Response(Serializers.pwdrst(pwdrst, many=False).data)

    def get_throttles(self):
        if self.action in ["start"]:
            self.throttle_scope = "password_reset"
        return super().get_throttles()
