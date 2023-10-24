import reversion
from django.utils import timezone
from fullctl.django.management.commands.base import CommandInterface

from billing.payment_processors.processor import InternalProcessorError
from billing.models import Invoice, OrganizationProduct, Subscription


def catch_internal_processor_error(fn):
    """
    decorator to catch internal processor errors and log them
    """

    def wrapper(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        except InternalProcessorError as exc:
            self.log_error(f"\n\n---- INTERNAL PROCESSING ERROR\n\n{exc}\n\n----\n\n")

    return wrapper

class Command(CommandInterface):
    help = "Progresses billing subscription cycles and product expiry"

    def run(self, *args, **kwargs):
        self.progress_product_expiry()
        self.progress_subscription_cycles()
        self.sync_open_invoices()

    def progress_product_expiry(self, *args, **kwargs):
        qset = OrganizationProduct.objects.filter(expires__lt=timezone.now())
        for org_prod in qset:
            self.log_info(f"Expiring {org_prod.product} for {org_prod.org}")
            if org_prod.product.expiry_replacement_product_id:
                replacement_product = org_prod.product.expiry_replacement_product
            else:
                replacement_product = None

            org_prod.delete()

            if replacement_product and replacement_product.can_add_to_org(org_prod.org):
                self.log_info(
                    f"Replacing expired product with {replacement_product} for {org_prod.org}"
                )
                replacement_product.add_to_org(org_prod.org)

    def progress_subscription_product_expiry(self, subscription):
        qset = subscription.subscription_product_set.filter(expires__lt=timezone.now())
        for subscription_product in qset:
            self.log_info(
                f"Expiring {subscription_product.product} from subscription {subscription}"
            )
            if subscription_product.product.expiry_replacement_product_id:
                replacement_product = (
                    subscription_product.product.expiry_replacement_product
                )
                if replacement_product and replacement_product.can_add_to_org(
                    subscription.org
                ):
                    self.log_info(
                        f"Replacing expired product with {replacement_product} in subscription {subscription}"
                    )
                    replacement_product.add_to_org(subscription.org)

    @catch_internal_processor_error
    def progress_subscription_cycles(self):
        qset = Subscription.objects.filter(status="ok")

        for subscription in qset:
            self.log_info(
                f"checking subscription {subscription} ({subscription.id}) ..."
            )

            if not subscription.subscription_cycle:
                subscription.start_subscription_cycle()
                self.log_info(
                    f"-- started new billing subscription_cycle: {subscription.subscription_cycle}"
                )
            else:
                self.log_info(
                    f"-- subscription_cycle: {subscription.subscription_cycle}"
                )

            for subscription_product in subscription.subscription_product_set.all():
                self.collect(subscription_product, subscription.subscription_cycle)

            for subscription_cycle in subscription.subscription_cycle_set.filter(
                status__in=["open", "failed"]
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
                    if subscription_cycle.status == "failed":
                        # we are retrying a failed subscription cycle charge

                        self.log_info("-- retrying failed subscription cycle charge")

                    self.log_info(
                        f"-- charging ${subscription_cycle.price} for subscription cycle: {subscription_cycle}"
                    )

                    with reversion.create_revision():
                        subscription_cycle_charge = subscription_cycle.charge(
                            commit=self.commit
                        )

                    with reversion.create_revision():
                        if subscription_cycle_charge:
                            subscription_cycle_charge.payment_charge.sync_status(
                                commit=self.commit
                            )

            for subscription_cycle in subscription.subscription_cycle_set.filter(
                subscription_cycle_charge_set__payment_charge__status__in=["pending"]
            ).distinct("id"):
                subscription_cycle_charges = subscription_cycle.subscription_cycle_charge_set.filter(
                    payment_charge__status="pending"
                )
                for subscription_cycle_charge in subscription_cycle_charges:
                    self.log_info(
                        f"-- syncing pending subscription cycle charge: {subscription_cycle_charge}"
                    )
                    subscription_cycle_charge.payment_charge.sync_status(
                        commit=self.commit
                    )

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

    def sync_open_invoices(self):
        qset = Invoice.objects.filter(status="pending").order_by("created")

        for invoice in qset:
            if not invoice.data.get("stripe_invoice"):
                continue

            self.log_info(f"syncing open invoice {invoice}")
            invoice.sync_status(commit=self.commit)
