import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from whitelabel_fullctl.models import OrganizationWhiteLabeling


import account.forms

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

    invitation_form = account.forms.InviteToOrganization(
        initial=request.GET, user=user, org=request.selected_org
    )
    create_org_form = account.forms.CreateOrganization()
    create_org_key_form = account.forms.CreateOrgAPIKey()
    create_key_form = account.forms.CreateAPIKey()
    user_settings_form = account.forms.UserSettings(
        initial={"opt_promotions": user.user_settings.opt_promotions}
    )

    if user.has_usable_password():
        change_pwd_form = account.forms.ChangePassword(user)
    else:
        change_pwd_form = account.forms.ChangePasswordBase()
        env.update(initial_password=True)

    if user.has_usable_password() and not request.selected_org.is_personal:
        edit_org_form = account.forms.EditOrganizationPasswordProtected(
            user,
            request.selected_org,
            initial={
                "name": request.selected_org.name,
                "slug": request.selected_org.slug,
            },
        )
    else:
        edit_org_form = account.forms.EditOrganization(
            request.selected_org,
            initial={
                "name": request.selected_org.name,
                "slug": request.selected_org.slug,
            },
        )

    org_whitelabel = OrganizationWhiteLabeling.objects.filter(
        org__slug=request.selected_org.slug
    ).first()

    if not org_whitelabel:
        org_whitelabel_components = {
            "name": "FullCtl",
            "show_logo": json.dumps(True),
        }
    else:
        css_dict = json.loads(org_whitelabel.css)
        org_whitelabel_components = {
            "name": org_whitelabel.org.name,
            "html_footer": org_whitelabel.html_footer if org_whitelabel.html_footer else json.dumps(org_whitelabel.html_footer),
            "css": {
                "primary_color": css_dict.get("primary_color", json.dumps(None)),
                "logo_width": css_dict.get("logo_width", json.dumps(None))

            },
            "dark_logo_url": org_whitelabel.dark_logo_url if org_whitelabel.dark_logo_url else json.dumps(org_whitelabel.dark_logo_url),
            "light_logo_url": org_whitelabel.light_logo_url if org_whitelabel.light_logo_url else json.dumps(org_whitelabel.light_logo_url),
            "show_logo": json.dumps(org_whitelabel.show_logo),
            "custom_org": json.dumps(True)
        }

    env.update(
        change_user_info_form=form,
        change_pwd_form=change_pwd_form,
        create_org_form=create_org_form,
        edit_org_form=edit_org_form,
        invitation_form=invitation_form,
        create_org_key_form=create_org_key_form,
        create_key_form=create_key_form,
        user_settings_form=user_settings_form,
        can_invite=request.perms.check([request.selected_org, "users"], "c"),
        org_whitelabel=org_whitelabel_components,
    )

    return render(request, "account/controlpanel/index.html", env)
