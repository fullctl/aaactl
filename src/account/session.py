def set_selected_org(request, org=None, raise_on_denial=False):
    if not request.user.is_authenticated:
        return

    if org:
        if not request.perms.check(org, "r", explicit=True):
            org = None
            if raise_on_denial:
                raise PermissionError()

    if not org:
        org = request.user.personal_org

    request.session["selected_org"] = org.id

    return org
