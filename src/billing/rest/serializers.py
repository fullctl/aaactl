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

    prod = Product(read_only=True)

    class Meta:
        model = models.RecurringProduct

        fields = ["prod", "type", "price", "unit"]


@register
class PaymentMethod(serializers.ModelSerializer):

    country = serializers.CharField()

    class Meta:
        model = models.PaymentMethod
        fields = [
            "billcon",
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
    billcon = BillingContact()

    class Meta:
        model = models.OrderHistory
        fields = ["order_id", "description", "price", "processed", "items", "billcon"]

    def get_items(self, order_history):
        return [
            {"description": item.description, "price": item.price}
            for item in order_history.orderitem_set.all()
        ]


@register
class Subscription(serializers.ModelSerializer):

    recurring = RecurringProduct(read_only=True)
    items = serializers.SerializerMethodField()
    cycle = serializers.SerializerMethodField()
    name = serializers.CharField(read_only=True, source="group.name")

    class Meta:
        model = models.Subscription
        fields = [
            "name",
            "recurring",
            "org",
            "cycle_interval",
            "cycle",
            "pay",
            "items",
        ]

    def get_cycle(self, sub):
        if not sub.cycle:
            return None
        return {
            "start": sub.cycle.start,
            "end": sub.cycle.end,
        }

    def get_items(self, sub):
        if not sub.cycle:
            return []
        return [
            {
                "description": subprod.prod.description,
                "type": subprod.prod.recurring.type_description,
                "usage": subprod.cycle_usage,
                "cost": subprod.cycle_cost,
                "name": subprod.prod.name,
                "unit_name": subprod.prod.recurring.unit,
                "unit_name_plural": subprod.prod.recurring.unit_plural,
            }
            for subprod in sub.subprod_set.all()
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

    prod = serializers.CharField(required=False)
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

    def validate_prod(self, value):
        try:
            return models.Product.objects.get(name=value)
        except models.Product.DoesNotExist:
            raise serializers.ValidationError("Unknown product")

    def validate_payment_method(self, value):
        org = self.context.get("org")
        if not value:
            return 0
        try:
            return models.PaymentMethod.objects.get(id=value, billcon__org=org)
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
            billcon, created = models.BillingContact.objects.get_or_create(
                org=org, name=data.get("holder"), email=data.get("email"), status="ok"
            )
            data["payment_method"] = models.PaymentMethod(billcon=billcon)

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

        pay_method = data["payment_method"]
        processor = data["processor"]
        prod = data.get("prod")
        user = self.context.get("user")
        org = self.context.get("org")

        reversion.set_user(user)
        reversion.set_comment("Billing setup completed")

        if not pay_method.id:
            pay_method.processor = processor.id
            for field in self.required_billing_address_fields:
                setattr(pay_method, field, data.get(field))
            pay_method.save()

        if prod and prod.is_recurring:
            sub = models.Subscription.get_or_create(
                org,
                prod.group,
                # TODO: allow to specify?
                "month",
            )
            sub.pay = pay_method
            sub.save()

            if not sub.cycle:
                sub.start_cycle()

            if not sub.subprod_set.filter(prod=prod).exists():
                sub.add_prod(prod)

        models.Subscription.set_payment_method(org, pay_method)

        processor.setup_billing(**data.get("processor_data"))
