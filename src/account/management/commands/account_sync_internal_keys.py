from django.core.management.base import BaseCommand

from account.models import APIKey


class Command(BaseCommand):
    help = "Syncs permissions from settings to all internal api keys"

    def handle(self, *args, **kwargs):

        updated = APIKey.sync_internal_perms()
        for key in updated:
            self.stdout.write("Updated key {}...".format(key.key[:6]))

        if not updated:
            self.stdout.write("No keys needed to be updated")
