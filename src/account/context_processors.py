from django.conf import settings


def permissions(request):
    context = {}

    try:
        instances = [request.selected_org]
    except AttributeError:
        return {"permissions": context}
    ops = [("c", "create"), ("r", "read"), ("u", "update"), ("d", "delete")]

    for instance in instances:
        if not instance:
            continue
        for namespace in instance.permission_namespaces:
            for op, name in ops:
                key = "{}_{}_{}".format(
                    name,
                    instance.HandleRef.tag,
                    namespace.replace(".{org_id}", "").replace(".", "__"),
                )
                context[key] = request.perms.check(
                    namespace.format(org_id=instance.id), op, ignore_grant_all=True
                )

    return {"permissions": context}


def info(request):
    return {
        "billing_env": settings.BILLING_ENV,
        "release_env": settings.RELEASE_ENV,
        "version": settings.PACKAGE_VERSION,
        "server_email": settings.SERVER_EMAIL,
        "google_analytics_id": settings.GOOGLE_ANALYTICS_ID,
        "cloudflare_analytics_id": settings.CLOUDFLARE_ANALYTICS_ID,
        "enable_email_confirmation": settings.ENABLE_EMAIL_CONFIRMATION,
    }
