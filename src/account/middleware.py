from django.contrib import messages
from django.utils.translation import gettext as _
from django.shortcuts import redirect
from django.urls import reverse

from django_grainy.util import Permissions
from account.session import set_selected_org
from account.models import Organization


class RequestAugmentation:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def set_selected_org(self, request):

        org_slug = request.GET.get("org")
        if org_slug == "personal":
            set_selected_org(request, request.user.personal_org)
        elif org_slug:
            try:
                org = Organization.objects.get(slug=org_slug)
                set_selected_org(request, org, raise_on_denial=True)
            except Organization.DoesNotExist:
                pass
            except PermissionError:
                messages.error(
                    request,
                    _(
                        "You do not have the permissions to perform this action in {}"
                    ).format(org.label),
                )

        try:
            request.session["selected_org"]
            org = Organization.objects.get(id=request.session["selected_org"])
        except Organization.DoesNotExist:
            org = Organization.personal_org(request.user)
            set_selected_org(request, org)
        except KeyError:
            org = set_selected_org(request)

        if not request.perms.check(org, "r"):
            org = set_selected_org(request)

        request.selected_org = org

    def process_view(self, request, view_func, view_args, view_kwargs):
        request.perms = Permissions(request.user)
        self.set_selected_org(request)
