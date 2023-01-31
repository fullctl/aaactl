from rest_framework import serializers
from fullctl.django.rest.decorators import serializer_registry
from fullctl.django.rest.serializers import ModelSerializer

import applications.models as models

Serializers, register = serializer_registry()


@register
class Service(ModelSerializer):

    class Meta:
        model = models.Service
        fields = ["name", "slug", "api_url", "service_url", "logo"]
