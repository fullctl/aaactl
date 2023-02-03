import reversion
from django.db import transaction
from django.utils import timezone
from fullctl.django.management.commands.base import CommandInterface

from billing.models import OrganizationProduct, Subscription


class Command(CommandInterface):
    help = "Progresses billing subscription cycles and product expiry"

    def run(self, *args, **kwargs):
        self.progress_product_expiry()
        self.progress_subscription_cycles()

    def progress_product_expiry(self, *args, **kwargs):
        qset = OrganizationProduct.objects.filter(expires__lt=timezone.now())
        for org_prod in qset:
            self.log_info(f"Expiring {org_prod.product} for {org_prod.org}")
            org_prod.delete()

    def progress_subscription_cycles(self):
        qset = Subscription.objects.filter(status="ok")

        for subscription in qset:
            self.log_info(f"checking subscription {subscription} ...")

            if not subscription.subscription_cycle:
                subscription.start_subscription_cycle()
                self.log_info(
                    f"-- started new billing subscription_cycle: {subscription.subscription_cycle}"
                )

            for subscription_product in subscription.subscription_product_set.all():
                self.collect(subscription_product, subscription.subscription_cycle)

            for subscription_cycle in subscription.subscription_cycle_set.filter(
                status="ok"
            ):
                if not subscription_cycle.ended and subscription.charge_type == "end":
                    continue
                if not subscription.payment_method_id:
                    Subscription.set_payment_method(subscription.org)
                if not subscription.payment_method_id:
                    self.log_info(
                        f"-- no payment method set, unable to charge subscription cycle for org {subscription.org}"
                    )
                    break
                if not subscription_cycle.charged:
                    self.log_info(
                        f"-- charging ${subscription_cycle.price} for subscriptionxcycle: {subscription_cycle}"
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
            self.log_info(f"{org} -> {product}: {usage}")
            subscription_cycle.update_usage(subscription_product, usage)
        except KeyError as exc:
            self.log_error(f"{exc}")
