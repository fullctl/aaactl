from urllib.parse import urlparse

from django.contrib import messages
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import login as fn_login
from django.contrib.auth import logout as fn_logout
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import resolve, reverse
from django.utils.translation import gettext as _
from oauth2_provider.oauth2_backends import get_oauthlib_core

import account.forms
from account.models import EmailConfirmation, Invitation, PasswordReset
from account.session import set_selected_org

# Create your views here.


def valid_redirect(path, fallback):
    if not path:
        return fallback

    parts = urlparse(path)

    try:
        resolve(parts.path)
    except Http404:
        return fallback

    return path


def login(request):

    env = {}

    if request.user.is_authenticated:
        messages.info(request, _("Already logged in"))
        return redirect(reverse("account:controlpanel"))

    if request.method == "POST":
        form = account.forms.Login(data=request.POST)
        redirect_next = valid_redirect(
            request.POST.get("next"), reverse("account:controlpanel")
        )
        print("redirecting", redirect_next)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )

            if user is not None:
                fn_login(request, user)

                # redirect_next is alraedy cleaned and validated
                # through valid_redirect at this point
                return redirect(redirect_next)  # lgtm[py/url-redirection]
            else:
                messages.error(request, _("Login failed: Wrong username / password"))

    else:
        form = account.forms.Login()

    env.update(login_form=form, password_login_enabled=settings.PASSWORD_LOGIN_ENABLED)

    return render(request, "account/auth/login.html", env)


def logout(request):
    fn_logout(request)

    return redirect(reverse("account:auth-login"))


def register(request):

    env = {}

    if request.method == "POST":
        form = account.forms.RegisterUser(data=request.POST)
        if form.is_valid():
            try:
                del form.cleaned_data["password_confirmation"]
                del form.cleaned_data["captcha"]
                user = get_user_model().objects.create_user(**form.cleaned_data)
                fn_login(request, user, backend="django_grainy.backends.GrainyBackend")
                redirect_next = valid_redirect(
                    request.POST.get("next"), reverse("account:controlpanel")
                )

                return redirect(redirect_next)
            except Exception as exc:
                messages.error(request, _("Registration error: {}").format(exc))

    else:
        form = account.forms.RegisterUser()

    env.update(register_form=form, password_login_enabled=settings.PASSWORD_LOGIN_ENABLED)

    return render(request, "account/auth/register.html", env)


def start_reset_password(request):
    form = account.forms.StartPasswordReset()
    env = {"form": form}
    return render(request, "account/auth/reset-password.html", env)


def reset_password(request, secret):
    try:
        pwdrst = PasswordReset.objects.get(secret=secret)
    except PasswordReset.DoesNotExist:
        messages.error(_("Password reset session not found"))
        return redirect("/")

    form = account.forms.PasswordReset(initial={"secret": secret})
    env = {"pwdrst": pwdrst, "form": form}

    return render(request, "account/auth/reset-password.html", env)


@login_required
def accept_invite(request, secret):
    try:
        inv = Invitation.objects.get(secret=secret)
    except Invitation.DoesNotExist:
        messages.error(request, _("Invitation not found"))
        return redirect("/")

    if inv.expired:
        messages.error(request, _("The invite has expired"))
        return redirect("/")

    inv.complete(request.user)
    messages.info(request, _("You have joined {}").format(inv.org.label))

    set_selected_org(request, inv.org)

    if inv.service:
        return redirect(inv.service.invite_redirect.format(org=inv.org))
    else:
        return redirect("/")


@login_required
def confirm_email(request, secret):
    try:
        emconf = EmailConfirmation.objects.get(secret=secret)
    except EmailConfirmation.DoesNotExist:
        messages.error(request, _("Email confirmation process not found"))
        return redirect("/")

    if emconf.email != request.user.email:
        messages.error(
            request,
            _(
                "The email of the user currenty logged in does not match the email linked to the email confirmation process"
            ),
        )
        return redirect("/")

    emconf.complete()
    messages.success(request, _("Email address confirmed!"))

    return redirect("/")


oauth_profile_scopes = ["profile", "api_keys", "provider:peeringdb"]


# @protected_resource(scopes=oauth_profile_scopes)
def oauth_profile(request):

    from account.rest.serializers import Serializers

    user = request.user

    oauth = get_oauthlib_core()

    oauth_email, _ = oauth.verify_request(request, scopes=["email"])
    oauth_api_keys, _ = oauth.verify_request(request, scopes=["api_keys"])

    oauth_provider_passthru = []

    for social_auth in user.social_auth.all():
        key = f"provider:{social_auth.provider}"
        verify, _ = oauth.verify_request(request, scopes=[key])
        if verify:
            oauth_provider_passthru.append(social_auth)

    json_params = {}

    if "pretty" in request.GET:
        json_params.update(indent=2)

    data = dict(
        id=user.id,
        user_name=user.username,
        given_name=user.first_name,
        family_name=user.last_name,
        is_superuser=user.is_superuser,
        is_staff=user.is_staff,
        name=f"{user.first_name} {user.last_name}",
        # TODO: dont assume oauth implies verification
        verified_user=True,
        organizations=[
            Serializers.org(instance=org.org, context={"user": user}).data
            for org in user.orguser_set.all()
        ],
    )

    print(data)

    if oauth_email:
        data.update(dict(email=user.email))

    for social_auth in oauth_provider_passthru:
        provider = social_auth.provider
        data[provider] = social_auth.extra_data
        if "access_token" in data[provider]:
            del data[provider]["access_token"]
        if "token_type" in data[provider]:
            del data[provider]["token_type"]

    return JsonResponse(data, json_dumps_params=json_params)
