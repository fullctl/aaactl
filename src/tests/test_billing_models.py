from datetime import datetime, timedelta, timezone

import pytest

from billing.models import (
    OrderHistory,
    SubscriptionCycle,
    SubscriptionCycleProduct,
    SubscriptionProduct,
)


def test_product_group(db, billing_objects):
    assert str(billing_objects.product.group) == "Test Group"
    assert str(billing_objects.product_sub_fixed.group) == "Test Group"
    assert str(billing_objects.product_sub_metered.group) == "Test Group"


def test_recurring_products(db, billing_objects):
    assert billing_objects.product.is_recurring is False
    assert billing_objects.product_sub_fixed.is_recurring is True
    assert billing_objects.product_sub_metered.is_recurring is True


def test_recurring_product_type(db, billing_objects):
    assert billing_objects.product_sub_fixed.recurring.type_description == "Fixed Price"
    assert (
        billing_objects.product_sub_metered.recurring.type_description
        == "Metered Usage"
    )

    # test_product_modifier():
    """
    Test how product modifiers affects price.
    """


def test_subscription_products(db, billing_objects):

    """
    Test adding a product to subscription.
    """
    subscription = billing_objects.monthly_subscription
    product_sub_fixed = billing_objects.product_sub_fixed
    subscription.add_prod(product_sub_fixed)
    assert SubscriptionProduct.objects.filter(sub=subscription).count() == 1


def test_subscription_cycle_start(db, billing_objects):

    """
    Test how cycle is calculated in terms of time.
    """
    subscription = billing_objects.monthly_subscription

    # Test cycle start
    assert subscription.cycle_start is None
    subscription.start_cycle()
    assert subscription.cycle_start == datetime.now(timezone.utc).date()

    # Cannot re-start with active
    with pytest.raises(OSError):
        subscription.start_cycle()


def test_subscription_cycle(db, billing_objects):

    """
    Test how cycle is calculated in terms of time and frequency.
    """
    m_subscription = billing_objects.monthly_subscription

    # Start a cycle two months ago
    two_months_ago = (datetime.now(timezone.utc) - timedelta(days=60)).date()
    m_subscription.start_cycle(two_months_ago)
    assert m_subscription.cycle is None
    assert (
        SubscriptionCycle.objects.first().start.month + 1
        == SubscriptionCycle.objects.first().end.month
    )

    # now start a cycle two weeks ago
    two_weeks_ago = (datetime.now(timezone.utc) - timedelta(days=14)).date()
    m_subscription.start_cycle(two_weeks_ago)
    assert m_subscription.cycle
    assert SubscriptionCycle.objects.count() == 2


def test_end_cycle(db, billing_objects, mocker):

    # Overrides creating the charge on Stripe's end.
    mocker.patch(
        "billing.payment_processors.stripe.stripe.Charge.create",
        return_value={"id": 1234},
    )

    subscription = billing_objects.monthly_subscription
    two_weeks_ago = (datetime.now(timezone.utc) - timedelta(days=14)).date()
    subscription.start_cycle(two_weeks_ago)

    subscription.pay = billing_objects.payment_method
    subscription.save()

    # FIXME - This doesn't seem to be the test we want
    # but currently there is no way to force end a cycle (?)
    with pytest.raises(OSError):
        subscription.end_cycle()


def test_subcycle_charge(db, billing_objects, mocker):
    # Overrides creating the charge on Stripe's end.
    mocker.patch(
        "billing.payment_processors.stripe.stripe.Charge.create",
        return_value={"id": 1234},
    )
    subscription = billing_objects.monthly_subscription
    subscription.pay = billing_objects.payment_method
    two_weeks_ago = (datetime.now(timezone.utc) - timedelta(days=14)).date()
    subscription.start_cycle(two_weeks_ago)
    subcycle = subscription.cycle_set.first()
    subcycle.charge()
    subcycle_charge = subcycle.cyclechg_set.first()
    payment_charge = subcycle_charge.chg

    assert subcycle_charge.cycle == subcycle
    assert payment_charge.price == subcycle.price
    assert payment_charge.description == subscription.charge_description


def test_subcycle_charge_exists(db, billing_objects, mocker):
    # Overrides creating the charge on Stripe's end.
    mocker.patch(
        "billing.payment_processors.stripe.stripe.Charge.create",
        return_value={"id": 1234},
    )
    subscription = billing_objects.monthly_subscription
    subscription.pay = billing_objects.payment_method
    two_weeks_ago = (datetime.now(timezone.utc) - timedelta(days=14)).date()
    subscription.start_cycle(two_weeks_ago)
    subcycle = subscription.cycle_set.first()
    subcycle.charge()

    subcycle_charge = subcycle.cyclechg_set.first()

    # Returns charge if charge is still "pending"
    assert subcycle.charge() == subcycle_charge

    # Now we set status of payment charge from ok to pending
    subcycle_charge = subcycle.cyclechg_set.first()
    payment_charge = subcycle_charge.chg
    payment_charge.status = "ok"
    payment_charge.save()
    subcycle.refresh_from_db()

    # Raises error if we retry an "ok" charge
    with pytest.raises(OSError, match="Cycle was already charged successfully"):
        subcycle.charge()


def test_calc_subscription_charge(db, billing_objects):
    """
    Test how subscription charges are calculated.
    """

    # Create cycle
    subscription = billing_objects.monthly_subscription
    two_months_ago = (datetime.now(timezone.utc) - timedelta(days=60)).date()
    cycle = subscription.start_cycle(two_months_ago)

    # Create product subscriptions

    product_fixed = billing_objects.product_sub_fixed
    subscription.add_prod(product_fixed)
    fixed_subprod = product_fixed.sub_set.first()

    product_metered = billing_objects.product_sub_metered
    subscription.add_prod(product_metered)
    metered_subprod = product_metered.sub_set.first()

    # Create Subscription Cycle Products
    fixed_cycleprod = SubscriptionCycleProduct.objects.create(
        cycle=cycle, subprod=fixed_subprod, usage=1
    )

    assert fixed_cycleprod.price == 125.99

    metered_cycleprod = SubscriptionCycleProduct.objects.create(
        cycle=cycle, subprod=metered_subprod, usage=0
    )

    # Adjust usage
    assert metered_cycleprod.price == 0
    metered_cycleprod.usage = 50
    metered_cycleprod.save()

    assert metered_cycleprod.price == 25

    # Get price for whole cycle
    assert cycle.price == 150.99

    # test_subscription_modifier():
    """
    # Test subscription modifiers.
    """


def test_order_history(db, billing_objects, mocker):
    mocker.patch(
        "billing.payment_processors.stripe.stripe.Charge.create",
        return_value={"id": 1234},
    )
    subscription = billing_objects.monthly_subscription
    subscription.pay = billing_objects.payment_method
    two_weeks_ago = (datetime.now(timezone.utc) - timedelta(days=14)).date()
    subscription.start_cycle(two_weeks_ago)
    subcycle = subscription.cycle_set.first()
    subcycle.charge()

    subcycle_charge = subcycle.cyclechg_set.first()
    payment_charge = subcycle_charge.chg

    order_history = OrderHistory.create_from_chg(payment_charge)
    assert order_history


# test_order_history_create_from_chg():


def test_billing_contact(db, billing_objects):
    billcon = billing_objects.billing_contact
    assert billcon.active is False
