import logging
import datetime

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
import reversion

from billing.models import (
    Product,
    ProductGroup,
    RecurringProduct,
    Subscription,
    SubscriptionCycle,
    SubscriptionCycleProduct,
    PaymentMethod,
)

from billing.payment_processors.paypal import PaypalProcessor


logging.basicConfig(level=logging.INFO)


class Command(BaseCommand):
    help = "Progresses billing cycles"

    def add_arguments(self, parser):
        pass

    def log(self, msg):
        self.stdout.write(f"{msg}")

    @reversion.create_revision()
    def handle(self, *args, **options):
        self.progress_cycles()

    def progress_cycles(self):
        qset = Subscription.objects.filter(status="ok")

        for sub in qset:
            self.log(f"checking subscription {sub} ...")

            if not sub.cycle:
                sub.start_cycle()
                self.log(f"-- started new billing cycle: {sub.cycle}")

            for subprod in sub.subprod_set.all():
                self.collect(subprod, sub.cycle)

            for cycle in sub.cycle_set.filter(status="ok"):
                if not cycle.ended:
                    continue
                if not sub.pay_id:
                    Subscription.set_payment_method(sub.org)
                if not sub.pay_id:
                    self.log(
                        f"-- no payment method set, unable to charge previous cycle for org {sub.org}"
                    )
                    break
                if not cycle.charged:
                    self.log(f"-- charging previous cycle: {cycle}")
                    with reversion.create_revision():
                        cyclechg = cycle.charge()

                    with reversion.create_revision():
                        cyclechg.chg.sync_status()

    def collect(self, subprod, cycle):

        org = cycle.sub.org

        service = subprod.prod.component
        bridge = service.bridge(org)
        product = subprod.prod.name

        try:
            usage = bridge.usage(product)
            self.log(f"{org} -> {product}: {usage}")
            cycle.update_usage(subprod, usage)
        except KeyError as exc:
            self.log(f"{exc}")
