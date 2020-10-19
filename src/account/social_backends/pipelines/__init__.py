from django_grainy.helpers import int_flags
from django.conf import settings

def sync_peeringdb(backend, details, response, uid, user, *args, **kwargs):

    if backend.name  != "peeringdb":
        return

    social = kwargs.get("social") or backend.strategy.storage.user.get_social_auth(
        backend.name, uid
    )

    if social:
        # TODO: remove old permissions
        for network in social.extra_data.get("networks", []):
            asn = network["asn"]
            perms = network["perms"]
            user.grainy_permissions.add_permission(f"verified.asn.{asn}.peeringdb", perms)





