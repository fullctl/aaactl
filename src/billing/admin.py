from django import forms
from django.contrib import admin
from django.utils.translation import gettext as _
from fullctl.django.admin import BaseAdmin

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
    list_display = ("name", "group", "component", "description", "price", "recurring_product")
    search_fields = ("name", "component", "group")
    readonly_fields = BaseAdmin.readonly_fields + ("recurring_product",)
    inlines = (ProductModifierInline, RecurringProductInline)
    form = ProductForm

    def recurring_product(self, obj):
        if obj.is_recurring_product:
            return _("Yes")
        return _("No")


@admin.register(ProductModifier)
class ProductModifieradmin(BaseAdmin):
    list_display = ("product", "type", "value", "duration", "code")
    search_fields = ("product__name", "code")


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
    fields = ("product",)
    extra = 0


@admin.register(Subscription)
class SubscriptionAdmin(BaseAdmin):
    list_display = ("group", "org", "subscription_cycle", "subscription_cycle_start")
    search_fields = ("group__name", "product__name", "org__name")
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
    list_display = ("subscription", "start", "end", "charged", "organization_name")
    search_fields = ("subscription__product__name", "subscription__org__name", "group__name", "subscription__id")
    inlines = (SubscriptionCycleProductInline, SubscriptionCycleChargeInline)

    def organization_name(self, obj):
        return obj.subscription.org.name


@admin.register(SubscriptionProductModifier)
class SubscriptionProductModifierAdmin(BaseAdmin):
    list_display = ("subscription_product", "type", "value", "valid", "source")
    search_fields = ("subscription_product__name", "subscription_product__subscription__org___name")


class OrderHistoryItemInline(admin.TabularInline):
    model = OrderHistoryItem
    extra = 0
    fields = ("subscription_cycle_product", "description", "price")


@admin.register(OrderHistory)
class OrderHistoryAdmin(BaseAdmin):
    list_display = ("id", "org", "billing_contact", "price", "notes", "processed")
    search_fields = ("billing_contact__name",)
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
    list_display = ("id", "name", "billing_contact", "processor", "status")
    search_fields = ("billing_contact__name",)
    form = PaymentMethodForm


@admin.register(PaymentCharge)
class PaymentChargeAdmin(BaseAdmin):
    list_display = ("id", "pay", "billing_contact", "price", "status", "created", "updated")
    search_fields = ("pay__billing_contact__name",)

    def billing_contact(self, obj):
        return obj.pay.billing_contact


@admin.register(CustomerData)
class CustomerDataAdmin(BaseAdmin):
    list_dispaly = ("id", "billing_contact")
    search_fields = ("billing_contact_name",)


@admin.register(ProductGroup)
class ProductGroupAdmin(BaseAdmin):
    list_display = ("id", "name")


@admin.register(BillingContact)
class BillingContactAdmin(BaseAdmin):
    list_display = ("id", "org", "name", "email", "created")
    search_fields = ("org__name", "name", "email")
