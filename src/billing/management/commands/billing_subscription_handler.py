import logging

import reversion
from django.core.management.base import BaseCommand

from billing.models import Subscription, SubscriptionCycleProduct  # PaymentMethod,

logging.basicConfig(level=logging.INFO)


class Command(BaseCommand):
    help = "Charge and process due subscription payments"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        # pay = PaymentMethod.objects.get(id=1)
        sub = Subscription.objects.get(id=1)

        SubscriptionCycleProduct.objects.get_or_create(
            cycle=sub.cycle, subprod=sub.subprod_set.first(), usage=1
        )

        with reversion.create_revision():
            cyclechg = sub.cycle.charge()

        with reversion.create_revision():
            cyclechg.chg.sync_status()
