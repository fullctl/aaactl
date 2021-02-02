from django.conf import settings
from django_grainy.helpers import int_flags


def sync_peeringdb(backend, details, response, uid, user, *args, **kwargs):

    if backend.name != "peeringdb":
        return

    social = kwargs.get("social") or backend.strategy.storage.user.get_social_auth(
        backend.name, uid
    )

    if social:

        namespaces = []

        for network in social.extra_data.get("networks", []):
            asn = network["asn"]
            perms = network["perms"]
            namespace = f"verified.asn.{asn}.peeringdb"
            user.grainy_permissions.add_permission(namespace, perms)
            namespaces.append(namespace)

        # delete old

        user.grainy_permissions.filter(
            namespace__regex=r"^verified\.asn\.\d+\.peeringdb$"
        ).exclude(namespace__in=namespaces).delete()
