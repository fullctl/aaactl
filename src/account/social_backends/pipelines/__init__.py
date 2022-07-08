import social_core.pipeline.user

from account.models import UserSettings


def get_username(strategy, details, backend, user=None, *args, **kwargs):

    if "username" in details:
        details["username"] = details["username"].lower()

    return social_core.pipeline.user.get_username(
        strategy, details, backend, user=user, *args, **kwargs
    )


def sync_peeringdb(backend, details, response, uid, user, *args, **kwargs):

    if backend.name != "peeringdb":
        return

    social = kwargs.get("social") or backend.strategy.storage.user.get_social_auth(
        backend.name, uid
    )

    if social:

        namespaces = []

        social.extra_data["email"] = details["email"]
        social.save()
        networks = social.extra_data.get("networks") or []

        for network in networks:
            asn = network["asn"]
            perms = network["perms"]
            namespace = f"verified.asn.{asn}.peeringdb"
            user.grainy_permissions.add_permission(namespace, perms)
            namespaces.append(namespace)

        # delete old

        user.grainy_permissions.filter(
            namespace__regex=r"^verified\.asn\.\d+\.peeringdb$"
        ).exclude(namespace__in=namespaces).delete()


def auto_confirm_email(backend, details, response, uid, user, *args, **kwargs):

    if user.email and user.email == details.get("email"):
        usercfg, _ = UserSettings.objects.get_or_create(user=user)
        usercfg.email_confirmed = True
        usercfg.save()
