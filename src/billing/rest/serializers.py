import reversion
from django.utils.translation import gettext as _
from rest_framework import serializers

import billing.forms as forms
import billing.models as models
import billing.payment_processors as processors
from account.rest.serializers import FormValidationMixin


class Serializers:
    pass


HANDLEREF_FIELDS = ["id", "status", "created", "updated"]


def register(cls):
    if not hasattr(cls, "ref_tag"):
        cls.ref_tag = cls.Meta.model.HandleRef.tag
        cls.Meta.fields += HANDLEREF_FIELDS
    setattr(Serializers, cls.ref_tag, cls)
    return cls


@register
class Product(serializers.ModelSerializer):
    class Meta:
        model = models.Product

        fields = ["name", "component", "description", "group", "price"]


@register
class RecurringProduct(serializers.ModelSerializer):

    product = Product(read_only=True)

    class Meta:
        model = models.RecurringProduct

        fields = ["product", "type", "price", "unit"]


@register
class PaymentMethod(serializers.ModelSerializer):

    country = serializers.CharField()

    class Meta:
        model = models.PaymentMethod
        fields = [
            "billing_contact",
            "custom_name",
            "holder",
            "country",
            "city",
            "address1",
            "address2",
            "postal_code",
            "state",
        ]


@register
class BillingContact(FormValidationMixin, serializers.ModelSerializer):

    form = forms.BillingContactForm
    required_context = []

    class Meta:
        model = models.BillingContact
        fields = ["name", "email"]


@register
class OrderHistory(serializers.ModelSerializer):

    items = serializers.SerializerMethodField()
    billing_contact = BillingContact()

    class Meta:
        model = models.OrderHistory
        fields = [
            "order_id",
            "description",
            "price",
            "processed",
            "items",
            "billing_contact",
        ]

    def get_items(self, order_history):
        return [
            {"description": item.description, "price": item.price}
            for item in order_history.orderitem_set.all()
        ]


@register
class Subscription(serializers.ModelSerializer):

    recurring_product = RecurringProduct(read_only=True)
    items = serializers.SerializerMethodField()
    subscription_cycle = serializers.SerializerMethodField()
    name = serializers.CharField(read_only=True, source="group.name")

    class Meta:
        model = models.Subscription
        fields = [
            "name",
            "recurring_product",
            "org",
            "subscription_cycle_interval",
            "subscription_cycle",
            "payment_method",
            "items",
        ]

    def get_subscription_cycle(self, subscription):
        if not subscription.subscription_cycle:
            return None
        return {
            "start": subscription.subscription_cycle.start,
            "end": subscription.subscription_cycle.end,
        }

    def get_items(self, subscription):
        if not subscription.subscription_cycle:
            return []
        return [
            {
                "description": subscription_product.product.description,
                "type": subscription_product.product.recurring_product.type_description,
                "usage": subscription_product.subscription_cycle_usage,
                "cost": subscription_product.subscription_cycle_cost,
                "name": subscription_product.product.name,
                "unit_name": subscription_product.product.recurring_product.unit,
                "unit_name_plural": subscription_product.product.recurring_product.unit_plural,
            }
            for subscription_product in subscription.subscriptionproduct_set.all()
        ]


@register
class BillingSetup(serializers.Serializer):
    ref_tag = "setup"

    required_billing_address_fields = [
        "holder",
        "city",
        "country",
        "address1",
        "postal_code",
    ]

    # Setup init data (forms.BillingSetupInitForm)

    product = serializers.CharField(required=False)
    redirect = serializers.CharField(required=False, allow_blank=True)

    # Payment option (forms.SelectPaymentMethodForm)

    payment_method = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )

    # Billing address (forms.BillingAddressForm)
    # Only needed when a new payment option is being created

    holder = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    state = serializers.CharField(required=False, allow_blank=True)
    address1 = serializers.CharField(required=False, allow_blank=True)
    address2 = serializers.CharField(required=False, allow_blank=True)
    postal_code = serializers.CharField(required=False, allow_blank=True)

    # agreements

    agreement_tos = serializers.BooleanField(required=True)

    def validate_product(self, value):
        try:
            return models.Product.objects.get(name=value)
        except models.Product.DoesNotExist:
            raise serializers.ValidationError("Unknown product")

    def validate_payment_method(self, value):
        org = self.context.get("org")
        if not value:
            return 0
        try:
            return models.PaymentMethod.objects.get(id=value, billing_contact__org=org)
        except models.PaymentMethod.DoesNotExist:
            raise serializers.ValidationError("Payment method not found")

    def validate(self, data):
        org = self.context.get("org")
        if not data.get("payment_method"):
            field_errors = {}
            for field in self.required_billing_address_fields:
                if not data.get(field):
                    field_errors[field] = _("Input required")
            if field_errors:
                raise serializers.ValidationError(field_errors)
            billing_contact, created = models.BillingContact.objects.get_or_create(
                org=org, name=data.get("holder"), email=data.get("email"), status="ok"
            )
            data["payment_method"] = models.PaymentMethod(
                billing_contact=billing_contact
            )

        processor = data["processor"] = processors.default()(data["payment_method"])

        if not data["payment_method"].id and processor.Form:
            form = processor.Form(self.context.get("data"))
            if not form.is_valid():
                raise serializers.ValidationError(form.errors)
            data["processor_data"] = form.cleaned_data
        else:
            data["processor_data"] = {}

        return data

    @reversion.create_revision()
    def save(self):
        data = self.validated_data

        payment_method_method = data["payment_method"]
        processor = data["processor"]
        product = data.get("product")
        user = self.context.get("user")
        org = self.context.get("org")

        reversion.set_user(user)
        reversion.set_comment("Billing setup completed")

        if not payment_method_method.id:
            payment_method_method.processor = processor.id
            for field in self.required_billing_address_fields:
                setattr(payment_method_method, field, data.get(field))
            payment_method_method.save()

        if product and product.is_recurring_product:
            subscription = models.Subscription.get_or_create(
                org,
                product.group,
                # TODO: allow to specify?
                "month",
            )
            subscription.payment_method = payment_method_method
            subscription.save()

            if not subscription.subscription_cycle:
                subscription.start_subscription_cycle()

            if not subscription.subscriptionproduct_set.filter(product=product).exists():
                subscription.add_product(product)

        models.Subscription.set_payment_method(org, payment_method_method)

        processor.setup_billing(**data.get("processor_data"))
