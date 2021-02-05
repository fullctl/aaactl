"""
Payment processor interface
"""

import reversion
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse

MAP = {}


def register(cls):
    MAP[cls.id] = cls
    print("MAP UPDATED", MAP)
    return cls


def get_processor(_id):
    return MAP[_id]


class PaymentProcessor(object):
    id = "_processor"
    name = "Payment Processor Interface"

    @property
    def agreement_cancel_url(self):
        return "{}{}".format(
            settings.HOST_URL, reverse("billing:agreement-cancel", args=(self.id,))
        )

    @property
    def agreement_success_url(self):
        return "{}{}".format(
            settings.HOST_URL, reverse("billing:agreement-success", args=(self.id,))
        )

    @property
    def default_currency(self):
        return settings.BILLING_DEFAULT_CURRENCY

    @property
    def agreement_name(self):
        return settings.BILLING_AGREEMENT_NAME

    @property
    def agreement_description(self):
        return settings.BILLING_AGREEMENT_DESCRIPTION

    @property
    def billcon(self):
        return self.payment_method.billcon

    @property
    def billcon_customer(self):
        try:
            return self.payment_method.billcon.customer
        except ObjectDoesNotExist:
            from billing.models import CustomerData

            customer, created = CustomerData.objects.get_or_create(billcon=self.billcon)
            return customer

    @property
    def data(self):
        return self.payment_method.data

    def __init__(self, payment_method, **kwargs):
        self.load(payment_method)

    def load(self, payment_method):
        self.payment_method = payment_method

    def save(self):
        self.payment_method.save()
        self.billcon_customer.save()

    @reversion.create_revision()
    def sync_charge(self, chg):
        if chg.status == "pending":
            return self._sync_charge(chg)
        return chg.status

    def _sync_charge(self, chg, status=None):
        if status:
            chg.status = status
            chg.save()

            try:
                chg.cyclechg.status = status
                chg.cyclechg.save()
            except ObjectDoesNotExist:
                pass

        return status
