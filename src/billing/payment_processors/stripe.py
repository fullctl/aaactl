import reversion
import stripe
from django import forms
from django.conf import settings
from django.utils.translation import gettext as _

from billing.payment_processors.processor import PaymentProcessor


class Stripe(PaymentProcessor):
    id = "stripe"
    name = _("Stripe")

    class Form(forms.Form):

        stripe_token = forms.CharField(widget=forms.HiddenInput())

        @property
        def template(self):
            return "billing/setup/stripe.html"

    @property
    def source(self):
        return self.data.get("stripe_card")

    @property
    def customer(self):
        return self.billcon_customer.data.get("stripe_customer")

    @property
    def form(self):
        return self.Form()

    @classmethod
    def public_key(self):
        return settings.STRIPE_PUBLIC_KEY

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.api_key = settings.STRIPE_SECRET_KEY

    def setup_customer(self):

        # check if customer has already been created
        # on stripe's end

        if self.customer:
            return self.customer

        customer = stripe.Customer.create(
            description=f"billcon{self.payment_method.billcon.id}",
            api_key=self.api_key,
        )

        self.billcon_customer.data["stripe_customer"] = customer["id"]
        self.save()

        return customer["id"]

    def setup_card(self, token):

        if self.data.get("stripe_card"):
            return self.data["stripe_card"]

        self.setup_customer()

        card = stripe.Customer.create_source(
            self.customer, source=token, api_key=self.api_key
        )

        self.data["stripe_card"] = card["id"]
        self.payment_method.custom_name = "Credit Card {}".format(card["last4"])
        self.payment_method.status = "ok"
        self.save()

        details = self.payment_method

        stripe.Customer.modify_source(
            self.customer,
            card["id"],
            address_city=details.city,
            address_country=details.country,
            address_zip=details.postal_code,
            address_line1=details.address1,
            address_line2=details.address2,
            address_state=details.state,
            name=details.holder,
            api_key=self.api_key,
        )

        return card["id"]

    @reversion.create_revision()
    def setup_billing(self, **kwargs):
        if self.source:
            self.payment_method.status = "ok"
            self.save()
            return
        self.setup_card(kwargs.pop("stripe_token"), **kwargs)

    @reversion.create_revision()
    def charge(self, chg):
        if not self.source:
            raise ValueError("Payment method not setup.")

        charge = stripe.Charge.create(
            customer=self.customer,
            source=self.source,
            amount=int(chg.price * 100),
            description=chg.description,
            api_key=self.api_key,
            currency=self.default_currency,
        )

        chg.status = "pending"

        chg.data["stripe_charge"] = charge["id"]
        chg.save()

    def _sync_charge(self, chg, status=None):

        reversion.set_comment("Stripe charge status sync")

        if not chg.data.get("stripe_charge"):
            return super()._sync_charge(chg, "failed")

        charge = stripe.Charge.retrieve(chg.data["stripe_charge"], api_key=self.api_key)

        if charge["status"] == "succeeded":
            return super()._sync_charge(chg, "ok")

        elif charge["status"] == "failed":
            return super()._sync_charge(chg, "failed")
