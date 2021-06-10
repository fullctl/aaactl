import datetime
import secrets
import uuid

import dateutil.relativedelta
import reversion
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _
from django_countries.fields import CountryField
from django_grainy.decorators import grainy_model

import account.models
import applications.models
import billing.const as const
import billing.payment_processors
import billing.product_handlers
from common.models import HandleRefModel

# Create your models here.


@reversion.register()
class ProductGroup(HandleRefModel):

    """
    Describes a container for a set of products (cyclic or one-time purchases)

    This allows the grouping of products for billing purposes, which can be useful if you want.

    An example here would be "Fullctl" as a product group for all it's underlying
    products/services (ixctl, prefixctl etc.)
    """

    name = models.CharField(max_length=255)
    subscription_cycle_anchor = models.DateField(
        null=True,
        blank=True,
        help_text=_(
            "If specified, sets a day of the month to be used as the anchor point for subscription cycles"
        ),
    )

    class HandleRef:
        tag = "prodgrp"


    class Meta:
        db_table = "billing_product_group"
        verbose_name = _("Product Group")
        verbose_name_plural = _("Product Groups")

    def __str__(self):
        return self.name


@reversion.register()
class Product(HandleRefModel):

    """
    Describes a product or service.
    """

    # example: fullctl.prefixctl.prefixes
    name = models.CharField(
        max_length=255, help_text=_("Internal product name"), unique=True
    )

    component = models.ForeignKey(
        applications.models.Service,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_("Product belongs to component"),
    )

    # example: actively monitored prefixes
    description = models.CharField(
        max_length=255,
        help_text=_("Description of the product or service being billed"),
    )

    group = models.ForeignKey(
        ProductGroup,
        related_name="prod_set",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=_("Allows you to group products together for billing purposes"),
    )

    price = models.DecimalField(
        default=0.00,
        max_digits=6,
        decimal_places=2,
        help_text=_(
            "Price charge on initial setup / purchase. For recurring pricing this could specify a setup fee. For non-recurring pricing, this is the product price."
        ),
    )

    data = JSONField(
        help_text=_("Arbitrary extra data you want to define for this product"),
        blank=True,
        default=dict,
    )

    class HandleRef:
        tag = "prod"

    class Meta:
        db_table = "billing_product"
        verbose_name = _("Product")
        verbose_name_plural = _("Products")


    @property
    def is_recurring(self):
        return hasattr(self, "recurring") and bool(self.recurring.id)

    def __str__(self):
        return f"{self.name}({self.id})"

    def create_transactions(self, user):
        order_number = "ORDER_" + unique_order_id()
        self._create_order(user, order_number)

        invoice_number = "INVOICE_" + unique_invoice_id()
        self._create_invoice(user, invoice_number)
        self._create_payment(user, invoice_number)

    def _create_order(self, user, order_number):
        order = Order.objects.create(
            user=user,
            amount=self.price,
            product=self,
            description=self.description,
            order_number=order_number,
        )
        return order

    def _create_invoice(self, user, invoice_number):
        invoice = Invoice.objects.create(
            # Not sure how we want to access this
            user=user,
            amount=self.price,
            product=self,
            description=self.description,
            invoice_number=invoice_number,
        )
        return invoice

    def _create_payment(self, user, invoice_number):
        payment = Payment.objects.create(
            user=user,
            amount=self.price,
            # billing_contact=None,
            # payment_method=None,
            invoice_number=invoice_number,
        )
        return payment


@reversion.register()
class RecurringProduct(HandleRefModel):

    """
    Describes a product that can be subscribed to

    Currently supports metered or fixed pricing.
    """

    # product information
    prod = models.OneToOneField(
        Product, on_delete=models.CASCADE, related_name="recurring"
    )

    # metered or fixed
    type = models.CharField(
        max_length=255,
        choices=const.BILLING_PRODUCT_RECURRING_TYPES,
        default=None,
        null=True,
    )

    price = models.DecimalField(
        default=0.00,
        max_digits=6,
        decimal_places=2,
        help_text=_(
            "Price in the context of recurring charges. For fixed recurring pricing this would be the price charged each cycle. For metered pricing this would be the usage price per metered unit."
        ),
    )

    unit = models.CharField(
        max_length=32,
        default="Unit",
        help_text=_("Label for a unit in the context of usage"),
    )

    unit_plural = models.CharField(
        max_length=40,
        default="Units",
        help_text=_("Label for multiple units in the context of usage"),
    )

    metered_url = models.URLField(
        null=True,
        blank=True,
        help_text=_(
            "For metered charges, specify the url that is used to retrieve the current metered value"
        ),
    )

    data = JSONField(
        help_text=_(
            "Arbitrary extra data you want to define for this recurring product"
        ),
        blank=True,
        default=dict,
    )

    class Meta:
        db_table = "billing_recurring_product"
        verbose_name = _("Recurring Product Settings")
        verbose_name_plural = _("Recurring Product Settings")
        # FIXME: why is this weird on postgres
        # unique_together = ["prod", "cycle"]

    class HandleRef:
        tag = "recurring"

    @property
    def name(self):
        return f"{self.prod.name}.recurring"

    @property
    def type_description(self):
        if self.type == "metered":
            return _("Metered Usage")
        elif self.type == "fixed":
            return _("Fixed Price")
        else:
            return _("Subscription")

    def __str__(self):
        return f"{self.name}({self.id})"


@reversion.register()
class ProductModifier(HandleRefModel):

    """
    Describes a price modification template for a product

    It will be used to apply a price modification to a subscription
    of the same product
    """

    prod = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="modifier_set"
    )
    type = models.CharField(max_length=255, choices=const.BILLING_MODIFIER_TYPES)
    value = models.PositiveIntegerField(default=0)
    duration = models.IntegerField(default=0, help_text=_("Duration in days"))
    code = models.CharField(
        max_length=255, null=True, blank=True, help_text=_("activation code")
    )

    class HandleRef:
        tag = "prodmod"

    class Meta:
        db_table = "billing_product_modifier"
        verbose_name = _("Product Price Modifier")
        verbose_name_plural = _("Product Price Modifiers")


@reversion.register()
@grainy_model("billing.services", realted="org")
class Subscription(HandleRefModel):

    """
    Describes an organization's subscription to a product group
    """

    org = models.ForeignKey(
        account.models.Organization, on_delete=models.CASCADE, related_name="sub_set"
    )

    group = models.ForeignKey(
        ProductGroup, related_name="sub_set", on_delete=models.CASCADE
    )

    cycle_interval = models.CharField(
        max_length=255, choices=const.BILLING_CYCLE_CHOICES, default="month"
    )
    cycle_start = models.DateTimeField(
        help_text=_("Start of billing cycle"), blank=True, null=True
    )
    cycle_frequency = models.PositiveIntegerField(default=1)

    pay = models.ForeignKey(
        "billing.PaymentMethod",
        on_delete=models.SET_NULL,
        null=True,
        related_name="sub_set",
        help_text=_("User payment option that will be charged by this sub"),
    )

    data = JSONField(
        default=dict, blank=True, help_text=_("Any extra data for the subscription")
    )

    class HandleRef:
        tag = "sub"

    class Meta:
        db_table = "billing_subscription"
        verbose_name = _("Subscription")
        verbose_name_plural = _("Subscriptions")

    @classmethod
    def get_or_create(cls, org, group, cycle="month"):

        sub, created_sub = cls.objects.get_or_create(
            org=org, group=group, cycle_interval=cycle
        )

        return sub

    @classmethod
    def set_payment_method(cls, org, pay=None, replace=None):
        if not pay:
            pay = PaymentMethod.get_for_org(org).first()

        qset = org.sub_set
        if replace:
            qset = qset.filter(pay=replace)

        if pay:
            qset.update(pay=pay)

    @property
    def cycle(self):
        return self.get_cycle(datetime.date.today())

    @property
    def charge_description(self):
        return f"{self.group.name} Service Charges"

    def __str__(self):
        return f"{self.group.name} : {self.org.name}"

    def get_cycle(self, date):
        return self.cycle_set.filter(start__lte=date, end__gte=date).first()

    @reversion.create_revision()
    def add_prod(self, prod):
        subprod, _ = SubscriptionProduct.objects.get_or_create(
            sub=self, prod=prod
        )
        return subprod

    @reversion.create_revision()
    def end_cycle(self):
        """
        end current subscription cycle prematurely
        """

        if not self.cycle:
            return
        self.cycle.end = datetime.date.today()
        self.cycle.save()
        self.cycle.charge()
        self.start_cycle()

    def start_cycle(self, start=None, force=False):
        if not start:
            start = datetime.date.today()

        cycle_anchor = self.group.subscription_cycle_anchor

        if self.cycle_interval == "month":
            if cycle_anchor:
                start = start.replace(day=cycle_anchor.day)
            end = start + dateutil.relativedelta.relativedelta(months=1)

        elif self.cycle_interval == "year":
            end = start + dateutil.relativedelta.relativedelta(years=1)

        if self.cycle:
            if not force:
                raise OSError(
                    _(
                        "Currently have an active cycle, pass `force` = True to end and start a new one"
                    )
                )
            else:
                self.end_cycle()

        if not self.cycle_start:
            self.cycle_start = start
            self.save()

        return SubscriptionCycle.objects.create(sub=self, start=start, end=end)


@reversion.register()
class SubscriptionProduct(HandleRefModel):

    """
    Links a product to a subscription
    """

    sub = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name="subprod_set"
    )

    prod = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sub_set")

    data = JSONField(
        default=dict,
        blank=True,
        help_text=_("Any extra data for the subscription item"),
    )

    class HandleRef:
        tag = "subprod"

    class Meta:
        db_table = "billing_subscription_product"
        verbose_name = _("Subscription Product")
        verbose_name_plural = _("Subscription Products")

    @property
    def cycle_cost(self):
        cycle = self.sub.cycle
        if not cycle:
            return 0
        try:
            cycleprod = cycle.cycleprod_set.get(subprod=self)
            return cycleprod.price
        except SubscriptionCycleProduct.DoesNotExist:
            return 0

    @property
    def cycle_usage(self):
        cycle = self.sub.cycle
        if not cycle:
            return 0
        try:
            cycleprod = cycle.cycleprod_set.get(subprod=self)
            return cycleprod.usage
        except SubscriptionCycleProduct.DoesNotExist:
            return 0

    def __str__(self):
        return f"{self.sub} - {self.prod.name}"


@reversion.register()
class SubscriptionCycle(HandleRefModel):

    """
    Describes a billing cycle for a subscription with a specified
    start and end date.

    Once the end date is reached, the cycle will be billed.
    """

    sub = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name="cycle_set"
    )

    start = models.DateField()
    end = models.DateField()

    class Meta:
        db_table = "billing_subscription_cycle"
        verbose_name = _("Subscription Cycle")
        verbose_name_plural = _("Subscription Cycles")

    class HandleRef:
        tag = "cycle"

    @property
    def price(self):

        """
        The current total of the cycle
        """

        price = 0
        for charge in self.cycleprod_set.all():
            price += float(charge.price)
        return price

    @property
    def ended(self):
        """
        Has this cycle ended?
        """

        return self.end < datetime.date.today()

    @property
    def charged(self):
        """
        Has this cycle been charged already ?
        """

        return self.cyclechg_set.filter(chg__status="ok").exists()

    def __str__(self):
        return f"{self.sub} {self.start} - {self.end}"

    def update_usage(self, subprod, usage):

        """
        Set the usage for a subscription product in this cycle
        """

        cycleprod, created = SubscriptionCycleProduct.objects.get_or_create(
            cycle=self,
            subprod=subprod,
        )

        cycleprod.usage = usage
        cycleprod.save()

    def charge(self):

        """
        Charge the cost of the cycle to the customer's payment method
        """

        if self.charged:
            raise OSError("Cycle was already charged successfully")

        self.status = "expired"
        self.save()

        if not self.price:
            return

        pending_chg = self.cyclechg_set.filter(chg__status="pending").first()
        if pending_chg:
            return pending_chg

        chg = PaymentCharge.objects.create(
            pay=self.sub.pay, price=self.price, description=self.sub.charge_description
        )
        self.sub.pay.processor_instance.charge(chg)

        return SubscriptionCycleCharge.objects.create(
            cycle=self, chg=chg, status="pending"
        )

    def create_transactions(self, user):
        order_number = "ORDER_" + unique_order_id()
        self._create_orders(user, order_number)

        invoice_number = "INVOICE_" + unique_invoice_id()
        self._create_invoices(user, invoice_number)
        self._create_payment(user, invoice_number)

    def _create_orders(self, user, order_number):
        for subprod in self.sub.subprod_set.all():
            Order.objects.create(
                user=user,
                amount=self.price,
                subscription=self.sub,
                product=subprod.prod,
                description=self.sub.charge_description,
                order_number=order_number,
            )

    def _create_invoices(self, user, invoice_number):
        for subprod in self.sub.subprod_set.all():
            Invoice.objects.create(
                # Not sure how we want to access this
                user=user,
                amount=self.price,
                subscription=self.sub,
                product=subprod.prod,
                description=self.sub.charge_description,
                invoice_number=invoice_number,
            )

    def _create_payment(self, user, invoice_number):
        payment = Payment.objects.create(
            user=user,
            amount=self.price,
            billing_contact=self.sub.pay.billcon,
            payment_method=self.sub.pay,
            invoice_number=invoice_number,
        )
        return payment


@reversion.register()
class SubscriptionCycleCharge(HandleRefModel):

    """
    Describes a billing charge made for a subscription cycle
    """

    cycle = models.ForeignKey(
        SubscriptionCycle, on_delete=models.CASCADE, related_name="cyclechg_set"
    )
    chg = models.OneToOneField(
        "billing.PaymentCharge", on_delete=models.CASCADE, related_name="cyclechg"
    )

    class Meta:
        db_table = "billing_subscription_cycle_charge"
        verbose_name = _("Subscription Cycle Charge")
        verbose_name_plural = _("Subscription Cycle Charges")

    class HandleRef:
        tag = "cyclechg"


@reversion.register()
class SubscriptionCycleProduct(HandleRefModel):

    """
    Describes a relationship of a product to a subscription cycle, letting us
    specify the product's usage for the cycle.
    """

    cycle = models.ForeignKey(
        SubscriptionCycle, on_delete=models.CASCADE, related_name="cycleprod_set"
    )
    subprod = models.ForeignKey(
        SubscriptionProduct, on_delete=models.CASCADE, related_name="cycleprod_set"
    )
    usage = models.PositiveIntegerField(
        default=0, help_text=_("Usage attributed to cycle for this product")
    )

    class Meta:
        db_table = "billing_subscription_cycle_product"
        verbose_name = _("Subscription Cycle Product")
        verbose_name_plural = _("Subscription Cycle Product")

    class HandleRef:
        tag = "cycleprod"

    @property
    def price(self):

        """
        price of the product in the subscription cycle
        """

        recurring = self.subprod.prod.recurring
        if recurring.type == "metered":
            price = float(self.usage) * float(recurring.price)
        else:
            price = recurring.price

        # apply modifiers

        for mod in self.subprod.modifier_set.all():
            if mod.is_valid:
                price = mod.apply(price, recurring.price)

        return price

    def __str__(self):
        return f"{self.subprod}"


@reversion.register()
class SubscriptionProductModifier(HandleRefModel):

    """
    Describes a modification for a specific product in a subscription, allowing
    us to make certain products in a subscription reduced in price or free
    entirely.
    """

    subprod = models.ForeignKey(
        SubscriptionProduct, on_delete=models.CASCADE, related_name="modifier_set"
    )
    type = models.CharField(max_length=255, choices=const.BILLING_MODIFIER_TYPES)
    value = models.IntegerField(default=0)
    valid = models.DateTimeField(help_text=_("Valid until"))
    source = models.CharField(
        max_length=255, help_text=_("source of modifier, why was it applied")
    )

    class HandleRef:
        tag = "submod"

    class Meta:
        db_table = "billing_subscription_modifier"
        verbose_name = _("Subscription Price Modifier")
        verbose_name_plural = _("Subscription Price Modifiers")

    @property
    def is_valid(self):
        return timezone.now() < self.valid

    def apply(self, price, unit_price=0):
        """
        applies modifier to a given price and returns the modified
        price
        """
        if self.type == "free":
            return 0

        if self.type == "quantity":
            price -= float(unit_price * self.value)
        elif self.type == "reduction":
            price -= self.value
        elif self.type == "reduction_p":
            price -= price * (self.value / 100.0)

        return max(price, 0)


def unique_id(Model, field):
    i = 0
    while i < 1000:
        unique_id = "{}".format(secrets.token_urlsafe(10))

        if not Model.objects.filter(**{field: unique_id}).exists():
            return unique_id
        i += 1
    raise OSError(f"Could not generate a unique {Model} id")


def unique_order_history_id():
    return unique_id(OrderHistory, "order_id")


def unique_order_id():
    return unique_id(Order, "order_number")


def unique_invoice_id():
    return unique_id(Invoice, "invoice_number")


@reversion.register()
class OrderHistory(HandleRefModel):

    """
    Describes processed orders
    """

    billcon = models.ForeignKey(
        "billing.BillingContact",
        on_delete=models.SET_NULL,
        null=True,
        related_name="order_set",
    )

    chg = models.OneToOneField(
        "billing.PaymentCharge",
        on_delete=models.SET_NULL,
        related_name="order",
        null=True,
    )

    billed_to = models.CharField(
        max_length=255,
        help_text=_(
            "Holds the name of the payment method that was billled for archiving purposes."
        ),
    )

    notes = models.CharField(
        max_length=255, null=True, blank=True, help_text=_("Order specific notes")
    )

    processed = models.DateTimeField(help_text=("When was this order processed"))

    order_id = models.CharField(
        max_length=16, default=unique_order_history_id, unique=True
    )

    class HandleRef:
        tag = "order"

    class Meta:
        db_table = "billing_order_history"
        verbose_name = _("Order History Entry")
        verbose_name_plural = _("Order History Entries")

    @classmethod
    def create_from_chg(cls, chg):
        order = cls(
            chg=chg,
            billcon=chg.pay.billcon,
            billed_to=chg.pay.name,
            processed=datetime.datetime.now(),
            order_id=unique_order_history_id(),
        )
        order.save()

        try:
            for cycleprod in chg.cyclechg.cycle.cycleprod_set.all():
                OrderHistoryItem.objects.create(
                    order=order,
                    cycleprod=cycleprod,
                    description=cycleprod.subprod.prod.description,
                    price=cycleprod.price,
                )

        except SubscriptionCycleCharge.DoesNotExist:
            OrderHistoryItem.objects.create(
                order=order, price=chg.price, description=chg.description
            )

        return order

    @property
    def price(self):
        price = 0
        for orderitem in self.orderitem_set.all():
            price += orderitem.price
        return price

    @property
    def description(self):
        return self.chg.description

    @property
    def organization_name(self):
        try:
            return self.chg.cyclechg.cycle.sub.org.name
        except SubscriptionCycleCharge.DoesNotExist:
            return "-"


@reversion.register()
class OrderHistoryItem(HandleRefModel):

    order = models.ForeignKey(
        OrderHistory, on_delete=models.CASCADE, related_name="orderitem_set"
    )

    cycleprod = models.OneToOneField(
        SubscriptionCycleProduct,
        on_delete=models.SET_NULL,
        related_name="orderitem",
        null=True,
        blank=True,
    )

    description = models.CharField(max_length=255)

    price = models.DecimalField(
        default=0.0, max_digits=6, decimal_places=2, help_text=_("Price charged")
    )

    class HandleRef:
        tag = "orderitem"

    class Meta:
        db_table = "billing_order_history_item"
        verbose_name = _("Order History Item")
        verbose_name_plural = _("Order History Items")


@reversion.register()
class CustomerData(HandleRefModel):
    billcon = models.OneToOneField(
        "billing.BillingContact", on_delete=models.CASCADE, related_name="customer"
    )
    data = JSONField(default=dict, blank=True)

    class HandleRef:
        tag = "cust"

    class Meta:
        db_table = "billing_customer_data"
        verbose_name = _("Customer Data")
        verbose_name_plural = _("Customer Data")

    def __str__(self):
        return f"{self.billcon.name} <{self.billcon.email}> ({self.id})"


@reversion.register()
@grainy_model("billing.contact", related="org")
class BillingContact(HandleRefModel):

    org = models.ForeignKey(
        account.models.Organization,
        on_delete=models.CASCADE,
        related_name="billcon_set",
    )

    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "billing_contact"
        verbose_name = _("Billing Contact")
        verbose_name_plural = _("Billing Contacts")

    class HandleRef:
        tag = "billcon"

    @property
    def active(self):
        for pay in self.pay_set.filter(status="ok"):
            if pay.sub_set.filter(status="ok").exists():
                return True
        return False

    def __str__(self):
        return self.name


@reversion.register()
class PaymentMethod(HandleRefModel):

    """
    Describes a payment option linked to a billing contact
    """

    billcon = models.ForeignKey(
        BillingContact, on_delete=models.CASCADE, related_name="pay_set"
    )
    custom_name = models.CharField(max_length=255, null=True, blank=True)
    processor = models.CharField(max_length=255)
    data = JSONField(default=dict, blank=True)

    holder = models.CharField(max_length=255)
    country = CountryField()
    city = models.CharField(max_length=255)
    address1 = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, null=True, blank=True)
    postal_code = models.CharField(max_length=255)
    state = models.CharField(max_length=255, null=True, blank=True)

    class HandleRef:
        tag = "pay"

    class Meta:
        db_table = "billing_payment_method"
        verbose_name = _("Payment Method")
        verbose_name_plural = _("Payment Methods")

    @classmethod
    def get_for_org(cls, org, status="ok"):
        return cls.objects.filter(billcon__org=org, status=status)

    @property
    def name(self):
        if self.custom_name:
            return f"{self.billcon.name}: {self.custom_name}"

        return f"{self.billcon.name}: {self.processor}-{self.id}"

    @property
    def processor_instance(self):
        processor_cls = billing.payment_processors.PROCESSORS.get(self.processor)
        return processor_cls(self)

    def __str__(self):
        return self.name


@reversion.register()
class PaymentCharge(HandleRefModel):

    pay = models.ForeignKey(
        PaymentMethod, on_delete=models.CASCADE, related_name="chg_set"
    )
    price = models.DecimalField(
        default=0.0,
        max_digits=6,
        decimal_places=2,
        help_text=_("Price attributed to cycle for this product"),
    )
    description = models.CharField(max_length=255, null=True, blank=True)
    data = JSONField(default=dict, blank=True, help_text=_("Any extra data"))

    class Meta:
        db_table = "billing_charge"
        verbose_name = _("Payment Charge")
        verbose_name_plural = _("Payment Charges")

    class HandleRef:
        tag = "chg"

    def __str__(self):
        return f"{self.pay.name} Charge {self.id}"

    @reversion.create_revision()
    def capture(self):
        self.status = "ok"
        self.save()

        OrderHistory.create_from_chg(self)

    @reversion.create_revision()
    def sync_status(self):
        if self.status == "pending":
            self.pay.processor_instance.sync_charge(self)
            if self.status == "ok":
                self.capture()

        return self.status


class Transaction(HandleRefModel):

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="%(class)s_transaction_set",
    )

    # Should this be auto_now_add ? Or is default=now better.
    created = models.DateTimeField(
        help_text=_("When transaction was created."), default=timezone.now
    )
    currency = models.CharField(
        max_length=255, choices=const.CURRENCY_TYPES, default="USD"
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2, blank=False)
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class MoneyTransaction(Transaction):

    billing_contact = models.ForeignKey(
        "billing.BillingContact",
        on_delete=models.CASCADE,
        related_name="%(class)s_money_transaction_set",
        null=True,
    )
    payment_method = models.ForeignKey(
        "billing.PaymentMethod",
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_payment_method",
        help_text=_("User payment option that will be charged by this transaction"),
    )

    payment_processor_txn_id = models.CharField(blank=True, max_length=255)

    class Meta:
        abstract = True


@reversion.register()
class Order(Transaction):
    product = models.ForeignKey(
        "billing.Product", on_delete=models.CASCADE, related_name="order_set", null=True
    )
    subscription = models.ForeignKey(
        "billing.Subscription",
        on_delete=models.CASCADE,
        related_name="order_set",
        null=True,
    )

    description = models.TextField(blank=True)
    order_number = models.CharField(blank=True, max_length=255)

    class HandleRef:
        # Doing ord for now because "order" is taken
        tag = "ord"

    class Meta:
        db_table = "billing_order"
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")


@reversion.register()
class Invoice(Transaction):

    product = models.ForeignKey(
        "billing.Product",
        on_delete=models.CASCADE,
        related_name="invoice_set",
        null=True,
    )
    subscription = models.ForeignKey(
        "billing.Subscription",
        on_delete=models.CASCADE,
        related_name="invoice_set",
        null=True,
    )
    description = models.TextField(blank=True)
    invoice_number = models.CharField(blank=True, max_length=255)

    class HandleRef:
        tag = "invoice"

    class Meta:
        db_table = "billing_invoice"
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")


@reversion.register()
class Payment(MoneyTransaction):

    invoice_number = models.CharField(blank=True, max_length=255)

    class HandleRef:
        tag = "payment"

    class Meta:
        db_table = "billing_payment"
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")


@reversion.register()
class Deposit(MoneyTransaction):
    class HandleRef:
        tag = "deposit"

    class Meta:
        db_table = "billing_deposit"
        verbose_name = _("Deposit")
        verbose_name_plural = _("Deposits")


@reversion.register()
class Withdrawal(MoneyTransaction):
    class HandleRef:
        tag = "withdrawal"

    class Meta:
        db_table = "billing_withdrawal"
        verbose_name = _("Withdrawal")
        verbose_name_plural = _("Withdrawals")


@reversion.register()
class Ledger(models.Model):

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    class HandleRef:
        tag = "ledger"

    class Meta:
        db_table = "billing_ledgers"
        verbose_name = _("Ledger")
        verbose_name_plural = _("Ledgers")
