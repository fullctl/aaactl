from django.contrib.auth import get_user_model
from fullctl.django.rest.decorators import serializer_registry
from fullctl.django.rest.serializers import ModelSerializer
from rest_framework import serializers

import account.models as account_models
import applications.models as application_models
import billing.models as billing_models
from account.rest.serializers import Serializers as AccountSerializers
from oauth2_provider.models import AccessToken

Serializers, register = serializer_registry()


@register
class Service(ModelSerializer):
    products = serializers.SerializerMethodField()
    trial_product_name = serializers.SerializerMethodField()

    org_can_trial = serializers.SerializerMethodField()
    org_has_access = serializers.SerializerMethodField()

    class Meta:
        model = application_models.Service
        fields = [
            "id",
            "name",
            "slug",
            "service_url",
            "api_url",
            "group",
            "logo",
            "trial_product",
            "trial_product_name",
            "products",
            "org_can_trial",
            "org_has_access",
            "always_show_dashboard",
            "cross_promote",
        ]

    def get_products(self, obj):
        return [product.name for product in obj.products_that_grant_access]

    def get_trial_product_name(self, obj):
        if not obj.trial_product_id:
            return None
        return obj.trial_product.name

    def get_org_can_trial(self, obj):
        org = self.context.get("org")
        if not org:
            return None

        if not obj.trial_product_id:
            return False

        return obj.trial_product.can_add_to_org(org)

    def get_org_has_access(self, obj):
        org = self.context.get("org")
        if not org:
            return None

        for org_product in org.products.filter(product__in=obj.products.all()):
            if not org_product.expired:
                return True

        return False


@register
class User(ModelSerializer):
    ref_tag = "user"

    organizations = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "first_name",
            "last_name",
            "username",
            "email",
            "organizations",
            "is_superuser",
            "is_staff",
        ]

    def get_organizations(self, obj):
        return [
            AccountSerializers.org(instance=org.org, context={"user": obj}).data
            for org in obj.org_user_set.all()
        ]


@register
class Impersonation(ModelSerializer):
    ref_tag = "impersonation"

    class Meta:
        model = account_models.Impersonation
        fields = ["id", "superuser", "user"]


@register
class Product(ModelSerializer):
    class Meta:
        model = billing_models.Product
        fields = ["name", "description", "data", "price", "expiry_period", "renewable"]


@register
class OrgnaizationProduct(ModelSerializer):
    name = serializers.SerializerMethodField()
    component = serializers.SerializerMethodField()
    product_data = serializers.SerializerMethodField()

    class Meta:
        model = billing_models.OrganizationProduct
        fields = [
            "org",
            "product",
            "name",
            "component",
            "expires",
            "subscription",
            "product_data",
        ]

    def get_component(self, org_product):
        return org_product.product.component.name.lower()

    def get_name(self, org_product):
        return org_product.product.name

    def get_product_data(self, org_product):
        return org_product.product.data


@register
class ContactMessage(ModelSerializer):
    service_slug = serializers.SerializerMethodField()

    class Meta:
        model = account_models.ContactMessage
        fields = [
            "id",
            "user",
            "name",
            "email",
            "message",
            "type",
            "created",
            "service",
            "service_slug",
        ]

    def get_service_slug(self, obj):
        if not obj.service_id:
            return None
        return obj.service.slug

    def save(self):
        instance = super().save()
        instance.notify()
        return instance

@register
class OauthAccessToken(ModelSerializer):
    expired = serializers.SerializerMethodField()

    ref_tag = "oauth_access_token"

    class Meta:
        model = AccessToken
        fields = ["expires", "expired"]

    def get_expired(self, obj):
        return obj.is_expired()