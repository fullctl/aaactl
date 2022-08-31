from django.contrib.auth import get_user_model

from fullctl.django.rest.decorators import serializer_registry
from fullctl.django.rest.serializers import ModelSerializer

import applications.models as application_models

from rest_framework import serializers

from account.rest.serializers import Serializers as AccountSerializers

Serializers, register = serializer_registry()


@register
class Service(ModelSerializer):
    class Meta:
        model = application_models.Service
        fields = ["id", "name", "slug", "service_url", "api_url", "group", "logo"]

@register
class User(ModelSerializer):
    ref_tag = "user"

    organizations = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ["id", "first_name", "last_name", "username", "email", "organizations", "is_superuser", "is_staff"]

    def get_organizations(self, obj):
        return [
            AccountSerializers.org(instance=org.org, context={"user": obj}).data
            for org in obj.org_user_set.all()
        ]
