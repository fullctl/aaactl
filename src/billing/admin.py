from django import forms
from django.contrib import admin
from django.urls import path
from django.utils.translation import gettext as _
from fullctl.django.admin import BaseAdmin
from applications.service_bridge import get_client_bridge, get_client_bridge_cls
from django.http import JsonResponse
import billing.product_handlers
from billing.models import (
    BillingContact,
    CustomerData,
    OrderHistory,
    OrderHistoryItem,
    OrganizationProduct,
    OrganizationProductHistory,
    PaymentCharge,
    PaymentMethod,
    Product,
    ProductGroup,
    ProductModifier,
    ProductPermissionGrant,
    RecurringProduct,
    Subscription,
    SubscriptionCycle,
    SubscriptionCycleCharge,
    SubscriptionCycleProduct,
    SubscriptionProduct,
    SubscriptionProductModifier,
)

# Register your models here.
class ChoiceFieldNoValidation(forms.ChoiceField):
    def validate(self, value):
        pass

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


class ProductPermissionGrantInline(admin.StackedInline):
    model = ProductPermissionGrant
    fields = ("managed_permission",)
    extra = 1


@admin.register(Product)
class ProductAdmin(BaseAdmin):
    list_display = (
        "name",
        "group",
        "component",
        "component_billable_entity",
        "description",
        "price",
        "recurring_product",
    )
    search_fields = ("name", "component", "group")
    readonly_fields = BaseAdmin.readonly_fields + ("recurring_product",)
    inlines = (
        ProductModifierInline,
        RecurringProductInline,
        ProductPermissionGrantInline,
    )
    form = ProductForm

    def recurring_product(self, obj):
        if obj.is_recurring_product:
            return _("Yes")
        return _("No")


@admin.register(ProductModifier)
class ProductModifieradmin(BaseAdmin):
    list_display = ("product", "type", "value", "duration", "code")
    search_fields = ("product__name", "code")


@admin.register(OrganizationProduct)
class OrganizationProduct(BaseAdmin):
    list_display = ("org", "product", "subscription", "subscription_product", "component", "component_object", "created", "updated", "expires")
    search_fields = ("product__name", "org__name", "org__slug")
    readonly_fields = ("component_object", "component")
    list_filter = ("product__component__slug",)

    def component_object(self, obj):
        try:
            return obj.subscription_product.component_object_name
        except AttributeError:
            return None

    def component(self, obj):
        try:
            return obj.product.component.slug
        except AttributeError:
            return None

@admin.register(OrganizationProductHistory)
class OrganizationProductHistoryAdmin(BaseAdmin):
    list_display = ("org", "product", "component_object_id", "component_object_name", "created", "updated")
    search_fields = ("product__name", "org__name", "org__slug")
    list_filter = ("product__component__slug",)

class SubscriptionProductModifierInline(admin.TabularInline):
    model = SubscriptionProductModifier
    fields = ("type", "value", "valid", "source")
    extra = 1


class SubscriptionCycleInline(admin.TabularInline):
    model = SubscriptionCycle
    fields = ("start", "end")
    extra = 0

class SubscriptionProductForm(forms.ModelForm):
    component_object_id = ChoiceFieldNoValidation(choices=[])

    class Meta:
        model = SubscriptionProduct
        fields = "__all__"


class SubscriptionProductInline(admin.TabularInline):
    model = SubscriptionProduct
    form = SubscriptionProductForm
    fields = ("product","component", "component_object_id", "component_object_name", "ends_next_cycle")
    readonly_fields =("component", "component_object_name")
    extra = 0

    def has_change_permission(self, request, obj=None):
        # for signals to work correctly, dont allow changes to
        # existing sub - product relationships directly
        #
        # the user is forced to instead delete the existing relationship
        # and add a new one to make a change
        return False



@admin.register(Subscription)
class SubscriptionAdmin(BaseAdmin):
    list_display = ("group", "org", "subscription_cycle", "subscription_cycle_start")
    search_fields = ("group__name", "product__name", "org__name")
    inlines = (
        SubscriptionProductInline,
        SubscriptionCycleInline,
    )


    class Media:
        js = ('billing/admin.js',)  # Include the JavaScript file in Django admin

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('component-entities/', self.admin_site.admin_view(self.load_component_objects), name='ajax_load_component_objects'),
        ]
        return my_urls + urls

    def load_component_objects(self, request):
        """
        This view returns a list of component objects for a given product.
        """
        product_id = request.GET.get('product_id')
        org_id = request.GET.get('org_id')
        product = Product.objects.get(id=product_id)

        bridge = get_client_bridge(product.component.slug, product.component_billable_entity)

        objects = [
            { "id": obj.id, "name": obj.name} for obj in 
            bridge.objects(org=org_id)
        ]

        return JsonResponse(objects, safe=False)

class SubscriptionCycleProductInline(admin.TabularInline):
    model = SubscriptionCycleProduct
    extra = 0


class SubscriptionCycleChargeInline(admin.TabularInline):
    model = SubscriptionCycleCharge
    extra = 0


@admin.register(SubscriptionCycle)
class SubscriptionCycleAdmin(BaseAdmin):
    list_display = ("subscription", "start", "end", "charged", "organization_name")
    search_fields = (
        "subscription__product__name",
        "subscription__org__name",
        "group__name",
        "subscription__id",
    )
    inlines = (SubscriptionCycleProductInline, SubscriptionCycleChargeInline)

    def organization_name(self, obj):
        return obj.subscription.org.name


@admin.register(SubscriptionProductModifier)
class SubscriptionProductModifierAdmin(BaseAdmin):
    list_display = ("subscription_product", "type", "value", "valid", "source")
    search_fields = (
        "subscription_product__name",
        "subscription_product__subscription__org___name",
    )


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
    list_display = (
        "id",
        "payment_method",
        "billing_contact",
        "price",
        "status",
        "created",
        "updated",
    )
    search_fields = ("payment_method__billing_contact__name",)

    def billing_contact(self, obj):
        return obj.payment_method.billing_contact


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
