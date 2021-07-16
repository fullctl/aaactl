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
        parser.add_argument("--commit", action="store_true", help="commit database changes and credit card charges")

    def log(self, msg):
        if not self.commit:
            msg = f"[pretend] {msg}"
        self.stdout.write(f"{msg}")

    @reversion.create_revision()
    def handle(self, *args, **options):
        self.commit = options.get("commit")

        try:
            sid = transaction.savepoint()
            self.progress_cycles()

            if not self.commit:
                raise Rollback()

        except Rollback:
            if sid:
                transaction.savepoint_rollback(sid)
            else:
                transaction.rollback()
            self.log("Ran in non-committal mode, rolling back changes")

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
                    self.log(f"-- charging ${cycle.price} for previous cycle: {cycle}")

                    if not self.commit:
                        continue

                    with reversion.create_revision():
                        cyclechg = cycle.charge()

                    with reversion.create_revision():
                        if cyclechg:
                            cyclechg.chg.sync_status()

    def collect(self, subprod, cycle):

        org = cycle.sub.org

        service = subprod.prod.component
        if not service:
            cycle.update_usage(subprod, None)
            return
        bridge = service.bridge(org)
        product = subprod.prod.name

        try:
            usage = bridge.usage(product)
            self.log(f"{org} -> {product}: {usage}")
            cycle.update_usage(subprod, usage)
        except KeyError as exc:
            self.log(f"{exc}")
