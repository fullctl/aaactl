import reversion
from django.core.management.base import BaseCommand
from django.db import transaction

from billing.models import Subscription


class Rollback(Exception):
    pass


# FIXME: use fullctl.django base command
class Command(BaseCommand):
    help = "Progresses billing cycles"

    def add_arguments(self, parser):
        parser.add_argument(
            "--commit",
            action="store_true",
            help="commit database changes and credit card charges",
        )

    def log(self, msg):
        if not self.commit:
            msg = f"[pretend] {msg}"
        self.stdout.write(f"{msg}")

    @reversion.create_revision()
    def handle(self, *args, **options):
        self.commit = options.get("commit")

        try:
            sid = transaction.savepoint()
            self.progress_subscription_cycles()

            if not self.commit:
                raise Rollback()

        except Rollback:
            if sid:
                transaction.savepoint_rollback(sid)
            else:
                transaction.rollback()
            self.log("Ran in non-committal mode, rolling back changes")

    def progress_subscription_cycles(self):
        qset = Subscription.objects.filter(status="ok")

        for subscription in qset:
            self.log(f"checking subscription {subscription} ...")

            if not subscription.subscription_cycle:
                subscription.start_subscription_cycle()
                self.log(
                    f"-- started new billing subscription_cycle: {subscription.subscription_cycle}"
                )

            for subscription_product in subscription.subproduct_set.all():
                self.collect(subscription_product, subscription.subscription_cycle)

            for subscription_cycle in subscription.cycle_set.filter(status="ok"):
                if not subscription_cycle.ended:
                    continue
                if not subscription.pay_id:
                    Subscription.set_payment_method(subscription.org)
                if not subscription.pay_id:
                    self.log(
                        f"-- no payment method set, unable to charge previous subscription_cycle for org {subscription.org}"
                    )
                    break
                if not subscription_cycle.charged:
                    self.log(
                        f"-- charging ${subscription_cycle.price} for previous subscription_cycle: {subscription_cycle}"
                    )

                    if not self.commit:
                        continue

                    with reversion.create_revision():
                        subscription_cycle_charge = subscription_cycle.charge()

                    with reversion.create_revision():
                        if subscription_cycle_charge:
                            subscription_cycle_charge.payment_charge.sync_status()

    def collect(self, subscription_product, subscription_cycle):

        org = subscription_cycle.subscription.org

        service = subscription_product.product.component
        if not service:
            subscription_cycle.update_usage(subscription_product, None)
            return
        bridge = service.bridge(org)
        product = subscription_product.product.name

        try:
            usage = bridge.usage(product)
            self.log(f"{org} -> {product}: {usage}")
            subscription_cycle.update_usage(subscription_product, usage)
        except KeyError as exc:
            self.log(f"{exc}")
