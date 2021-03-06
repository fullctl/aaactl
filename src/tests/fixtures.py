from __future__ import print_function

import pytest
from django.test import Client


class BillingObjects(object):
    def __init__(self, handle="test"):
        from django.contrib.auth import get_user_model
        from rest_framework.test import APIClient

        from account.models import Organization
        from billing.models import (
            BillingContact,
            PaymentMethod,
            Product,
            ProductGroup,
            ProductModifier,
            RecurringProduct,
            Subscription,
        )

        self.product_group = ProductGroup.objects.create(
            name="Test Group",
        )

        self.other_product_group = ProductGroup.objects.create(
            name="Other Group",
        )

        self.product = Product.objects.create(
            name="test",
            description="test product",
            group=self.product_group,
            price=10.00,
            data={"foo": "bar"},
        )

        self.product_sub_fixed = Product.objects.create(
            name="test.sub.fixed",
            description="test product: fixed subscription",
            group=self.product_group,
            price=0.00,
            data={"foo": "bar"},
        )

        RecurringProduct.objects.create(
            prod=self.product_sub_fixed, type="fixed", price=125.99, data={"foo": "bar"}
        )

        self.product_sub_metered = Product.objects.create(
            name="test.sub.metered",
            description="test product: metered subscription",
            group=self.product_group,
            price=0.00,
            data={"foo": "bar"},
        )

        RecurringProduct.objects.create(
            prod=self.product_sub_metered,
            type="metered",
            price=0.50,
            data={"foo": "bar"},
        )

        ProductModifier.objects.create(
            prod=self.product,
            type="reduction",
            value=10,
            duration=30,
            code="TESTREDUCTION",
        )

        ProductModifier.objects.create(
            prod=self.product,
            type="quantity",
            value=2,
            duration=30,
            code="TESTQUANTITY",
        )

        self.org = Organization.objects.create(name="Subscription Org", slug="sub_org")

        self.monthly_subscription = Subscription.objects.create(
            org=self.org,
            group=self.product_group,
            cycle_interval="month",
            cycle_start=None,  # Set none to start
            pay=None,  # Set none to start
        )

        self.monthly_subscription.add_prod(self.product_sub_metered)

        self.yearly_subscription = Subscription.objects.create(
            org=self.org,
            group=self.product_group,
            cycle_interval="year",
            cycle_start=None,  # Set none to start
            pay=None,  # Set none to start
        )

        self.yearly_subscription.add_prod(self.product_sub_metered)

        self.billing_contact = BillingContact.objects.create(
            org=self.org, name="William Contact", email="billcon@localhost"
        )

        self.payment_method = PaymentMethod.objects.create(
            billcon=self.billing_contact,
            custom_name="Test Customer",
            processor="stripe",
            holder="William Contact",
            country="US",
            city="Chicago",
            address1="3400 Test Ave",
            postal_code="60600",
            state="IL",
            data={"stripe_card": "5200828282828210"},
        )

        self.user = get_user_model().objects.create_user(
            username="user_{}".format(handle),
            email="{}@localhost".format(handle),
            password="test",
        )
        self.org.add_user(self.user, perms="crud")

        self.api_client = APIClient()
        self.api_client.login(username=self.user.username, password="test")

        self.client = Client()
        self.client.login(username=self.user.username, password="test")


class AccountObjects(object):
    def __init__(self, handle):
        from django.contrib.auth import get_user_model
        from django_grainy.util import Permissions
        from rest_framework.test import APIClient

        from account.models import Organization

        self.user = user = get_user_model().objects.create_user(
            username="user_{}".format(handle),
            email="{}@localhost".format(handle),
            password="test",
        )

        self.api_key = user.key_set.first()

        personal_org = user.personal_org

        personal_org.name = "PersonalOrg{}".format(handle)
        personal_org.slug = "personalorg{}".format(handle)
        personal_org.save()

        self.org = org = Organization.objects.create(name=handle, slug=handle)
        org.add_user(user, perms="crud")

        self.other_org = Organization.objects.create(
            name="Other {}".format(handle), slug="other-{}".format(handle)
        )

        self.user_unpermissioned = (
            user_unpermissioned
        ) = get_user_model().objects.create_user(
            username="user_{}_unperm".format(handle),
            email="{}_unperm@localhost".format(handle),
            password="test",
        )

        org.add_user(user_unpermissioned, perms="r")

        self.api_client = APIClient()
        self.api_client.login(username=user.username, password="test")

        self.api_client_unperm = APIClient()
        self.api_client_unperm.login(
            username=user_unpermissioned.username, password="test"
        )

        self.api_client_anon = APIClient()

        self.client = Client()
        self.client.login(username=user.username, password="test")

        self.client_anon = Client()

        self.perms = Permissions(user)


def make_account_objects(handle="test"):
    return AccountObjects(handle)


def make_billing_objects():
    return BillingObjects()


@pytest.fixture
def client_anon():
    return Client()


@pytest.fixture
def api_client_anon():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def account_objects():
    return make_account_objects()


@pytest.fixture
def billing_objects():
    return make_billing_objects()


@pytest.fixture
def account_objects_b():
    return make_account_objects("test_b")


@pytest.fixture
def charge_objects(billing_objects, mocker):
    from datetime import datetime, timedelta, timezone

    from billing.models import OrderHistory, SubscriptionCycleProduct

    mocker.patch(
        "billing.payment_processors.stripe.stripe.Charge.create",
        return_value={"id": 1234},
    )
    subscription = billing_objects.monthly_subscription

    product_fixed = billing_objects.product_sub_fixed
    subscription.add_prod(product_fixed)
    fixed_subprod = product_fixed.sub_set.first()

    subscription.pay = billing_objects.payment_method
    two_weeks_ago = (datetime.now(timezone.utc) - timedelta(days=14)).date()
    subscription.start_cycle(two_weeks_ago)
    subcycle = subscription.cycle_set.first()

    SubscriptionCycleProduct.objects.create(
        cycle=subcycle, subprod=fixed_subprod, usage=1
    )

    subcycle.charge()

    subcycle_charge = subcycle.cyclechg_set.first()
    payment_charge = subcycle_charge.chg

    order_history = OrderHistory.create_from_chg(payment_charge)

    return {
        "subscription": subscription,
        "subcycle": subcycle,
        "subcycle_charge": subcycle_charge,
        "payment_charge": payment_charge,
        "order_history": order_history,
    }


def create_transaction_data(billing_objects):
    return {
        "user": billing_objects.user,
        "amount": 1200.99,
    }


def create_money_transaction_data(billing_objects):
    return {
        "user": billing_objects.user,
        "amount": 1200.99,
        "billing_contact": billing_objects.billing_contact,
        "payment_method": billing_objects.payment_method,
    }


@pytest.fixture
def order(billing_objects):
    from billing.models import Order

    data = create_transaction_data(billing_objects)
    data.update(
        {
            "product": billing_objects.product,
            "description": "This product is helpful",
            "order_number": 132,
        }
    )
    order = Order.objects.create(**data)
    return order


@pytest.fixture
def invoice(billing_objects):
    from billing.models import Invoice

    data = create_transaction_data(billing_objects)
    data.update(
        {
            "subscription": billing_objects.monthly_subscription,
            "description": "This subscription is helpful",
            "invoice_number": 312,
        }
    )
    invoice = Invoice.objects.create(**data)
    return invoice


@pytest.fixture
def payment(billing_objects):
    from billing.models import Payment

    data = create_money_transaction_data(billing_objects)
    data.update({"invoice_number": 1231})
    payment = Payment.objects.create(**data)
    return payment


@pytest.fixture
def deposit(billing_objects):
    from billing.models import Deposit

    data = create_money_transaction_data(billing_objects)
    deposit = Deposit.objects.create(**data)
    return deposit


@pytest.fixture
def withdrawal(billing_objects):
    from billing.models import Withdrawal

    data = create_money_transaction_data(billing_objects)
    withdrawal = Withdrawal.objects.create(**data)
    return withdrawal


@pytest.fixture
def ledger(withdrawal, order, invoice):
    import billing.models

    withdrawal = billing.models.Ledger(content_object=withdrawal).save()
    order = billing.models.Ledger(content_object=order).save()
    invoice = billing.models.Ledger(content_object=invoice).save()
    return [withdrawal, order, invoice]
