import social_core.pipeline.user

from account.models import UserPermissionOverride, UserSettings


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
            overrides = []
            override = UserPermissionOverride.objects.create(
                namespace=namespace,
                org=None,
                user=user,
                permissions=perms,
            )
            overrides.append(override)
            user = override.user
            namespaces.append(namespace)

        # delete old
        for override in overrides:
            override.delete()


def auto_confirm_email(backend, details, response, uid, user, *args, **kwargs):

    if user.email and user.email == details.get("email"):
        user_settings, _ = UserSettings.objects.get_or_create(user=user)
        user_settings.email_confirmed = True
        user_settings.save()
