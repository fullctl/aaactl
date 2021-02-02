from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

import account.forms
from account.decorators import org_view

# Create your views here.


@login_required
def index(request):
    env = {}
    user = request.user

    form = account.forms.ChangeInformation(
        user,
        initial={
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
        },
    )

    invitation_form = account.forms.InviteToOrganization(initial=request.GET)
    create_org_form = account.forms.CreateOrganization()
    if user.has_usable_password():
        change_pwd_form = account.forms.ChangePassword(user)
        edit_org_form = account.forms.EditOrganizationPasswordProtected(
            user,
            request.selected_org,
            initial={
                "name": request.selected_org.name,
                "slug": request.selected_org.slug,
            },
        )
    else:
        change_pwd_form = account.forms.ChangePasswordBase()
        env.update(initial_password=True)
        edit_org_form = account.forms.EditOrganization(
            request.selected_org,
            initial={
                "name": request.selected_org.name,
                "slug": request.selected_org.slug,
            },
        )
    env.update(
        form=form,
        change_pwd_form=change_pwd_form,
        create_org_form=create_org_form,
        edit_org_form=edit_org_form,
        invitation_form=invitation_form,
        can_invite=request.perms.check([request.selected_org, "users"], "c"),
    )

    return render(request, "account/controlpanel/index.html", env)


@login_required
def change_password(request):

    user = request.user
    env = {}

    if user.has_usable_password():
        form = account.forms.ChangePassword(user)
    else:
        form = account.forms.ChangePasswordBase()
        env.update(initial_password=True)

    env.update(form=form)

    return render(request, "account/controlpanel/change-password.html", env)


@login_required
def change_information(request):
    env = {}
    user = request.user

    if not user.has_usable_password():
        return redirect(
            reverse("account:change-password")
            + "?next={}".format(reverse("account:change-information"))
        )

    form = account.forms.ChangeInformation(
        user,
        initial={
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
        },
    )

    env.update(form=form)

    return render(request, "account/controlpanel/change-information.html", env)


@login_required
def create_organization(request):
    env = {}
    user = request.user

    form_create_org = account.forms.CreateOrganization()
    form_change_user = account.forms.ChangeInformation(user)
    env.update(form=form_change_user, form_create_org=form_create_org)

    return render(request, "account/controlpanel/create-organization.html", env)


@login_required
@require_http_methods(["GET"])
@org_view(["manage"])
def edit_organization(request):
    env = {}
    user = request.user

    form = account.forms.EditOrganization(
        request.selected_org,
        initial={"name": request.selected_org.name, "slug": request.selected_org.slug},
    )

    env.update(form=form)

    return render(request, "account/controlpanel/edit-organization.html", env)


@login_required
@org_view(["users"])
def invite(request):
    env = {}
    user = request.user

    form = account.forms.InviteToOrganization(initial=request.GET)
    env.update(
        form=form, can_invite=request.perms.check([request.selected_org, "users"], "c")
    )
    return render(request, "account/controlpanel/invite.html", env)


@login_required
@org_view(["users"])
def users(request):
    env = {}
    form = account.forms.ChangeInformation(None)
    env.update(form=form)
    return render(request, "account/controlpanel/users.html", env)


@login_required
def social(request):
    env = {}
    return render(request, "account/controlpanel/social.html", env)


@login_required
def api_keys(request):
    env = {}
    return render(request, "account/controlpanel/api-keys.html", env)
