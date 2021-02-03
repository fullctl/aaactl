from django import forms
from django.contrib import admin
from django.utils.translation import gettext as _
from django_handleref.admin import VersionAdmin
from reversion.admin import VersionAdmin as ReversionAdmin

import billing.product_handlers
from billing.models import (
    BillingContact,
    CustomerData,
    OrderHistory,
    OrderHistoryItem,
    PaymentCharge,
    PaymentMethod,
    Product,
    ProductGroup,
    ProductModifier,
    RecurringProduct,
    Subscription,
    SubscriptionCycle,
    SubscriptionCycleCharge,
    SubscriptionCycleProduct,
    SubscriptionProduct,
    SubscriptionProductModifier,
)

# Register your models here.


class BaseAdmin(VersionAdmin, ReversionAdmin):
    readonly_fields = ("version",)


class ProductForm(forms.ModelForm):
    pass


class ProductModifierInline(admin.TabularInline):
    model = ProductModifier
    fields = ("type", "value", "duration", "code")
    extra = 0


class RecurringProductInline(admin.StackedInline):
    model = RecurringProduct
    fields = ("type", "price", "unit", "unit_plural", "metered_url", "data")
    extra = 0


@admin.register(Product)
class ProductAdmin(BaseAdmin):
    list_display = ("name", "group", "component", "description", "price", "recurring")
    search_fields = ("name", "component", "group")
    readonly_fields = BaseAdmin.readonly_fields + ("recurring",)
    inlines = (ProductModifierInline, RecurringProductInline)
    form = ProductForm

    def recurring(self, obj):
        if obj.is_recurring:
            return _("Yes")
        return _("No")


@admin.register(ProductModifier)
class ProductModifieradmin(BaseAdmin):
    list_display = ("prod", "type", "value", "duration", "code")
    search_fields = ("prod__name", "code")


class SubscriptionProductModifierInline(admin.TabularInline):
    model = SubscriptionProductModifier
    fields = ("type", "value", "valid", "source")
    extra = 1


class SubscriptionCycleInline(admin.TabularInline):
    model = SubscriptionCycle
    fields = ("start", "end")
    extra = 0


class SubscriptionProductInline(admin.TabularInline):
    model = SubscriptionProduct
    fields = ("prod",)
    extra = 0


@admin.register(Subscription)
class SubscriptionAdmin(BaseAdmin):
    list_display = ("group", "org", "cycle", "cycle_start")
    search_fields = ("group__name", "prod__name", "org__name")
    inlines = (
        SubscriptionProductInline,
        SubscriptionCycleInline,
    )


class SubscriptionCycleProductInline(admin.TabularInline):
    model = SubscriptionCycleProduct
    extra = 0


class SubscriptionCycleChargeInline(admin.TabularInline):
    model = SubscriptionCycleCharge
    extra = 0


@admin.register(SubscriptionCycle)
class SubscriptionCycleAdmin(BaseAdmin):
    list_display = ("sub", "start", "end", "charged", "organization_name")
    search_fields = ("sub__prod__name", "sub__org__name", "group__name", "sub__id")
    inlines = (SubscriptionCycleProductInline, SubscriptionCycleChargeInline)

    def organization_name(self, obj):
        return obj.sub.org.name


@admin.register(SubscriptionProductModifier)
class SubscriptionProductModifierAdmin(BaseAdmin):
    list_display = ("subprod", "type", "value", "valid", "source")
    search_fields = ("subprod__name", "subprod__sub__org___name")


class OrderHistoryItemInline(admin.TabularInline):
    model = OrderHistoryItem
    extra = 0
    fields = ("cycleprod", "description", "price")


@admin.register(OrderHistory)
class OrderHistoryAdmin(BaseAdmin):
    list_display = ("id", "org", "billcon", "price", "notes", "processed")
    search_fields = ("billcon__name",)
    inlines = (OrderHistoryItemInline,)
    readonly_fields = ("org",)

    def org(self, obj):
        return obj.org


class PaymentMethodForm(forms.ModelForm):
    processor = forms.ChoiceField(
        choices=billing.payment_processors.choices(), required=True
    )


@admin.register(PaymentMethod)
class PaymentMethodAdmin(BaseAdmin):
    list_display = ("id", "name", "billcon", "processor", "status")
    search_fields = ("billcon__name",)
    form = PaymentMethodForm


@admin.register(PaymentCharge)
class PaymentChargeAdmin(BaseAdmin):
    list_display = ("id", "pay", "billcon", "price", "status", "created", "updated")
    search_fields = ("pay__billcon__name",)

    def billcon(self, obj):
        return obj.pay.billcon


@admin.register(CustomerData)
class CustomerDataAdmin(BaseAdmin):
    list_dispaly = ("id", "billcon")
    search_fields = ("billcon_name",)


@admin.register(ProductGroup)
class ProductGroupAdmin(BaseAdmin):
    list_display = ("id", "name")


@admin.register(BillingContact)
class BillingContactAdmin(BaseAdmin):
    list_display = ("id", "org", "name", "email", "created")
    search_fields = ("org__name", "name", "email")
