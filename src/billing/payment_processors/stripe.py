import reversion
import stripe
from django import forms
from django.conf import settings
from django.utils.translation import gettext as _

from billing.payment_processors.processor import PaymentProcessor
stripe.api_key = settings.STRIPE_SECRET_KEY

def payment_method_name(stripe_payment_method_id):

    """
    Returns the name of a stripe payment method based on the type

    Currently supports card and us_bank_account
    """

    stripe_pm = stripe.PaymentMethod.retrieve(stripe_payment_method_id)

    if stripe_pm.type == "card":
        pm_name = stripe_pm.card.brand + " " + stripe_pm.card.last4
    elif stripe_pm.type == "us_bank_account":
        pm_name = stripe_pm.us_bank_account.bank_name + " " + stripe_pm.us_bank_account.last4
    else:
        pm_name = None

    return pm_name


class Stripe(PaymentProcessor):
    id = "stripe"
    name = _("Stripe")

    class Form(forms.Form):
        client_secret = forms.CharField(widget=forms.HiddenInput())
        setup_intent_id = forms.CharField(widget=forms.HiddenInput())

        @property
        def template(self):
            return "billing/setup/stripe-elements.html"

    @property
    def source(self):
        return self.data.get("stripe_payment_method", self.data.get("stripe_card"))

    @property
    def customer(self):
        return self.billing_contact_customer.data.get("stripe_customer")

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
            description=f"billing_contact{self.payment_method.billing_contact.id}",
            name=self.payment_method.billing_contact.name,
            email=self.payment_method.billing_contact.email,
            api_key=self.api_key,
        )

        self.billing_contact_customer.data["stripe_customer"] = customer["id"]
        self.save()

        return customer["id"]

    def setup_card(self, token):
        # DEPRECATED
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

    def setup_unconfirmed_payment_method(self, client_secret, setup_intent_id):

        self.setup_customer()

        self.payment_method.status = "unconfirmed"

        self.data["stripe_setup_intent"] = setup_intent_id
        self.data["stripe_client_secret"] = client_secret

        self.save()

    def link_customer(self):

        stripe.PaymentMethod.attach(
            self.source,
            customer=self.customer,
        )



    @reversion.create_revision()
    def setup_billing(self, **kwargs):
        if self.source:
            self.payment_method.status = "ok"
            self.save()
            return
        self.setup_unconfirmed_payment_method(**kwargs)

    @reversion.create_revision()
    def charge(self, payment_charge):
        if not self.source:
            raise ValueError("Payment method not setup.")

        payment_intent = None
        charge = None

        try:
            if self.source.startswith("pm_"):
                payment_intent = stripe.PaymentIntent.create(
                    amount=int(payment_charge.price * 100),
                    currency=self.default_currency,
                    description=payment_charge.details,
                    customer=self.customer,
                    payment_method=self.source,
                    confirm=True,
                    automatic_payment_methods={"enabled": True, "allow_redirects":"never"},
                    api_key=self.api_key,
                )
                self.log.info("stripe payment intent", status="ok", payment_intent=payment_intent)
            
            else:
            
                # Legacy charge. This should be removed once all customers have been migrated to payment intents

                charge = stripe.Charge.create(
                    customer=self.customer,
                    source=self.source,
                    amount=int(payment_charge.price * 100),
                    description=payment_charge.details,
                    api_key=self.api_key,
                    currency=self.default_currency,
                )
                self.log.info("stripe charge", status="ok", payment_charge=payment_charge)

        except Exception as e:
            # failed to charge on the stripe end, log the error
            # and mark the charge as failed
            payment_charge.status = "failed"
            payment_charge.data["processor_failure"] = str(e)
            payment_charge.save()
            self.log.error(
                "stripe charge", status="failed", payment_charge=payment_charge, error=e
            )
            return

        payment_charge.status = "pending"

        if self.source.startswith("pm_"):
            payment_charge.data["stripe_payment_intent"] = payment_intent["id"]
            payment_charge.data["processor_txn_id"] = payment_intent["id"]
        else:
            payment_charge.data["stripe_charge"] = charge["id"]
            payment_charge.data["processor_txn_id"] = charge["id"]
            payment_charge.data["receipt_url"] = charge["receipt_url"]
        payment_charge.save()

    def _sync_charge(self, payment_charge, status=None):
        reversion.set_comment("Stripe charge status sync")

        if not payment_charge.data.get("stripe_charge"):
            return super()._sync_charge(payment_charge, "failed")

        charge = stripe.Charge.retrieve(
            payment_charge.data["stripe_charge"], api_key=self.api_key
        )

        if charge["status"] == "succeeded":
            return super()._sync_charge(payment_charge, "ok")

        elif charge["status"] == "failed":
            return super()._sync_charge(payment_charge, "failed")

    def _sync_invoice(self, invoice, **kwargs):
        reversion.set_comment("Stripe invoice status sync")

        if not invoice.data.get("stripe_invoice"):
            return super()._sync_invoice(invoice, "failed")

        stripe_invoice = stripe.Invoice.retrieve(
            invoice.data["stripe_invoice"], api_key=self.api_key
        )

        if not stripe_invoice["charge"]:
            return

        stripe_charge = stripe.Charge.retrieve(
            stripe_invoice["charge"], api_key=self.api_key
        )

        if stripe_invoice["status"] == "paid":
            invoice.data["stripe_charge"] = stripe_charge

            return super()._sync_invoice(invoice, "ok")

        elif stripe_invoice["status"] == "uncollectible":
            return super()._sync_invoice(invoice, "failed")

    def create_invoice(self, invoice, charge_automatically=False):
        """
        Creates a strip invoice from a aaactl Invoice instance
        """

        # if the invoice has already been created raise ValueError

        if invoice.data.get("stripe_invoice"):
            raise ValueError("Stripe invoice already created")

        for invoice_line in invoice.invoice_line_set.all():
            stripe.InvoiceItem.create(
                customer=self.customer,
                amount=int(invoice_line.amount * 100),
                currency=invoice_line.currency,
                description=invoice_line.description,
                api_key=self.api_key,
            )

        stripe_invoice = stripe.Invoice.create(
            customer=self.customer,
            days_until_due=30,
            api_key=self.api_key,
            description="FullCtl Invoice",
            collection_method="charge_automatically"
            if charge_automatically
            else "send_invoice",
        )

        stripe.Invoice.finalize_invoice(
            stripe_invoice["id"],
            api_key=self.api_key,
        )

        invoice.data["stripe_invoice"] = stripe_invoice["id"]
        invoice.save()

        return stripe_invoice
