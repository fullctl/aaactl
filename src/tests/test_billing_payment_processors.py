import pytest
from django.conf import settings

import billing.payment_processors as bpp
from billing import models


def test_processor_default():
    assert bpp.default() == bpp.stripe.Stripe


@pytest.mark.django_db
def test_payment_processor_interface(billing_objects):
    payment_processor = bpp.processor.PaymentProcessor(billing_objects.payment_method)
    assert payment_processor.data == {"stripe_card": "5200828282828210"}
    assert payment_processor.billcon_customer.billcon == billing_objects.billing_contact


@pytest.mark.django_db
def test_stripe_processor(billing_objects):
    stripe = bpp.stripe.Stripe(billing_objects.payment_method)
    assert "stripe_token" in stripe.form.fields
    assert stripe.customer is None
    assert stripe.source == "5200828282828210"
    assert stripe.public_key() == settings.STRIPE_PUBLIC_KEY


@pytest.mark.django_db
def test_stripe_setup_customer(billing_objects, mocker):
    mocker.patch(
        "billing.payment_processors.stripe.stripe.Customer.create",
        return_value={"id": 1234},
    )
    stripe = bpp.stripe.Stripe(billing_objects.payment_method)
    assert stripe.customer is None
    stripe.setup_customer()
    assert stripe.customer == 1234


@pytest.mark.django_db
def test_stripe_charge_invalid(billing_objects):
    billing_objects.payment_method.data = {}
    billing_objects.payment_method.save()
    stripe = bpp.stripe.Stripe(billing_objects.payment_method)
    with pytest.raises(ValueError, match="Payment method not setup."):
        stripe.charge({})


@pytest.mark.django_db
def test_stripe_setup_card(billing_objects, mocker):
    last_4 = billing_objects.payment_method.data["stripe_card"][-4:]
    billing_objects.payment_method.data = {}
    billing_objects.payment_method.save()

    mocker.patch(
        "billing.payment_processors.stripe.stripe.Customer.create",
        return_value={"id": 1234},
    )
    mocker.patch(
        "billing.payment_processors.stripe.stripe.Customer.create_source",
        return_value={"id": 2345, "last4": last_4},
    )
    mocker.patch(
        "billing.payment_processors.stripe.stripe.Customer.modify_source",
        return_value=None,
    )
    stripe = bpp.stripe.Stripe(billing_objects.payment_method)
    card_id = stripe.setup_card("token")
    assert card_id == 2345
    assert stripe.data["stripe_card"] == 2345
    assert stripe.payment_method.custom_name == "Credit Card " + str(last_4)
    assert stripe.payment_method.status == "ok"


@pytest.mark.django_db
def test_stripe_sync_charge_success(billing_objects, mocker):
    stripe = bpp.stripe.Stripe(billing_objects.payment_method)
    chg = models.PaymentCharge.objects.create(
        pay=billing_objects.payment_method,
        price=100,
        description="Test payment",
        status="pending",
        data={"stripe_charge": 1234},
    )
    mocker.patch(
        "billing.payment_processors.stripe.stripe.Charge.retrieve",
        return_value={"status": "succeeded"},
    )
    stripe.sync_charge(chg)
    assert chg.status == "ok"
