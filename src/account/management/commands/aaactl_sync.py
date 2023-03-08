from django.contrib.auth import get_user_model
from fullctl.django.management.commands.base import CommandInterface

from account.models import Organization
from applications.models import Service
from applications.service_bridge import Bridge


class Command(CommandInterface):

    """
    Sync user and organization information to connected
    service applications
    """

    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument("type", type=str, choices=("org", "user", "org_user"))
        parser.add_argument("id", type=int)

    def run(self, *args, **kwargs):
        typ = kwargs.get("type")
        pk = kwargs.get("id")

        for svc in Service.objects.filter(status="ok"):
            if not svc.api_url:
                self.log_info(f"No api url specified for {svc.name}, skipping ..")
                continue

            self.log_info(f"Syncing {typ} {pk} to {svc.name}")
            fn = getattr(self, f"sync_{typ}")

            if self.commit:
                try:
                    fn(svc, pk)
                except Exception as e:
                    self.log_error(f"Error syncing {typ} {pk} to {svc.name}: {e}")
                    self.stdout.write(f"Error syncing {typ} {pk} to {svc.name}: {e}")
                    continue

    def sync_org(self, svc, pk):
        org = Organization.objects.get(pk=pk)
        bridge = Bridge(svc, org)
        bridge.sync_org()

    def sync_user(self, svc, pk):
        user = get_user_model().objects.get(pk=pk)
        bridge = Bridge(svc, None, user=user)
        bridge.sync_user()

    def sync_org_user(self, svc, pk):
        user = get_user_model().objects.get(pk=pk)
        bridge = Bridge(svc, None, user=user)
        bridge.sync_org_user()
